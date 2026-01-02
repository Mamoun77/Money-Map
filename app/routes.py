from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta, datetime
import tempfile
import os

import random
import smtplib 
from email.mime.text import MIMEText # For sending emails to the user
from email.mime.multipart import MIMEMultipart

# for AI integrations
from app.ai_integrations.conversational_ai_agent.agent import initialize_agent, invoke_agent
from app.ai_integrations.ocr.ocr import extract_text
from app.ai_integrations.add_record_agent.agent import parse_financial_record


# for records exportation
from flask import send_file
import pandas as pd
from io import BytesIO

# for currency conversion
import requests
import time

# Simple in-memory cache for currency rates
# Structure: { 'FROM_TO': (rate, timestamp) }
_currency_cache = {}
CACHE_DURATION = 48 * 3600  # 48 hours in seconds

def get_conversion_rate(from_currency='USD', to_currency='USD'):
    """Get conversion rate with caching and timeout"""
    if from_currency == to_currency:
        return 1.0
    
    cache_key = f"{from_currency}_{to_currency}"
    current_time = time.time()

    # Check cache
    if cache_key in _currency_cache:
        rate, timestamp = _currency_cache[cache_key]
        if current_time - timestamp < CACHE_DURATION:
            return rate

    # Define fallback rates
    fallback_rates = {'USD': 1.0, 'JOD': 0.71}  # 1 USD = 0.71 JOD

    try:
        # Try to fetch from a reliable free API with a strict timeout
        response = requests.get(
            f"https://open.er-api.com/v6/latest/{from_currency}",
            timeout=3
        )
        response.raise_for_status()
        data = response.json()

        rate = data['rates'].get(to_currency)
        if rate:
            _currency_cache[cache_key] = (rate, current_time)
            return rate

    except Exception as e:
        print(f"Currency fetch failed: {e}. Using fallback.")

    # Fallback logic
    try:
        if from_currency in fallback_rates and to_currency in fallback_rates:
            return fallback_rates[to_currency] / fallback_rates[from_currency]
    except:
        pass

    return 1.0 # Default if everything fails


# Store verification codes temporarily for multiple users
verification_codes = {}


app = Flask(__name__)

app.secret_key = os.environ['SECRET_KEY']  # Add SECRET_KEY to your .env file
app.config['SQLALCHEMY_DATABASE_URI'] = (f"""mysql+pymysql://{os.environ['MYSQL_USERNAME']}:{os.environ['MYSQL_PASSWORD']}@{os.environ['MYSQL_HOST']}/{os.environ['DATABASE_NAME']}""")
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

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FinancialGoal(db.Model):
    __tablename__ = 'financial_goals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    time_period = db.Column(db.Enum('week', 'month', 'year'), nullable=False)
    account_ids = db.Column(db.Text, nullable=False)  # Comma-separated
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

def rendering_records_accounts_categories(): # For fetching records, accounts, and categories from the database for the current user
    records = db.session.query(Records, Accounts, Categories)\
        .join(Accounts, Records.account_id == Accounts.id)\
        .outerjoin(Categories, Records.category_id == Categories.id)\
        .filter(Records.user_id == current_user.id)\
        .all()
    
    # records_list = []
    # for expense, account, category in records:
    #     print(f"Processing record {expense.id}: category={category.name if category else 'None'}")
    #     records_list.append({...})
    # print(f"Total records for user: {Records.query.filter_by(user_id=current_user.id).count()}")
    
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
            'category': category.name if category else 'Uncategorized',
            'account': account.name
        })

    # Check for records with invalid category_id
    orphaned = db.session.query(Records).outerjoin(
        Categories, Records.category_id == Categories.id
    ).filter(Categories.id == None, Records.category_id != None).all()

    print(f"Found {len(orphaned)} records with invalid category_id")
    for r in orphaned:
        print(f"Record {r.id}: category_id={r.category_id} (doesn't exist)")

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

