def extract_key_values(response):
    blocks = response['Blocks']
    key_map, value_map, block_map = {}, {}, {}

    for block in blocks:
        block_map[block['Id']] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if "KEY" in block.get('EntityTypes', []):
                key_map[block['Id']] = block
            else:
                value_map[block['Id']] = block

    def get_text(block):
        return " ".join(
            word['Text'] for rel in block.get('Relationships', [])
            for cid in rel.get('Ids', [])
            if (word := block_map.get(cid)) and word['BlockType'] == 'WORD'
        )

    extracted = {}
    for key_id, key_block in key_map.items():
        key_text = get_text(key_block)
        for rel in key_block.get('Relationships', []):
            if rel['Type'] == 'VALUE':
                for value_id in rel['Ids']:
                    value_block = value_map.get(value_id)
                    if value_block:
                        extracted[key_text] = get_text(value_block)
    return extracted


def extract_tables(response):
    blocks = response['Blocks']
    block_map = {block['Id']: block for block in blocks}
    tables = []

    for block in blocks:
        if block['BlockType'] == 'TABLE':
            rows = []
            for rel in block.get('Relationships', []):
                if rel['Type'] == 'CHILD':
                    for cell_id in rel['Ids']:
                        cell = block_map[cell_id]
                        if cell['BlockType'] == 'CELL':
                            r, c = cell['RowIndex'], cell['ColumnIndex']
                            content = " ".join(
                                word['Text'] for cr in cell.get('Relationships', [])
                                for wid in cr.get('Ids', [])
                                if (word := block_map.get(wid)) and word['BlockType'] == 'WORD'
                            )
                            while len(rows) < r:
                                rows.append([])
                            row = rows[r - 1]
                            while len(row) < c:
                                row.append("")
                            row[c - 1] = content.strip()
            tables.append(rows)
    return tables
