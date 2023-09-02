import json
import urllib.parse
import boto3
import re
from datetime import datetime
from decimal import Decimal
from re import sub

print('Loading function...')

s3 = boto3.client('s3')

tx = boto3.client('textract')


def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        print("CONTENT TYPE: " + response['ContentType'])
        print("Sending to Textract...")
        
        # Call Amazon Textract
        tx_response = tx.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }) 
        print("Document text detection completed.")
        #print(json.dumps(tx_response))
        
        # Print detected text
        #for item in tx_response["Blocks"]:
        #    if item["BlockType"] == "LINE":
        #        print ( item["Text"])
        # Print  filename, date, total.
        rcpt_total = ''
        rcpt_date = ''
        for item in tx_response["Blocks"]:
            if item["BlockType"] == "LINE":
                match = re.search(r'(?:[\£\$\€\₹]{1}[,\d]+\.?\d*)', item["Text"])
                if match is not None:
                    rcpt_total = match.group(0)
                    rcpt_total = Decimal(sub(r'[^\d.]', '', rcpt_total))

        for item in tx_response["Blocks"]:
            if item["BlockType"] == "LINE":
                match = re.search(r'(\d+/\d+/\d+)',item["Text"])
                if match is not None:
                    rcpt_date = datetime.strptime(match.group(1), '%m/%d/%Y').date()
        if rcpt_date is not None:
            print('Receipt file: {} dated {} for the amount of {}'.format(key,rcpt_date,rcpt_total) )

        # Update Summary file
        s3r = boto3.resource('s3')

        content_object = s3r.Object('expense-tracker-project-try', 'totals.json')
        file_content = content_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
        print(json_content)
        
        
        summary = json_content
        
        sum =summary['total']
        sum = sum + float(rcpt_total)
        summary['total'] = sum

        summary['receipts'].append({'Receipt Date': str(rcpt_date), 'Amount': str(rcpt_total)})
        
        print(json.dumps(summary))
        
        s3.put_object(
            Body=str(json.dumps(summary)),
            Bucket='expense-tracker-project-try',
            Key='totals.json'
        )

    except Exception as e:
        print("Error during text detection")
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
