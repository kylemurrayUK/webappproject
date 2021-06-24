import os
import calendar
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message


# Configure application
app = Flask(__name__)

BODYPARTS = ["Shoulders", "Chest", "Back", "Core", "Hips", "Upper Legs", "Lower Legs", "Spinal Erector"]
SHOULDERS = ["Pike Push-up", "Elevated Pike Push-up", "Handstand Push-up", "Raise Handstand Push-up"]
CHEST = ["Knee Push-up", "Regular Push-up", "Deficit Push-up", "Weighted Deficit Push-up"]
BACK = ["Stool Assisted Chin-ups", "Regular Chin-ups", "Chin and Pull-up Combo", "Weight Chin and Pull-up Combo"]
CORE = ["Knee High Plank", "Knee Low Plank", "High Plank", "Low Plank"]
HIPS = ["Glute Bridge", "One-Legged Glute Bridge", "Hip Thrust", "One-Legged Hip Thrust"]
UPPERLEGS = ["Air squats", "Bulgarian split squats", "Weighted Bulgarian split squats", "Pistol Squat"]
LOWERLEGS = ["Heel Raises", "One-legged Heel Raises", "One legged Toe-Touches", "Time extended One legged Toe-Touches"]
SPINALERECTOR = ["Towel Deadlift", "Towel Deadlift", "Towel Deadlift", "Towel Deadlift"]

app.config["MAIL_DEFAULT_SENDER"] = ('CS50 Exercise App', 'exerciseappscheduler@gmail.com')
app.config["MAIL_PASSWORD"] = 'Username!1'
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = True
app.config['MAIL_USERNAME'] = 'exerciseappscheduler@gmail.com'

