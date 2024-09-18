import datetime
import json
from time import sleep
import flask
import boto3
import sys
import uuid
from boto3.dynamodb.conditions import Key, Attr
from flask import redirect, render_template, request, jsonify, url_for
# from pymysql import connect
from sqlalchemy.orm import DeclarativeBase, mapped_column, sessionmaker
from sqlalchemy import (Column, String, Integer, JSON, ForeignKey, DateTime,
                        create_engine, Float)

app = flask.Flask(__name__)

# Define the connection parameters
# DB_HOST = "finance.c9kayga8eues.us-east-1.rds.amazonaws.com"  # Replace with your RDS endpoint
# DB_PORT = "3306"  # Default MariaDB port
# DB_NAME = "finance"  # Replace with your database name
# DB_USER = "mohammadgh"  # Replace with your RDS username
# # todo - check if you can use another way to store the password
# DB_PASSWORD = os.getenv("DB_PASSWORD")  # Replace with your RDS password

# # SQLAlchemy connection URL
# connection_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# connection_url = 'sqlite:///finance.db'
# engine = create_engine(connection_url)
# Session = sessionmaker(bind=engine)
# session = Session()

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('users') # type: ignore
# transactions_table = dynamodb.Table('transactions') # type: ignore
categories_table = dynamodb.Table('categories') # type: ignore
sqs_client = boto3.client('sqs', region_name='us-east-1')
transaction_queue_url = 'https://sqs.us-east-1.amazonaws.com/593793064844/transaction-events'


# class Base(DeclarativeBase):
#     pass


# # user table
# class User(Base):
#     __tablename__ = 'users'
#     user_id = Column(Integer, primary_key=True, autoincrement=True)
#     email = Column(String(255))
#     name = Column(String(255))
#     preferences = Column(JSON)

#     def __repr__(self) -> str:
#         return (f"User(user_id={self.user_id!r}, email={self.email!r}, "
#                 f"name={self.name!r}, preferences={self.preferences!r})")


# class Transaction(Base):
#     __tablename__ = 'transactions'
#     transaction_id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = mapped_column(ForeignKey("users.user_id"))
#     amount = Column(Float)
#     date = Column(String(255))
#     category_id = mapped_column(ForeignKey("categories.category_id"))
#     type = Column(String(255))
#     description = Column(String(255))

#     def __repr__(self) -> str:
#         return (
#             f"Transaction(transaction_id={self.transaction_id!r}, "
#             f"user_id={self.user_id!r}, amount={self.amount!r}, "
#             f"date={self.date!r}, category_id={self.category_id!r}, "
#             f"type={self.type!r}, description={self.description!r})")


# class Category(Base):
#     __tablename__ = 'categories'
#     category_id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = mapped_column(ForeignKey("users.user_id"))
#     name = Column(String(255))
#     description = Column(String(255))

#     def __repr__(self) -> str:
#         return (
#             f"Category(category_id={self.category_id!r}, user_id={self.user_id!r}, "
#             f"name={self.name!r}, description={self.description!r})")

# Base.metadata.create_all(engine)


@app.route('/', methods=['GET'])
def index():
    return render_template('home.html')


@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/users', methods=['GET'])
def users_management():
    return render_template('users_management.html')


