import datetime
import flask
import boto3
import uuid
from boto3.dynamodb.conditions import Key, Attr
from flask import render_template, request, jsonify
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
transactions_table = dynamodb.Table('transactions') # type: ignore
categories_table = dynamodb.Table('categories') # type: ignore


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
            'email': request.form["email"],
            'name': request.form["name"],
            'preferences': request.form["preferences"]
        }
        users_table.put_item(Item=new_user)

        # new_user = User(
        #     email=request.form["email"],
        #     name=request.form["name"],
        #     preferences=request.form["preferences"]
        # )
        # session.add(new_user)
        # session.commit()
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
        # user = session.get(User, user_id)
        if 'Item' in response:
            user = response['Item']
            return render_template('update_user.html', user=user), 201
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
    email = data.get('email')
    name = data.get('name')
    preferences = data.get('preferences')

    try:
        users_table.update_item(
            Key={
                'user_id': str(user_id)
            },
            UpdateExpression='SET email = :e, name = :n, preferences = :p',
            ExpressionAttributeValues={
                ':e': email, ':n': name, ':p': preferences
            },
            ReturnValues='UPDATED_NEW'
        )

        return jsonify({'message': 'User updated successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


    # user = session.get(User, user_id)
    # if user:
    #     try:
    #         # Retrieve the JSON data from the request
    #         user.email = data.get('email')  # Use .get() to avoid KeyError
    #         user.name = data.get('name')  # Use .get() to avoid KeyError
    #         user.preferences = data.get('preferences')

    #         session.commit()
    #     except Exception as e:
    #         return jsonify({'error': str(e)}), 400
    # else:
    #     return jsonify({'error': 'User not found'}), 404
    
    # print("User updated successfully!")


@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user.
    """
    # user = session.get(User, user_id)
    # if user:
    #     try:
    #         session.delete(user)
    #         session.commit()
    #         return jsonify({'message': 'User deleted successfully'})
    #     except Exception as e:
    #         return jsonify({'error': str(e)}), 400
    # else:
    #     return jsonify({'error': 'User not found'}), 404
    
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


# Transaction Service
@app.route('/transactions', methods=['GET', 'POST'])
def record_transaction():
    """
     Record a new transaction.
    """
    if request.method == 'POST':
        try:
            primary_key = str(uuid.uuid4())
            new_transaction = {
                'transaction_id': primary_key,
                'user_id': str(request.form["user_id"]),
                'amount': request.form["amount"],
                'date': request.form["date"],
                'category_id': str(request.form["category_id"]),
                'type': request.form["type"],
                'description': request.form["description"]
            }
            transactions_table.put_item(Item=new_transaction)
            # new_transaction = Transaction(
            #     user_id=int(request.form["user_id"]),
            #     amount=float(request.form["amount"]),
            #     date=request.form["date"],
            #     category_id=int(request.form["category_id"]),
            #     type=request.form["type"],
            #     description=request.form["description"]
            # )
            # session.add(new_transaction)
            # session.commit()
            return jsonify({'message': 'Transaction created successfully',
                            'transaction_id': primary_key}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return render_template('record_transaction.html')


@app.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """
    Retrieve details of a specific transaction.
    """
    # transaction = session.get(Transaction, transaction_id)
    # if transaction:
    #     return render_template('update_transaction.html', transaction=transaction), 201
    # else:
    #     return jsonify({'error': 'Transaction not found'}), 404
    
    try:
        response = transactions_table.get_item(
            Key={
                'transaction_id': str(transaction_id)
            }
        )
        if 'Item' in response:
            transaction = response['Item']
            return render_template('update_transaction.html', transaction=transaction), 201
        else:
            return jsonify({'error': 'Transaction not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/transactions/<transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """
    Update a transaction.
    """
    # transaction = session.get(Transaction, transaction_id)
    # if transaction:
    #     try:
    #         transaction.user_id = int(data.get('user_id'))
    #         transaction.amount = data.get('amount')
    #         transaction.date = data.get('date')
    #         transaction.category_id = int(data.get('category_id'))
    #         transaction.type = data.get('type')
    #         transaction.description = data.get('description')

    #         session.commit()
    #         return jsonify({'message': 'Transaction updated successfully'}), 201
    #     except Exception as e:
    #         return jsonify({'error': str(e)}), 400
    # else:
    #     return jsonify({'error': 'Transaction not found'}), 404
    

    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    trans_date = data.get('date')
    category_id = data.get('category_id')
    trans_type = data.get('type')
    description = data.get('description')

    try:
        transactions_table.update_item(
            Key={
                'transaction_id': str(transaction_id)
            },
            UpdateExpression='SET user_id = :ui, amount = :a, trans_date = :d, category_id = :ci, trans_type = :t, description = :desc',
            ExpressionAttributeValues={
                ':ui': user_id, ':a': amount, ':d': trans_date, ':ci': category_id, ':t': trans_type, ':desc': description
            },
            ReturnValues='UPDATED_NEW'
        )
        return jsonify({'message': 'Transaction updated successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/transactions/<transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """
    Delete a transaction.
    """
    # transaction = session.get(Transaction, transaction_id)
    # if transaction:
    #     try:
    #         session.delete(transaction)
    #         session.commit()
    #         return jsonify({'message': 'Transaction deleted successfully'})
    #     except Exception as e:
    #         return jsonify({'error': str(e)}), 400
    # else:
    #     return jsonify({'error': 'Transaction not found'}), 404
    
    try:
        transactions_table.delete_item(
            Key={
                'transaction_id': str(transaction_id)
            }
        )
        return jsonify({'message': 'Transaction deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    


# Category Service
@app.route('/categories', methods=['POST'])
def create_category():
    """
    Create a new category.
    """
    # try:
    #     new_category = Category(
    #         user_id=int(request.form["user_id"]),
    #         name=request.form["name"],
    #         description=request.form["description"]
    #     )
    #     session.add(new_category)
    #     session.commit()
    #     return jsonify({'message': 'Category created successfully',
    #                     'category_id': new_category.category_id}), 201
    # except Exception as e:
    #     return jsonify({'error': str(e)}), 400
    
    try:
        primary_key = str(uuid.uuid4())
        new_category = {
            'category_id': primary_key,
            'user_id': str(request.form["user_id"]),
            'name': request.form["name"],
            'description': request.form["description"]
        }
        categories_table.put_item(Item=new_category)
        return jsonify({'message': 'Category created successfully', 'category_id': primary_key}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/categories', methods=['GET'])
def get_categories():
    """
    Retrieve all categories.
    """
    if request.args.get('create'):
        return render_template('create_category.html')
    
    # try:
    #     categories = session.query(Category).all()
    #     return jsonify({ i + 1: repr(categories[i]) for i in range(len(categories))}), 201
    # except Exception as e:
    #     return jsonify({'error': str(e)}), 400

    try:
        response = categories_table.scan()
        categories = response['Items']
        return jsonify({ i + 1: repr(categories[i]) for i in range(len(categories))}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/categories/<category_id>', methods=['PUT'])
def update_category(category_id):
    """
    Update a category.
    """
    # category = session.get(Category, category_id)
    # if category:
    #     try:
    #         data = request.get_json()
    #         category.user_id = int(data.get('user_id'))
    #         category.name = data.get('name')
    #         category.description = data.get('description')

    #         session.commit()
    #         return jsonify({'message': 'Category updated successfully'}), 201
    #     except Exception as e:
    #         return jsonify({'error': str(e)}), 400
    # else:
    #     return jsonify({'error': 'Category not found'}), 404
    
    data = request.get_json()
    user_id = data.get('user_id')
    name = data.get('name')
    description = data.get('description')

    try:
        categories_table.update_item(
            Key={
                'category_id': str(category_id)
            },
            UpdateExpression='SET user_id = :ui, name = :n, description = :d',
            ExpressionAttributeValues={
                ':ui': user_id, ':n': name, ':d': description
            },
            ReturnVlues='UPDATED_NEW'
        )
        return jsonify({'message': 'Category updated successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    """
    Delete a category.
    """
    # category = session.get(Category, category_id)
    # if category:
    #     try:
    #         session.delete(category)
    #         session.commit()
    #         return jsonify({'message': 'Category deleted successfully'})
    #     except Exception as e:
    #         return jsonify({'error': str(e)}), 400
    # else:
    #     return jsonify({'error': 'Category not found'}), 404
    
    try:
        categories_table.delete_item(
            Key={
                'category_id': str(category_id)
            }
        )
        return jsonify({'message': 'Category deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Report Generation Service
@app.route('/reports', methods=['POST'])
def generate_report():
    """
    Generate a report.
    """

    # todo - Implement report generation logic
    # user = session.get(User, int(request.form["user_id"]))
    response = users_table.get_item(Key={'user_id': str(request.form["user_id"])})
    if 'Item' not in response:
        return jsonify({'error': 'User not found'}), 404
    user = response['Item']

    response = transactions_table.scan(FilterExpression=Attr('user_id').eq(user['user_id']))
    transactions = response['Items']

    # transactions = session.query(Transaction).filter_by(user_id=user.user_id).all()
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