agent_initialized = False
@app.route('/ai_agent', methods=['GET', 'POST'])
@login_required
def ai_agent():
    global agent_initialized
    
    if request.method == 'POST':
        if not agent_initialized:
            initialize_agent(current_user.username, current_user.email)
            agent_initialized = True

        query = request.form.get('query')
        response = invoke_agent(query)
        return jsonify({'response': response})
    
    else:  # if the method is GET

        initialize_agent(current_user.username, current_user.email)

        records_list, accounts, categories = rendering_records_accounts_categories()
        return render_template('ai_agent.html',
                                username=current_user.username,
                                records=records_list,
                                accounts=accounts,
                                categories=categories)


@app.route('/home')
@login_required
def home():
    from collections import defaultdict
    from sqlalchemy import func
    
    # Get user's currency preference
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    user_currency = user_settings.currency if user_settings else 'USD'
    
    # Get conversion rate ONCE
    conversion_rate = get_conversion_rate('USD', user_currency)
    
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
    
    # Calculate monthly averages (convert all to user's currency)
    monthly_data = defaultdict(lambda: {'income': 0, 'spending': 0})
    category_totals = defaultdict(float)
    
    for record, category_name, account_name in records_query:
        month = record.date.strftime('%Y-%m')
        # Convert amount using the rate we fetched once
        amount = float(record.amount) * conversion_rate
        
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
    
    # Calculate total balance (convert to user's currency)
    total_balance = db.session.query(func.sum(Accounts.balance)).filter_by(user_id=current_user.id).scalar() or 0
    total_balance = float(total_balance) * conversion_rate
    
    # Calculate savings rate
    total_income = sum(m['income'] for m in monthly_data.values())
    total_spending = sum(m['spending'] for m in monthly_data.values())
    savings_rate = int(((total_income - total_spending) / total_income * 100)) if total_income > 0 else 0
    
    records_list, accounts, categories = rendering_records_accounts_categories()
    
    # Convert account balances to user's currency
    for account in accounts:
        account.balance = float(account.balance) * conversion_rate
    
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
                         chart_data=chart_data,
                         user_currency=user_currency)


@app.route('/accounts')
@login_required
def accounts():
    # Get user's currency preference
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    user_currency = user_settings.currency if user_settings else 'USD'
    
    # Get conversion rate ONCE
    conversion_rate = get_conversion_rate('USD', user_currency)
    
    records_list, accounts, categories = rendering_records_accounts_categories()
    
    # Convert account balances to user's currency
    for account in accounts:
        account.balance = float(account.balance) * conversion_rate
    
    return render_template('accounts.html',
                         username=current_user.username,
                         records=records_list,
                         accounts=accounts,
                         categories=categories,
                         user_currency=user_currency)


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
    # Get user's currency preference
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    user_currency = user_settings.currency if user_settings else 'USD'
    
    # Get conversion rate 
    conversion_rate = get_conversion_rate('USD', user_currency)
    
    records_list, accounts, categories = rendering_records_accounts_categories()
    
    # Convert record amounts to user's currency
    for record in records_list:
        record['amount'] = float(record['amount']) * conversion_rate
    
    return render_template('records.html',
                         username=current_user.username,
                         records=records_list,
                         accounts=accounts,
                         categories=categories,
                         user_currency=user_currency)


