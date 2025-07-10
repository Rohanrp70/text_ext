def extract_raw_text(response):
    return "\n".join(
        block['Text'] for block in response['Blocks']
        if block['BlockType'] == 'LINE'
    )
