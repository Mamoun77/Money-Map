from ai_integrations.conversational_ai_agent import invoke_agent
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv('./credentials.env') #load environment variables (credentials and API keys) from a .env file

print(os.getenv('MYSQL_USERNAME'))  # Example of accessing an environment variable