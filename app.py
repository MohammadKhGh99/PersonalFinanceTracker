import datetime
import flask
import boto3
from flask import render_template, request, jsonify
from sqlalchemy.orm import DeclarativeBase, mapped_column, sessionmaker
from sqlalchemy import (Column, String, Integer, JSON, ForeignKey, DateTime,
                        create_engine)

app = flask.Flask(__name__)
engine = create_engine('sqlite:///finance.db')
Session = sessionmaker(bind=engine)
session = Session()


class Base(DeclarativeBase):
    pass


# user table
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String)
    name = Column(String)
    preferences = Column(JSON)

    def __repr__(self) -> str:
        return (f"User(user_id={self.user_id!r}, email={self.email!r}, "
                f"name={self.name!r}, preferences={self.preferences!r})")


class Transaction(Base):
    __tablename__ = 'transactions'
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(ForeignKey("users.user_id"))
    amount = Column(Integer)
    date = Column(String)
    category_id = mapped_column(ForeignKey("categories.category_id"))
    type = Column(String)
    description = Column(String)

    def __repr__(self) -> str:
        return (
            f"Transaction(transaction_id={self.transaction_id!r}, "
            f"user_id={self.user_id!r}, amount={self.amount!r}, "
            f"date={self.date!r}, category_id={self.category_id!r}, "
            f"type={self.type!r}, description={self.description!r})")


class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(ForeignKey("users.user_id"))
    name = Column(String)
    description = Column(String)

    def __repr__(self) -> str:
        return (
            f"Category(category_id={self.category_id!r}, user_id={self.user_id!r}, "
            f"name={self.name!r}, description={self.description!r})")

