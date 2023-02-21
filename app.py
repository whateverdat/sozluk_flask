import os

from flask import Flask, render_template, session, request, redirect, flash, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session.__init__ import Session
from random import randrange, randint

from module import db_access, db_execute, login_required, letters

app = Flask(__name__)

# Set secret key
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
            

# Mainpage
@app.route('/')
def index():

    return render_template("index.html")
    

# Search
@app.route('/search', methods=["GET", "POST"])
def search():

    # Method is get (Dynamic Search)
    if request.method == "GET":

        # Get data according to user input
        search_query = str(request.args.get("q"))

        # When user inputs
        if len(search_query) > 3 :
            words = db_access("SELECT word FROM word WHERE word LIKE ? ORDER BY word LIMIT 10", [search_query + "%"])
            
        # When there is no input
        else:
            words = []

        # Create dynamic search
        return render_template("search.html",  words=words)

    # Method is post (Regular Search, form is submitted)
    else:

        # Get input and perform query
        search_query = str(request.form.get("q"))
        words = db_access("SELECT word FROM word WHERE word LIKE ? ORDER BY word LIMIT 50", [search_query + "%"])
        

        # If there is no result
        if len(words) == 0:
            flash("No result")
            return render_template("index.html")

        # If result is unique, redirect to the dictionary route
        elif len(set(words)) == 1: 
            words = db_access("SELECT word FROM word WHERE word = ? LIMIT 1", [search_query + "%"]) 
            return redirect(url_for("dictionary", word = search_query))

        # If results are multiple, perform search
        return render_template("results.html", words=words)


# Dictionary Pages
@app.route('/dictionary/<word>', methods=["GET", "POST"])
def dictionary(word):

    # Method is post (used to create practice entries)
    if request.method == "POST":

        # Get the current word and all the words within user's practice list
        current_word = request.form.get('submit')
        practice = str(db_access("SELECT word FROM practice WHERE user_id = ?", [str(session.get("user_id"))]))
        
        # If the word already exists in user's list
        if current_word in practice:
            flash("Word is already in your practice list.")
            return redirect("/practice")
        
        # Create dictionary data
        db_execute("INSERT INTO practice (user_id, word) VALUES (?, ?)", [str(session.get("user_id")), current_word])
        flash("Word has successfuly been added to your practice list.")
        return redirect("/practice")

    # Method is get, renders dictionary page
    else:
        # Select word and descriptions from database
        words = db_access("SELECT word, type, description FROM word WHERE word LIKE ?", [word])
        
        # If word is not completed, yet can be with extra letters (ex: 'searchi') complete it.
        if not words:
            words = db_access("SELECT word, type, description FROM word WHERE word LIKE ?", [word + '%'])

        # Render result
        return render_template("dictionary.html", words=words)


# Register
@app.route('/register', methods=["GET", "POST"])
def register():

     # Clear any previous session
    session.clear()
    
    # Method is POST
    if request.method == "POST":
        
        # Get user input
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        # If there is an empty field
        if not username or not password or not confirm:
            flash("Please fill the blank areas.", 400)
            return render_template("register.html")

        # If username is taken
        usernames = db_access("SELECT username FROM users")
        if username in usernames:
            flash("Username taken.", 409)
            return render_template("register.html")

        #If passwords do not match
        if not request.form.get("password") == request.form.get("confirm"):
            flash("Passwords do not match.", 400)
            return render_template("register.html")
        
        # Generate hash
        password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # Register user to the users table and redirect
        db_access("INSERT INTO users (username, hash) VALUES (?, ?)", (username, password))
    
        # Log in and redirect
        session_id = db_access("SELECT id FROM users WHERE username = ?", [username])
        session["user_id"] = session_id[0][0]
        return redirect("/")
    
    # Method is GET
    else:
        return render_template("register.html")


# Log in
@app.route('/login', methods=["GET", "POST"])
def login():
    
    # Clear any previous session
    session.clear()

    # Method is POST
    if request.method == "POST":
        
        # Get user input
        username = str(request.form.get("username"))
        password = request.form.get("password")
        
        # Load users from database
        user = db_access("SELECT * FROM users WHERE username = ?", [username])

        if len(user) == 0 or not check_password_hash(user[0][2], password):
            flash("Incorrect credentials.")
            return render_template("login.html")

        # Log user in and redirect
        session["user_id"] = user[0][0]
        return redirect("/")

    # Method is GET
    else: 
        return render_template("login.html")


# Log Out
@app.route('/logout')
def logout():

    # Clear session and redirect
    session.clear()
    return redirect("/")


