import json
import boto3
import os


dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('users') # type: ignore
sqs_client = boto3.client('sqs', region_name='us-east-1')

queue_name = os.environ['SQS_QUEUE_NAME']


# Users Management
def handle_user():
    """
     Handle users: register, get, update ,and delete.
    """
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_name, 
            MaxNumberOfMessages=1, 
            WaitTimeSeconds=5, 
            MessageAttributeNames=['All']
        )
        
        if 'Messages' in response:
            print('Receiving message for users management')
            message = response['Messages'][0]
            if 'MessageAttributes' in message:
                handle_type = message['MessageAttributes']['method_sender']['StringValue']
                if handle_type == 'register_user':
                    print('Start Recording User')
                    try:
                        user = json.loads(message['Body'])
                        users_table.put_item(Item=user)
                        print('User registered')
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print('ERROR while registering user: ' + str(e))
                        raise e
                elif handle_type == 'get_user':
                    print('Getting user')
                    try:
                        user_id = json.loads(message['Body'])['user_id']
                        response = users_table.get_item(
                            Key={
                                'user_id': user_id
                            }
                        )
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        if 'Item' in response:
                            user = response['Item']
                            sqs_client.send_message(
                                QueueUrl=queue_name, 
                                MessageBody=json.dumps(user),
                                MessageAttributes={
                                    'method_sender': {
                                        'DataType': 'String',
                                        'StringValue': 'user/get_user'
                                    }
                                }
                            )
                            print('user sent to display it to user')
                            # sleep(10)
                        else:
                            print('User not found')
                    except Exception as e:
                        print('ERROR while get user: ' + str(e))
                        raise e
                elif handle_type == 'update_user':
                    print('Updating user')
                    try:
                        user = json.loads(message['Body'])
                        email = user.get('update-email')
                        user_name = user.get('update-name')
                        preferences = user.get('update-preferences')
                        user_id = user.get('user_id')

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
                        print('User updated')
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print('ERROR while update user: ' + str(e))
                        raise e

                elif handle_type == 'delete_user':
                    print('Deleting user')
                    try:
                        user_id = json.loads(message['Body'])['user_id']
                        users_table.delete_item(
                            Key={
                                'user_id': user_id
                            }
                        )
                        print('User deleted')
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print('ERROR while delete user: ' + str(e))
                        raise e
        print('...')


if __name__ == '__main__':
    handle_user()
