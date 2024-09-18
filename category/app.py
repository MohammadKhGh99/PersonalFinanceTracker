import json
from queue import Queue
from time import sleep
import flask
from flask import render_template, request, jsonify
import uuid
import boto3
import os


dynamodb = boto3.resource('dynamodb')
categories_table = dynamodb.Table('categories') # type: ignore
sqs_client = boto3.client('sqs', region_name='us-east-1')

queue_name = os.environ['SQS_QUEUE_NAME']


# Category Service
def handle_category():
    """
     Handle categories: record, get, update ,and delete.
    """
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_name, 
            MaxNumberOfMessages=1, 
            WaitTimeSeconds=5, 
            MessageAttributeNames=['All']
        )
        
        if 'Messages' in response:
            print('Receiving message')
            message = response['Messages'][0]
            if 'MessageAttributes' in message:
                handle_type = message['MessageAttributes']['method_sender']['StringValue']
                if handle_type == 'create_category':
                    print('Start Creating Category')
                    try:
                        category = json.loads(message['Body'])
                        categories_table.put_item(Item=category)
                        print('Category created')
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print('ERROR while creating category: ' + str(e))
                        raise e
                elif handle_type == 'get_category':
                    print('Getting Category')
                    try:
                        category_id = json.loads(message['Body'])['category_id']
                        response = categories_table.get_item(
                            Key={
                                'category_id': category_id
                            }
                        )
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        if 'Item' in response:
                            category = response['Item']
                            sqs_client.send_message(
                                QueueUrl=queue_name, 
                                MessageBody=json.dumps(category),
                                MessageAttributes={
                                    'method_sender': {
                                        'DataType': 'String',
                                        'StringValue': 'category/get_category'
                                    }
                                }
                            )
                            print('category sent to display it to user')
                            # sleep(10) 
                        else:
                            print('Category not found')
                    except Exception as e:
                        print('ERROR while get category: ' + str(e))
                        raise e
                elif handle_type == 'get_categories':
                    print('Getting All Categories')
                    try:
                        response = categories_table.scan()
                        categories = { i + 1: repr(response['Items'][i]) for i in range(len(response['Items']))}
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        sqs_client.send_message(
                            QueueUrl=queue_name, 
                            MessageBody=json.dumps(categories),
                            MessageAttributes={
                                'method_sender': {
                                    'DataType': 'String',
                                    'StringValue': 'category/get_categories'
                                }
                            }
                        )
                        print('categories sent to display it to user')
                        # sleep(10)
                    except Exception as e:
                        print('ERROR while getting categories: ' + str(e))
                        raise e
                elif handle_type == 'update_category':
                    print('Updating category')
                    try:
                        category = json.loads(message['Body'])
                        user_id = category.get('user_id')
                        name = category.get('name')
                        description = category.get('description')

                        categories_table.update_item(
                            Key={
                                'category_id': category['category_id']
                            },
                            UpdateExpression='SET user_id = :ui, name = :n, description = :d',
                            ExpressionAttributeValues={
                                ':ui': user_id, ':n': name, ':d': description
                            },
                            ReturnVlues='UPDATED_NEW'
                        )
                        
                        print('Category updated')
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print('ERROR while update category: ' + str(e))
                        raise e

                elif handle_type == 'delete_category':
                    print('Deleting category')
                    try:
                        category_id = json.loads(message['Body'])['category_id']
                        categories_table.delete_item(
                            Key={
                                'category_id': category_id
                            }
                        )
                        print('Category deleted')
                        sqs_client.delete_message(QueueUrl=queue_name, ReceiptHandle=message['ReceiptHandle'])
                    except Exception as e:
                        print('ERROR while delete category: ' + str(e))
                        raise e
        print('...')


if __name__ == '__main__':
    handle_category()
