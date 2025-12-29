# crawlerd_web/api/projects.py
import sqlite3
import traceback
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Form
from typing import List
from pydantic import BaseModel
from crawlerd_web.database import get_db_connection
import asyncio

router = APIRouter()

# --- Pydantic Models for Response ---
class Deployment(BaseModel):
    id: int
    project_name: str
    node_url: str
    initialized: bool
    dataset_name: str | None = None
    created_at: str
    updated_at: str

class FileUpdate(BaseModel):
    path: str
    content: str

# --- API Endpoints ---

@router.get("/deployments", response_model=List[Deployment], summary="列出所有部署实例")
async def list_deployments():
    """
    从数据库中获取所有部署信息，连接 projects 和 nodes 表以获取详细名称和URL。
    """
    conn = get_db_connection()
    query = """
        SELECT
            d.id,
            p.name as project_name,
            n.url as node_url,
            d.initialized,
            d.dataset_name,
            d.created_at,
            d.updated_at
        FROM deployments d
        JOIN projects p ON d.project_id = p.id
        JOIN nodes n ON d.node_id = n.id
        ORDER BY d.updated_at DESC;
    """
    deployments_cursor = conn.execute(query).fetchall()
    conn.close()
    return [Deployment(**dict(row)) for row in deployments_cursor]

@router.post("/deployments", summary="将一个项目部署到指定的单个节点")
async def create_deployment(
    request: Request,
    project_name: str = Form(...),
    node_url: str = Form(...),
    file: UploadFile = File(...)
):
    """
    接收一个 .zip 文件，并将其部署到指定的单个 Agent 节点。
    成功后，在数据库中创建项目、节点和部署之间的关联记录。
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip files are allowed.")

    agent_client = request.app.state.agent_client
    conn = get_db_connection()

    try:
        try:
            # 1. 验证节点是否存在于数据库中
            node_row = conn.execute("SELECT id FROM nodes WHERE url = ?", (node_url,)).fetchone()
            if not node_row:
                raise HTTPException(status_code=404, detail=f"Node with URL '{node_url}' not found. Please register the node first.")
            node_id = node_row['id']
            
            # 2. 部署到 Agent
            content = await file.read()
            deploy_url = f"{node_url}/projects/{project_name}"
            files = {'file': (file.filename, content, file.content_type)}
            
            try:
                response = await agent_client.post(deploy_url, files=files)
                response.raise_for_status()
                
                # 2.5 获取项目的 info (包含 module_class_name 和 dataset_name)
                info_response = await agent_client.get(f"{node_url}/projects/{project_name}/info")
                info_response.raise_for_status()
                info_data = info_response.json()
                module_class_name = info_data.get("module_class_name")
                dataset_name = info_data.get("dataset_name")

                if not module_class_name:
                    raise HTTPException(status_code=500, detail=f"Agent could not extract module:ClassName for project '{project_name}'.")

            except Exception as e:
                print(f"Error communicating with agent at {node_url}:")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Failed to deploy to agent at {node_url}: {str(e)}")

            # 3. 查找或创建项目记录
            project_row = conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,)).fetchone()
            if not project_row:
                cursor = conn.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
                project_id = cursor.lastrowid
            else:
                project_id = project_row['id']

            # 4. 在 deployments 表中创建关联记录，包含 module_class_name 和 dataset_name
            try:
                conn.execute(
                    """
                    INSERT INTO deployments (project_id, node_id, module_class_name, dataset_name, initialized) VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(project_id, node_id) DO UPDATE SET 
                        module_class_name=excluded.module_class_name, 
                        dataset_name=excluded.dataset_name,
                        initialized=1, 
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (project_id, node_id, module_class_name, dataset_name)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                raise HTTPException(status_code=409, detail=f"Deployment of '{project_name}' on '{node_url}' already exists.")

            return {"status": "success", "detail": f"Project '{project_name}' successfully deployed to node '{node_url}'. Module:ClassName: {module_class_name}"}

        except HTTPException:
            raise
        except Exception as e:
            print("Unexpected error in create_deployment:")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        conn.close()