def check_spending_limits(user_id):
    """Check if user has exceeded spending limits and create notifications"""

    # Get user settings to check if notifications are enabled
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not settings or not settings.notification_enabled:
        return
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    
    # Daily limit check
    daily_expenses = db.session.query(func.sum(Records.amount))\
        .filter(Records.user_id == user_id, 
                Records.type == 'expense',
                Records.date == today)\
        .scalar() or 0
    
    if daily_expenses > 50:
        # Check if notification already exists for today
        existing = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.title == 'Daily Spending Limit Exceeded',
            func.date(Notification.created_at) == today
        ).first()
        
        if not existing:
            notif = Notification(
                user_id=user_id,
                title='Daily Spending Limit Exceeded',
                message=f'Your daily expenses have reached {float(daily_expenses):.2f}, exceeding the 50 limit warning.'
            )
            db.session.add(notif)
    
    # Weekly limit check
    weekly_expenses = db.session.query(func.sum(Records.amount))\
        .filter(Records.user_id == user_id,
                Records.type == 'expense',
                Records.date >= week_ago)\
        .scalar() or 0
    
    if weekly_expenses > 400:
        existing = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.title == 'Weekly Spending Limit Exceeded',
            Notification.created_at >= datetime.utcnow() - timedelta(days=7)
        ).first()
        
        if not existing:
            notif = Notification(
                user_id=user_id,
                title='Weekly Spending Limit Exceeded',
                message=f'Your weekly expenses have reached {float(weekly_expenses):.2f}, exceeding the 400 limit warning.'
            )
            db.session.add(notif)
    
    # Monthly limit check
    monthly_expenses = db.session.query(func.sum(Records.amount))\
        .filter(Records.user_id == user_id,
                Records.type == 'expense',
                Records.date >= month_ago)\
        .scalar() or 0
    
    if monthly_expenses > 2000:
        existing = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.title == 'Monthly Spending Limit Exceeded',
            Notification.created_at >= datetime.utcnow() - timedelta(days=30)
        ).first()
        
        if not existing:
            notif = Notification(
                user_id=user_id,
                title='Monthly Spending Limit Exceeded',
                message=f'Your monthly expenses have reached {float(monthly_expenses):.2f}, exceeding the 2000 limit warning.'
            )
            db.session.add(notif)
    
    db.session.commit()

@app.route('/add_record', methods=['POST'])
@login_required
def add_record():
    # Get user's currency preference
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    user_currency = user_settings.currency if user_settings else 'USD'
    
    # Get conversion rate FROM user currency TO USD
    conversion_rate = get_conversion_rate(user_currency, 'USD')

    # Check if photo is included (AI mode)
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename != '':

            # Save photo temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                photo.save(tmp_file.name)
                tmp_path = tmp_file.name
            
            try:
                # Extract text from image
                ocr_text = extract_text(tmp_path)
                print(f"OCR Text: {ocr_text[:200]}")
                
                # Get user's accounts and categories
                accounts = [acc.name for acc in Accounts.query.filter_by(user_id=current_user.id).all()]
                categories = [cat.name for cat in Categories.query.filter_by(user_id=current_user.id).all()]
                print(f"Accounts: {accounts}")
                print(f"Categories: {categories}")
                
                # Get current datetime
                current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                # Parse with AI
                parsed_data = parse_financial_record(ocr_text, accounts, categories, current_datetime)
                print(f"Parsed data: {parsed_data}")
                
                # Check if valid
                if parsed_data['valid_input'] == 'not_valid':
                    print("Invalid input detected")
                    os.unlink(tmp_path)
                    return jsonify({'error': 'Invalid receipt image'}), 400
                
                # Find account and category IDs
                accounts_query = Accounts.query.filter_by(user_id=current_user.id).all()
                categories_query = Categories.query.filter_by(user_id=current_user.id).all()
                
                account = Accounts.query.filter_by(user_id=current_user.id, name=parsed_data['account']).first()
                category = Categories.query.filter_by(user_id=current_user.id, name=parsed_data['category']).first()
                
                print(f"Account found: {account}")
                print(f"Category found: {category}")
                print(f"Category ID in parsed_data would be: {category.id if category else 'None'}")
                print(f"Category name match: parsed='{parsed_data['category']}' vs found='{category.name if category else 'None'}'")
                
                # Create record
                new_record = Records(
                    user_id=current_user.id,
                    account_id=account.id if account else accounts_query[0].id,
                    amount=float(parsed_data['amount']) * conversion_rate,
                    category_id=category.id if category else None,
                    type=parsed_data['type'].lower(),
                    date=parsed_data['date'],
                    time=parsed_data['time'],
                    description=parsed_data['description']
                )
                
                print(f"New record created: {new_record}")
                
                db.session.add(new_record)
                db.session.commit()
                
                # Update account balance
                update_account = Accounts.query.get(new_record.account_id)
                if new_record.type == 'income':
                    update_account.balance += new_record.amount
                else:
                    update_account.balance -= new_record.amount
                db.session.commit()
                
                print("Record committed to database")

                verify_record = Records.query.get(new_record.id)
                print(f"Verified record - user_id: {verify_record.user_id}, category_id: {verify_record.category_id}, type: {verify_record.type}")

                print("------------------------------------------------")
                print("All done")
                print("------------------------------------------------")

                print(f"Record ID: {new_record.id}")
                print(f"Record in DB: {Records.query.get(new_record.id)}")
                
                check_spending_limits(current_user.id)
                check_goal_achievements(current_user.id)
                
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
            
            return '', 204
    
    # Manual mode - form data provided
    new_record = Records(
        user_id=current_user.id,
        account_id=int(request.form.get('account')),
        amount=float(request.form.get('amount')) * conversion_rate,
        category_id=int(request.form.get('category')),
        type=request.form.get('type'),
        date=request.form.get('date'),
        time=request.form.get('time'),
        description=request.form.get('description')
    )

    db.session.add(new_record)
    db.session.commit()
    
    # Update account balance
    account = Accounts.query.get(new_record.account_id)
    if new_record.type == 'income':
        account.balance += new_record.amount
    else:
        account.balance -= new_record.amount
    db.session.commit()

    check_spending_limits(current_user.id)
    check_goal_achievements(current_user.id)

    return '', 204

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
    
    # Get user's currency to convert back to USD
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    user_currency = user_settings.currency if user_settings else 'USD'
    
    # Get conversion rate to convert FROM user currency TO USD
    conversion_rate = get_conversion_rate(user_currency, 'USD')

    record = Records.query.get(record_id)
    
    # Store old values before updating
    old_amount = record.amount
    old_account_id = record.account_id
    old_type = record.type
    
    # Convert account name to ID
    account = Accounts.query.filter_by(user_id=current_user.id, name=data.get('account')).first()
    # Convert category name to ID
    category = Categories.query.filter_by(user_id=current_user.id, name=data.get('category')).first()

    # Update record
    record.account_id = account.id if account else record.account_id
    record.amount = float(data.get('amount')) * conversion_rate
    record.category_id = category.id if category else record.category_id
    record.type = data.get('type')
    record.date = data.get('date')
    record.time = data.get('time')
    record.description = data.get('description')
    
    # Update old account (reverse old transaction)
    old_account = Accounts.query.get(old_account_id)
    if old_type == 'income':
        old_account.balance -= old_amount
    else:
        old_account.balance += old_amount
    
    # Update new account (apply new transaction)
    new_account = Accounts.query.get(record.account_id)
    if record.type == 'income':
        new_account.balance += record.amount
    else:
        new_account.balance -= record.amount
    
    db.session.commit()

    check_goal_achievements(current_user.id)
    
    return '', 204



