import datetime
import json
import boto3
import os


dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('users') # type: ignore
transactions_table = dynamodb.Table('transactions') # type: ignore
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
                if handle_type == 'generate_report':
                    print('Start Generating Report')
                    try:
                        user_id = json.loads(message['Body'])['user_id']
                        start_date = json.loads(message['Body'])['start_date']
                        end_date = json.loads(message['Body'])['end_date']
                        report_format = json.loads(message['Body'])['report_format']

                        response = users_table.get_item(
                            Key={
                                'user_id': user_id
                            }
                        )
                        if 'Item' not in response:
                            print(f'User [{user_id}] not found')
                            sqs_client.delete_message(
                                QueueUrl=queue_name, 
                                ReceiptHandle=message['ReceiptHandle']
                            )
                            continue
                        user = response['Item']
                        response = transactions_table.query(
                            KeyConditionExpression='user_id = :user_id',
                            ExpressionAttributeValues={
                                ':user_id': user_id
                            }
                        )
                        if 'Items' not in response:
                            print(f'No transactions found for user [{user_id}]')
                            sqs_client.delete_message(
                                QueueUrl=queue_name, 
                                ReceiptHandle=message['ReceiptHandle']
                            )
                            continue
                        transactions = response['Items']
                        print('Generating report for user: ' + user_id)
                        # Generate report
                        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                        
                        # filter transactions that between start_date and end_date using dynamodb
                        transactions = [transaction for transaction in transactions if start_date <= datetime.datetime.strptime(transaction['trans_date'], "%Y-%m-%d") <= end_date]
                        
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
    
                        print('Report generated')
                        sqs_client.delete_message(
                            QueueUrl=queue_name, 
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print('ERROR while generating report: ' + str(e))
                        raise e
        print('...')


if __name__ == '__main__':
    handle_user()
