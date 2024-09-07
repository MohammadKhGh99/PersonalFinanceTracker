import flask
import boto3
from flask import render_template

app = flask.Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('home.html')


@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')


# User Management Service
@app.route('/users/register', methods=['POST'])
def register_user():
    """
    Register a new user.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('users')
    item = {
        'user_id': 10,
        'email': 'mohammad.gh454@outlook.com',
        'name': 'Mohammad Gh',
        'preferences': {
            'currency': 'USD',
            'timezone': 'UTC'
        }
    }
    table.put_item(Item=item)
    print("User added successfully!")


@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get user profile details.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('users')
    response = table.get_item(
        Key={
            'user_id': int(user_id)
        }
    )
    return response['Item']


@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update user profile.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('users')
    table.update_item(
        Key={
            'user_id': int(user_id)
        },
        UpdateExpression='SET email = :val1',
        ExpressionAttributeValues={
            ':val1': 'mohammad.gh45@gmail.com'
        }
    )
    print("User updated successfully!")


@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('users')
    table.delete_item(
        Key={
            'user_id': int(user_id)
        }
    )
    print("User deleted successfully!")


@app.route('/users/login', methods=['GET', 'POST'])
def login_user():
    """
    Login a user.
    """
    if flask.request.method == 'POST':
        # TODO - Implement login logic
        return "User logged in successfully!"
    else:
        return "Please login to access the application."


# Transaction Service
@app.route('/transactions', methods=['POST'])
def record_transaction():
    """
     Record a new transaction.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('transactions')
    item = {
        'transaction_id': '12345',
        'user_id': 10,
        'amount': 100.0,
        'date': '2020-01-01',
        'category_id': '0',
        'type': 'expense',
        'description': 'Test transaction'
    }
    table.put_item(Item=item)
    print("Transaction added successfully!")


@app.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """
    Retrieve details of a specific transaction.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('transactions')
    response = table.get_item(
        Key={
            'transaction_id': f'{transaction_id}'
        }
    )
    return response['Item']


@app.route('/transactions/<transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """
    Update a transaction.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('transactions')
    table.update_item(
        Key={
            'transaction_id': f'{transaction_id}'
        },
        UpdateExpression='SET amount = :val1',
        ExpressionAttributeValues={
            ':val1': 200.0
        }
    )
    print("Transaction updated successfully!")


@app.route('/transactions/<transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """
    Delete a transaction.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('transactions')
    table.delete_item(
        Key={
            'transaction_id': f'{transaction_id}'
        }
    )
    print("Transaction deleted successfully!")


# Category Service
@app.route('/categories', methods=['POST'])
def create_category():
    """
    Create a new category.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('categories')
    item = {
        'category_id': '0',
        'user_id': 10,
        'name': 'Test category',
        'description': 'Test category description'
    }
    table.put_item(Item=item)
    print("Category added successfully!")


@app.route('/categories', methods=['GET'])
def get_categories():
    """
    Retrieve all categories.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('categories')
    response = table.scan()
    return response['Items']


@app.route('/categories/<category_id>', methods=['PUT'])
def update_category(category_id):
    """
    Update a category.
    """
    # TODO - improve this function to update any attribute of the category
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('categories')
    table.update_item(
        Key={
            'category_id': f'{category_id}'
        },
        UpdateExpression='SET name = :val1',
        ExpressionAttributeValues={
            ':val1': 'Updated category'
        }
    )
    print("Category updated successfully!")


@app.route('/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    """
    Delete a category.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('categories')
    table.delete_item(
        Key={
            'category_id': f'{category_id}'
        }
    )
    print("Category deleted successfully!")


# Report Generation Service

# Notification Service

# Authentication and Authorization Service


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