@app.route('/settings')
@login_required
def settings():
    # Fetch user settings from database
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    user_currency = user_settings.currency if user_settings else 'USD'
    
    # If no settings exist, create default ones
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()

    records_list, accounts, categories = rendering_records_accounts_categories()

    # No conversion needed for accounts_list since it's just for display names
    accounts_list = [{'id': acc.id, 'name': acc.name, 'icon': acc.icon, 'balance': float(acc.balance)} for acc in accounts]

    return render_template('settings.html',
                         currency=user_settings.currency,
                         language=user_settings.language,
                         notifications=user_settings.notification_enabled,
                         username=current_user.username,
                         first_name=current_user.first_name,
                         last_name=current_user.last_name,
                         email=current_user.email,
                         records=records_list,
                         accounts=accounts_list,
                         categories=categories,
                         user_currency=user_currency)


@app.route('/save_settings', methods=['POST'])
@login_required
def save_settings():
    try:
        currency = request.form.get('currency', 'USD')
        language = request.form.get('language', 'en')
        notifications = request.form.get('notifications') == 'on'
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validate required fields
        if not email or not username:
            return jsonify({'error': 'Email and username are required'}), 400
        
        # Check if email is taken by another user
        existing_email = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_email:
            return jsonify({'error': 'Email already in use'}), 400
        
        # Check if username is taken by another user
        existing_username = User.query.filter(User.username == username, User.id != current_user.id).first()
        if existing_username:
            return jsonify({'error': 'Username already in use'}), 400
        
        # Update user settings in UserSettings table
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if settings:
            settings.currency = currency
            settings.language = language
            settings.notification_enabled = notifications
        else:
            # Create settings if they don't exist
            settings = UserSettings(
                user_id=current_user.id,
                currency=currency,
                language=language,
                notification_enabled=notifications
            )
            db.session.add(settings)
        
        # Update user information in Users table
        user = User.query.get(current_user.id)
        if user:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = username
            
            # Update password only if provided
            if password:
                user.password = generate_password_hash(password)
        
        db.session.commit()
        
        return '', 204
    except Exception as e:
        print(f"Error saving settings: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/settings/categories', methods=['GET'])
@login_required
def get_categories():

    categories = Categories.query.filter_by(user_id=current_user.id).all()
    categories_list = [{'id': cat.id, 'name': cat.name} for cat in categories]
    return jsonify(categories_list)

@app.route('/settings/add_category', methods=['POST'])
@login_required
def add_category():
    data = request.get_json()
    new_category = Categories(
        user_id=current_user.id,
        name=data.get('name')   
    )

    db.session.add(new_category)
    db.session.commit()
    return '', 204  # No Content returned, just that the addition was successful

@app.route('/settings/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):

    categorie = Categories.query.get(category_id)
    db.session.delete(categorie) # Delete the category from the DB
    db.session.commit()
    return '', 204

@app.route('/settings/edit_category/<int:category_id>', methods=['POST'])
@login_required
def edit_category(category_id):
    data = request.get_json()

    categorie = Categories.query.get(category_id)
    
    categorie.name = data.get('name') # Update category name in database with data

    db.session.commit()

    return '', 204

@app.route('/get_theme')
@login_required
def get_theme():
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    return jsonify({'dark_mode': settings.theme == 'dark'})

@app.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    data = request.get_json()
    dark_mode = data.get('dark_mode')
    new_theme = 'dark' if dark_mode else 'light'

    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    settings.theme = new_theme
    db.session.commit()

    return '', 204



def send_verification_email(to_email, code):
    """Send verification code via email"""
    from_email = os.environ['APP_ACCOUNT_EMAIL_ADDRESS']
    password = os.environ['APP_ACCOUNT_PASSWORD']
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = 'Money Map - Password Recovery Code'
    
    # the HTML body of the email
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #10b981;">Password Recovery</h2>
            <p>Your verification code is:</p>
            <h1 style="color: #333; font-size: 36px; letter-spacing: 5px;">{code}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p style="color: #666; font-size: 12px;">If you didn't request this, please ignore this email.</p>
        </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587) # for sending email via Gmail SMTP server
        server.starttls()
        server.login(from_email, password) # Login to the email server from the app credentials
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.route('/recover_password')
def recover_password():
    return render_template('recover_password.html')

@app.route('/recover/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    email = data.get('email')
    
    user = User.query.filter_by(email=email).first() # Check if the email exists in the database
    if not user:
        return jsonify({'message': 'Email not found'}), 404
    
    code = str(random.randint(100000, 999999)) # Generate a 6-digit verification code
    expires_at = datetime.utcnow() + timedelta(minutes=10) # Code expires in 10 minutes
    
    verification_codes[email] = { # Store the code and its expiration time
        'code': code,
        'expires': expires_at
    }
    
    if send_verification_email(email, code):
        return jsonify({'message': 'Code sent successfully'}), 200
    else:
        return jsonify({'message': 'Failed to send email'}), 500

@app.route('/recover/verify_code', methods=['POST'])
def verify_code():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')
    
    if email not in verification_codes:
        return jsonify({'message': 'No code found'}), 400
    
    stored = verification_codes[email]
    
    if datetime.utcnow() > stored['expires']: # Check if the code has expired
        del verification_codes[email]
        return jsonify({'message': 'Code expired'}), 400
    
    if stored['code'] != code: # Check if the code matches
        return jsonify({'message': 'Invalid code'}), 400
    
    return jsonify({'message': 'Code verified'}), 200

@app.route('/recover/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('password')
    
    if email not in verification_codes:
        return jsonify({'message': 'Session expired'}), 400
    
    user = User.query.filter_by(email=email).first()
    user.password = generate_password_hash(new_password)
    db.session.commit()

    del verification_codes[email] # Remove the verification code after successful reset

    return jsonify({'message': 'Password reset successful'}), 200


# Notification routes
@app.route('/notifications/get', methods=['GET'])
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    
    # Get user settings to check if notifications are enabled
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    notification_enabled = settings.notification_enabled if settings else True
    
    notifications_list = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
    } for n in notifications]
    
    return jsonify({
        'notifications': notifications_list,
        'notification_enabled': notification_enabled
    })

@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == current_user.id: # Ensures the notification belongs to the current user
        notification.is_read = True
        db.session.commit()
    return '', 204

@app.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({Notification.is_read: True}) # mark all unread notifications as read
    db.session.commit()
    return '', 204

@app.route('/export/csv')
@login_required
def export_csv():
    # Fetch all records for current user
    records_query = db.session.query(
        Records,
        Categories.name.label('category_name'),
        Accounts.name.label('account_name')
    ).outerjoin(
        Categories, Records.category_id == Categories.id
    ).join(
        Accounts, Records.account_id == Accounts.id
    ).filter(
        Records.user_id == current_user.id
    ).order_by(Records.date.desc(), Records.time.desc()).all() # Order by date and time descending
    
    # Prepare data for CSV
    data = []
    for record, category_name, account_name in records_query:
        data.append({
            'Date': record.date.strftime('%Y-%m-%d'),
            'Time': record.time.strftime('%H:%M:%S'),
            'Description': record.description,
            'Type': record.type.capitalize(),
            'Amount': float(record.amount),
            'Category': category_name if category_name else 'Uncategorized',
            'Account': account_name
        })
    
    # Create DataFrame and CSV
    df = pd.DataFrame(data)
    
    # Create BytesIO object
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'money_map_records_{datetime.now().strftime("%Y%m%d")}.csv' # file name with current date
    )


