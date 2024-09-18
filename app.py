import json
import flask
import boto3
import uuid
from flask import render_template, request, jsonify


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
    """
    Home page.
    """
    return render_template('home.html')


@app.route('/home', methods=['GET'])
def home():
    """
    Home page.
    """
    return render_template('home.html')


@app.route('/users', methods=['GET'])
def users_management():
    """
    Users management page.
    """
    return render_template('users_management.html')


# User Management Service
@app.route('/users/register', methods=['POST'])
def register_user():
    """
    Register a new user.
    """
    try:
        print("Sending message from main to user to user SQS")
        primary_key = str(uuid.uuid4())
        new_user = {
            'user_id': primary_key,
            'email': request.form["register-email"],
            'user_name': request.form["register-name"],
            'preferences': request.form["register-preferences"]
        }
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps(new_user),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'register_user',
                    'DataType': 'String'
                }
            }
        )
        print("Message sent to user SQS")
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
        print('Send message to get user')
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps({'user_id': str(user_id)}),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'get_user',
                    'DataType': 'String'
                }
            }
        )   
        print('Message sent to get user')

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
                if handle_type == 'user/get_user':
                    print('receive user details')
                    user = json.loads(message['Body'])

                    # Delete the message from the queue after processing
                    sqs_client.delete_message(
                        QueueUrl=transaction_queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    # Check if the user is found
                    if user:
                        return render_template('users_management.html', user=user), 201
                    else:
                        return jsonify({'error': f'User [{user_id}] not found'}), 404
            else:
                print('No messages in queue, retrying...')
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update user profile.
    """
    data = request.get_json()
    data['user_id'] = str(user_id)

    try:
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps(data),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'update_user',
                    'DataType': 'String'
                }
            }
        )
        return jsonify({'message': f'User [{user_id}] updated successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user.
    """
    try:
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps({'user_id': str(user_id)}),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'delete_user',
                    'DataType': 'String'
                }
            }
        )
        return jsonify({'message': f'User [{user_id}] deleted successfully'})
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
    """
    Transactions management page.
    """
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
    """
    Category management page.
    """
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
    try:
        print("Sending message from main to report generation SQS")
        report_details = {
            'user_id': request.form["user_id"],
            'start_date': request.form["start_date"],
            'end_date': request.form["end_date"],
            'report_format': request.form["report_format"]
        }
        sqs_client.send_message(
            QueueUrl=transaction_queue_url,
            MessageBody=json.dumps(report_details),
            MessageAttributes={
                'method_sender': {
                    'StringValue': 'generate_report',
                    'DataType': 'String'
                }
            }
        )
        print("Message sent to report SQS")
        return jsonify({'message': 'Report generated successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Notification Service

# Authentication and Authorization Service


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
