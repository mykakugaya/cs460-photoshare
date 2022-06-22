# SKELETON CODE

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64
import datetime
from dateutil import parser

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

### LOGIN CODE ###
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
# cursor = conn.cursor()
# cursor.execute("SELECT email from Users")
# users = cursor.fetchall()

# Get all user emails
def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''
# Login user
@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

# Logout user
@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

# Register page
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

# Register a new user
@app.route("/register", methods=['POST'])
def register_user():
	try:
		email = request.form.get('email')
		password = request.form.get('password')
		first_name = request.form.get('first_name')
		last_name = request.form.get('last_name')
		gender = request.form.get('gender')
		dob = parser.parse(request.form.get('dob'))
		hometown = request.form.get('hometown')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test = isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, gender, dob, hometown) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, first_name, last_name, gender, dob, hometown)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

# determine if email is unique
def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

### END LOGIN CODE ###


### USER PROFILE CODE ###
# User profile page
@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")
	
# get user_id from user email
def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

# get all user info
def getUserInfoFromEmail(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()

# get all photos for a user
def getUserPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

# get all albums for a user
def getUserAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, name, date_created FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

### END USER PROFILE CODE ###


### ALBUM CODE ###
# create new album
@app.route('/new_album', methods=['GET', 'POST'])
@flask_login.login_required
def new_album():
	# if GET, show create album form
	if flask.request.method == 'GET':
		return render_template('album.html', name=flask_login.current_user.id, message='Create a new album')
	# if POST, create album and redirect to the album page
	else:
		try:
			name = request.form.get('name')
			date_created = datetime.date.today()
			user_id = getUserIdFromEmail(flask_login.current_user.id)
		except:
			print("couldn't find all tokens")
			return flask.redirect(flask.url_for('new_album'))
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Albums (name, date_created, user_id) VALUES ('{0}', '{1}', '{2}')".format(name, date_created, user_id))
		conn.commit()
		cursor.execute('''SELECT name, date_created FROM Albums WHERE album_id = LAST_INSERT_ID()''')
		newAlbum = cursor.fetchone()
		return render_template('album.html', name=flask_login.current_user.id, message='Album Created!', album=newAlbum)

# get all photos in a specific album
def getAlbumPhotos(album_id):
	conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute("SELECT caption, photo_id, data, likes FROM Photos WHERE album_id = '{0}'".format(album_id))
	album_photos = [] 
	for tup in cursor.fetchall():
		photo_id = int(tup[1])
		cursor.execute("SELECT T.name FROM Tags T, TaggedWith TW WHERE T.tag_id = TW.tag_id AND TW.photo_id = {0}".format(photo_id))
		album_photos.append(
			{
				"photoId": photo_id,
				"caption": str(tup[0]), 
				"url": str(tup[2].decode()),
				"likes": getPhotoLikes(photo_id),
				"tags": [t[0] for t in cursor.fetchall()]
			}
		)
	return album_photos

# get album info from album_id
def getAlbumInfo(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT name, date_created FROM Albums WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchone()

### END ALBUM CODE ###


### PHOTO CODE ###
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# upload a photo to an album
@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_id = request.form.get('album_id')	##TODO: not sure yet how we'll get album_id from form
		imgfile = request.files['photo']
		photo_data = imgfile.read()
		caption = request.form.get('caption')
		date = datetime.date.today()

		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (user_id, album_id, data, caption, date_added) VALUES (%s, %s, %s )''', (uid, album_id, photo_data, caption, date))
		conn.commit()
		return render_template('album.html', name=flask_login.current_user.id, message='Photo uploaded!', album=getAlbumInfo(album_id), photos=getAlbumPhotos(album_id), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')	##TODO: specify album id

### END PHOTO CODE ###

### COMMENTS, LIKES, TAGS CODE ###


# Default landing page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)