# User Management Service
@app.route('/users/register', methods=['GET', 'POST'])
def register_user():
    """
    Register a new user.
    """
    if request.method == 'GET':
        return render_template('register_user.html')
    try:
        primary_key = str(uuid.uuid4())
        new_user = {
            'user_id': primary_key,
            'email': request.form["register-email"],
            'user_name': request.form["register-name"],
            'preferences': request.form["register-preferences"]
        }
        users_table.put_item(Item=new_user)
        return render_template('users_management.html', alert_message='User created successfully')
        return jsonify({'message': 'User created successfully',
                        'user_id': primary_key}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get user profile details.
    """
    try:
        response = users_table.get_item(
            Key={
                'user_id': str(user_id)
            }
        )
        if 'Item' in response:
            user = response['Item']
            return render_template('users_management.html', user=user), 201
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update user profile.
    """
    data = request.get_json()
    email = data.get('update-email')
    user_name = data.get('update-name')
    preferences = data.get('update-preferences')

    try:
        users_table.update_item(
            Key={
                'user_id': str(user_id)
            },
            UpdateExpression='SET email = :e, user_name = :n, preferences = :p',
            ExpressionAttributeValues={
                ':e': email, ':n': user_name, ':p': preferences
            },
            ReturnValues='UPDATED_NEW'
        )

        return jsonify({'message': 'User updated successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user.
    """
    try:
        users_table.delete_item(
            Key={
                'user_id': str(user_id)
            }
        )
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/users/login', methods=['GET', 'POST'])
def login_user():
    """
    Login a user.
    """
    if request.method == 'POST':
        # todo - Implement login logic
        return "User logged in successfully!"
    else:
        return "Please login to access the application."


@app.route('/transactions', methods=['GET'])
def transactions_management():
    return render_template('transactions_service.html')


# Transaction Service
@app.route('/transactions', methods=['POST'])
def record_transaction():
    """
     Record a new transaction.
    """
    try:
        print("Sending message from main to transaction to transaction SQS")
        primary_key = str(uuid.uuid4())
        new_transaction = {
            'transaction_id': primary_key,
            'user_id': str(request.form["user_id"]),
            'amount': request.form["amount"],
            'trans_date': request.form["date"],
            'category_id': str(request.form["category_id"]),
            'trans_type': request.form["type"],
            'description': request.form["description"]
        }
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps(new_transaction),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'record_transaction',
                    'DataType': 'String'
                }
            }
        )
        print("Message sent to transaction SQS")
        return jsonify({'message': 'Transaction created successfully',
                        'transaction_id': primary_key}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """
    Retrieve details of a specific transaction.
    """
    try:
        print('Send message to get transaction')
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps({'transaction_id': str(transaction_id)}),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'get_transaction',
                    'DataType': 'String'
                }
            }
        )
        print('Message sent to get transaction')
        
        while True:
            # Poll the SQS queue for the response message
            response = sqs_client.receive_message(
                QueueUrl=transaction_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,
                MessageAttributeNames=['All']
            )

            # Check if messages are received
            if 'Messages' in response:
                message = response['Messages'][0]
                handle_type = message['MessageAttributes']['method_sender']['StringValue']
                if handle_type == 'transaction/get_transaction':
                    print('receive transaction details')
                    transaction = json.loads(message['Body'])

                    # Delete the message from the queue after processing
                    sqs_client.delete_message(
                        QueueUrl=transaction_queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    # Check if the transaction is found
                    if transaction:
                        return render_template('transactions_service.html', transaction=transaction), 201
                    else:
                        return jsonify({'error': 'Transaction not found'}), 404        
            else:
                print('No messages in queue, retrying...')
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/transactions/<transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """
    Update a transaction.
    """
    data = request.get_json()
    data['transaction_id'] = str(transaction_id)
    try:
        # send message to transaction service to update the transaction
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps(data),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'update_transaction',
                    'DataType': 'String'
                }
            }
        )
        return jsonify({'message': f'Transaction [{transaction_id}] updated successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/transactions/<transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """
    Delete a transaction.
    """
    try:
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps({'transaction_id': str(transaction_id)}),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'delete_transaction',
                    'DataType': 'String'
                }
            }
        )
        return jsonify({'message': f'Transaction [{transaction_id}] deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/category', methods=['GET'])
def category_management():
    return render_template('category_service.html')


# Category Service
@app.route('/categories', methods=['POST'])
def create_category():
    """
    Create a new category.
    """
    try:
        print("Sending message from main to category to category SQS")
        primary_key = str(uuid.uuid4())
        new_category = {
            'category_id': primary_key,
            'user_id': str(request.form["user_id"]),
            'name': request.form["name"],
            'description': request.form["description"]
        }
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps(new_category),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'create_category',
                    'DataType': 'String'
                }
            }
        )
        print("Message sent to category SQS")        
        return jsonify({'message': 'Category created successfully', 
                        'category_id': primary_key}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/categories/<category_id>', methods=['GET'])
def get_category(category_id):
    """
    Retrieve details of a specific category.
    """
    try:
        print('Send message to get category')
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps({'category_id': str(category_id)}),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'get_category',
                    'DataType': 'String'
                }
            }
        )
        print('Message sent to get category')
        
        while True:
            # Poll the SQS queue for the response message
            response = sqs_client.receive_message(
                QueueUrl=transaction_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,
                MessageAttributeNames=['All']
            )

            # Check if messages are received
            if 'Messages' in response:
                message = response['Messages'][0]
                handle_type = message['MessageAttributes']['method_sender']['StringValue']
                if handle_type == 'category/get_category':
                    print('receive transaction details')
                    category = json.loads(message['Body'])

                    # Delete the message from the queue after processing
                    sqs_client.delete_message(
                        QueueUrl=transaction_queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    # Check if the transaction is found
                    if category:
                        return render_template('category_service.html', category=category), 201
                    else:
                        return jsonify({'error': 'Transaction not found'}), 404        
            else:
                print('No messages in queue, retrying...')
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/categories', methods=['GET'])
def get_categories():
    """
    Retrieve all categories.
    """
    if request.args.get('create'):
        return render_template('create_category.html')
    try:
        print('Send message to get categories')
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps({'category_id': 'all'}),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'get_categories',
                    'DataType': 'String'
                }
            }
        )
        print('Message sent to get categories')

        while True:
            # Poll the SQS queue for the response message
            response = sqs_client.receive_message(
                QueueUrl=transaction_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,
                MessageAttributeNames=['All']
            )

            # Check if messages are received
            if 'Messages' in response:
                message = response['Messages'][0]
                handle_type = message['MessageAttributes']['method_sender']['StringValue']
                if handle_type == 'category/get_categories':
                    print('receive categories details')
                    categories = json.loads(message['Body'])

                    # Delete the message from the queue after processing
                    sqs_client.delete_message(
                        QueueUrl=transaction_queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    # Check if the categories are found
                    if categories:
                        return jsonify(categories), 201
                    else:
                        return jsonify({'error': 'Categories not found'}), 404
            else:
                print('No messages in queue, retrying...')
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/categories/<category_id>', methods=['GET', 'PUT'])
def update_category(category_id):
    """
    Update a category.
    """
    if request.method == 'GET':
        return render_template('update_category.html')
    data = request.get_json()
    data['category_id'] = str(category_id)

    try:
        # send message to category service to update the category
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps(data),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'update_category',
                    'DataType': 'String'
                }
            }
        )
        return jsonify({'message': f'Category [{category_id}] updated successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    """
    Delete a category.
    """
    try:
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps({'transaction_id': str(category_id)}),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'delete_category',
                    'DataType': 'String'
                }
            }
        )
        return jsonify({'message': f'Category [{category_id}] deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Report Generation Service
@app.route('/reports', methods=['POST'])
def generate_report():
    """
    Generate a report.
    """

    # todo - Implement report generation logic
    response = users_table.get_item(Key={'user_id': str(request.form["user_id"])})
    if 'Item' not in response:
        return jsonify({'error': 'User not found'}), 404
    user = response['Item']

    response = transactions_table.scan(FilterExpression=Attr('user_id').eq(user['user_id']))
    transactions = response['Items']

    start_date = datetime.datetime.strptime(request.form["start_date"], "%Y-%m-%d")
    end_date = datetime.datetime.strptime(request.form["end_date"], "%Y-%m-%d")
    
    # filter transactions that between start_date and end_date using dynamodb
    transactions = [transaction for transaction in transactions if start_date <= datetime.datetime.strptime(transaction['trans_date'], "%Y-%m-%d") <= end_date]
    
    report_format = request.form["report_format"]
    if report_format == 'pdf':
        # todo - Implement PDF report generation logic
        return "PDF report generated successfully!"
    elif report_format == 'csv':
        # todo - Implement CSV report generation logic
        return "CSV report generated successfully!"
    elif report_format == 'excel':
        # todo - Implement Excel report generation logic
        return "Excel report generated successfully!"
    else:
        return "Invalid report format. Please use either 'csv', 'pdf' or 'excel'."
    

# Notification Service

# Authentication and Authorization Service


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
