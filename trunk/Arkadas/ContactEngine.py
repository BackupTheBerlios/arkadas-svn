# -*- coding: utf-8 -*-

# Copyright © 2006-2007 Paul Johnson <thrillerator@googlemail.com>
#
# This file is part of Arkadas.
#
# Arkadas is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Arkadas is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Arkadas; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA

import os
from datetime import datetime
from uuid import uuid4

try:
	import sqlite3
except ImportError:
	from pysqlite2 import dbapi2 as sqlite3 

NAME_ORDER = ("family", "given", "additional", "prefix", "suffix")
ADDRESS_ORDER = ("street", "city", "region", "code", "country", "box", "extended")

class ContactDB:
	"""
	This class is used for the DB connection.
	It includes the functions to load contacts and groups.
	"""
	
	def __init__(self, filename=None):
		self.conn = None

		if filename is not None:
			self.load(filename)

	def load(self, filename, create=True):
		"""
		Load DB from file and if it doesn't exists create it.
		"""
		
		if os.path.exists(filename):
			self.conn = sqlite3.connect(filename)
		elif create:
			self.create(filename)

		return True

	def create(self, filename):
		"""
		Create DB and fill with tables.
		"""
		
		self.conn = sqlite3.connect(filename)

		query = """create table contacts(
			contact_id	integer primary key,
			uuid		text unique,
			created		text,
			modified	text,
			name_f		text,
			name_g		text,
			name_a		text,
			name_p		text,
			name_s		text,
			nickname	text,
			title		text,
			org			text,
			bday		text,
			note		text,
			photo		text
		);
		create table contents(
			content_id	integer primary key,
			contact_id	integer,
			name		text,
			type		text,
			value		text
		);
		create table addresses(
			address_id	integer primary key,
			contact_id	integer,
			type		text,
			street		text,
			city		text,
			region		text,
			code		text,
			country		text,
			box			text,
			extended	text
		);
		create table groups(
			group_id	integer primary key,
			name		text,
			desc		text
		);
		create table members(
			member_id	integer primary key,
			group_id	integer,
			contact_id	integer
		);"""

		try:
			self.conn.executescript(query)
			return True
		except:
			raise
			return False

	def getList(self, group_id=-1):
		"""
		Get list of contacts in specified group.
		Group-ID = -1 return all
		Group-ID = 0 return uncategorized 
		"""
		
		if group_id > 0:
			return self.conn.execute("select contact_id from members where group_id=?", (group_id,)).fetchall()
		elif group_id==0:
			return self.conn.execute("select contact_id from contacts where contact_id not in (select contact_id from members)").fetchall()
		else:
			return self.conn.execute("select contact_id from contacts").fetchall()

	def getGroups(self):
		return self.conn.execute("select * from groups order by name").fetchall()

	def addGroup(self, name, desc=""):
		query = "insert into groups values(null, ?, ?)"
		cur = self.conn.execute(query, (name, desc))
		self.conn.commit()
		return cur.lastrowid

	def editGroup(self, group_id, name, desc=""):
		query = "update groups set name=?, desc=? where group_id=?"
		cur = self.conn.execute(query, (name, desc, group_id))
		self.conn.commit()

	def removeGroup(self, group_id):
		query = "delete from groups where group_id=?"
		self.conn.execute(query, (group_id,))
		query = "delete from members where group_id=?"
		self.conn.execute(query, (group_id,))
		self.conn.commit()

	def getContact(self, id):
		"""
		Fetches contact and contents from DB.
		Return Contact object.
		"""
		
		if isinstance(id, Contact): return id
		
		try:
			data = self.conn.execute("select * from contacts where contact_id=?", (id,)).fetchone()

			contact = Contact(self.conn, data[0], Name(*data[4:9]), data[1], data[2], data[3], *data[9:])

			for row in self.conn.execute("select * from contents where contact_id=?", (id,)).fetchall():
				getattr(contact, row[2]+"_list").append(Content(row[0], *row[2:]))

			for row in self.conn.execute("select * from addresses where contact_id=?", (id,)).fetchall():
				contact.adr_list.append(Address(row[0], *row[2:]))

			return contact
		except:
			return None

	def addContact(self):
		query = "insert into contacts(contact_id) values(null)"
		cur = self.conn.execute(query)
		self.conn.commit()
		return self.getContact(cur.lastrowid)

	def removeContact(self, obj):
		id = self.getIDfromObj(obj)
		
		query = "delete from contacts where contact_id=?"
		self.conn.execute(query, (id,))
		query = "delete from addresses where contact_id=?"
		self.conn.execute(query, (id,))
		query = "delete from contents where contact_id=?"
		self.conn.execute(query, (id,))
		query = "delete from members where contact_id=?"
		self.conn.execute(query, (id,))
		self.conn.commit()

	def addToGroup(self, group_id, contact_id):
		if self.isInGroup(group_id, contact_id): return False
		
		query = "insert into members values(null,?,?)"
		self.conn.execute(query, (group_id,contact_id))
		self.conn.commit()
		return True

	def removeFromGroup(self, group_id, contact_obj):
		contact_id = self.getIDfromObj(contact_obj)
		if self.isInGroup(group_id, contact_id): return False
		
		query = "delete from members where group_id=? and contact_id=?"
		self.conn.execute(query, (group_id,contact_id))
		self.conn.commit()
		return True
		
	def isInGroup(self, group_id, contact_id):
		query = "select count(*) from members where group_id=? and contact_id=?"
		return int(self.conn.execute(query, (group_id,contact_id)).fetchone()[0]) > 0
		
	def getIDfromObj(self, obj):
		if isinstance(obj, Contact):
			id = obj.id
		else:
			id = obj
		return id

