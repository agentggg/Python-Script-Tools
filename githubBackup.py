#!/usr/bin/env python3
import requests
import base64
import json
import mysql.connector
from datetime import datetime
import logging
import os
import environ
# Create an instance of environ.Env
env = environ.Env()

# Read environment variables from the specified .env file
env_file_path = os.path.join(os.path.dirname(__file__), '.env')

# Configure logging
log_filename = 'databaseBackupLog.log'
logging.basicConfig(filename=log_filename, level=logging.DEBUG)
with open(env_file_path, 'r') as file:
    # Read the entire file as a single string
    file_contents = file.read()

    # You can now work with the file_contents variable
    print(file_contents)


try:
    # Access environment variables
    OWNER = env('OWNER')
    REPO = env('REPO')
    AUTH = env('AUTH')
    DB_USER = env('DB_USER')
    DB_PASSWORD = env('DB_PASSWORD')
    DB_HOST = env('DB_HOST')
    DB_NAME = env('DB_NAME')
    DB_PORT = env('DB_PORT', default=3306, cast=int)

    class DatetimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            return super().default(obj)

    # Define your GitHub personal access token
    auth_token = AUTH

    # Define the owner and repo values for your GitHub repository
    owner = OWNER
    repo = REPO

    # MySQL database configuration
    db_config = {
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,
        'database': DB_NAME,
        'port': DB_PORT,
    }

    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(**db_config)

        # Create a cursor for executing SQL queries
        cursor = connection.cursor()

        try:
            # Execute the SQL query to retrieve all table names
            cursor.execute('SHOW TABLES')

            # Fetch all rows from the query result
            tables = cursor.fetchall()

            # Create a dictionary to store table data
            table_data = {}

            # Iterate through each table
            for table in tables:
                table_name = table[0]

                # Execute a SELECT query to retrieve all rows from the table
                cursor.execute(f'SELECT * FROM {table_name}')

                # Fetch all rows from the query result
                rows = cursor.fetchall()

                # Convert the rows to a list of dictionaries (each row as a dictionary)
                table_data[table_name] = [dict(zip(cursor.column_names, row)) for row in rows]

            # Convert the table data to JSON using the custom encoder
            json_data = json.dumps(table_data, indent=4, cls=DatetimeEncoder)

            # Generate a unique file name for the JSON dump
            file_name = datetime.now().strftime('%m-%d-%Y %H:%M:%S:%f') + '_data.json'

            # GitHub API URL for creating or updating a file
            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_name}'

            # Encode the JSON data as Base64
            encoded_json_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')

            # Request payload with file data
            payload = {
                'message': f'Add file {file_name}',
                'content': encoded_json_data,
                'branch': 'main',  # Specify the branch to create/update the file
            }

            # Request headers including the GitHub API version and authentication
            headers = {
                'Authorization': f'token {auth_token}',
                'Accept': 'application/vnd.github.v3+json',  # Specify the API version
            }

            # Make the PUT request to create or update the file
            response = requests.put(url, json=payload, headers=headers)

            # Check the response status code
            if response.status_code == 201:
                print("File uploaded successfully.")
            else:
                print(f"Error uploading file to GitHub: {response.text}")

        except Exception as db_error:
            print(f"Database Error: {db_error}")
            logging.exception(db_error)

        finally:
            # Close the database connection
            cursor.close()
            connection.close()

    except mysql.connector.Error as conn_error:
        print(f"Database Connection Error: {conn_error}")
        logging.exception(conn_error)

except Exception as env_error:
    print(f"Environment Variable Error: {env_error}")
    logging.exception(env_error)