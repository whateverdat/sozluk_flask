from flask import redirect, session
from functools import wraps
import sqlite3 as sql

# Function to access the database 
def db_access(*args):

    # Read from database
    with sql.connect("database.db") as database:
        db = database.cursor()
        
        # Need to count arguments for formatting purposes
        if len(args) == 1:
            rows = db.execute(args[0])
            rows = db.fetchall()
            data = [row[0] for row in rows] # Store in list
            
            # If the query returns multiple values from each row, return output as is
            if "*" in args[0] or "," in args[0]:  
                return rows

            # If query returns one value from each row, return as list 
            else:         
                return data

        # --The function takes either 1 or 2 arg-- In this case, either format is fine
        else: 
            rows = db.execute(args[0], args[1])
            rows = db.fetchall()

            data = [row for row in rows] # Store in list
            return data
            

# Function to execute query on database
def db_execute(*args):

    # Read from database
    with sql.connect("database.db") as database:
        db = database.cursor()

        # Need to count arguments:
        if len(args) == 1:
            db.execute(args[0]) # Execute query
            return 0

        else:   # The function takes either 1 or 2 argc
            db.execute(args[0], args[1]) # Execute query
            return 0

# Log in requirement: https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Function to format the data returened from SQL: https://stackoverflow.com/questions/12400272/how-do-you-filter-a-string-to-only-contain-letters
def letters(input):
    valids = []
    for character in input:
        if character.isalpha() or character == '-' or character =="'":
            valids.append(character)
    return ''.join(valids)