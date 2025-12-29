# crawlerd_web/api/nodes.py
import sqlite3
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from crawlerd_web.database import get_db_connection

router = APIRouter()

class NodePayload(BaseModel):
    url: str
    alias: str | None = None

@router.get("/nodes", summary="获取所有 Agent 节点的状态")
async def list_nodes(request: Request):
    """
    从数据库中读取所有已注册的 Agent 节点，并从每个节点获取其状态。
    """
    agent_client = request.app.state.agent_client
    node_statuses = []
    
    conn = get_db_connection()
    db_nodes = conn.execute("SELECT url, alias FROM nodes").fetchall()
    conn.close()

    for node_row in db_nodes:
        node_url = node_row["url"]
        node_alias = node_row["alias"]
        try:
            response = await agent_client.get(f"{node_url}/status")
            response.raise_for_status()
            status_data = response.json()
            status_data["url"] = node_url
            status_data["alias"] = node_alias
            status_data["agent_status"] = "online"
            node_statuses.append(status_data)
        except Exception as e:
            node_statuses.append({
                "url": node_url,
                "alias": node_alias,
                "agent_status": "offline",
                "error": str(e)
            })
            
    return node_statuses

@router.post("/nodes", summary="注册一个新的 Agent 节点")
async def register_node(node: NodePayload):
    """
    将一个新的 Agent 节点 URL 保存到数据库中。
    """
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO nodes (url, alias) VALUES (?, ?)", (node.url, node.alias))
        conn.commit()
    except sqlite3.IntegrityError:
        # 这个错误发生在 url 字段的 UNIQUE 约束失败时
        conn.close()
        raise HTTPException(status_code=400, detail=f"Node with URL {node.url} already exists.")
    finally:
        conn.close()
    
    return {"status": "success", "message": f"Node {node.url} registered."}
