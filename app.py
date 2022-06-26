# SKELETON CODE

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64
import datetime
from dateutil import parser
from PIL import Image

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
		return render_template('login.html')
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
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file: /profile

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or create an account</a>"

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
		first_name = request.form.get('firstname')
		last_name = request.form.get('lastname')
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
# Profile page by user_id
@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	albums = getUserAlbums(uid)
	friends = getUserFriends(uid)
	userInfo = getUserInfo(uid)
	return render_template('profile.html', name=flask_login.current_user.id, message="Profile Page", albums=albums, user=userInfo, id=getUserIdFromEmail(flask_login.current_user.id), myFriends=friends)
	
@app.route('/profile/<int:uid>')
def profile(uid):
	albums = getUserAlbums(uid)
	userInfo = getUserInfo(uid)
	friends = getUserFriends(uid)
	# if a user is logged in
	if flask_login.current_user.is_authenticated:
		myFriends = getUserFriends(getUserIdFromEmail(flask_login.current_user.id))
		if userInfo[3] == flask_login.current_user.id:
			return flask.redirect(flask.url_for('protected'))
		else:
			return render_template('profile.html', name=flask_login.current_user.id, message="Profile Page", albums=albums, user=userInfo, id=uid, friends=friends, myFriends=myFriends, myId=getUserIdFromEmail(flask_login.current_user.id))
	else:
		return render_template('profile.html', name="anonymous user", message="Profile Page", albums=albums, user=userInfo, id=uid, friends=friends, myId=1000000, anonymous=True)
	
# get user_id from user email
def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

