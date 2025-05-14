from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from agent.agent import react_agent_graph
from langchain_core.messages import AIMessage, ToolMessage
import logging
import json
from datetime import datetime
import os

# 创建logs目录（如果不存在）
os.makedirs('logs', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/nl2sql_api_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="NL2SQL API",
    description="API for converting natural language to SQL queries",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    dialect: Optional[str] = "SQLite"

class QueryResponse(BaseModel):
    sql_query: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    steps: List[dict] = []

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        # 记录请求
        logger.info(f"Received query request: {json.dumps(request.model_dump(), ensure_ascii=False)}")
        
        initial_state = {
            "input": request.question,
            "top_k": request.top_k,
            "dialect": request.dialect,
            "messages": []
        }
        
        response = QueryResponse(steps=[])
        sql_query = None
        result = None
        
        for step in react_agent_graph.stream(initial_state, stream_mode=["values"]):
            message = step[1]["messages"]
            if len(message) > 0:
                message = message[-1]
                
            step_info = {
                "type": message.__class__.__name__,
                "content": str(message)
            }
            
            if isinstance(message, AIMessage):
                if message.tool_calls:
                    for action in message.tool_calls:
                        if action.get('name') == 'sql_db_query':
                            sql_query = action.get('args', {}).get('query')
                if message.response_metadata.get("finish_reason") == "stop":
                    result = message.content
            elif isinstance(message, ToolMessage):
                result = message.content
                
            response.steps.append(step_info)
        
        response.sql_query = sql_query
        response.result = result
        
        # 记录响应
        logger.info(f"Query response: {json.dumps(response.model_dump(), ensure_ascii=False)}")
        
        return response
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing query: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy"} 