@router.post("/deployments/bulk", summary="将一个项目批量部署到指定的多个节点")
async def create_bulk_deployment(
    request: Request,
    project_name: str = Form(...),
    node_urls: str = Form(..., description="Comma-separated list of node URLs"),
    file: UploadFile = File(...)
):
    """
    接收一个 .zip 文件，并将其部署到指定的多个 Agent 节点。
    使用并发请求提高效率，并统一处理数据库记录。
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip files are allowed.")

    agent_client = request.app.state.agent_client
    
    target_node_urls = [url.strip() for url in node_urls.split(',') if url.strip()]
    if not target_node_urls:
        raise HTTPException(status_code=400, detail="No target node URLs provided.")

    # Read content once for all deployments
    content = await file.read()
    
    async def deploy_to_node(node_url):
        """Helper function to deploy to a single node and return result."""
        try:
            deploy_url = f"{node_url}/projects/{project_name}"
            files = {'file': (file.filename, content, file.content_type)}
            
            response = await agent_client.post(deploy_url, files=files)
            response.raise_for_status()
            
            # Get module class name and dataset name
            info_response = await agent_client.get(f"{node_url}/projects/{project_name}/info")
            info_response.raise_for_status()
            info_data = info_response.json()
            module_class_name = info_data.get("module_class_name")
            dataset_name = info_data.get("dataset_name")
            
            if not module_class_name:
                 return {"node": node_url, "status": "failed", "detail": "Agent could not extract module:ClassName."}
            
            return {"node": node_url, "status": "success", "module_class_name": module_class_name, "dataset_name": dataset_name}

        except Exception as e:
            return {"node": node_url, "status": "failed", "detail": f"Agent deployment failed: {str(e)}"}

    # 1. Pre-fetch node IDs from DB to avoid async DB calls inside the loop (which is tricky with sqlite)
    conn = get_db_connection()
    try:
        placeholders = ','.join('?' for _ in target_node_urls)
        nodes_query = f"SELECT id, url FROM nodes WHERE url IN ({placeholders})"
        nodes_rows = conn.execute(nodes_query, target_node_urls).fetchall()
        node_map = {row['url']: row['id'] for row in nodes_rows}
    finally:
        conn.close()

    # Filter out nodes that are not registered
    valid_target_nodes = []
    results_summary = []
    for url in target_node_urls:
        if url in node_map:
            valid_target_nodes.append(url)
        else:
            results_summary.append({"node": url, "status": "failed", "detail": "Node not registered."})
            
    if not valid_target_nodes:
         # If no valid nodes, return early with whatever errors we have
         raise HTTPException(status_code=400, detail={"message": "No valid registered nodes found.", "summary": results_summary})

    # 2. Concurrent deployment to agents
    tasks = [deploy_to_node(url) for url in valid_target_nodes]
    deployment_results = await asyncio.gather(*tasks)
    
    # 3. Batch update database
    conn = get_db_connection()
    try:
        # Ensure project exists
        project_row = conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,)).fetchone()
        if not project_row:
            cursor = conn.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
            project_id = cursor.lastrowid
        else:
            project_id = project_row['id']
            
        for res in deployment_results:
            if res['status'] == 'success':
                node_url = res['node']
                node_id = node_map[node_url]
                module_class_name = res['module_class_name']
                dataset_name = res.get('dataset_name')
                
                try:
                    conn.execute(
                        """
                        INSERT INTO deployments (project_id, node_id, module_class_name, dataset_name, initialized) VALUES (?, ?, ?, ?, 1)
                        ON CONFLICT(project_id, node_id) DO UPDATE SET 
                            module_class_name=excluded.module_class_name, 
                            dataset_name=excluded.dataset_name,
                            initialized=1, 
                            updated_at=CURRENT_TIMESTAMP
                        """,
                        (project_id, node_id, module_class_name, dataset_name)
                    )
                    results_summary.append({"node": node_url, "status": "success", "detail": f"Deployed successfully. Dataset: {dataset_name}"})
                except sqlite3.Error as e:
                     results_summary.append({"node": node_url, "status": "failed", "detail": f"Database error: {str(e)}"})
            else:
                results_summary.append(res) # Append the failure result from deploy_to_node

        conn.commit()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database transaction failed: {str(e)}")
    finally:
        conn.close()

    
    # Check overall success
    overall_success = any(res["status"] == "success" for res in results_summary)
    if not overall_success:
        raise HTTPException(status_code=500, detail={"message": "All deployments failed.", "summary": results_summary})
    
    return {"status": "success", "summary": results_summary}



class InitPayload(BaseModel):
    # module_name is now automatically extracted and stored, so no need for user input here
    pass

@router.post("/deployments/{deployment_id}/init", summary="初始化一个指定的部署")
async def initialize_deployment(deployment_id: int, request: Request): # Removed payload: InitPayload
    """
    在指定的节点上，为一个已部署的项目运行 'init' 命令。
    这会创建 Kafka topics 并将项目标记为“已初始化”。
    """
    agent_client = request.app.state.agent_client
    conn = get_db_connection()

    try:
        # 1. 查找部署信息，包括 module_class_name
        query = """
            SELECT p.name as project_name, n.url as node_url, d.module_class_name
            FROM deployments d
            JOIN projects p ON d.project_id = p.id
            JOIN nodes n ON d.node_id = n.id
            WHERE d.id = ?;
        """
        deployment_row = conn.execute(query, (deployment_id,)).fetchone()
        
        if not deployment_row:
            raise HTTPException(status_code=404, detail=f"Deployment with ID {deployment_id} not found.")

        project_name = deployment_row['project_name']
        node_url = deployment_row['node_url']
        module_class_name = deployment_row['module_class_name']

        if not module_class_name:
            raise HTTPException(status_code=400, detail=f"Module:ClassName not found for deployment {deployment_id}. Please redeploy the project.")

        # 2. (Removed) Agent initialization is no longer required via explicit endpoint.
        # The agent now initializes internally when the job starts.
        # We just mark the deployment as initialized in the database.

        # 3. 更新数据库中的状态
        conn.execute("UPDATE deployments SET initialized = 1 WHERE id = ?", (deployment_id,))
        conn.commit()

        return {"status": "success", "message": f"Deployment {deployment_id} ({project_name} on {node_url}) initialized successfully."}

    finally:
        conn.close()

@router.delete("/deployments/{deployment_id}", summary="从指定节点删除一个部署")
async def delete_deployment(deployment_id: int, request: Request):
    """
    从数据库中删除一个部署记录，并命令对应的 agent 删除项目文件。
    """
    agent_client = request.app.state.agent_client
    conn = get_db_connection()

    try:
        # 1. 查找部署信息
        query = """
            SELECT p.name as project_name, n.url as node_url
            FROM deployments d
            JOIN projects p ON d.project_id = p.id
            JOIN nodes n ON d.node_id = n.id
            WHERE d.id = ?;
        """
        deployment_row = conn.execute(query, (deployment_id,)).fetchone()
        
        if not deployment_row:
            raise HTTPException(status_code=404, detail=f"Deployment with ID {deployment_id} not found.")

        project_name = deployment_row['project_name']
        node_url = deployment_row['node_url']

        # 2. 调用 Agent 的删除接口
        try:
            agent_delete_url = f"{node_url}/projects/{project_name}"
            response = await agent_client.delete(agent_delete_url)
            response.raise_for_status()
        except Exception as e:
            # 如果 agent 删除失败，我们依然尝试从数据库删除（可选，取决于业务逻辑）
            print(f"WARNING: Agent at {node_url} failed to delete project '{project_name}': {str(e)}")

        # 3. 从数据库中删除部署记录
        conn.execute("DELETE FROM deployments WHERE id = ?", (deployment_id,))
        conn.commit()

        return {"status": "success", "message": f"Deployment {deployment_id} ({project_name} on {node_url}) deleted successfully."}

    finally:
        conn.close()

@router.get("/deployments/{deployment_id}/logs", summary="获取部署项目的日志")
async def get_deployment_logs(deployment_id: int, request: Request):
    """
    从对应的 Agent 获取指定部署项目的日志。
    """
    agent_client = request.app.state.agent_client
    conn = get_db_connection()

    try:
        query = """
            SELECT p.name as project_name, n.url as node_url
            FROM deployments d
            JOIN projects p ON d.project_id = p.id
            JOIN nodes n ON d.node_id = n.id
            WHERE d.id = ?;
        """
        deployment_row = conn.execute(query, (deployment_id,)).fetchone()
        
        if not deployment_row:
            raise HTTPException(status_code=404, detail=f"Deployment with ID {deployment_id} not found.")

        project_name = deployment_row['project_name']
        node_url = deployment_row['node_url']

        agent_logs_url = f"{node_url}/projects/{project_name}/logs"
        response = await agent_client.get(agent_logs_url)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        return response.json() # Agent's endpoint returns JSON like {"logs": "..."}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching logs from agent at {node_url}:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs from agent: {str(e)}")
    finally:
        conn.close()

@router.get("/deployments/{deployment_id}/files", summary="List project files")
async def list_deployment_files(deployment_id: int, request: Request):
    """
    Proxy request to agent to list all files in the project.
    """
    agent_client = request.app.state.agent_client
    conn = get_db_connection()
    try:
        query = """
            SELECT p.name as project_name, n.url as node_url
            FROM deployments d
            JOIN projects p ON d.project_id = p.id
            JOIN nodes n ON d.node_id = n.id
            WHERE d.id = ?;
        """
        row = conn.execute(query, (deployment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        url = f"{row['node_url']}/projects/{row['project_name']}/files"
        try:
            resp = await agent_client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    finally:
        conn.close()

@router.get("/deployments/{deployment_id}/files/content", summary="Read file content")
async def read_deployment_file(deployment_id: int, path: str, request: Request):
    """
    Proxy request to agent to read a specific file.
    """
    agent_client = request.app.state.agent_client
    conn = get_db_connection()
    try:
        query = """
            SELECT p.name as project_name, n.url as node_url
            FROM deployments d
            JOIN projects p ON d.project_id = p.id
            JOIN nodes n ON d.node_id = n.id
            WHERE d.id = ?;
        """
        row = conn.execute(query, (deployment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deployment not found")

        url = f"{row['node_url']}/projects/{row['project_name']}/files/content"
        try:
            resp = await agent_client.get(url, params={"path": path})
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    finally:
        conn.close()

@router.put("/deployments/{deployment_id}/files/content", summary="Update file content")
async def update_deployment_file(deployment_id: int, update: FileUpdate, request: Request):
    """
    Proxy request to agent to update a specific file.
    """
    agent_client = request.app.state.agent_client
    conn = get_db_connection()
    try:
        query = """
            SELECT p.name as project_name, n.url as node_url
            FROM deployments d
            JOIN projects p ON d.project_id = p.id
            JOIN nodes n ON d.node_id = n.id
            WHERE d.id = ?;
        """
        row = conn.execute(query, (deployment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deployment not found")

        url = f"{row['node_url']}/projects/{row['project_name']}/files/content"
        try:
            resp = await agent_client.put(url, json=update.dict())
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    finally:
        conn.close()

@router.get("/deployments/{deployment_id}/stats", summary="Get project stats")
async def get_deployment_stats(deployment_id: int, request: Request):
    """
    Proxy request to agent to fetch on-demand stats for a project.
    """
    agent_client = request.app.state.agent_client
    conn = get_db_connection()
    try:
        query = """
            SELECT p.name as project_name, n.url as node_url
            FROM deployments d
            JOIN projects p ON d.project_id = p.id
            JOIN nodes n ON d.node_id = n.id
            WHERE d.id = ?;
        """
        row = conn.execute(query, (deployment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deployment not found")

        url = f"{row['node_url']}/projects/{row['project_name']}/stats"
        try:
            resp = await agent_client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    finally:
        conn.close()

