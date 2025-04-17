from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from utils.prompt import SYSTEM_PROMPT_SQL
import tools.sql_tool as sql_tool
import yaml
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from utils.schema_utils import engine
from langchain import hub

# 加载配置
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
# 加载环境变量
load_dotenv()

llm = init_chat_model(model=os.getenv("model"), 
                      api_key=os.getenv("api_key"), 
                      base_url=os.getenv("base_url"), 
                      max_tokens=config["max_tokens"], 
                      temperature=config["temperature"])

# 初始化数据库
db = SQLDatabase(engine)
# 初始化工具
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
# 初始化系统提示
query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

from typing_extensions import Annotated, TypedDict
from agent.state import State

class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}


from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool


def execute_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}

def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}

from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

graph_builder = StateGraph(State).add_sequence(
    [write_query, execute_query, generate_answer]
)
graph_builder.add_edge(START, "write_query")
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory, interrupt_before=["execute_query"])
