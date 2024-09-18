import json
from queue import Queue
from time import sleep
import flask
from flask import render_template, request, jsonify
import uuid
import boto3
import os


dynamodb = boto3.resource('dynamodb')
transactions_table = dynamodb.Table('transactions') # type: ignore
sqs_client = boto3.client('sqs', region_name='us-east-1')

queue_name = os.environ['SQS_QUEUE_NAME']


# Transaction Service
def handle_transaction():
    """
     Handle transactions: record, get, update ,and delete.
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
                if handle_type == 'record_transaction':
                    print('Start Recording Transaction')
                    try:
                        transaction = json.loads(message['Body'])
                        transactions_table.put_item(Item=transaction)
                        print('Transaction recorded')
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print('ERROR while recording transaction: ' + str(e))
                        raise e
                elif handle_type == 'get_transaction':
                    print('Getting transaction')
                    try:
                        transaction_id = json.loads(message['Body'])['transaction_id']
                        response = transactions_table.get_item(
                            Key={
                                'transaction_id': transaction_id
                            }
                        )
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        if 'Item' in response:
                            transaction = response['Item']
                            sqs_client.send_message(
                                QueueUrl=queue_name, 
                                MessageBody=json.dumps(transaction),
                                MessageAttributes={
                                    'method_sender': {
                                        'DataType': 'String',
                                        'StringValue': 'transaction/get_transaction'
                                    }
                                }
                            )
                            print('transaction sent to display it to user')
                            # sleep(10)
                        else:
                            print('Transaction not found')
                    except Exception as e:
                        print('ERROR while get transaction: ' + str(e))
                        raise e
                elif handle_type == 'update_transaction':
                    print('Updating transaction')
                    try:
                        transaction = json.loads(message['Body'])
                        user_id = transaction.get('user_id')
                        amount = transaction.get('amount')
                        trans_date = transaction.get('date')
                        category_id = transaction.get('category_id')
                        trans_type = transaction.get('type')
                        description = transaction.get('description')

                        transactions_table.update_item(
                            Key={
                                'transaction_id': transaction['transaction_id']
                            },
                            UpdateExpression='SET user_id = :ui, amount = :a, trans_date = :d, category_id = :ci, trans_type = :t, description = :desc',
                            ExpressionAttributeValues={
                                ':ui': user_id, ':a': amount, ':d': trans_date, ':ci': category_id, ':t': trans_type, ':desc': description
                            },
                            ReturnValues='UPDATED_NEW'
                        )
                        print('Transaction updated')
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print('ERROR while update transaction: ' + str(e))
                        raise e

                elif handle_type == 'delete_transaction':
                    print('Deleting transaction')
                    try:
                        transaction_id = json.loads(message['Body'])['transaction_id']
                        transactions_table.delete_item(
                            Key={
                                'transaction_id': transaction_id
                            }
                        )
                        print('Transaction deleted')
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print('ERROR while delete transaction: ' + str(e))
                        raise e
        print('...')


if __name__ == '__main__':
    handle_transaction()
