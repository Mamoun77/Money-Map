from ai_integrations.conversational_ai_agent import invoke_agent
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
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
app.config['SQLALCHEMY_DATABASE_URI'] = (f"""mysql+pymysql://{os.getenv('MYSQL_USERNAME')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('DATABASE_NAME')}""")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Accounts(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10))
    balance = db.Column(db.Numeric(10, 2), default=0.00)

class Categories(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.Enum('expense', 'income', 'both'), default='both')

class Records(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))    
    type = db.Column(db.Enum('expense', 'income'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    description = db.Column(db.Text)

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    language = db.Column(db.String(10), default='en')
    theme = db.Column(db.String(20), default='light')
    notification_enabled = db.Column(db.Boolean, default=True)

def rendering_records_accounts_categories(): # For fetching records, accounts, and categories from the database for the current user
    records = db.session.query(Records, Accounts, Categories)\
        .join(Accounts, Records.account_id == Accounts.id)\
        .join(Categories, Records.category_id == Categories.id)\
        .filter(Records.user_id == current_user.id)\
        .all()
    
    accounts = Accounts.query.filter_by(user_id=current_user.id).all()
    categories = Categories.query.filter_by(user_id=current_user.id).all()
    
    # Transform the joined query results into a usable format
    records_list = []
    for expense, account, category in records:
        records_list.append({
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'type': expense.type,
            'date': expense.date,
            'time': expense.time,
            'category': category.name,
            'account': account.name
        })
    return records_list, accounts, categories

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # type: ignore # for redirect to login if not logged in

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# The login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST': 
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Account not found. Please register first.', 'warning')
            return redirect(url_for('register'))

        if not check_password_hash(user.password, password):
            flash('Invalid username or password', 'danger')
            return render_template('login.html')

        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('home'))
    
    return render_template('login.html') # Render login template if the method is GET

# The register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_password, 
                   first_name=first_name, last_name=last_name)
        db.session.add(user)
        db.session.commit()
        
        # Create default settings for user
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html') # Render register template if the method is GET

# The logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# The home route
@app.route('/')
@login_required
def other():
    return redirect(url_for('home'))

@app.route('/ai_agent', methods=['GET', 'POST'])
@login_required
def ai_agent():
    if request.method == 'POST':
        query = request.form.get('query')
        response = invoke_agent(query)
        return jsonify({'response': response})
    
    else:  # Else if the method is GET


        return render_template('ai_agent.html',
                                username=current_user.username,
                                records=records_test,
                                accounts=accounts_test,
                                categories=categories_test)

@app.route('/home')
@login_required
def home():
    from collections import defaultdict
    from sqlalchemy import func
    
    # Fetch user's records from DB
    records_query = db.session.query(
        Records,
        Categories.name.label('category_name'),
        Accounts.name.label('account_name')
    ).join(
        Categories, Records.category_id == Categories.id
    ).join(
        Accounts, Records.account_id == Accounts.id
    ).filter(
        Records.user_id == current_user.id
    ).all()
    
    # Calculate monthly averages
    monthly_data = defaultdict(lambda: {'income': 0, 'spending': 0})
    category_totals = defaultdict(float)
    
    for record, category_name, account_name in records_query:
        month = record.date.strftime('%Y-%m')
        amount = float(record.amount)
        
        if record.type == 'income':
            monthly_data[month]['income'] += amount
        else:
            monthly_data[month]['spending'] += amount
            category_totals[category_name] += amount
    
    avg_spending = sum(m['spending'] for m in monthly_data.values()) / len(monthly_data) if monthly_data else 0
    avg_income = sum(m['income'] for m in monthly_data.values()) / len(monthly_data) if monthly_data else 0
    
    # Sort months chronologically
    sorted_months = sorted(monthly_data.keys())
    
    # Get user's categories
    user_categories = Categories.query.filter_by(user_id=current_user.id).all()
    category_names = [cat.name for cat in user_categories]
    
    # Prepare chart data
    chart_data = {
        'category_labels': [cat for cat in category_names if category_totals.get(cat, 0) > 0],
        'category_values': [category_totals.get(cat, 0) for cat in category_names if category_totals.get(cat, 0) > 0],
        'trend_labels': [month[-2:] for month in sorted_months[-6:]] if len(sorted_months) >= 6 else [month[-2:] for month in sorted_months],
        'trend_income': [monthly_data[m]['income'] for m in sorted_months[-6:]] if len(sorted_months) >= 6 else [monthly_data[m]['income'] for m in sorted_months],
        'trend_spending': [monthly_data[m]['spending'] for m in sorted_months[-6:]] if len(sorted_months) >= 6 else [monthly_data[m]['spending'] for m in sorted_months]
    }
    
    # Calculate total balance
    total_balance = db.session.query(func.sum(Accounts.balance)).filter_by(user_id=current_user.id).scalar() or 0
    
    # Calculate savings rate
    total_income = sum(m['income'] for m in monthly_data.values())
    total_spending = sum(m['spending'] for m in monthly_data.values())
    savings_rate = int(((total_income - total_spending) / total_income * 100)) if total_income > 0 else 0
    
    records_list, accounts, categories = rendering_records_accounts_categories()
    
    return render_template('home.html',
                         username=current_user.username,
                         records=records_list,
                         accounts=accounts,
                         categories=categories,
                         total_balance=f'{float(total_balance):.2f}',
                         avg_spending=f'{avg_spending:.2f}',
                         avg_income=f'{avg_income:.2f}',
                         top_category=max(category_totals, key=category_totals.get) if category_totals else 'N/A',
                         savings_rate=str(savings_rate),
                         chart_data=chart_data)