mail = Mail(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///exercise.db")


def dayofweek():
    # easier to return actual week day as string rather than use numerical output as this can be reused in email and index page
    weekdays = ["Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday"]
    today = date.today()
    return weekdays[today.weekday()]


def getsets(val):
    # converts this to an integer so that there is no decimal points when returning value
    val = int(val)
    if (val % 3 == 0):
        set1 = val / 3
        set2 = val / 3
        set3 = val / 3
    else:
        set1 = ((val - (val % 3)) / 3)
        set2 = ((val - (val % 3)) / 3)
        set3 = ((val - (val % 3)) / 3)
        if (val % 3 == 1):
            set1 = set1 + 1
        elif (val % 3 == 2):
            set1 = set1 + 1
            set2 = set2 + 1
    return set1, set2, set3


emails = db.execute("SELECT id, email, username FROM users")

# function that sends out exercise routine for that day


def email():
    for i in range(0, len(emails)):
        with app.app_context():
            # code essentially mirrors code in index function. Ideally would be refactored into a function
            day = dayofweek()
            exercises = []

            if day == "Monday" or day == "Wednesday" or day == "Friday":
                for j in range(len(BODYPARTS)):
                    if j < 4:
                        exercises.append(BODYPARTS[j])
                        musclegroup = "Upper Body"
            if day == "Tuesday" or day == "Thursday":
                for j in range(len(BODYPARTS)):
                    if j > 3:
                        exercises.append(BODYPARTS[j])
                        musclegroup = "Lower body"
            reps = []

            for j in range(len(exercises)):
                reps.append(db.execute("SELECT reps FROM exercises WHERE id = ? AND bodypart = ?", emails[i]['id'], exercises[j]))

            level = []

            for j in range(len(exercises)):
                specificlevel = db.execute("SELECT level FROM exercises WHERE id = ? AND bodypart = ?",
                                           emails[i]['id'], exercises[j])
                specificlevel = specificlevel[0]['level']
                level.append(specificlevel)

            bodypartmove = []
            # gets specific move for that bodypart base on level
            for j in range(len(exercises)):
                # formats the name of bodypart to match lists above
                bodypart = exercises[j].replace(" ", "").upper()
                # uses the eval function to pass that formatted name as the name of a list
                specificmove = eval(bodypart)[level[j] - 1]
                bodypartmove.append(specificmove)
            overload = []
            exercisereps = []
            # gets amount of reps
            for j in range(len(exercises)):
                exercise = {exercises[j]: reps[j][0]['reps']}
                exercisereps.append(exercise)
                if reps[j][0]['reps'] > 36:
                    if exercises[j] == 'Core':
                        if reps[j][0]['reps'] >= 240:
                            overload.append(exercises[j])
                    else:
                        overload.append(exercises[j])

            # get sets for exercises
            sets = []
            for j in range(len(exercises)):
                subset = []
                reps = exercisereps[j][exercises[j]]
                if (exercises[j] == 'Core' or exercises[j] == 'Shoulders' or exercises[j] == 'Lower Legs'):
                    set1 = reps / 2
                    set2 = reps / 2
                    subset.append(round(set1))
                    subset.append(round(set2))
                    sets.append(subset)
                else:
                    set1, set2, set3 = getsets(reps)
                    subset.append(round(set1))
                    subset.append(round(set2))
                    subset.append(round(set3))
                    sets.append(subset)

            username = emails[i]['username']

            remindermessage = Message(subject="Todays exercise routine", recipients=[emails[i]['email']])
            remindermessage.html = render_template('reminderemail.html', exercises=exercises, day=day, musclegroup=musclegroup, exercisereps=exercisereps,
                                                   level=level, bodypartmove=bodypartmove, sets=sets, emails=emails, username=username, overload=overload)
            mail.send(remindermessage)


def increasereps():
    count = db.execute("SELECT COUNT(*) FROM users")
    for i in range(count[0]['COUNT(*)']):
        for bodypart in BODYPARTS:
            # Core group a special case as reps measured in seconds not reps
            if bodypart == "Core":
                corereps = db.execute("SELECT reps FROM exercises WHERE bodypart = 'Core' AND id = ?", i + 1)
                if corereps[0]['reps'] == 240:
                    continue
                else:
                    db.execute("UPDATE exercises SET reps = reps + 5 WHERE bodypart = ? AND id = ?", bodypart, i + 1)
            # lower legs don't increase unless done by the users in the settings page
            elif bodypart == "Lower Legs":
                continue
            else:
                db.execute("UPDATE exercises SET reps = reps + 1 WHERE bodypart = ? AND id = ?", bodypart, i + 1)


# this is my scheduler for running my email service and increasing my reps
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    sched = BackgroundScheduler(daemon=True)
    # sends out the exercise schedule for the day at 7 in the morning as this i pretty much the earliest most people will exercise
    sched.add_job(email, 'cron', hour=7)
    # increases reps at 6 when most people will have finished exercising
    sched.add_job(increasereps, 'cron', hour=18)
    sched.start()


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
@login_required
def index():
    """Show exercise for that day"""
    day = dayofweek()
    exercises = []

    if day == "Monday" or day == "Wednesday" or day == "Friday":
        for i in range(len(BODYPARTS)):
            if i < 4:
                exercises.append(BODYPARTS[i])
        musclegroup = "Upper Body"
    if day == "Tuesday" or day == "Thursday":
        for i in range(len(BODYPARTS)):
            if i > 3:
                exercises.append(BODYPARTS[i])
        musclegroup = "Lower body"
    reps = []
    for i in range(len(exercises)):
        reps.append(db.execute("SELECT reps FROM exercises WHERE id = ? AND bodypart = ?", session["user_id"], exercises[i]))

    level = []

    for i in range(len(exercises)):
        specificlevel = db.execute("SELECT level FROM exercises WHERE id = ? AND bodypart = ?", session["user_id"], exercises[i])
        specificlevel = specificlevel[0]['level']
        level.append(specificlevel)

    bodypartmove = []
    # gets specific move for that bodypart base on level
    for i in range(len(exercises)):
        # formats the name of bodypart to match lists above
        bodypart = exercises[i].replace(" ", "").upper()
        # uses the eval function to pass that formatted name as the name of a list
        specificmove = eval(bodypart)[level[i] - 1]
        bodypartmove.append(specificmove)
    exercisereps = []
    # gets amount of reps
    for i in range(len(exercises)):
        exercise = {exercises[i]: reps[i][0]['reps']}
        exercisereps.append(exercise)
    # get sets for exercises
    sets = []
    for i in range(len(exercises)):
        subset = []
        reps = exercisereps[i][exercises[i]]
        if (exercises[i] == 'Core' or exercises[i] == 'Shoulders' or exercises[i] == 'Lower Legs'):
            set1 = reps / 2
            set2 = reps / 2
            subset.append(round(set1))
            subset.append(round(set2))
            sets.append(subset)
        else:
            set1, set2, set3 = getsets(reps)
            subset.append(round(set1))
            subset.append(round(set2))
            subset.append(round(set3))
            sets.append(subset)

    return render_template("index.html", exercises=exercises, day=day, musclegroup=musclegroup, exercisereps=exercisereps,
                           level=level, bodypartmove=bodypartmove, sets=sets)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Change Settings Feature."""

    if request.method == "GET":
        upperbody = db.execute(
            "SELECT bodypart, reps, level FROM exercises WHERE id = ? AND (bodypart ='Chest' OR bodypart ='Back' OR bodypart='Shoulders' OR bodypart='Core')", session["user_id"])
        lowerbody = db.execute(
            "SELECT bodypart, reps, level FROM exercises WHERE id = ? AND (bodypart ='Upper Legs' OR bodypart ='Hips' OR bodypart='Spinal Erector' OR bodypart='Lower Legs')", session["user_id"])

        upperexercises = []
        for bodypart in upperbody:
            exercises = bodypart['bodypart'].replace(" ", "").upper()
            specificmove = eval(exercises)[bodypart['level'] - 1]
            upperexercises.append(specificmove)

        lowerexercises = []
        for bodypart in lowerbody:
            exercises = bodypart['bodypart'].replace(" ", "").upper()
            specificmove = eval(exercises)[bodypart['level'] - 1]
            lowerexercises.append(specificmove)

        return render_template("settings.html", upperbody=upperbody, lowerbody=lowerbody, upperexercises=upperexercises, lowerexercises=lowerexercises)

    if request.method == "POST":
        for bodypart in BODYPARTS:
            levelname = bodypart+"level"
            repsname = bodypart+"reps"
            bodypartlevel = request.form.get(levelname)
            bodypartreps = request.form.get(repsname)
            db.execute("UPDATE exercises SET reps = ?, level = ? WHERE bodypart = ?", bodypartreps, bodypartlevel, bodypart)

        return redirect("/settings")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("registration.html")
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        usernamecheck = db.execute("SELECT * FROM users WHERE username = ?", username)
        if not request.form.get("username"):
            return apology("Username cannot be blank.")
        if not request.form.get("password"):
            return apology("Password cannot be blank.")
        if not request.form.get("confirmation"):
            return apology("Password cannot be blank.")
        if len(request.form.get("password")) < 8:
            return apology("The password must be at least 8 characters long.")
        if request.form.get("password").isalpha() == True:
            return apology("Must contain at least one number.")
        if request.form.get("password").isalnum() == True:
            return apology("Must contain at least one special character.")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords must match up.")
        elif len(usernamecheck) > 0:
            return apology("Username already in use")
        if not request.form.get("email"):
            return apology("Must have an email")
        else:
            unhashedpassword = request.form.get("password")
            password = generate_password_hash(unhashedpassword)
            email = request.form.get("email")
            confmessage = Message("You have successfully been registered to the CS50 exercise app!", recipients=[email])
            confmessage.body = "We would recommend going onto the setting page to tailor your workout for you."
            try:
                mail.send(confmessage)
            except:
                return apology("Looks like an invalid email address")
            db.execute("INSERT INTO users(username, hash, email) VALUES(?, ?, ?)", username, password, email)
            userID = db.execute("SELECT id FROM users WHERE username = ?", username)
            userID = userID[0]['id']
            for bodypart in BODYPARTS:
                if bodypart == "Core":
                    db.execute("INSERT INTO exercises(id, bodypart, level, reps) VALUES (?, ?, ?, 60)",
                               userID, bodypart, request.form.get("level"))
                else:
                    db.execute("INSERT INTO exercises(id, bodypart, level, reps) VALUES (?, ?, ?, 12)",
                               userID, bodypart, request.form.get("level"))
            return render_template("login.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)