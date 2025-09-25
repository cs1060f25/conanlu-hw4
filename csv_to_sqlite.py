#!/usr/bin/env python3
"""
CSV to SQLite Converter

This script converts a CSV file with a header row to a SQLite database.
The header row should contain valid SQL column names (no spaces, no special characters).

Usage: python csv_to_sqlite.py <database_name> <csv_file>
"""

import csv
import sqlite3
import sys
import os


def create_table_from_csv(cursor, csv_file, table_name):
    """
    Create a SQLite table based on the CSV header row.
    Returns the column names for data insertion.
    """
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # Get the header row
        
        # Validate that we have column names
        if not header:
            raise ValueError("CSV file appears to be empty or has no header row")
        
        # Create table with column names from header (no quotes around column names)
        column_definitions = ', '.join(f"{col} TEXT" for col in header)
        create_table_sql = f"CREATE TABLE {table_name} ({column_definitions})"
        
        cursor.execute(create_table_sql)
        return header


def insert_csv_data(cursor, csv_file, column_names, table_name):
    """
    Insert data from CSV file into the SQLite table.
    """
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        # Prepare the INSERT statement (no quotes around column names)
        placeholders = ', '.join(['?' for _ in column_names])
        column_list = ', '.join(column_names)
        insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
        
        # Insert each row
        for row in reader:
            values = [row.get(col, '') for col in column_names]
            cursor.execute(insert_sql, values)


def main():
    """
    Main function to handle command line arguments and convert CSV to SQLite.
    """
    if len(sys.argv) != 3:
        print("Usage: python csv_to_sqlite.py <database_name> <csv_file>")
        print("Example: python csv_to_sqlite.py data.db input.csv")
        sys.exit(1)
    
    database_name = sys.argv[1]
    csv_file = sys.argv[2]
    
    # Validate that CSV file exists
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found")
        sys.exit(1)
    
    try:
        # Connect to SQLite database (creates if doesn't exist)
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()
        
        # Extract table name from CSV filename (remove .csv extension)
        table_name = os.path.splitext(os.path.basename(csv_file))[0]
        
        # Drop existing table if it exists
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Create table from CSV header
        print(f"Reading CSV file: {csv_file}")
        column_names = create_table_from_csv(cursor, csv_file, table_name)
        print(f"Created table '{table_name}' with columns: {', '.join(column_names)}")
        
        # Insert data from CSV
        print("Inserting data...")
        insert_csv_data(cursor, csv_file, column_names, table_name)
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        print(f"Successfully converted CSV to SQLite database: {database_name}")
        print(f"Table name: {table_name}")
        
    except FileNotFoundError:
        print(f"Error: Could not find file '{csv_file}'")
        sys.exit(1)
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"Error with SQLite database: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