Base.metadata.create_all(engine)


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
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('users')
    # item = {
    #     'user_id': 10,
    #     'email': 'mohammad.gh454@outlook.com',
    #     'name': 'Mohammad Gh',
    #     'preferences': {
    #         'currency': 'USD',
    #         'timezone': 'UTC'
    #     }
    # }
    # table.put_item(Item=item)
    # print("User added successfully!")
    try:
        new_user = User(
            email=request.form["email"],
            name=request.form["name"],
            preferences=request.form["preferences"]
        )
        session.add(new_user)
        session.commit()
        return jsonify({'message': 'User created successfully',
                        'user_id': new_user.user_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get user profile details.
    """
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('users')
    # response = table.get_item(
    #     Key={
    #         'user_id': int(user_id)
    #     }
    # )
    # return response['Item']
    user = session.query(User).get(user_id)
    if user:
        return repr(user), 201
    else:
        return jsonify({'error': 'Transaction not found'}), 404


@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update user profile.
    """
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('users')
    # table.update_item(
    #     Key={
    #         'user_id': int(user_id)
    #     },
    #     UpdateExpression='SET email = :val1',
    #     ExpressionAttributeValues={
    #         ':val1': 'mohammad.gh45@gmail.com'
    #     }
    # )
    # print("User updated successfully!")
    user = session.query(User).get(user_id)
    if user:
        try:
            user.email = request.form['email']
            user.name = request.form['name']
            user.preferences = request.form['preferences']

            session.commit()
            return jsonify({'message': 'User updated successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'User not found'}), 404



@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user.
    """
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('users')
    # table.delete_item(
    #     Key={
    #         'user_id': int(user_id)
    #     }
    # )
    # print("User deleted successfully!")
    
    user = session.query(User).get(user_id)
    if user:
        try:
            session.delete(user)
            session.commit()
            return jsonify({'message': 'User deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'User not found'}), 404


@app.route('/users/login', methods=['GET', 'POST'])
def login_user():
    """
    Login a user.
    """
    if request.method == 'POST':
        # TODO - Implement login logic
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
        # dynamodb = boto3.resource('dynamodb')
        # table = dynamodb.Table('transactions')
        # item = {
        #     'transaction_id': '12345',
        #     'user_id': 10,
        #     'amount': 100.0,
        #     'date': '2020-01-01',
        #     'category_id': '0',
        #     'type': 'expense',
        #     'description': 'Test transaction'
        # }
        # table.put_item(Item=item)
        # print("Transaction added successfully!")
        try:
            new_transaction = Transaction(
                user_id=int(request.form["user_id"]),
                amount=float(request.form["amount"]),
                date=request.form["date"],
                category_id=int(request.form["category_id"]),
                type=request.form["type"],
                description=request.form["description"]
            )
            session.add(new_transaction)
            session.commit()
            return jsonify({'message': 'Transaction created successfully',
                            'transaction_id': new_transaction.transaction_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return render_template('record_transaction.html')


@app.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """
    Retrieve details of a specific transaction.
    """
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('transactions')
    # response = table.get_item(
    #     Key={
    #         'transaction_id': f'{transaction_id}'
    #     }
    # )
    # return response['Item']
    transaction = session.query(Transaction).get(transaction_id)
    if transaction:
        return repr(transaction), 201
    else:
        return jsonify({'error': 'Transaction not found'}), 404


@app.route('/transactions/<transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """
    Update a transaction.
    """
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('transactions')
    # table.update_item(
    #     Key={
    #         'transaction_id': f'{transaction_id}'
    #     },
    #     UpdateExpression='SET amount = :val1',
    #     ExpressionAttributeValues={
    #         ':val1': 200.0
    #     }
    # )
    # print("Transaction updated successfully!")
    transaction = session.query(Transaction).get(transaction_id)
    if transaction:
        try:
            transaction.user_id = int(request.form['user_id'])
            transaction.amount = float(request.form['amount'])
            transaction.date = request.form['date']
            # transaction.date = datetime.datetime.strptime(request.form['date'],
            #                                               "%Y-%m-%d %H:%M:%S")
            transaction.category_id = int(request.form['category_id'])
            transaction.type = request.form['type']
            transaction.description = request.form['description']

            session.commit()
            return jsonify({'message': 'Transaction updated successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'Transaction not found'}), 404


@app.route('/transactions/<transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """
    Delete a transaction.
    """
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('transactions')
    # table.delete_item(
    #     Key={
    #         'transaction_id': f'{transaction_id}'
    #     }
    # )
    # print("Transaction deleted successfully!")

    transaction = session.query(Transaction).get(transaction_id)
    if transaction:
        try:
            session.delete(transaction)
            session.commit()
            return jsonify({'message': 'Transaction deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'Transaction not found'}), 404


# Category Service
@app.route('/categories', methods=['GET', 'POST'])
def create_category():
    """
    Create a new category.
    """
    if request.method == 'GET':
        return render_template('create_category.html')
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('categories')
    # item = {
    #     'category_id': '0',
    #     'user_id': 10,
    #     'name': 'Test category',
    #     'description': 'Test category description'
    # }
    # table.put_item(Item=item)
    # print("Category added successfully!")

    try:
        new_category = Category(
            user_id=int(request.form["user_id"]),
            name=request.form["name"],
            description=request.form["description"]
        )
        session.add(new_category)
        session.commit()
        return jsonify({'message': 'Category created successfully',
                        'category_id': new_category.category_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/categories', methods=['GET'])
def get_categories():
    """
    Retrieve all categories.
    """
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('categories')
    # response = table.scan()
    # return response['Items']

    categories = session.query(Category).all()
    return jsonify(categories), 201


@app.route('/categories/<category_id>', methods=['PUT'])
def update_category(category_id):
    """
    Update a category.
    """
    # TODO - improve this function to update any attribute of the category
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('categories')
    # table.update_item(
    #     Key={
    #         'category_id': f'{category_id}'
    #     },
    #     UpdateExpression='SET name = :val1',
    #     ExpressionAttributeValues={
    #         ':val1': 'Updated category'
    #     }
    # )
    # print("Category updated successfully!")

    category = session.query(Category).get(category_id)
    if category:
        try:
            category.user_id = int(request.form['user_id'])
            category.name = request.form['name']
            category.description = request.form['description']

            session.commit()
            return jsonify({'message': 'Category updated successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'Category not found'}), 404


@app.route('/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    """
    Delete a category.
    """
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('categories')
    # table.delete_item(
    #     Key={
    #         'category_id': f'{category_id}'
    #     }
    # )
    # print("Category deleted successfully!")

    category = session.query(Category).get(category_id)
    if category:
        try:
            session.delete(category)
            session.commit()
            return jsonify({'message': 'Category deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'Category not found'}), 404


# Report Generation Service

# Notification Service

# Authentication and Authorization Service


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
