from ai_integrations.conversational_ai_agent import invoke_agent
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv('../credentials.env') #load environment variables (credentials and API keys) from a .env file


records_test = [
    {
        'id': 1,
        'description': 'Grocery Shopping',
        'amount': '85.50',
        'type': 'expense',
        'category': 'Food & Dining',
        'account': 'Checking Account',
        'date': '2025-11-05',
        'time': '14:30'
    },
    {
        'id': 2,
        'description': 'Salary Deposit',
        'amount': '3200.00',
        'type': 'income',
        'category': 'Salary',
        'account': 'Checking Account',
        'date': '2025-11-01',
        'time': '09:00'
    },
    {
        'id': 3,
        'description': 'Coffee Shop',
        'amount': '4.50',
        'type': 'expense',
        'category': 'Food & Dining',
        'account': 'Cash',
        'date': '2025-11-05',
        'time': '08:15'
    },
    {
        'id': 4,
        'description': 'Electric Bill',
        'amount': '120.00',
        'type': 'expense',
        'category': 'Utilities',
        'account': 'Checking Account',
        'date': '2025-11-03',
        'time': '16:45'
    },
    {
        'id': 5,
        'description': 'Freelance Project',
        'amount': '500.00',
        'type': 'income',
        'category': 'Freelance',
        'account': 'Savings Account',
        'date': '2025-10-28',
        'time': '11:20'
    },
    {
        'id': 6,
        'description': 'Uber Ride',
        'amount': '25.75',
        'type': 'expense',
        'category': 'Transportation',
        'account': 'Checking Account',
        'date': '2025-11-07',
        'time': '18:30'
    },
    {
        'id': 7,
        'description': 'Netflix Subscription',
        'amount': '15.99',
        'type': 'expense',
        'category': 'Entertainment',
        'account': 'Checking Account',
        'date': '2025-11-01',
        'time': '10:00'
    },
    {
        'id': 8,
        'description': 'Online Shopping',
        'amount': '67.20',
        'type': 'expense',
        'category': 'Shopping',
        'account': 'Credit Card',
        'date': '2025-11-06',
        'time': '20:15'
    },
    {
        'id': 9,
        'description': 'Restaurant Dinner',
        'amount': '45.00',
        'type': 'expense',
        'category': 'Food & Dining',
        'account': 'Credit Card',
        'date': '2025-11-08',
        'time': '19:45'
    },
    {
        'id': 10,
        'description': 'Gas Station',
        'amount': '55.00',
        'type': 'expense',
        'category': 'Transportation',
        'account': 'Checking Account',
        'date': '2025-11-04',
        'time': '07:30'
    },
    {
        'id': 11,
        'description': 'Salary Deposit',
        'amount': '3200.00',
        'type': 'income',
        'category': 'Salary',
        'account': 'Checking Account',
        'date': '2025-10-01',
        'time': '09:00'
    },
    {
        'id': 12,
        'description': 'Internet Bill',
        'amount': '89.99',
        'type': 'expense',
        'category': 'Utilities',
        'account': 'Checking Account',
        'date': '2025-10-15',
        'time': '12:00'
    },
    {
        'id': 13,
        'description': 'Movie Tickets',
        'amount': '32.00',
        'type': 'expense',
        'category': 'Entertainment',
        'account': 'Cash',
        'date': '2025-10-20',
        'time': '18:00'
    },
    {
        'id': 14,
        'description': 'Freelance Consulting',
        'amount': '750.00',
        'type': 'income',
        'category': 'Freelance',
        'account': 'Savings Account',
        'date': '2025-11-10',
        'time': '14:00'
    },
    {
        'id': 15,
        'description': 'Clothing Store',
        'amount': '120.00',
        'type': 'expense',
        'category': 'Shopping',
        'account': 'Credit Card',
        'date': '2025-10-25',
        'time': '15:30'
    }
]

accounts_test = [
        {
            'id': '1',
            'name': 'Checking Account',
            'balance': '2340.00',
            'icon': '💳',
            'type': 'Checking',
            'last_updated': 'Today',
            'transaction_count': '24'
        },
        {
            'id': '2',
            'name': 'Savings Account',
            'balance': '3080.00',
            'icon': '💰',
            'type': 'Savings',
            'last_updated': 'Yesterday',
            'transaction_count': '12'
        },
        {
            'id': '3',
            'name': 'Cash',
            'balance': '450.00',
            'icon': '💵',
            'type': 'Cash',
            'last_updated': '2 days ago',
            'transaction_count': '8'
        }
    ]

categories_test = ['Food & Dining', 'Salary', 'Utilities', 'Freelance', 'Transportation', 'Entertainment', 'Shopping']

app = Flask("Money-Map")

app.secret_key = os.getenv('SECRET_KEY')  # Add SECRET_KEY to your .env file
app.config['SQLALCHEMY_DATABASE_URI'] = (f"""mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}""")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # type: ignore # for redirect to login if not logged in

