# NL2SQL Streamlit Agent

一个基于 Langchain 和 Streamlit 的自然语言转 SQL 查询Agent助手 Demo，能够将用户的自然语言问题自动转换为 SQL 查询并执行。

## 功能特点

- 支持自然语言输入，自动生成对应的 SQL 查询
- 提供友好的 Web 界面，使用 Streamlit 构建
- 支持 PostgreSQL 数据库（可基于sqlalchemy支持的数据库类型进行拓展，包括MySQL、PostgreSQL、SQLite、Oracle等）
- 提供查询执行确认机制，确保 SQL 安全性
- 可视化展示查询执行过程

## 环境要求

- Python 3.8+
- PostgreSQL 数据库
- 其他依赖包（见 requirements.txt）

## 安装步骤

1. 克隆项目到本地：
```bash
git clone https://github.com/yourusername/nl2sql_streamlit_agent.git
cd nl2sql_streamlit_agent
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖包：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
   创建 `.env` 文件并添加以下配置：
   ```bash
   # LLM API配置
   model=your_model_name        # 例如：gpt-3.5-turbo
   api_key=your_api_key        # 你的API密钥
   base_url=your_base_url      # API基础URL（如果使用自定义API端点）
   ```

5. 配置数据库连接：
   
   a. 创建 `config.yaml` 文件并配置数据库连接信息：
   ```yaml
   db_url: "postgresql+psycopg2://username:password@localhost:5432/database_name"
   max_tokens: 2000
   temperature: 0.2
   model_path: "defog/sqlcoder-7b-2"
   ```

   b. 数据库连接URL格式说明：
   - `postgresql+psycopg2://`: 数据库驱动类型
   - `username`: 数据库用户名
   - `password`: 数据库密码
   - `localhost`: 数据库主机地址
   - `5432`: 数据库端口号
   - `database_name`: 数据库名称

   c. 确保数据库已正确安装并运行：
   ```bash
   # 检查PostgreSQL服务状态
   sudo service postgresql status  # Linux
   # 或
   brew services list  # MacOS
   ```

   d. 创建数据库和用户（如果尚未创建）：
   ```sql
   CREATE DATABASE database_name;
   CREATE USER username WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE database_name TO username;
   ```

## 运行应用

1. 启动 Streamlit 应用：
```bash
streamlit run app.py
```

2. 在浏览器中访问：`http://localhost:8501`

## 使用说明

1. 在输入框中输入自然语言问题，例如："每个产品的总销量是多少？"
2. 点击"生成 SQL"按钮
3. 系统会显示生成的 SQL 查询
4. 确认是否执行 SQL 查询
5. 查看查询结果

## 项目结构

```
nl2sql_streamlit_agent/
├── app.py              # 主应用文件
├── app_chains.py       # 基于 LangChain 的应用实现
├── agent/             # Agent 相关代码
│   ├── agent.py
│   └── agent_chains.py
├── utils/             # 工具函数
│   ├── schema_utils.py
│   └── prompt.py
├── .env              # 环境变量配置文件
├── config.yaml       # 数据库和模型配置文件
└── requirements.txt    # 项目依赖
```

## 开发说明

- `app.py`: 使用基础的 LangChain，Streamlit 实现
- `app_chains.py`: 使用 LangGraph 有状态实现，提供human-in-loop 更强大的交互功能

## 注意事项

- 确保数据库连接信息正确配置
- 建议在开发环境中使用测试数据库
- 注意 SQL 注入风险，建议添加适当的输入验证
- 请妥善保管 API 密钥，不要将其提交到版本控制系统中
- 建议使用环境变量或配置文件来管理敏感信息
- 确保数据库用户具有适当的权限
- 定期备份数据库

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

[添加许可证信息]