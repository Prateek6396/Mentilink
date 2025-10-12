from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('MENTILINK_SECRET', 'change-me-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mentilink.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# register blueprints
from Routes.auth import auth_bp
from Routes.dashboard import dashboard_bp
from Routes.sessions import sessions_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(sessions_bp, url_prefix='/sessions')

# import models so tables are known
import models.user
import models.session
import models.slot

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
