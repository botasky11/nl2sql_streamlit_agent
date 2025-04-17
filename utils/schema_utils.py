import streamlit as st
import yaml
from sqlalchemy import create_engine, text
import pandas as pd


# 加载配置
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

engine = create_engine(config["db_url"])

# 提取数据库 Schema
@st.cache_data
def extract_schema():
    with engine.connect() as conn:
        table_names = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        schema = ""
        for table in table_names:
            table_name = table[0]
            columns = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")).fetchall()
            col_info = ", ".join([f"{col[0]} ({col[1]})" for col in columns])
            schema += f"表 {table_name} 包含字段: {col_info}\n"
        return schema

# 执行 SQL
def execute_sql(sql_query):
    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df