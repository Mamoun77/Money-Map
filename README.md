# Money Map 💰🗺️

Money Map is a smart personal finance web application designed to empower users to take control of their financial health. By combining traditional expense tracking with advanced AI capabilities, Money Map makes managing money effortless and insightful.

## 🚀 Key Features

*   **📊 Interactive Dashboard:** Get a clear overview of your financial status with dynamic charts showing spending trends, income vs. expenses, and category breakdowns.
*   **🧾 AI Receipt Scanner:** Say goodbye to manual entry! Upload photos of your receipts, and our AI (powered by Google Cloud Vision and Gemini) will automatically extract details like merchant, date, amount, and category.
*   **🤖 Conversational AI Agent:** Have a question about your finances? Just ask! The built-in AI assistant can analyze your data to answer queries like "How much did I spend on groceries last month?" and even send detailed email reports.
*   **🎯 Financial Goals:** Set custom savings targets for specific accounts and time periods. Track your progress in real-time and celebrate your achievements.
*   **🔔 Smart Alerts:** Stay on budget with intelligent notifications that warn you when you're approaching daily, weekly, or monthly spending limits.
*   **🌍 Multi-Currency Support:** Travel the world without worry. Money Map supports multiple currencies with real-time conversion, standardizing your analytics to your preferred base currency.
*   **📂 Data Export:** Your data belongs to you. Export your entire transaction history to CSV at any time for offline analysis.
*   **🔐 Secure & Private:** Features secure user authentication, password recovery via email, and robust data protection.

## 🛠️ Technology Stack

*   **Backend:** Python, Flask
*   **Database:** MySQL, SQLAlchemy ORM
*   **Artificial Intelligence:**
    *   **LLM:** Google Gemini (via LangChain) for natural language understanding and data parsing.
    *   **OCR:** Google Cloud Vision API for text extraction from images.
*   **Frontend:** HTML5, CSS3, JavaScript, Bootstrap/Custom CSS
*   **Utilities:** Pandas (Data Analysis), Forex-Python (Currency Conversion)

## ⚙️ Setup & Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/money-map.git
    cd money-map
    ```

2.  **Install Dependencies**
    Ensure you have Python installed, then install the required packages:
    ```bash
    pip install flask flask-login flask-sqlalchemy langchain langchain-google-genai google-cloud-vision pandas forex-python python-dotenv pymysql
    ```

3.  **Database Configuration**
    Ensure you have a MySQL server running and create a database (e.g., `money_map_db`).

4.  **Environment Variables**
    Create a `credentials.env` file in the project root (or update the path in the code) with the following keys:
    ```env
    SECRET_KEY=your_secret_key

    # Database
    MYSQL_USERNAME=your_db_user
    MYSQL_PASSWORD=your_db_password
    MYSQL_HOST=localhost
    DATABASE_NAME=money_map_db
    MYSQL_PORT=3306

    # AI Services
    GOOGLE_API_KEY=your_gemini_api_key
    GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-vision-credentials.json

    # Email Service (for notifications & password recovery)
    APP_ACCOUNT_EMAIL_ADDRESS=your_email@gmail.com
    APP_ACCOUNT_PASSWORD=your_email_app_password
    ```

5.  **Run the Application**
    ```bash
    python -m app.routes
    ```
    Visit `http://localhost:5000` in your browser.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
