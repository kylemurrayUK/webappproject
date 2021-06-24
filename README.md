# YOUR PROJECT TITLE
#### Video Demo:  https://www.youtube.com/watch?v=DNUTtze1Jjg
#### Description:
My project is a web application based on the finance application from week 9that tracks the users reps for each bodypart and their level and then assigns them
exercises based on this level. It then sends them an email a day with that days exercises, based on the day of the week, and increased the users reps for
each exercise daily. Below I will go through each file in the project.
## Templates
#### apology.html
This contains the apology page from finance with a different image. I worked out how to image pulls its background with the 'alt' tag in the url. This is used
to tell the user if they have commited an error or whether there has been an error server side.
#### index.html
This gives several tables with that days exercise. There was a function in the main application.py file that gets the day of the week. Most of the processing
is done on the server side with several lists being passed to the html page. The application.py quries into the sql database with tha users id and pulls either
all the upperbody or lowerbody exercises based on what day it is. It then uses a specially written function that splits the reps into 3 or 2 sets depending on
the bodypart. It also uses the users level (levels are from 1 to 4) to index into a locally held list of exercises for that bodypart and then displays that along
with the reps. I have then used jinja syntax to loop over the lists and create a table for each bodypart that contains the exercise, reps and sets.
#### layout.html
The only thing I have really kept from the finance app is the ability to swap for a mobile device. I have changed the loop by reading the bootstrap documentation
and have changed the buttons.
#### login.html
This queuries the database in much the same way finance did but with a different look.
#### registration.html
This registers the user. It asks the user for a username, password, email and level. Upon submit this checks whether the username is in use, whether the password
passes the tests (ie minimum 8 characters), whether they have inputted info for all field and whether the email is valid. If those checks are passed then it
creates a new users, storing their info. It also creates a series of entries into the exercises table, one for each bodypart, with a level and a default amount
of reps. It will then send a confirmation email to the users email address.
#### reminderemail.html
Essentially has the same functionality as the index page but is connected to a schedulerapi module I have downloaded. This uses a cron trigger to run every day at
7am. The email function is then triggered that uses this html apge as a template. It presents the information in much the same way the index page does.
#### settings.html
Upon a GET request this displays 2 tables. One for upperbody and one for lowerbody. It presents the users current level for each bodypart, along with the exercise
associated with that level and then the amount of reps for that bodypart. It displays these in number fields that can be changed up to a certain limit. Upon a post
request the program loops through the body parts and inserts the new numbers back into the database. It then refreshes the page to show the suer the new reps along
with any exercise changes.
#### application.py
Most of the functions of this have been covered in the above pages but there are certain things that haven;t. The main one is the function that increases the reps
daily. This uses an update function to add either 1, 5 or nothing depending on the exercise. This is then linked the scheduler which again uses a cron trigger
to execute this once a day at 18:00. This file also contains the list of bodyparts and their associated exercises. I did this as I thought it would be quicker than
having them stored into a database and having to query that database evertime.
#### exercise.db
This database has two tables with the following schema:
CREATE TABLE users (id INTEGER, username TEXT NOT NULL, hash TEXT NOT NULL, email TEXT, PRIMARY KEY(id));
CREATE TABLE exercises (id INTEGER, bodypart TEXT NOT NULL, level INTEGER, reps INTEGER, FOREIGN KEY(id) REFERENCES users(id));
CREATE UNIQUE INDEX username ON users(username);
#### helpers.db
Contains some functions from finance but has been massively stripped back. The only functions that remain is the apology function and the login_required tag
function.
#### requirements.txt
Contains a list of all the external modules I have used.