# Change password   
@app.route("/options", methods=["GET", "POST"])
@login_required
def options():

    # Method is POST
    if request.method == "POST":

        # Get user input
        current_pass = request.form.get("password")
        new_pass = request.form.get("new-password")
        confirm = request.form.get("confirm")

        # Get user data
        session_id = session.get("user_id")
        user = db_access("SELECT * FROM users WHERE id = ?", [session_id])

        # Check if there are empty fields
        if not current_pass or not new_pass or not confirm:
            flash("Please fill out all the fields.")
            return render_template("options.html")

        # Check if the current password is entered correctly
        elif not check_password_hash(user[0][2], current_pass):
            flash("Incorrect password", 400)
            return render_template("options.html")

        # Check if confirmation matches the new passowrd
        elif not new_pass == confirm:
            flash("Passwords do not match!", 400)
            return render_template("options.html")

        # Check if new and old passwords are the same or the field is empty
        elif current_pass == new_pass or not new_pass:
            flash("New password cannot be same as the old one, or empty!", 400)
            return render_template("options.html")
        
        # Execute password change
        new_pass = generate_password_hash(new_pass, method='pbkdf2:sha256', salt_length=8)
        db_execute("UPDATE users SET hash = ? WHERE id = ?", [new_pass, session_id])

        # Flash and redirect
        flash("Password has been successfully changed.")
        return redirect("/")

    # If request is get
    else:
        return render_template("options.html")


# Practice List
@app.route("/practice", methods=["GET", "POST"])
@login_required
def practice():

    # Method is post, start practice
    if request.method == "POST":

        # If button start is clicked, start quiz
        if request.form.get("start"):
            return redirect("/quiz")
        
        # If button remove is clicked, remove the clicked word from user's list
        elif request.form.get("remove"):
            db_execute("DELETE FROM practice WHERE user_id = ? AND word = ?", [str(session.get("user_id")), request.form.get("remove")])
            flash("Word removed successfully.")
            return redirect("/practice")

    # Method is get
    else:
        # Access user data for practice list
        words = db_access("SELECT word FROM practice WHERE user_id = ?", [str(session.get("user_id"))]) 
        
        # Calculate scores, get correct and incorrect amounts for each word
        correct = db_access("SELECT correct FROM practice WHERE user_id = ?", [str(session.get("user_id"))])
        incorrect = db_access("SELECT incorrect FROM practice WHERE user_id = ?", [str(session.get("user_id"))])
        
        # Store scores
        scores = []
        for i in range(0, len(words)):
            total = correct[i][0] - incorrect[i][0]
            scores.append(total)
        
        # IF user has no words in their list
        if not words:
            flash("There are no words in your practice list. Search for words to add to your list.")
            return redirect("/")

        # If user has a valid list, render practice page
        else:
            return render_template("practice.html", words=words, scores=scores)


# Quiz
@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():

    if request.method == "GET":
        
        # Load user data  
        words = db_access("SELECT word FROM practice WHERE user_id = ? AND session = 'false'", [str(session.get("user_id"))])

        # If all words are answered for this session, end session
        if not words:
            db_execute("UPDATE practice SET session = 'false' WHERE user_id = ?", [str(session.get("user_id"))])
            return redirect('/practice')
        
        # Create variable and store a random definition for each word in the asking order
        definitions = []
        for i in range(0, len(words)):
            definition = db_access("SELECT description FROM word WHERE word = ? LIMIT 5", [str(words[i][0])])
            random = randint(0, len(definition) -1)
            definitions.append(definition[random])

        # Select random definitions for the quiz
        randoms = []
        for i in range(0, 1000):
            random = db_access("SELECT description FROM word WHERE description IS NOT NULL AND id = ?", [randrange(26000)])
            
            # If random accessed description is somehow null
            if not random:
                continue

            # If not add to randoms
            else:
                randoms.append(random[0])

        # Select random word from user's practice list to show
        select = randint(0, len(words)-1)

        return render_template("quiz.html", words=words, definitions=definitions, randoms=randoms, select=select)
    
    # Method is post (To answer quiz questions)
    if request.method == "POST":
        
        # The correct answer is clicked
        if request.form.get("true"):
            word = request.form.get("true")
            db_execute("UPDATE practice SET correct = correct + 1 WHERE user_id = ? AND word = ?", [str(session.get("user_id")), word])
            db_execute("UPDATE practice SET session = 'true' WHERE user_id = ? AND word = ?", [str(session.get("user_id")), word])
            flash("Correct!")

        # A wrong answer is clicked
        elif request.form.get("false"):
            word = request.form.get("false")
            db_execute("UPDATE practice SET incorrect = incorrect + 1 WHERE user_id = ? AND word = ?", [str(session.get("user_id")), word])
            db_execute("UPDATE practice SET session = 'true' WHERE user_id = ? AND word = ?", [str(session.get("user_id")), word])
            
            # Get correct definition from the hidden input tag in the html to display
            correct = request.form.get("definition")
            flash(f"Answer for '{word}' was: '{str(correct)}'")
           
        return redirect('/quiz')
