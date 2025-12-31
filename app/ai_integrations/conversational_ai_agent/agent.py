from langchain.agents import create_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

# Import the email tool
from .email_tool import send_financial_report_email

# Load environment variables from the root credentials.env if available
# Adjust relative path as needed: current dir -> conversational_ai_agent -> ai_integrations -> app -> root
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../../credentials.env'))

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-09-2025",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# Use default port 3306 if MYSQL_PORT is not set
db_port = os.getenv("MYSQL_PORT", "3306")
mysql_uri = f'mysql+mysqlconnector://{os.getenv("MYSQL_USERNAME")}:{os.getenv("MYSQL_PASSWORD")}@{os.getenv("MYSQL_HOST")}:{db_port}/{os.getenv("DATABASE_NAME")}'
db = SQLDatabase.from_uri(mysql_uri)

agent = None
current_user_email = None

import time
def initialize_agent(username, user_email):
    global agent, current_user_email
    start_time = time.time()
    
    current_user_email = user_email

    system_prompt = f"""You are a SQL expert assistant for an expense tracking app. Follow these instructions:

        CORE CAPABILITIES:
        - Always verify table schemas before querying
        - Use proper MySQL syntax
        - Format results clearly and concisely
        - If no data exists, state that explicitly
        - Double-check date ranges in queries
        - Provide short, actionable insights, tips, or budget suggestions when relevant
        - Keep explanations brief and focused on practical guidance
        - Use a conversational tone
        - Your response should be plain text with currency symbols, no tables, and you can use "\\n" for new lines

        USER CONTEXT:
        - The user you are assisting is "{username}" with email "{user_email}"
        - All responses and database queries should be tailored to their financial data and history

        EMAIL REPORTS:
        - When the user requests a "financial summary", "report", or "email report", generate a comprehensive text report covering:
        * Total income and expenses (current month and overall)
        * Top spending categories with amounts
        * Account balances summary
        * Spending trends (compared to previous periods)
        * Budget recommendations or insights
        - After generating the report, ALWAYS use the send_financial_report_email tool to send it to the user's email
        - Confirm to the user that the report has been sent
        - Format the report text clearly for readability
        - Include specific numbers, percentages, and actionable insights in reports
        """
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    
    # Combine SQL tools with email tool
    all_tools = toolkit.get_tools() + [send_financial_report_email]
    
    agent = create_agent(llm, all_tools, system_prompt=system_prompt)
    
    end_time = time.time()
    initialization_time = end_time - start_time
    print(f"Agent initialized in {initialization_time:.2f} seconds.")

def invoke_agent(user_query):
    global current_user_email
    
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": str(user_query)}
        ]
    })
    
    return response['messages'][-1].content
