import boto3
import json
import urllib.parse
import uuid
import time
from datetime import datetime
import os

from textract_utils import extract_key_values, extract_tables
from common import extract_raw_text
from gpt_fallback import extract_with_openai

s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('DocumentMetadata')

openai_api_key = os.environ.get('OPENAI_API_KEY')

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    print(f"✅ Processing document: {key} from bucket: {bucket}")

    try:
        # Choose Textract method
        if key.lower().endswith('.pdf'):
            print("📄 PDF detected – using async Textract")
            job = textract.start_document_analysis(
                DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': key}},
                FeatureTypes=["FORMS", "TABLES"]
            )
            job_id = job['JobId']
            while True:
                result = textract.get_document_analysis(JobId=job_id)
                status = result['JobStatus']
                print(f"⏳ Textract status: {status}")
                if status == 'SUCCEEDED':
                    break
                elif status == 'FAILED':
                    raise Exception("Textract job failed.")
                time.sleep(2)
            response = result
        else:
            print("🖼️ Image detected – using sync Textract")
            response = textract.analyze_document(
                Document={'S3Object': {'Bucket': bucket, 'Name': key}},
                FeatureTypes=["FORMS", "TABLES"]
            )

        print(f"🔍 Block count: {len(response['Blocks'])}")

        # Textract extraction
        extracted_fields = extract_key_values(response)
        tables = extract_tables(response)

        print("📋 Extracted Fields:")
        print(json.dumps(extracted_fields, indent=2))

        print("📊 Extracted Tables:")
        print(json.dumps(tables, indent=2))

        filename_lower = key.lower()

        # Extract raw text always
        raw_text = extract_raw_text(response)

        # Basic heuristics
        valid_fields = {k: v for k, v in extracted_fields.items() if v.strip()}
        total_field_length = sum(len(v.strip()) for v in valid_fields.values())
        average_field_length = total_field_length / len(valid_fields) if valid_fields else 0

        print(f"📊 Fallback Heuristics - Field Count: {len(valid_fields)}, Total Length: {total_field_length}, Avg Field Length: {average_field_length:.2f}")

        # 🔍 Trigger fallback if the filename contains 'resume' or if fields are too sparse
        if 'resume' in filename_lower or not valid_fields or total_field_length < 50 or average_field_length < 10:
            print("🧠 Fallback: Using GPT to extract structured fields.")
            extracted_fields = extract_with_openai(raw_text, openai_api_key)

        if not extracted_fields and not tables:
            print("⚠️ Still no usable data. Skipping DynamoDB insert.")
            return {
                'statusCode': 204,
                'body': json.dumps(f"No usable content extracted from {key}")
            }

        doc_id = str(uuid.uuid4())
        item = {
            'doc_id': doc_id,
            'filename': key,
            'upload_time': datetime.utcnow().isoformat(),
            'extracted_fields': extracted_fields,
            'tables': tables,
            'raw_text': raw_text 
        }

        table.put_item(Item=item)
        print(f"✅ Stored in DynamoDB with doc_id: {doc_id}")

        return {
            'statusCode': 200,
            'body': json.dumps(f"Document {key} processed successfully with ID {doc_id}")
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps("Failed to process document.")
        }