@app.route('/accounts')
@login_required
def accounts():

    records_list, accounts, categories = rendering_records_accounts_categories()

    
    return render_template('accounts.html',
                         username=current_user.username,
                         records=records_list,
                         accounts=accounts,
                         categories=categories)

@app.route('/add_account', methods=['POST'])
@login_required
def add_account():
    data = request.get_json()
    new_account = Accounts(
        user_id=current_user.id,
        name=data.get('name'),
        icon=data.get('icon'),
        balance=data.get('balance', 0.00)
    )
    db.session.add(new_account)
    db.session.commit()
    return '', 204  # No Content returned, just that the addition was successful

@app.route('/delete_account/<int:account_id>', methods=['POST'])
@login_required
def delete_account(account_id):

    account = Accounts.query.get(account_id)
    db.session.delete(account) # Delete the account from the DB
    db.session.commit()

    return '', 204  # No Content returned, just that the deletion was successful

@app.route('/edit_account/<int:account_id>', methods=['POST'])
@login_required
def edit_account(account_id):
    data = request.get_json()

    account = Accounts.query.get(account_id)

    account.name = data.get('name')
    account.balance = data.get('balance')
    account.icon = data.get('icon')

    db.session.commit()

    return '', 204



@app.route('/records')
@login_required
def records():

    records_list, accounts, categories = rendering_records_accounts_categories()
    
    return render_template('records.html',
                         username=current_user.username,
                         records=records_list,
                         accounts=accounts,
                         categories=categories)


@app.route('/add_record', methods=['POST'])
@login_required
def add_record():
    data = request.get_json()

    print("*" * 100)
    print(int(data.get('account')))
    print("type:", type(int(data.get('account'))))
    print("*" * 100)

    new_record = Records(
        user_id=current_user.id,
        account_id=int(data.get('account')),
        amount=data.get('amount'),
        category_id=int(data.get('category')),
        type=data.get('type'),
        date=data.get('date'),
        time=data.get('time'),
        description=data.get('description')
    )

    db.session.add(new_record)
    db.session.commit()



    return '', 204  # No Content returned, just that the addition was successful

@app.route('/delete_record/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):

    record = Records.query.get(record_id) # Retrieve the record by ID
    db.session.delete(record)
    db.session.commit()

    return '', 204  # No Content returned, just that the deletion was successful

@app.route('/update_record/<int:record_id>', methods=['POST'])
@login_required
def update_record(record_id):
    data = request.get_json()

    record = Records.query.get(data.get('id'))

    record.account_id = data.get('account')
    record.amount = data.get('amount')
    record.category_id = data.get('category')
    record.type = data.get('type')
    record.date = data.get('date')
    record.time = data.get('time')
    record.description = data.get('description')
    
    db.session.commit()

    # Update record in database with data
    return '', 204



@app.route('/settings')
@login_required
def settings():
    currency = 'USD'
    language = 'en'
    notifications = True
    
    return render_template('settings.html',
                         currency=currency,
                         language=language,
                         notifications=notifications,
                         username="current_user.username",
                         records=records_test,
                         accounts=accounts_test,
                         categories=categories_test)

@app.route('/save_settings', methods=['POST'])
@login_required
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