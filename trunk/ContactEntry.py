#	This file is part of Arkadas.
#
#	Arkadas is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; either version 2 of the License, or
#	(at your option) any later version.
#
#	Arkadas is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with Arkadas; if not, write to the Free Software
#	Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import codecs, quopri, urllib

foldmarks = ['\r\n\t', '\r\n ',  '\n\t', '\n ']
foldmark = '\n '

tel_types = [ 'VOICE', 'ISDN', 'CELL', 'CAR', 'VIDEO', 'PAGER', 'FAX', 'MODEM', 'BBS', 'PCS' ]
im_types = ['X-AIM', 'X-GADU-GADU', 'X-GROUPWISE', 'X-ICQ', 'X-IRC', 'X-JABBER', 'X-MSN', 'X-NAPSTER', 'X-YAHOO', 'X-ZEPHYR']

class Entry:

	def escape(self, s):
		"""escape vcard value string"""
		s = s.replace(',', '\,')
		s = s.replace(';', '\;')
		s = s.replace('\n', '\\n')
		s = s.replace('\r', '\\r')
		s = s.replace('\t', '\\t')
		return s

	def unescape(self, s):
		"""unescape vcard value string"""
		s = s.replace('\,', ',')
		s = s.replace('\;', ';')
		s = s.replace('\\n', '\n')
		s = s.replace('\\r', '\r')
		s = s.replace('\\t', '\t')
		return self.entities(s)

	def entities(self, s):
		s = s.replace('<', '&lt;')
		s = s.replace('>', '&gt;')
		s = s.replace('&', '&amp;')
		s = s.replace('"', '&quot;')
		return s


	def get_entries_from_dict(self):
		"""Fill window entries from vcard dictionary"""
		namelist = None
		self.fullname = '' ; self.name = 5 * ['']
		self.title = '' ; self.org = ''
		self.nick = '' ; self.note_text = ''
		self.photo = None ; self.pixbuf = None
		self.work_email = [] ; self.email = []
		self.work_address = [] ; self.address = []
		self.work_tel = [] ; self.tel = []
		self.work_url = '' ; self.url = ''
		self.work_videoconference = '' ; self.videoconference = ''
		self.im = []
		self.unknown_properties = {}

		def bday_from_dict(value):
			"""return (yyyy/mm/dd) from card dictionary"""
			try:
				(y, m, d) = value.split("-", 2)
				d = d.split('T')
				if y.isdigit() and m.isdigit() and d[0].isdigit():
					year = int(y); month = int(m); day = int(d[0])
					if month >=1 and month <=12:
						if day >= 1 and day <=31:
							return (year, month, day)
			except:
				pass
			return (None, None, None)

		for key in self.dict:
			value = self.dict[key]
			types = []

			try:
				typestring = key.split("TYPE=", 1)[1]
				if typestring.find(","):
					types = typestring.split(",")
			except:
				pass

			key = key.replace("TYPE=", "")
			key = key.replace(";", ",")
			try:
				valuelist = key.split(",")
				type = valuelist[0]
				del valuelist[0]
			except:
				valuelist = []
				type = key

			if type == "BDAY":
				(y, m, d) = bday_from_dict(value)
				if d:
					self.bday_year = y
					self.bday_month = m
					self.bday_day = d
			elif type == "URL":
				value = self.unescape(value)
				if value.find("callto://") >=0 or value.find("h323://") >=0:
					if "WORK" in valuelist:
						self.work_videoconference = value
					else:
						self.videoconference = value
				elif "WORK" in valuelist:
					if not value.startswith('http:') and len(value) > 0:
						value = "http://" + value
					self.work_url = value
				else:
					if not value.startswith('http:') and len(value) > 0:
						value = "http://" + value
					self.url = value
			elif type == "EMAIL":
				value = self.unescape(value)
				if "WORK" in valuelist:
					self.work_email.append(value)
				else:
					self.email.append(value)
			elif type == "ADR":
				value = self.unescape(value)
				if value.count(';') == 5:
					value += ';'
				if value.count(';') == 6:
					# pobox, extended, street, city, state, zip, country
					if "WORK" in valuelist:
						self.work_address = value.split(';')
					else:
						self.address = value.split(';')
				else:
					print "ADR malformed"
			elif type == "TEL":
				for i in tel_types:
					if i in valuelist: history = i ; break
				if "WORK" in valuelist:
					if "PREF" in valuelist:
						self.work_tel.insert(0,[value,history])
					else:
						self.work_tel.append([value,history])
				else:
					if "PREF" in valuelist:
						self.tel.insert(0,[value,history])
					else:
						self.tel.append([value,history])
			elif type == "ORG":
				self.org = self.unescape(value)
			elif type == "CATEGORIES":
				self.categories = value
			elif type == "N":
				# family, given, additional, prefixes, suffixes
				namelist = value.split(';')
			elif type == "FN":
				self.fullname = self.unescape(value)
			elif type == "NICKNAME":
				self.nick = self.unescape(value)
			elif type == "TITLE":
				self.title = self.unescape(value)
			elif type == "ROLE":
				self.role = self.unescape(value)
			elif type == "NOTE":
				self.note_text = self.unescape(value)
			elif type == "KEY":
				from webbrowser import _iscommand as iscommand
				if iscommand('gpg'):
					try:
						import base64, gpg
						k = gpg.Key()
						k.value = base64.decodestring(value)
						gnupg = gpg.MyGnuPG()
						(k.keyID, k.UserID) = gnupg.get_ID(k.value)
						self.key = k
					except:
						pass
				else:
					self.unknown_properties[key] = value
			elif type == "PHOTO":
				self.photo = value
				if "VALUE=URI" in valuelist:
					self.photo_type = "URI"
				elif "ENCODING=B" in valuelist or "BASE64" in valuelist:
					self.photo_type = "B64"
				else:
					self.photo = None
			elif type in im_types:
				self.im.append([self.unescape(value), type])
			elif type == "X-EVOLUTION-BLOG-URL":
				value = self.unescape(value)
			elif type == "X-EVOLUTION-FILE-AS":
				value = self.unescape(value)
			elif type == "UID":
				self.uuid = value
			elif type == "CLASS":
				self.classification = value
			elif type == "REV":
				self.rev = value
			elif type not in ['BEGIN', 'VERSION', 'PRODID', 'END']:
				self.unknown_properties[key] = value

		if namelist != None:
			for i in range(len(namelist)):
				self.name[i] = str(namelist[i])

		if not len(self.fullname) > 0:
			f = ''
			for i in (3,1,2,0,4):
				f += self.name[i].strip() + ' '
			self.fullname = f.strip().replace('  ',' ')

		del self.dict

	def get_dict_from_file(self, filename):

		def to_utf8(value, key):
			"""convert value from any to utf-8"""

			encoding = self.encoding

			# deal with vCard v2.1 inline encodings
			keylist = key.split(';')
			for item in keylist:
				if item.find("QUOTED-PRINTABLE") >= 0:
					value = quopri.decodestring(value)
				if item.find("CHARSET") == 0:
					encoding = item.split('=', 1)[0].lower()

			# convert from detected encoding to utf-8
			try:
				decoder = codecs.getdecoder(encoding)
				value = decoder(value)[0]
				#print value
			except:
				pass

			return value

		self.filename = filename
		self.dict = {}
		if not self.get_card_from_file(): return False

		for l in self.card:
			line = l.strip("\r\n")
			try:
				(key, value) = line.split(":", 1)
			except:
				continue
			key = key.upper()

			# avoid loss of dupes
			if self.dict.has_key(key):
				if key.find('EMAIL')==0 or key.find('TEL')==0 or key.find('ADR')==0:
					if key.find(',PREF')>=0:
						self.dict[key.replace(',PREF','')] = self.dict[key]
					elif key.find(':PREF')>=0:
						self.dict[key.replace('PREF','', 1)] = self.dict[key]
					else:
						self.dict[key+',PREF'] = self.dict[key]

			self.dict[key] = to_utf8(value, key)

		del self.card
		return True

	def decode_v30(self, contents):
		"""convert v3.0 card to utf-8"""
		# vcard version 3.0: encoding is global,
		# provided with the MIME header.
		# When we don't have the header, assume utf-8
		# if that fails, pop up dialog for the user to select
		# the encoding
		errors = 'strict'
		encoding = 'utf-8'
		while 1:
			decoder = codecs.getdecoder(encoding)
			try:
				data = decoder(contents, errors)[0]
				if errors == 'strict':
					assert '\0' not in data
				else:
					if '\0' in data:
						data = data.replace('\0', '\\0')
				break
			except:
				pass

			encoding, errors = self.get_encoding(
					"Data is not valid %s. Please select the file's encoding." % encoding)

		return encoding

	def get_card_from_file(self):
		"""Get card from file as list with lines unfolded"""
		self.card = []
		self.encoding = 'utf-8'
		try:
			file = open(self.filename, 'r')
			contents = file.read()
			file.close()

			for mark in foldmarks:
				contents = contents.replace(mark, '')

			lines = contents.splitlines()

			if lines[0].upper().find("BEGIN:VCARD") < 0:
				return False

			i = -1 ; length = len(lines) ; nesting = 0
			while i <= length:
				i += 1
				self.card.append(lines[i])
				# handle embedded cards and multiple card files
				if lines[i].upper().find("BEGIN:") >=0:
					nesting += 1
				elif lines[i].upper().find("END:") >=0:
					nesting -= 1
				if nesting <= 0:
					break
		except:
			raise
			return False

		if not (contents.upper().find("QUOTED-PRINTABLE") >=0 \
			or contents.upper().find("CHARSET=")) >=0:
			self.encoding = self.decode_v30(contents)

		return True
