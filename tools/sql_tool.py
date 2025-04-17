from langchain_core.tools import tool
from sqlalchemy import text
import pandas as pd
from utils.schema_utils import engine


@tool("sql_runner")
def run_sql(query: str) -> str:
    """
    Execute SQL query and return the result as a markdown table.
    """
    try:
        with engine.connect() as conn:
            # 清理SQL查询，去除代码块标记
            if query.startswith('```sql') and query.endswith('```'):
                query = query[7:-3].strip()
            elif query.startswith('```') and query.endswith('```'):
                query = query[3:-3].strip()
            
            # 执行SQL查询
            df = pd.read_sql_query(query, conn)
            
            # 将结果转换为Markdown表格格式
            if len(df) == 0:
                return "查询结果为空"
            
            # 将DataFrame转换为markdown表格字符串
            markdown_table = df.head(10).to_markdown(index=False)
            return markdown_table
    except Exception as e:
        return f"[ERROR]: {str(e)}"
    
