#! /usr/bin/python

import os
import json, re
import collections
import mysql.connector
import db_creditials as creds
from mysql.connector import errorcode

TABLES = collections.OrderedDict()
TABLES['schools'] = '''
	CREATE TABLE `schools` (
		`id` int(11) NOT NULL AUTO_INCREMENT,
		`name` varchar(64) NOT NULL UNIQUE,
		`slug` varchar(5) NOT NULL UNIQUE,
		PRIMARY KEY (`id`)
	) ENGINE=InnoDB
'''

TABLES['departments'] = '''
	CREATE TABLE `departments` (
		`id` int(11) NOT NULL AUTO_INCREMENT,
		`school_id` int(11) NOT NULL,
		`name` varchar(30) NOT NULL,
		`abbreviation` varchar(6),
		KEY `school_id` (`school_id`),
		CONSTRAINT `departments_fk_1` FOREIGN KEY (`school_id`) REFERENCES `schools` (`id`) ON UPDATE CASCADE,
		PRIMARY KEY (`id`, `school_id`, `name`)
	) ENGINE=InnoDB
'''

TABLES['courses'] = '''
	CREATE TABLE `courses` (
		`id` int(11) NOT NULL AUTO_INCREMENT,
		`department_id` int(11) NOT NULL,
		`number` int(11) NOT NULL,
		`title` varchar(128) NOT NULL,
		`description` varchar(8192),
		`prereq_str` varchar(2048),
		KEY `department_id` (`department_id`),
		CONSTRAINT `courses_fk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON UPDATE CASCADE,
		PRIMARY KEY (`id`)
	) ENGINE=InnoDB
'''

TABLES['prerequisites'] = '''
	CREATE TABLE `prerequisites` (
		`course_id` int(11) NOT NULL,
		`grouping` int(11) NOT NULL,
		`prereq_id` int(11) NOT NULL,
		CONSTRAINT `prerequisites_fk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON UPDATE CASCADE,
		CONSTRAINT `prerequisites_fk_2` FOREIGN KEY (`prereq_id`) REFERENCES `courses` (`id`) ON UPDATE CASCADE,
		PRIMARY KEY (`course_id`, `grouping`, `prereq_id`)
	) ENGINE=InnoDB
'''

def create_database(cursor, db):
	try:
		cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db))
		print "Created database: {}".format(db)
	except mysql.connector.Error as err:
		print "Failed creating database: {}".format(err)
		exit(1)

def create_tables(cursor):
	for name, ddl in TABLES.iteritems():
		try:
			print "Creating table {}:".format(name),
			cursor.execute(ddl)
		except mysql.connector.Error as err:
			if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
				print "Already exists.",
				try:
					truncate_table(cursor, name)
					print "Removed all data."
				except mysql.connector.Error as err:
					print "Failed to clear table."
					print err
			else:
				print err.msg 
		else:
			print "OK"

def truncate_table(cursor, name):
	fk_off = "SET FOREIGN_KEY_CHECKS = 0"
	cursor.execute(fk_off)

	query = "DELETE FROM %s" % (name)
	cursor.execute(query)

	alter = "ALTER TABLE %s auto_increment = 1" % name

	fk_on = "SET FOREIGN_KEY_CHECKS = 1"
	cursor.execute(fk_on)

	cursor.execute(alter);

def connect_to_db(cnx, cursor, db):
	try:
		cnx.database = db
		print "Connected to database: {}".format(db)
	except mysql.connector.Error as err:
		if err.errno == errorcode.ER_BAD_DB_ERROR:
			create_database(cursor, db)
			cnx.database = db
		else:
			print err
			exit(1)

def get_mysql_connection():
	try:
		
		return mysql.connector.connect(user=creds.user, password=creds.password, host=creds.host)
	except mysql.connector.Error as err:
		if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
			print "Something is wrong with your user name or password"
		elif err.errno == errorcode.ER_BAD_DB_ERROR:
			print "Database does not exists"
		else:
			print err

def get_courses():
	json_data = open('all_data_new.json')
	return json.load(json_data)

