from flask_login import UserMixin
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_principal import Principal, Permission, RoleNeed, identity_loaded, UserNeed, Identity, AnonymousIdentity, identity_changed


class User(UserMixin):
    def __init__(self, id, username, password, roles):
        self.id = id
        self.username = username
        self.password = password
        self.roles = roles

    def get_id(self):
        return self.id

    def get_roles(self):
        return self.roles
    

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-Principal
principals = Principal(app)

# Define roles
admin_permission = Permission(RoleNeed('admin'))
user_permission = Permission(RoleNeed('user'))

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    # todo - Replace with your user loading logic
    # todo - needs to got to database to get the user...
    return User.get(user_id)

# Identity loaded callback
@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # todo - Replace with your user authentication logic
        user = authenticate(username, password)
        if user:
            login_user(user)
            identity_changed.send(app, identity=Identity(user.id))
            return redirect(url_for('index'))
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    identity_changed.send(app, identity=AnonymousIdentity())
    return redirect(url_for('index'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        # todo - Replace with your password reset logic
        reset_password_for(email)
        return jsonify({'message': 'Password reset link sent'}), 200
    return render_template('reset_password.html')


@app.route('/admin')
@login_required
@admin_permission.require(http_exception=403)
def admin():
    return render_template('admin.html')

@app.route('/user')
@login_required
@user_permission.require(http_exception=403)
def user():
    return render_template('user.html')