# get all user info
def getUserInfo(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()

# get email from user id
def getUserEmail(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(uid))
	# print(cursor.fetchone()[0])
	return str(cursor.fetchone()[0])

# get all photos for a user
def getUserPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT caption, photo_id, data, num_likes, date_added, album_id FROM Photos P, Users U, Albums A WHERE P.album_id = A.album_id AND A.user_id = U.user_id AND U.user_id = '{0}'".format(uid))
	return convertTupToPhotosList(cursor.fetchall())

# get all albums for a user
def getUserAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, name, date_created, num_photos FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

### END USER PROFILE CODE ###


### FRIENDS CODE ###
# get all friends for a user
@app.route('/friends/<int:uid>')
@flask_login.login_required
def getUserFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT FW.user1_id AS uid, U.first_name, U.last_name FROM FriendsWith FW, Users U WHERE U.user_id = FW.user1_id AND FW.user2_id = {0} UNION SELECT FW.user2_id AS uid, U.first_name, U.last_name FROM FriendsWith FW, Users U WHERE U.user_id = FW.user2_id AND FW.user1_id = {0}".format(uid))
	# print(cursor.fetchall())
	return cursor.fetchall()

# add a new friend for a user
@app.route('/add_friend/<int:uid>', methods=['POST'])
@flask_login.login_required
def addFriend(uid):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO FriendsWith (user1_id, user2_id) VALUES ({0}, {1})".format(getUserIdFromEmail(flask_login.current_user.id), uid))
	conn.commit()
	return flask.redirect(flask.url_for('protected'))

# remove a friend for a user
@app.route('/remove_friend/<int:uid>', methods=['POST'])
@flask_login.login_required
def removeFriend(uid):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM FriendsWith WHERE user1_id = {0} AND user2_id = {1} OR user1_id = {1} AND user2_id = {0}".format(getUserIdFromEmail(flask_login.current_user.id), uid))
	conn.commit()
	return flask.redirect(flask.url_for('protected'))

### END FRIENDS CODE ###


### ALBUM CODE ###
# display one album and its photos
# album.html: albumId, album (name), date, userEmail, photos
@app.route('/album/<int:aid>', methods=['GET'])
def album(aid):
	# get album info
	albumInfo = getAlbumInfo(aid)
	print(albumInfo[3])
	owner = getUserEmail(albumInfo[3])
	# get photos for this album
	photos = getAlbumPhotos(aid)
	# if a user is logged in
	if flask_login.current_user.is_authenticated:
		return render_template('album.html', name=flask_login.current_user.id, message='View Album', albumId=albumInfo[0], album=albumInfo[1], date=albumInfo[2], numPhotos=albumInfo[4], owner=owner, photos=photos)
	else:
		return render_template('album.html', name="anonymous user", message='View Album', albumId=albumInfo[0], album=albumInfo[1], date=albumInfo[2], numPhotos=albumInfo[4], owner=owner, photos=photos, anonymous=True)

# create new album
# album.html: albumId, album (name), date, userEmail 
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
		cursor.execute('''SELECT album_id, name, date_created FROM Albums WHERE album_id = LAST_INSERT_ID()''')
		newAlbum = cursor.fetchone()
		return render_template('album.html', name=flask_login.current_user.id, message='New Album Created', albumId=newAlbum[0], album=newAlbum[1], date=newAlbum[2], numPhotos=0, owner=flask_login.current_user.id)

# delete an album
@app.route('/delete_album/<int:aid>', methods=['POST'])
@flask_login.login_required
def delete_album(aid):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Albums WHERE album_id = '{0}'".format(aid))
	conn.commit()
	return flask.redirect(flask.url_for('protected'))


# get all photos in a specific album
def getAlbumPhotos(album_id):
	# conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute("SELECT caption, photo_id, data, num_likes, date_added, album_id FROM Photos WHERE album_id = '{0}'".format(album_id))
	return convertTupToPhotosList(cursor.fetchall())

# receives a list of tuples, each tuple has (caption, photo_id, data, num_likes, date_added, album_id)
# convert to array for album.html and explore.html
def convertTupToPhotosList(photos):
	photosArr = [] 
	for tup in photos:
		photo_id = int(tup[1])
		tags = getPhotoTags(photo_id)		# get all tags for each photo in album
		photosArr.append(
			{
				"photoId": photo_id,
				"caption": str(tup[0]), 
				"data": str(tup[2].decode()),
				"numLikes": int(tup[3]),
				"tags": [t[0] for t in tags],
				"date": str(tup[4]),
				"albumId": int(tup[5])
				# "likes": getPhotoLikes(photo_id)
			}
		)
	return photosArr

# get album info from album_id
def getAlbumInfo(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, name, date_created, user_id, num_photos FROM Albums WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchone()

# get user id from album id
def getUserIdFromAlbum(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Albums WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchone()[0]

### END ALBUM CODE ###


### PHOTO CODE ###
# photo page
# photo.html: photoId, albumId, caption, date, numlikes, tags, comments
@app.route('/photo/<int:pid>', methods=['GET'])
def photo(pid):
	# get photo info
	photoInfo = getPhotoInfo(pid)
	caption = photoInfo.get('caption')
	photo_data = photoInfo.get('data')
	date = photoInfo.get('date')
	numlikes = photoInfo.get('likes')
	tags = photoInfo.get('tags')
	comments = photoInfo.get('comments')

	# get album info for this photo
	albumInfo = getAlbumInfo(photoInfo.get('albumId'))

	# get album owner
	owner = getUserEmail(albumInfo[3])
	# if a user is logged in
	if flask_login.current_user.is_authenticated:
		return render_template('photo.html', name=flask_login.current_user.id, message='Photo', photoId=pid, caption=caption, photo=photo_data, date=date, album=albumInfo, owner=owner, tags=tags, comments=comments, numLikes=numlikes)
	else:
		return render_template('photo.html', name="anonymous user", message='Photo', photoId=pid, caption=caption, photo=photo_data, date=date, album=albumInfo, owner=owner, tags=tags, comments=comments, numLikes=numlikes, anonymous=True)

# browse all photos
# browse.html: photos

# get photo info from photo_id
def getPhotoInfo(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT caption, photo_id, data, num_likes, album_id, date_added FROM Photos WHERE photo_id = '{0}'".format(pid))
	tup = cursor.fetchone()
	photo_id = int(tup[1])
	# get tags for this photo
	tags = getPhotoTags(photo_id)
	# get comments for this photo
	comments = getPhotoComments(pid)
	# get likes for this photo
	# likes = getPhotoLikes(pid)
	photoInfo = {
			"photoId": photo_id,
			"caption": str(tup[0]), 
			"data": str(tup[2].decode()),
			"date": str(tup[5]),
			"tags": [t[0] for t in tags],
			"comments": comments,
			"likes": int(tup[3]),
			"albumId": int(tup[4])
		}
	return photoInfo


# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# upload a photo to an album
# album.html: albumId, album (name), date, userEmail, photos (once photo is uploaded)
@app.route('/upload/<int:aid>', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file(aid):
	if request.method == 'POST':
		imgfile = request.files['photo']
		if allowed_file(imgfile.filename):
			uid = getUserIdFromEmail(flask_login.current_user.id)
			album_id = aid

			# Encode the file to get base64 string
			photo_data = base64.b64encode(imgfile.read())

			caption = request.form.get('caption')
			date = datetime.date.today()
			tagsStr = request.form.get('tags')
			tags = tagsStr.split(', ')	 # split tags into a list

			cursor = conn.cursor()
			cursor.execute('''INSERT INTO Photos ( album_id, data, caption, date_added) VALUES (%s, %s, %s, %s )''', ( album_id, photo_data, caption, date))
			conn.commit()

			# get the photo_id of the photo we just uploaded
			cursor.execute('''SELECT LAST_INSERT_ID() FROM Photos''') 
			pid = cursor.fetchone()[0]

			# update num_photos in albums
			cursor.execute('''UPDATE Albums SET num_photos = num_photos + 1 WHERE album_id = %s''', (album_id))

			# add tags to the photo in TaggedWith
			for tag in tags:
				tag = tag.lower()
				# check if the tag exists 
				cursor.execute("SELECT tag_id FROM Tags T WHERE T.word='{0}'".format(tag))
				
				fetched_tag = cursor.fetchone() 

				# tag already exists
				if fetched_tag: 
					tag_id = fetched_tag[0]
					cursor.execute('''UPDATE Tags SET num_tagged = num_tagged + 1 WHERE tag_id = {0}'''.format(tag_id)) 
					conn.commit()
					cursor.execute('''INSERT INTO TaggedWith (tag_id, photo_id) VALUES (%s, %s)''', (tag_id, pid))
					conn.commit()
				# create new tag
				else:
					cursor.execute('''INSERT INTO Tags (word) VALUES (%s)''', (tag))
					conn.commit()
					# last inserted tag_id
					cursor.execute('''SELECT LAST_INSERT_ID() FROM Tags''') 
					tag_id = cursor.fetchone()[0]
					cursor.execute('''INSERT INTO TaggedWith (tag_id, photo_id) VALUES (%s, %s)''', (tag_id, pid))
					conn.commit()

			# albumInfo = getAlbumInfo(album_id)
			# photos=getAlbumPhotos(album_id)
			# return render_template('album.html', name=flask_login.current_user.id, message='Photo uploaded!', albumId=album_id, album=albumInfo[1], date=albumInfo[2], photos=photos, base64=base64, owner=getUserEmail(albumInfo[3])) 
			return flask.redirect(flask.url_for('photo', pid=pid))
	#The method is GET: so if user reloads the page, it won't upload the same photo again
	else:
		# albumInfo = getAlbumInfo(album_id)
		# photos=getAlbumPhotos(album_id)
		return flask.redirect(flask.url_for('album', aid=album_id))

# delete a photo
@app.route('/delete_photo/<int:pid>', methods=['GET', 'POST'])
@flask_login.login_required
def delete_photo(pid):
	if request.method == 'POST':
		# uid = getUserIdFromEmail(flask_login.current_user.id)
		aid = getPhotoInfo(pid).get('albumId')
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Photos WHERE photo_id = '{0}'".format(pid))
		conn.commit()
		cursor.execute("DELETE FROM TaggedWith WHERE photo_id = '{0}'".format(pid))
		conn.commit()
		cursor.execute("DELETE FROM Comments WHERE photo_id = '{0}'".format(pid))
		conn.commit()
		cursor.execute("DELETE FROM LikedBy WHERE photo_id = '{0}'".format(pid))
		conn.commit()
		cursor.execute("UPDATE Albums SET num_photos = num_photos - 1 WHERE album_id = '{0}'".format(aid))
		conn.commit()
		return flask.redirect(flask.url_for('album', aid=aid))
	else:
		return flask.redirect(flask.url_for('album', aid=aid))

### END PHOTO CODE ###


### COMMENTS CODE ###
# get all comments on a photo
def getPhotoComments(photo_id):
	# conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute("SELECT U.user_id, U.first_name, U.last_name, C.date_posted, C.text FROM Comments C, Users U WHERE U.user_id = C.user_id AND photo_id = {0}".format(photo_id)) 
	return cursor.fetchall()

# add a comment to a photo
@app.route('/addComment/<int:pid>', methods=['POST'])
def addComment(pid):
	date = datetime.date.today()
	if request.form.get('comment') == None:
		return flask.redirect(flask.url_for('photo', pid=pid)) # redirect to the photo page
	if user_id == None: 
		user_id = 1000000
		# anonymous user
		cursor.execute("SELECT * FROM Users WHERE user_id = 1000000")
		if not cursor.fetchone():
			cursor.execute("INSERT INTO Users (user_id, first_name, last_name, email, password) VALUES ({0}, '{1}', '{2}', '{3}', '{4}')".format(user_id, "Anonymous", "User", "anon@anon.com", "anonymous"))
			conn.commit()
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Comments (user_id, photo_id, text, date_posted) VALUES ({0}, {1}, '{2}', {3})".format(flask_login.current_user.id, pid, request.form.get('comment'), date))
	conn.commit()
	return flask.redirect(flask.url_for('photo', pid=pid)) # redirect to the photo page

### END COMMENTS CODE ###


### TAGS CODE ###
# get all tags on a photo
def getPhotoTags(photo_id):
	# conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute("SELECT T.word FROM Tags T, TaggedWith TW WHERE T.tag_id = TW.tag_id AND TW.photo_id = {0}".format(photo_id)) 
	return cursor.fetchall()

# get all photos with a tag
def getPhotosWithTag(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT P.photo_id, P.data FROM Photos P, Tags T, TaggedWith TW WHERE P.photo_id = TW.photo_id AND TW.tag_id = T.tag_id AND T.word = '{0}'".format(tag)) 
	return cursor.fetchall()

# view photos by tag
# tag.html: tag, photos
@app.route('/tag/<tag>')
def tag(tag):
	photos = getPhotosWithTag(tag)
	photosArr = []
	for photo in photos:
		photosArr.append({
			'pid': photo[0],
			'data': photo[1].decode()
		})
	# if logged in
	if flask_login.current_user.is_authenticated:
		return render_template('tag.html', name=flask_login.current_user.id, tag=tag, photos=photosArr)
	# if not logged in
	else:
		return render_template('tag.html', name='anonymous user', tag=tag, photos=photosArr, anonymous=True)

# add a tag to a photo
# @app.route('/addTag/<int:pid>', methods=['POST'])
# def addTag(pid):
# 	tag = request.form.get('tag')
# 	if tag == None:
# 		return flask.redirect(flask.url_for('photo', pid=pid)) # redirect to the photo page
# 	cursor = conn.cursor()
# 	cursor.execute("INSERT INTO Tags (word) VALUES ('{0}')".format(tag))
# 	conn.commit()
# 	return flask.redirect(flask.url_for('photo', pid=pid)) # redirect to the photo page

### END TAGS CODE ###


### LIKES CODE ###
# get list of users who liked a photo
def getPhotoLikes(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM LikedBy WHERE photo_id = {0}".format(photo_id)) 
	return cursor.fetchone()[0]

# add a like to a photo
@app.route('/addLike/<int:pid>', methods=['POST'])
def addLike(pid):
	if user_id == None: 
		user_id = 1000000
		# anonymous user
		cursor.execute("SELECT * FROM Users WHERE user_id = 1000000")
		if not cursor.fetchone():
			cursor.execute("INSERT INTO Users (user_id, first_name, last_name, email, password) VALUES ({0}, '{1}', '{2}', '{3}', '{4}')".format(user_id, "Anonymous", "User", "anon@anon.com", "anonymous"))
			conn.commit()
	cursor = conn.cursor() 
	cursor.execute("INSERT INTO LikedBy (photo_id, user_id) VALUES (%s, %s)", (pid, user_id))
	cursor.execute("UPDATE Photos SET num_likes = num_likes + 1 WHERE photo_id = {0}".format(pid))
	conn.commit()
	return flask.redirect(flask.url_for('photo', pid=pid)) # redirect to the photo page

### END LIKES CODE ###


### TOP USERS AND TAGS CODE ###


### END TOP USERS AND TAGS CODE ###


# Default landing page
@app.route("/", methods=['GET'])
def hello():
	# if user is logged in
	if flask_login.current_user.is_authenticated:
		return render_template('hello.html', name=flask_login.current_user.id, message='Welcome to Photoshare')
	# if user is not logged in
	else:
		return render_template('hello.html', name='anonymous user', message='Welcome to Photoshare', anonymous=True)


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)