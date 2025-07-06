# CREATE AND POPULATE DATABASE for FLIGHTS

import numpy as np
import pandas as pd
import sqlite3 as sql
import plotly.express as px
import os
import glob
import json
from datetime import datetime
import threading

# Thread-local storage for database connections
thread_local = threading.local()

def get_db_connection():
    """Get a thread-safe database connection"""
    if not hasattr(thread_local, 'connection'):
        db_path = 'flight.sqlite'
        thread_local.connection = sql.connect(db_path, timeout=30)
        thread_local.connection.execute('PRAGMA journal_mode=WAL;')
        thread_local.cursor = thread_local.connection.cursor()
        
        # Create table if it doesn't exist
        thread_local.cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number TEXT NOT NULL,
            airline TEXT,
            aircraft TEXT,
            flight_status TEXT,
            departure_airport_iata TEXT,
            departure_airport_name TEXT,
            departure_airport_city TEXT,
            departure_airport_country TEXT,
            departure_airport_timezone TEXT,
            destination_airport_iata TEXT,
            destination_airport_name TEXT,
            destination_airport_city TEXT,
            destination_airport_country TEXT,
            destination_airport_timezone TEXT,
            scheduled_departure DATETIME,
            scheduled_arrival DATETIME,
            created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        thread_local.connection.commit()
    
    return thread_local.connection, thread_local.cursor
    

def populate_db(dic):
    connection, cursor = get_db_connection()
    flight_details = dic["airport"]["pluginData"]["schedule"]["departures"]["data"]

    departure_airport_iata = dic["airport"]["pluginData"]["details"]["code"]["iata"]
    departure_airport_name = dic["airport"]["pluginData"]["details"]["name"]
    departure_airport_country = dic["airport"]["pluginData"]["details"]["position"]["country"]["name"]
    departure_airport_city = dic["airport"]["pluginData"]["details"]["position"]["region"]["city"]
    departure_airport_timezone = dic["airport"]["pluginData"]["details"]["timezone"]["name"]

    for i in flight_details:
        flight_number = i["flight"]["identification"]["number"]["default"]
        if flight_number is None :
            flight_number = i["flight"]["identification"]["row"]
        aircraft = i["flight"]["aircraft"]["model"]["code"]+" "+i["flight"]["aircraft"]["model"]["text"]
        try:
            airline = i["flight"]["airline"]["name"]
        except :
            airline = ""
        
        destination_airport_iata = i["flight"]["airport"]["destination"]["code"]["iata"]
        destination_airport_timezone = i["flight"]["airport"]["destination"]["timezone"]["name"]
        destination_airport_name = i["flight"]["airport"]["destination"]["name"]
        destination_airport_country = i["flight"]["airport"]["destination"]["position"]["country"]["name"]
        destination_airport_city = i["flight"]["airport"]["destination"]["position"]["region"]["city"]

    
        flight_status = i["flight"]["status"]["text"]
        departure_time = i["flight"]["time"]["scheduled"]["departure"]
        arrival_time = i["flight"]["time"]["scheduled"]["arrival"]
    
        departure_time = datetime.fromtimestamp(departure_time).strftime('%Y-%m-%d %H:%M:%S')
        arrival_time = datetime.fromtimestamp(arrival_time).strftime('%Y-%m-%d %H:%M:%S')

        
        cursor.execute('''
                    INSERT INTO flights (
                        flight_number, airline, aircraft, flight_status,
                        departure_airport_iata, departure_airport_name, 
                        departure_airport_city, departure_airport_country, departure_airport_timezone,
                        destination_airport_iata, destination_airport_name,
                        destination_airport_city, destination_airport_country, destination_airport_timezone,
                        scheduled_departure, scheduled_arrival
                    ) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    flight_number, airline, 
                    aircraft,flight_status,
                    departure_airport_iata, departure_airport_name,
                    departure_airport_city, departure_airport_country, 
                    departure_airport_timezone,
                    destination_airport_iata, destination_airport_name,
                    destination_airport_city, destination_airport_country, 
                    destination_airport_timezone,
                    departure_time, arrival_time
                ))
        connection.commit()

def parse_all_json_files(folder_path = "./flight_data"):
    """
    Parse all JSON files in a given folder
    
    Args:
        folder_path (str): Path to the folder containing JSON files
        
    Returns:
        dict: Dictionary with filename as key and parsed JSON data as value
    """
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist!")
        return {}
    
    # Find all JSON files in the folder
    json_pattern = os.path.join(folder_path, "*.json")
    json_files = glob.glob(json_pattern)
    
    if not json_files:
        print(f"No JSON files found in '{folder_path}'")
        return {}
    
    print(f"Found {len(json_files)} JSON files in '{folder_path}'")
    
    parsed_data = {}
    successful_files = 0
    failed_files = []
    
    for file_path in json_files:
        filename = os.path.basename(file_path)
        print(f"Processing: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # print(data)
                populate_db(data)
                
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON Error in {filename}: {e}")
            failed_files.append((filename, f"JSON Error: {e}"))
            
        except FileNotFoundError:
            print(f"  ✗ File not found: {filename}")
            failed_files.append((filename, "File not found"))
            
        except Exception as e:
            print(f"  ✗ Unexpected error in {filename}: {e}")
            failed_files.append((filename, f"Unexpected error: {e}"))
            
    
    print(f"\n=== Summary ===")
    print(f"Total files found: {len(json_files)}")
    print(f"Successfully parsed: {successful_files}")
    print(f"Failed to parse: {len(failed_files)}")
    
    if failed_files:
        print(f"\nFailed files:")
        for filename, error in failed_files:
            print(f"  - {filename}: {error}")
    
    return parsed_data

parse_all_json_files()