class Contact(object):
	"""
	This class is used as container of the contact values.
	It contains the Content objects. 
	"""
	
	def __init__(self, conn, id, names, uuid=None, created="", modified="", nickname="", title="", org="", bday="", note="", photo=""):
		if not isinstance(conn, sqlite3.Connection): return None

		self.conn = conn
		self.id = id

		if uuid:
			self.uuid = uuid
		else:
			self.uuid = str(uuid4())
			
		if created:
			self.created = created
		else:
			self.created = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
			
		if modified:
			self.modified = modified
		else:
			self.modified = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

		self.names = names
		self.tel_list = []
		self.email_list = []
		self.adr_list = []
		self.url_list = []
		self.im_list = []
		self.nickname = nickname
		self.title = title
		self.org = org
		self.bday = bday
		self.note = note
		self.photo = photo

	def toList(self):
		order = ("nickname", "title", "org", "bday", "note", "photo")
		data = self.names.toList()
		data.extend([getattr(self, val) for val in order])
		return data

	def hasValue(self, attr):
		return bool(getattr(self, attr))

	def add(self, name):
		if name == "adr":
			query = "insert into addresses(contact_id) values(?)"
			cur = self.conn.execute(query, (self.id,))
			content = Address(cur.lastrowid)
		else:
			query = "insert into contents(contact_id, name) values(?,?)"
			cur = self.conn.execute(query, (self.id, name))
			content = Content(cur.lastrowid, name)
		getattr(self, name+"_list").append(content)
		return content

	def remove(self, content):
		if isinstance(content, Address):
			query = "delete from addresses where address_id=? and contact_id=?"
		else:
			query = "delete from contents where content_id=? and contact_id=?"
		self.conn.execute(query, (content.id, self.id))
		getattr(self, content.name+"_list").remove(content)

	def save(self):
		"""
		Move through the contents and save to DB. 
		"""
		
		try:
			self.modified = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
			
			query = """update contacts set
			uuid=?, modified=?,
			name_f=?, name_g=?, name_a=?, name_p=?, name_s=?,
			nickname=?, title=?, org=?, bday=?, note=?, photo=?
			where contact_id=?"""
			data = [self.uuid, self.modified]
			data.extend(self.toList())
			data.append(self.id)
			self.conn.execute(query, data)

			data = []
			for name in ("tel", "email", "url", "im"):
				namelist = getattr(self, name+"_list")
				for content in namelist:
					data.append(content.toList()[2:]+[content.id, self.id])

			query = "update contents set type=?, value=? where content_id=? and contact_id=?"
			self.conn.executemany(query, data)

			data = []
			for content in self.adr_list:
				data.append(content.toList()[2:]+[content.id, self.id])
			query = """update addresses set
			type=?, street=?, city=?, region=?, code=?, country=?, box=?, extended=?
			where address_id=? and contact_id=?"""
			self.conn.executemany(query, data)

			self.conn.commit()
			return True
		except:
			raise
			return False

class Name(object):
	def __init__(self, family="", given="", additional="", prefix="", suffix=""):
		self.family = family
		self.given = given
		self.additional = additional
		self.prefix = prefix
		self.suffix = suffix

	def toList(self):
		return [getattr(self, val) for val in NAME_ORDER]

class Content(object):
	def __init__(self, id, name, type="", value=""):
		self.id = id
		self.name = name
		self.type = type
		self.value = value

	def toList(self):
		order = ("id", "name", "type", "value")
		return [getattr(self, val) for val in order]

class Address(Content):
	def __init__(self, id, type=None, street="", city="", region="", code="", country="", box="", extended=""):
		Content.__init__(self, id, "adr", type)

		self.street = street
		self.city = city
		self.region = region
		self.code = code
		self.country = country
		self.box = box
		self.extended = extended

	def toList(self):
		return [self.id, self.name, self.type]+[getattr(self, val) for val in ADDRESS_ORDER]

	def isEmpty(self):
		for val in ADDRESS_ORDER:
			if getattr(self, val):
				return False
		return True
