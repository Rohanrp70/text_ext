import boto3
import json
import urllib.parse
import uuid
from datetime import datetime

s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('DocumentMetadata')

def lambda_handler(event, context):
    # Get bucket and file name from S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    print(f"Processing document: {key} from bucket: {bucket}")

    # Call Textract
    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=["TABLES", "FORMS"]
    )

    # Extract key-value pairs and tables
    extracted_data = extract_key_values(response)
    tables = extract_tables(response)

    # Generate a document ID
    doc_id = str(uuid.uuid4())

    # Save to DynamoDB
    table.put_item(Item={
        'doc_id': doc_id,
        'filename': key,
        'upload_time': datetime.utcnow().isoformat(),
        'extracted_fields': extracted_data,
        'tables': tables
    })

    return {
        'statusCode': 200,
        'body': json.dumps(f"Processed document {key} and stored with ID {doc_id}")
    }


def extract_key_values(response):
    blocks = response['Blocks']
    key_map = {}
    value_map = {}
    block_map = {}

    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if "KEY" in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    def get_text(result_block):
        text = ""
        if "Relationships" in result_block:
            for rel in result_block['Relationships']:
                if rel['Type'] == 'CHILD':
                    for cid in rel['Ids']:
                        word = block_map[cid]
                        if word['BlockType'] == 'WORD':
                            text += word['Text'] + " "
        return text.strip()

    extracted = {}

    for key_id, key_block in key_map.items():
        key_text = get_text(key_block)
        value_block = None
        for rel in key_block.get('Relationships', []):
            if rel['Type'] == 'VALUE':
                for value_id in rel['Ids']:
                    value_block = value_map.get(value_id)
                    if value_block:
                        val_text = get_text(value_block)
                        extracted[key_text] = val_text

    return extracted


def extract_tables(response):
    blocks = response['Blocks']
    block_map = {block['Id']: block for block in blocks}
    table_data = []

    for block in blocks:
        if block['BlockType'] == 'TABLE':
            rows = []
            for relationship in block.get('Relationships', []):
                if relationship['Type'] == 'CHILD':
                    for cell_id in relationship['Ids']:
                        cell = block_map[cell_id]
                        if cell['BlockType'] == 'CELL':
                            row_index = cell['RowIndex']
                            col_index = cell['ColumnIndex']
                            content = ""
                            if 'Relationships' in cell:
                                for rel in cell['Relationships']:
                                    if rel['Type'] == 'CHILD':
                                        for word_id in rel['Ids']:
                                            word = block_map.get(word_id)
                                            if word and word['BlockType'] == 'WORD':
                                                content += word['Text'] + " "
                            content = content.strip()

                            # Ensure rows list has enough rows
                            while len(rows) < row_index:
                                rows.append([])
                            row = rows[row_index - 1]

                            # Ensure row has enough columns
                            while len(row) < col_index:
                                row.append("")
                            row[col_index - 1] = content
            table_data.append(rows)

    return table_data
