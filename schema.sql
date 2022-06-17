-- CREATE DATABASE photoshare;
USE photoshare;
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS FriendsWith CASCADE; 
DROP TABLE IF EXISTS Albums CASCADE;
DROP TABLE IF EXISTS Photos CASCADE;
DROP TABLE IF EXISTS Comments CASCADE;
DROP TABLE IF EXISTS Tags CASCADE;
DROP TABLE IF EXISTS LikedBy CASCADE;
DROP TABLE IF EXISTS TaggedWith CASCADE;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE Users(
	user_id INTEGER AUTO_INCREMENT,
	first_name CHAR(50),
	last_name CHAR(50),
	email VARCHAR(50) NOT NULL,
	dob DATE,
	hometown CHAR(50),
	gender ENUM('M', 'F', 'O'),
	password VARCHAR(50) NOT NULL,
    UNIQUE (email),
	PRIMARY KEY (user_id) 
);

CREATE TABLE FriendsWith(
	user1_id INTEGER,
	user2_id INTEGER,
	PRIMARY KEY (user1_id, user2_id),
	FOREIGN KEY (user1_id) REFERENCES Users(user_id) 
        ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES Users(user_id) 
        ON DELETE CASCADE,
    CHECK (user1_id <> user2_id) 
);

CREATE TABLE Albums(
	album_id INTEGER AUTO_INCREMENT,
	name VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
	date_created DATE,
	num_photos INTEGER DEFAULT 0,
    PRIMARY KEY (album_id),
	FOREIGN KEY (user_id) REFERENCES Users(user_id) 
        ON DELETE CASCADE 
);

CREATE TABLE Photos(
	photo_id INTEGER AUTO_INCREMENT,
	album_id INTEGER NOT NULL,
	caption VARCHAR(250),
	data LONGBLOB NOT NULL,
	date_added DATE,
	num_likes INTEGER DEFAULT 0,
    PRIMARY KEY (photo_id),
	FOREIGN KEY (album_id) REFERENCES Albums(album_id)
        ON DELETE CASCADE 
);

CREATE TABLE LikedBy(
	photo_id INTEGER,
	user_id INTEGER,
    PRIMARY KEY(photo_id, user_id),
	FOREIGN KEY (photo_id) REFERENCES Photos(photo_id)
        ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) 
);

CREATE TABLE Tags(
	tag_id INTEGER AUTO_INCREMENT,
	word VARCHAR(50),
	num_tagged INTEGER DEFAULT 1,
	UNIQUE (word),
	PRIMARY KEY (tag_id) 
);

CREATE TABLE TaggedWith(
	photo_id INTEGER,
	tag_id INTEGER,
	PRIMARY KEY (photo_id, tag_id),
	FOREIGN KEY (photo_id) REFERENCES Photos(photo_id)
        ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES Tags(tag_id)
);

CREATE TABLE Comments(
	comment_id INTEGER AUTO_INCREMENT,
	text VARCHAR(250) NOT NULL,
    date_posted DATE,
    photo_id INTEGER,
	user_id INTEGER DEFAULT 1000000,
	PRIMARY KEY (comment_id),
	FOREIGN KEY (photo_id) REFERENCES Photos(photo_id)
        ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON DELETE CASCADE
);