# Financial Goals routes
@app.route('/settings/goals', methods=['GET'])
@login_required
def get_goals():
    # Get user's currency preference
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    user_currency = user_settings.currency if user_settings else 'USD'
    
    # Get conversion rate ONCE
    conversion_rate = get_conversion_rate('USD', user_currency)
    
    goals = FinancialGoal.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    goals_list = []
    for goal in goals:
        # Calculate progress
        account_ids = [int(x) for x in goal.account_ids.split(',')]

        income = db.session.query(func.sum(Records.amount))\
            .filter(Records.user_id == current_user.id,
                   Records.type == 'income',
                   Records.account_id.in_(account_ids),
                   Records.date >= goal.start_date,
                   Records.date <= goal.end_date).scalar() or 0
        
        expenses = db.session.query(func.sum(Records.amount))\
            .filter(Records.user_id == current_user.id,
                   Records.type == 'expense',
                   Records.account_id.in_(account_ids),
                   Records.date >= goal.start_date,
                   Records.date <= goal.end_date)\
            .scalar() or 0
        
        current_savings = float(income) - float(expenses)
        # Convert amounts to user's currency
        current_savings_converted = current_savings * conversion_rate
        target_amount_converted = float(goal.target_amount) * conversion_rate
        
        progress = max(0, (current_savings / float(goal.target_amount) * 100) if goal.target_amount > 0 else 0)
        
        # Get account names
        accounts = Accounts.query.filter(Accounts.id.in_(account_ids)).all()
        account_names = [acc.name for acc in accounts]
        
        goals_list.append({
            'id': goal.id,
            'goal_name': goal.goal_name,
            'target_amount': target_amount_converted,
            'current_savings': current_savings_converted,
            'progress': min(progress, 100),
            'time_period': goal.time_period,
            'account_names': account_names,
            'account_ids': goal.account_ids,
            'start_date': goal.start_date.strftime('%Y-%m-%d'),
            'end_date': goal.end_date.strftime('%Y-%m-%d')
        })
    
    return jsonify(goals_list)



