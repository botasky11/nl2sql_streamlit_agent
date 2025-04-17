# from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from utils.prompt import SYSTEM_PREFIX
import yaml
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from utils.schema_utils import engine
from langchain import hub
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from agent.state import AgentState
# react agent配置
class reactAgentConfig(BaseModel):
    username: str
    task_type: str = "sql_to_text" 
    verbose: bool = True
    handle_parsing_errors: bool = True
    max_iterations: int = 5

# 加载配置
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
# 加载环境变量
load_dotenv()
# 初始化llm
# llm = ChatOpenAI(model=os.getenv("model"), 
#                  api_key=os.getenv("api_key"), 
#                  base_url=os.getenv("base_url"), 
#                  max_tokens=config["max_tokens"], 
#                  temperature=config["temperature"])
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
# prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
# assert len(prompt_template.messages) == 1
# system_message = prompt_template.format(dialect=toolkit.dialect, top_k=5)

# # 使用LangGraph的create_react_agent构建agent
# react_agent_graph = create_react_agent(
#     model=llm,
#     tools=toolkit.get_tools(),
#     prompt=system_message,
#     config_schema=reactAgentConfig
# )


embeddings = OpenAIEmbeddings(model="text-embedding-3-large",
                              openai_api_key=os.getenv("api_key"))

# embedding_dim = len(embeddings.embed_query("hello world"))
# index = faiss.IndexFlatL2(embedding_dim)

# vector_store = FAISS(
#     embedding_function=embeddings,
#     index=index,
#     docstore=InMemoryDocstore(),
#     index_to_docstore_id={},
# )

# few shot examples
examples = [{"input": "What is the average number of citations received by publications in each year?", "query": "SELECT publication.year, AVG(publication.citation_num) AS average_citations FROM publication GROUP BY publication.year ORDER BY publication.year NULLS LAST;"},
           {"input": "What are the titles of all publications ordered alphabetically?", "query": "SELECT DISTINCT publication.title FROM publication ORDER BY publication.title ASC NULLS LAST;"},
           {"input": "What is the total number of citations received by publications in 2020?", "query": "SELECT SUM(publication.citation_num) AS total_citations FROM publication WHERE publication.year = 2020;"},
           {"input": "What is the ratio of publications to authors in the database?", "query": "SELECT CAST(COUNT(DISTINCT publication.pid) AS FLOAT) / NULLIF(COUNT(DISTINCT author.aid), 0) AS publication_to_author_ratio FROM publication, author;"},
           {"input": "Which author had the most publications in the year 2021 and how many publications did he/she have that year?", "query": "SELECT author.name, author.aid, COUNT(publication.pid) AS publication_count FROM writes JOIN author ON writes.aid = author.aid JOIN publication ON writes.pid = publication.pid WHERE publication.year = 2021 GROUP BY author.name, author.aid ORDER BY publication_count DESC NULLS LAST LIMIT 1;"},
           ]
example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    embeddings,
    FAISS,
    k=5,
    input_keys=["input"],
)


few_shot_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=PromptTemplate.from_template(
        "User input: {input}\nSQL query: {query}"
    ),
    input_variables=["input", "dialect", "top_k"],
    prefix=SYSTEM_PREFIX,
    suffix="User input: {input}\nSQL query: ",
)

full_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(prompt=few_shot_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("messages"),
    ]
)

# prompt_val = full_prompt.invoke(
#     {
#         "input": "How many arists are there",
#         "top_k": 5,
#         "dialect": "SQLite",
#         "agent_scratchpad": [],
#     }   
# )

react_agent_graph = create_react_agent(
    model=llm,
    tools=toolkit.get_tools(),
    prompt=full_prompt,
    state_schema=AgentState,
    config_schema=reactAgentConfig
)