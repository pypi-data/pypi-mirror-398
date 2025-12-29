#!/usr/bin/env python3
"""
Script to extract data from PostgreSQL INSERT statements and convert to JSON.
"""

import re
import json
import os
from pathlib import Path

def parse_insert_statement(insert_sql, table_name):
    """
    Parse a PostgreSQL INSERT statement and return the data as a list of dictionaries.

    Args:
        insert_sql (str): The INSERT statement
        table_name (str): Name of the table to extract data for

    Returns:
        list: List of dictionaries containing the parsed data
    """
    # Pattern to match INSERT INTO table_name (columns) VALUES (values)
    pattern = rf"INSERT INTO {table_name} \((.*?)\) VALUES\s*(.*?);"

    match = re.search(pattern, insert_sql, re.DOTALL | re.IGNORECASE)
    if not match:
        return []

    columns_str, values_str = match.groups()

    # Parse column names
    columns = [col.strip().strip('"') for col in columns_str.split(',')]

    # Parse values - handle multiple rows and complex values
    values_data = []
    values_pattern = r"\((.*?)\)"
    values_matches = re.findall(values_pattern, values_str, re.DOTALL)

    for value_match in values_matches:
        # Split by comma but be careful with quoted strings and NULL values
        values = []
        current_value = ""
        in_quotes = False
        quote_char = None

        i = 0
        while i < len(value_match):
            char = value_match[i]

            if not in_quotes and char in ("'", '"'):
                in_quotes = True
                quote_char = char
                current_value += char
            elif in_quotes and char == quote_char:
                # Check if this is an escaped quote or end of string
                if i + 1 < len(value_match) and value_match[i + 1] == quote_char:
                    # Escaped quote
                    current_value += char + char
                    i += 1
                else:
                    # End of quoted string
                    in_quotes = False
                    current_value += char
            elif not in_quotes and char == ',':
                # End of value
                values.append(current_value.strip())
                current_value = ""
            else:
                current_value += char

            i += 1

        # Add the last value
        if current_value.strip():
            values.append(current_value.strip())

        # Convert values to appropriate types
        parsed_values = []
        for value in values:
            value = value.strip()
            if value.upper() == 'NULL':
                parsed_values.append(None)
            elif value.upper() in ('TRUE', 'FALSE'):
                parsed_values.append(value.upper() == 'TRUE')
            elif value.startswith("'") and value.endswith("'"):
                # Remove quotes and handle escaped quotes
                parsed_value = value[1:-1].replace("''", "'")
                parsed_values.append(parsed_value)
            elif value.replace('.', '').replace('-', '').isdigit():
                # Try to parse as number
                if '.' in value:
                    parsed_values.append(float(value))
                else:
                    parsed_values.append(int(value))
            else:
                parsed_values.append(value)

        # Create dictionary
        row_dict = dict(zip(columns, parsed_values))
        values_data.append(row_dict)

    return values_data

def extract_table_data(sql_file_path, table_name):
    """
    Extract data for a specific table from the SQL file.

    Args:
        sql_file_path (str): Path to the SQL file
        table_name (str): Name of the table to extract

    Returns:
        list: List of dictionaries containing table data
    """
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Find all INSERT statements for this table
    all_data = []

    # Split by INSERT statements for this table
    insert_pattern = rf"INSERT INTO {table_name}.*?;"
    matches = re.findall(insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)

    for match in matches:
        data = parse_insert_statement(match, table_name)
        all_data.extend(data)

    return all_data

def main():
    """Main function to extract and save data as JSON."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    sql_file_path = project_root.parent.parent / "tables" / "kitex_common_postgres.sql"
    data_dir = project_root / "kite_common" / "data"

    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)

    # Tables to extract
    tables = ['countries', 'currencies', 'timezones', 'languages', 'error_codes']

    for table in tables:
        print(f"Extracting data for table: {table}")
        data = extract_table_data(sql_file_path, table)

        if data:
            # Save to JSON file
            json_file_path = data_dir / f"{table}.json"
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(data)} records to {json_file_path}")
        else:
            print(f"No data found for table: {table}")

if __name__ == "__main__":
    main()