@app.route('/settings/add_goal', methods=['POST'])
@login_required
def add_goal():
    data = request.get_json()
    
    # Get user's currency to convert back to USD
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    user_currency = user_settings.currency if user_settings else 'USD'
    
    # Get conversion rate FROM user currency TO USD
    conversion_rate = get_conversion_rate(user_currency, 'USD')
    
    # Calculate dates based on time period
    start_date = date.today()
    time_period = data.get('time_period')
    
    if time_period == 'week':
        end_date = start_date + timedelta(days=7)
    elif time_period == 'month':
        end_date = start_date + timedelta(days=30)
    else:  # year
        end_date = start_date + timedelta(days=365)
    
    # Convert target amount to USD for storage
    target_amount_usd = float(data.get('target_amount')) * conversion_rate
    
    new_goal = FinancialGoal(
        user_id=current_user.id,
        goal_name=data.get('goal_name'),
        target_amount=target_amount_usd,
        time_period=time_period,
        account_ids=','.join(map(str, data.get('account_ids'))),
        start_date=start_date,
        end_date=end_date
    )
    
    db.session.add(new_goal)
    db.session.commit()
    
    return '', 204

@app.route('/settings/delete_goal/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = FinancialGoal.query.get(goal_id)
    if goal and goal.user_id == current_user.id:
        goal.is_active = False
        db.session.commit()
    return '', 204

@app.route('/settings/edit_goal/<int:goal_id>', methods=['POST'])
@login_required
def edit_goal(goal_id):
    data = request.get_json()
    goal = FinancialGoal.query.get(goal_id)
    
    # Get user's currency to convert back to USD
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    user_currency = user_settings.currency if user_settings else 'USD'
    
    # Get conversion rate FROM user currency TO USD
    conversion_rate = get_conversion_rate(user_currency, 'USD')
    
    if goal and goal.user_id == current_user.id:
        goal.goal_name = data.get('goal_name')
        # Convert target amount to USD for storage
        goal.target_amount = float(data.get('target_amount')) * conversion_rate
        goal.account_ids = ','.join(map(str, data.get('account_ids')))
        
        # Recalculate end date if time period changed
        if data.get('time_period') != goal.time_period:
            goal.time_period = data.get('time_period')
            if goal.time_period == 'week':
                goal.end_date = goal.start_date + timedelta(days=7)
            elif goal.time_period == 'month':
                goal.end_date = goal.start_date + timedelta(days=30)
            else:
                goal.end_date = goal.start_date + timedelta(days=365)
        
        db.session.commit()
    
    return '', 204

@app.route('/settings/accounts', methods=['GET']) # for getting the accoutns for the goal section
@login_required
def get_accounts():
    accounts = Accounts.query.filter_by(user_id=current_user.id).all()
    accounts_list = [{'id': acc.id, 'name': acc.name, 'icon': acc.icon} for acc in accounts]
    return jsonify(accounts_list)

def check_goal_achievements(user_id):
    """Check if any goals have been achieved and create notifications"""
    
    # Get user settings to check if notifications are enabled
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not settings or not settings.notification_enabled:
        return
    
    goals = FinancialGoal.query.filter_by(user_id=user_id, is_active=True).all()
    
    for goal in goals:
        account_ids = [int(x) for x in goal.account_ids.split(',')]
        
        # Calculate current savings
        income = db.session.query(func.sum(Records.amount))\
            .filter(Records.user_id == user_id,
                   Records.type == 'income',
                   Records.account_id.in_(account_ids),
                   Records.date >= goal.start_date,
                   Records.date <= goal.end_date)\
            .scalar() or 0
        
        expenses = db.session.query(func.sum(Records.amount))\
            .filter(Records.user_id == user_id,
                   Records.type == 'expense',
                   Records.account_id.in_(account_ids),
                   Records.date >= goal.start_date,
                   Records.date <= goal.end_date)\
            .scalar() or 0
        
        current_savings = float(income) - float(expenses)
        
        # Check if goal is achieved
        if current_savings >= float(goal.target_amount):
            # Check if notification already exists for this goal
            existing = Notification.query.filter(
                Notification.user_id == user_id,
                Notification.title == f'Goal Achieved: {goal.goal_name}'
            ).first()
            
            if not existing:
                notif = Notification(
                    user_id=user_id,
                    title=f'Goal Achieved: {goal.goal_name}',
                    message=f'Congratulations! You\'ve reached your savings goal of ${float(goal.target_amount):.2f}. Current savings: ${current_savings:.2f}'
                )
                db.session.add(notif)
    
    db.session.commit()


# app.run(debug=True)