from pydantic import BaseModel
from typing import List, Optional
from agent.agent import react_agent_graph
from langchain_core.messages import AIMessage, ToolMessage
import logging
import json
from datetime import datetime
import os
import asyncio

# 创建logs目录（如果不存在）
os.makedirs('logs', exist_ok=True)
# 创建test目录（如果不存在）
os.makedirs('test', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/nl2sql_generate_sql_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    dialect: Optional[str] = "SQLite"

class QueryResponse(BaseModel):
    sql_query: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    steps: List[dict] = []

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
                            # 如果SQL查询以分号结尾，则去掉分号
                            if sql_query and sql_query.strip().endswith(';'):
                                sql_query = sql_query.strip()[:-1]
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
        return QueryResponse(error=error_msg)

def generate_query():
    dataset = {}
    current_dataset = None
    current_db = None
    question = None
    gold_sql = None
    
    with open("test/dev.sql", "r", encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Question"):
                # 解析新的数据集名称
                parts = line.split("|||")
                if len(parts) >= 2:
                    current_db = parts[1].strip()
                    question = parts[0].split(":", 1)[1].strip()
                    # 如果已经有数据集在处理中，保存它
                    current_dataset = dataset.get(current_db, None)
                    if current_dataset:
                        current_dataset['question'].append(question)
                    else:
                        dataset[current_db] = {
                            'question': [question],
                            'gold_sql': []
                        }
                
            elif line.startswith("SQL:"):
                gold_sql = line.split(":", 1)[1].strip()
                # 如果黄金标准SQL以分号结尾，则去掉分号
                if gold_sql.endswith(';'):
                    gold_sql = gold_sql[:-1]
                if current_db:
                    # 如果已经有数据集在处理中，保存它
                    current_dataset = dataset.get(current_db, None)
                    if current_dataset:
                        current_dataset['gold_sql'].append(gold_sql)
                    current_db = None
                    question = None
                    gold_sql = None 
    return dataset

async def run():
    # 测试问题
    # db_name = "concert_singer"
    db_name = "flight_2"

    # 清空输出文件
    with open(f"test/gold_example_{db_name}.txt", "w", encoding='utf-8') as f:
        pass
    with open(f"test/pred_example_{db_name}.txt", "w", encoding='utf-8') as f:
        pass
    
    dataset = generate_query()
    # print("Parsed dataset:")
    # print(json.dumps(dataset, indent=2, ensure_ascii=False))
    
    # 准备批量写入的数据
    gold_examples = []
    pred_examples = []
    errors = []
    
    if dataset and db_name in dataset:
        # 处理所有问题并收集结果
        for i, (question, gold_sql) in enumerate(zip(dataset[db_name]['question'], dataset[db_name]['gold_sql'])):
            print(f"\n处理问题 {i+1}/{len(dataset[db_name]['question'])}")
            print("Question:", question)
            
            response = await process_query(QueryRequest(question=question))
            
            # 确保生成的SQL没有分号结尾
            if response.sql_query and response.sql_query.strip().endswith(';'):
                response.sql_query = response.sql_query.strip()[:-1]
                
            print("Generated SQL:", response.sql_query)
            
            if response.error:
                print("Error:", response.error)
                errors.append(f"问题: {question}\n错误: {response.error}\n")
                # 如果出错，仍然需要添加一个占位符到预测结果中
                pred_examples.append(f"SELECT 'ERROR' AS result\n")
            else:
                # 收集有效的预测结果
                if not response.sql_query:
                    pred_examples.append(f"SELECT 'ERROR' AS result\n")
                else:
                    pred_examples.append(f"{response.sql_query}\n")
            
            # 收集黄金标准
            gold_examples.append(f"{gold_sql}\t{db_name}\n")
    
    # 批量写入文件
    if gold_examples:
        with open(f"test/gold_example_{db_name}.txt", "w", encoding='utf-8') as f:
            f.writelines(gold_examples)
    
    if pred_examples:
        with open(f"test/pred_example_{db_name}.txt", "w", encoding='utf-8') as f:
            f.writelines(pred_examples)
    
    # 如果有错误，写入错误日志
    if errors:
        with open("test/errors.log", "w", encoding='utf-8') as f:
            f.writelines(errors)
        print(f"\n处理过程中出现 {len(errors)} 个错误，详情请查看 test/errors.log")
    else:
        print("\n所有问题处理完成，没有错误")
    
    print(f"\n处理完成! 结果已写入:")
    print(f"- 黄金标准: test/gold_example_{db_name}.txt")
    print(f"- 预测结果: test/pred_example_{db_name}.txt")

if __name__ == "__main__":
    asyncio.run(run())