from langchain.agents import create_agent #for creating the agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit #for SQL database toolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate #for creating chat prompts templates
from langchain_google_genai import ChatGoogleGenerativeAI #for using Google Gemini LLM API
from dotenv import load_dotenv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, '../../credentials.env')) # load environment variables (credentials and API keys) from a .env file

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-09-2025",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    
    )

system_prompt = """You are a SQL expert assistant for an expense tracking app. Follow these instructions:
- Always verify table schemas before querying
- Use proper MySQL syntax
- Format results clearly and concisely
- If no data exists, state that explicitly
- Double-check date ranges in queries
- Provide short, actionable insights, tips, or budget suggestions when relevant
- Keep explanations brief and focused on practical guidance"""

mysql_uri = f'mysql+mysqlconnector://{os.getenv("MYSQL_USERNAME")}:{os.getenv("MYSQL_PASSWORD")}@{os.getenv("MYSQL_HOST")}:{os.getenv("MYSQL_PORT")}/{os.getenv("DATABASE_NAME")}'
db = SQLDatabase.from_uri(mysql_uri) # type: ignore

toolkit = SQLDatabaseToolkit(db=db, llm=llm) # setting up the SQL toolkit
agent = create_agent(llm, toolkit.get_tools(), system_prompt=system_prompt) # creating the agent

def invoke_agent(user_query):

    response = agent.invoke({
        "messages": [
            {"role": "user", "content": str(user_query)}
        ]
})
    
    return response['messages'][-1].content
