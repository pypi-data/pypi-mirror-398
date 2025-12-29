import asyncio
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from crawlerd_web.database import get_db_connection

router = APIRouter()

# --- Pydantic Models ---
class StartJobPayload(BaseModel):
    deployment_id: int


@router.get("/jobs", summary="列出所有 Agent 节点上正在运行的爬虫进程")
async def list_running_jobs(request: Request):
    """
    并发地从数据库中所有已注册的 Agent 获取正在运行的进程列表。
    """
    agent_client = request.app.state.agent_client
    
    conn = get_db_connection()
    nodes_cursor = conn.execute("SELECT url FROM nodes").fetchall()
    conn.close()
    
    tasks = []
    node_urls = [row["url"] for row in nodes_cursor]
    for node_url in node_urls:
        task = agent_client.get(f"{node_url}/jobs")
        tasks.append(task)
        
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_jobs = []
    for i, res in enumerate(results):
        node_url = node_urls[i]
        if isinstance(res, Exception):
            pass
        elif res.status_code == 200: # type: ignore
            jobs_on_node = res.json() # type: ignore
            for job in jobs_on_node:
                job['node_url'] = node_url
            all_jobs.extend(jobs_on_node)
            
    return all_jobs


@router.post("/jobs/start", summary="在一个指定的、已初始化的部署上启动一个爬虫任务")
async def start_job(payload: StartJobPayload, request: Request):
    """
    在一个指定的部署上启动一个爬虫工作进程。
    此端点要求对应的部署必须先被初始化。
    """
    agent_client = request.app.state.agent_client
    deployment_id = payload.deployment_id
    
    conn = get_db_connection()
    try:
        # 1. 查找部署信息并验证其是否已初始化
        query = """
            SELECT
                p.name as project_name,
                n.url as node_url,
                d.initialized,
                d.module_class_name
            FROM deployments d
            JOIN projects p ON d.project_id = p.id
            JOIN nodes n ON d.node_id = n.id
            WHERE d.id = ?;
        """
        deployment_row = conn.execute(query, (deployment_id,)).fetchone()
        
        if not deployment_row:
            raise HTTPException(status_code=404, detail=f"Deployment with ID {deployment_id} not found.")
        
        # Check removed: Deployment auto-initializes now.

        project_name = deployment_row['project_name']
        node_url = deployment_row['node_url']
        module_class_name = deployment_row['module_class_name']

        if not module_class_name:
            raise HTTPException(status_code=500, detail=f"Module:ClassName not found for deployment {deployment_id}.")


        # 2. 调用 agent 启动 'run' 进程
        run_payload = {"project_name": project_name, "module_name": module_class_name} # Use stored module_class_name
        response = await agent_client.post(f"{node_url}/jobs", json=run_payload)
        response.raise_for_status()
        return response.json()

    except HTTPException:
        raise # 重新抛出已知的 HTTP 异常
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        conn.close()


@router.delete("/jobs/{pid}", summary="强制停止一个运行中的爬虫任务 (Kill by PID)")
async def kill_job(pid: int, node_url: str, request: Request):
    """
    通过命令对应的 Agent 强制杀死指定的爬虫进程。
    """
    agent_client = request.app.state.agent_client

    try:
        response = await agent_client.delete(f"{node_url}/jobs/{pid}")
        response.raise_for_status()
        return {"status": "success", "message": f"Process {pid} on node {node_url} killed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to kill process {pid} on node {node_url}: {str(e)}")


@router.post("/jobs/schedule", summary="（占位）安排一个定时爬虫任务")
async def schedule_job():
    # TODO: Use APScheduler to schedule a job start
    return {"message": "Scheduling a new job - functionality not implemented yet."}