def insert_school(cursor, name, slug):
	query = (
		"INSERT INTO schools"
		"  (name, slug) "
		"  VALUES (%(name)s, %(slug)s)")
	data = {
		'name': name,
		'slug': slug
	}
	cursor.execute(query, data)
	print "Added school: {} ({})".format(name, cursor.lastrowid)
	return cursor.lastrowid

def insert_department(cursor, school_id, name, abbreviation):
	try:
		query = (
			"INSERT INTO departments"
			"  (school_id, name, abbreviation)"
			"  VALUES (%(school)s, %(name)s, %(abbreviation)s)")
		data = {
			'school': school_id,
			'name': name,
			'abbreviation': abbreviation
		}
		cursor.execute(query, data)
		print "Added department: {} ({})".format(name, cursor.lastrowid)
		return cursor.lastrowid
	except mysql.connector.Error as err:
		print "Failed creating department {}: {}".format(name, err)
		exit(1)

def insert_course(cursor, department_id, course):
	try:
		query = (
			"INSERT INTO courses"
			"  (department_id, number, title, description, prereq_str)"
			"  VALUES (%(department)s, %(number)s, %(title)s, %(description)s, %(prereq_str)s)")
		data = {
			"department": department_id,
			"number": course['number'],
			"title": course['title'],
			"description": course['description'],
			"prereq_str": course['prereqstr']
		}
		cursor.execute(query, data)
	except mysql.connector.Error as err:
		print "Failed creating course {}: {}".format(course['number'], err)
		exit(1)

def insert_course_prereqs(cursor, department_id, cdata):
	prereqstr = cdata['prereqstr']
	prereqs = get_prereq(prereqstr)

	course_query = '''
		SELECT 
			id
		FROM courses
		WHERE department_id = %(dept_id)s AND number = %(number)s
		LIMIT 1
	'''
	course_data = {
		'dept_id': department_id,
		'number': cdata['number']
	}
	cursor.execute(course_query, course_data)
	course_id = cursor.next()[0]

	for i, prereq in enumerate(prereqs):
		for option in prereq:
			p_dept, sep, p_num = option.partition(" ")
			query = '''
				INSERT INTO prerequisites
					(course_id, grouping, prereq_id)
					SELECT 
						%(course_id)s, %(grouping)s, id
				    FROM courses 
				    WHERE department_id = (SELECT id FROM departments WHERE abbreviation = %(p_dept)s LIMIT 1)
				    	AND number = %(p_num)s
			'''
			data = {
				"course_id": course_id,
				"grouping": i,
				"p_dept": p_dept,
				"p_num": p_num
			}
			cursor.execute(query, data)



def get_prereq(prereqstr):
	prereq_list = []
	if prereqstr:
		prereqs = prereqstr.split("Coreq")[0]
		ands = prereqs.split(" and")
		for prereq in ands:
			ors = set(re.findall("[A-Z]{2,4} [0-9]{4}", prereq))
			if len(ors) == 0:
				continue
			else:
				prereq_list.append(ors)
			# prereq_list.append(prereq)
			
		return prereq_list

	return prereq_list

def main():
	cnx = get_mysql_connection()
	cursor = cnx.cursor()
	connect_to_db(cnx, cursor, creds.database)
	create_tables(cursor)
	cnx.commit()

	schools = os.listdir('schools')
	for s in schools:
		json_file = open('schools/' + s)
		json_data = json.load(json_file)
		
		school_name = json_data['school']
		school_slug = json_data['slug']
		school_id = insert_school(cursor, school_name, school_slug)

		departments = json_data['departments']
		
		dept_dict = {} # Cache ids to prevent lookups later on
		
		# First pass through to add all the courses
		for department in departments:
			dept_name = department['name']
			dept_abbv = department['abbreviation']
			dept_id = insert_department(cursor, school_id, dept_name, dept_abbv)
			dept_dict[dept_abbv] = dept_id
			cnx.commit()

			courses = department['courses']
			for course in courses:
				insert_course(cursor, dept_id, course)
		cnx.commit()

		# Second pass through to add all the prereqs
		for department in departments:
			dept_id = dept_dict[department['abbreviation']]
			courses = department['courses']
			for course in courses:
				insert_course_prereqs(cursor, dept_id, course)
			cnx.commit()
			print "Added prerequisites: {}".format(department['name'])

if __name__ == '__main__':
	main()