class User(UserMixin, db.Model):
    __tablename__ = 'users' # specifys the table name in the original database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# The login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST': 
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, password=password).first() # filtering the user by username and password from the database
        
        # if the user is found and the password is correct
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home')) # redirect to the desired page or the home page
        
        # Check if username exists
        user_exists = User.query.filter_by(username=username).first()
        if not user_exists:
            flash('Account not found. Please register first.', 'warning')
            return redirect(url_for('register'))
        
        # if the user exists but the password is incorrect
        flash('Invalid username or password', 'danger')
        return render_template('login.html')
    
    return render_template('login.html') # if the mothod is GET, render the login page

# The register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# The logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# The home route
@app.route('/')
# @login_required
def other():
    return redirect(url_for('home'))

@app.route('/ai_agent', methods=['GET', 'POST'])
def ai_agent():
    if request.method == 'POST':
        query = request.form.get('query')
        response = invoke_agent(query)
        return jsonify({'response': response})
    return render_template('ai_agent.html',
                         username="current_user.username",
                         records=records_test,
                         accounts=accounts_test,
                         categories=categories_test)

@app.route('/home')
def home():
    from collections import defaultdict
    
    # Calculate monthly averages
    monthly_data = defaultdict(lambda: {'income': 0, 'spending': 0})
    category_totals = defaultdict(float)
    
    for record in records_test:
        month = record['date'][:7]
        amount = float(record['amount'])
        
        if record['type'] == 'income':
            monthly_data[month]['income'] += amount
        else:
            monthly_data[month]['spending'] += amount
            category_totals[record['category']] += amount
    
    avg_spending = sum(m['spending'] for m in monthly_data.values()) / len(monthly_data) if monthly_data else 0
    avg_income = sum(m['income'] for m in monthly_data.values()) / len(monthly_data) if monthly_data else 0
    
    # Sort months chronologically
    sorted_months = sorted(monthly_data.keys())
    
    # Prepare chart data - use all categories from categories_test
    chart_data = {
        'category_labels': [cat for cat in categories_test if category_totals.get(cat, 0) > 0 or cat in [r['category'] for r in records_test]],
        'category_values': [category_totals.get(cat, 0) for cat in categories_test if category_totals.get(cat, 0) > 0 or cat in [r['category'] for r in records_test]],
        'trend_labels': [month[-2:] for month in sorted_months[-6:]],  # Last 6 months
        'trend_income': [monthly_data[m]['income'] for m in sorted_months[-6:]],
        'trend_spending': [monthly_data[m]['spending'] for m in sorted_months[-6:]]
    }
    
    return render_template('home.html',
                         username="current_user.username",
                         records=records_test,
                         accounts=accounts_test,
                         categories=categories_test,
                         total_balance='3600.00',
                         avg_spending=f'{avg_spending:.2f}',
                         avg_income=f'{avg_income:.2f}',
                         top_category=max(category_totals, key=category_totals.get) if category_totals else 'N/A',
                         savings_rate='56',
                         chart_data=chart_data)
@app.route('/accounts')
def accounts():
    
    return render_template('accounts.html',
                         username="current_user.username",
                         records=records_test,
                         accounts=accounts_test,
                         categories=categories_test)

@app.route('/add_account', methods=['POST'])
def add_account():
    data = request.get_json()
    print("New account data received:", data)  
    return '', 204  # No Content returned, just that the addition was successful

@app.route('/delete_account/<int:account_id>', methods=['POST'])
def delete_account(account_id):

    print(f"Account with ID {account_id} deleted.")  
    return '', 204  # No Content returned, just that the deletion was successful

@app.route('/edit_account/<int:account_id>', methods=['POST'])
def edit_account(account_id):
    data = request.get_json()
    print(f"Account with ID {account_id} updated")  
    return '', 204



@app.route('/records')
# @login_required
def records():
    
    return render_template('records.html',
                         username="current_user.username",
                         records=records_test,
                         accounts=accounts_test,
                         categories=categories_test)


@app.route('/add_record', methods=['POST'])
def add_record():
    data = request.get_json()
    print("New record data received:", data)  
    return '', 204  # No Content returned, just that the addition was successful

@app.route('/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):

    print(f"Record with ID {record_id} deleted.")  
    return '', 204  # No Content returned, just that the deletion was successful

@app.route('/update_record/<int:record_id>', methods=['POST'])
def update_record(record_id):
    data = request.get_json()
    # Update record in database with data
    return '', 204



@app.route('/settings')
def settings():
    currency = 'USD'
    language = 'en'
    notifications = True
    
    return render_template('settings.html',
                         currency=currency,
                         language=language,
                         notifications=notifications)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    currency = request.form.get('currency', 'USD')
    language = request.form.get('language', 'en')
    notifications = request.form.get('notifications') == 'on'
    
    print(f"Settings saved: Currency={currency}, Language={language}, Notifications={notifications}")
    
    return '', 204


# @app.route('/test')
# def test():
#     flash('Registration successful! Please login.', 'success')
#     return ""



app.run(debug=True)