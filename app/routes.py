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
        'amount': '-$85.50',
        'type': 'expense',
        'category': 'Food & Dining',
        'account': 'Checking Account',
        'date': '2025-11-05',
        'time': '14:30'
    },
    {
        'id': 2,
        'description': 'Salary Deposit',
        'amount': '+$3,200.00',
        'type': 'income',
        'category': 'Salary',
        'account': 'Checking Account',
        'date': '2025-11-05',
        'time': '09:00'
    },
    {
        'id': 3,
        'description': 'Coffee Shop',
        'amount': '-$4.50',
        'type': 'expense',
        'category': 'Food & Dining',
        'account': 'Cash',
        'date': '2025-11-05',
        'time': '08:15'
    },
    {
        'id': 4,
        'description': 'Electric Bill',
        'amount': '-$120.00',
        'type': 'expense',
        'category': 'Utilities',
        'account': 'Checking Account',
        'date': '2025-11-05',
        'time': '16:45'
    },
    {
        'id': 5,
        'description': 'Freelance Project',
        'amount': '+$500.00',
        'type': 'income',
        'category': 'Freelance',
        'account': 'Savings Account',
        'date': '2025-11-03',
        'time': '11:20'
    }
]

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
    return render_template('ai_agent.html', username="current_user.username") # if the method is GET

@app.route('/home')
# @login_required
def home():

    accounts_test = [
        {'name': 'Checking test Account', 'balance': '$2,340.00', 'icon': '💳'},
        {'name': 'Savings Account', 'balance': '$3,080.00', 'icon': '💰'},
        {'name': 'Cash', 'balance': '$450.00', 'icon': '💵'},
        {'name': 'Investment Account', 'balance': '$1,550.00', 'icon': '🏦'}
    ]
    # return render_template('home.html', current_user.username)
    return render_template('home.html', 
                         username="current_user.username",
                         accounts=accounts_test,
                         total_balance='$3,600.00')

@app.route('/accounts')
def accounts():

    accounts_list = [
        {
            'id': '1',
            'name': 'Checking Account',
            'balance': '$2,340.00',
            'icon': '💳',
            'type': 'Checking',
            'last_updated': 'Today',
            'transaction_count': '24'
        },
        {
            'id': '2',
            'name': 'Savings Account',
            'balance': '$3,080.00',
            'icon': '💰',
            'type': 'Savings',
            'last_updated': 'Yesterday',
            'transaction_count': '12'
        },
        {
            'id': '3',
            'name': 'Cash',
            'balance': '$450.00',
            'icon': '💵',
            'type': 'Cash',
            'last_updated': '2 days ago',
            'transaction_count': '8'
        }
    ]

    return render_template('accounts.html', username="current_user.username", accounts=accounts_list)

@app.route('/records')
# @login_required
def records():
    # Filter options - replace with actual database queries
    accounts_list = ['Checking Account', 'Savings Account', 'Cash', 'Investment Account']
    categories_list = ['Food & Dining', 'Salary', 'Utilities', 'Freelance', 'Transportation', 'Entertainment', 'Shopping']
    
    return render_template('records.html',
                         username="current_user.username",
                         records=records_test,
                         accounts=accounts_list,
                         categories=categories_list)


@app.route('/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):

    print(f"Record with ID {record_id} deleted.")  # Placeholder for actual deletion logic

    return '', 204  # No Content returned, just that the deletion was successful

@app.route('/update_record/<int:record_id>', methods=['POST'])
def update_record(record_id):
    data = request.get_json()
    # Update record in database with data
    return '', 204

@app.route('/settings')
def settings():
    return render_template('settings.html')



# @app.route('/test')
# def test():
#     flash('Registration successful! Please login.', 'success')
#     return ""



app.run(debug=True)