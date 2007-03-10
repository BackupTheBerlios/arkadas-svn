# -*- coding: utf-8 -*-

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

import os, sys, subprocess
import gtk

try:
	import vobject
	HAVE_VOBJECT = True
except:
	HAVE_VOBJECT = False

import ContactEngine

import gettext
gettext.install("arkadas", "/usr/share/locale", unicode=1)

types = {
	"home":_("Home"), "work":_("Work"),
	"bday":_("Birthday"), "url":_("Website"),
	"email":"Email", "adr":_("Address"),
	"im":"Instant Messaging",
	"note":_("Notes:"), "tel":_("Phone"),
	# address types
	"box":_("Postbox"), "extended":_("Extended"),
	"street":_("Street"), "city":_("City"),
	"region":_("State"), "code":_("ZIP"), "country":_("Country"),
	# tel types
	"cell":_("Mobile"), "fax":_("Fax"),
	# im types
	"aim":"AIM", "gadu-gadu":"Gadu-Gadu",
	"groupwise":"GroupWise", "icq":"ICQ",
	"irc":"IRC", "jabber":"Jabber",
	"msn":"MSN", "napster":"Napster",
	"yahoo":"Yahoo", "zephyr":"Zephyr",
	}

tel_types = ("home", "work", "cell", "work_cell", "fax", "work_fax")
im_types = ("aim", "gadu-gadu", "groupwise", "icq", "irc", "jabber", "msn", "napster", "yahoo", "zephyr")

display_formats = ["%g %a %f", "%p %g %a %f %s", "%f, %g %a", "%f %g %a"]
address_formats = ["%street %extended\n%box\n%city %region %code\n%country",
					"%street %extended\n%box\n%code %city %region\n%country",]
sort_formats = ["%f %g %a", "%g %a %f"]

def import_vcard(filename, engine, photo_dir=""):
	contact = None

	vcards = vobject.readComponent(file(filename, "r"))

	for vcard in vcards:
		try:
			contact = engine.addContact()

			if vcard.version.value == "3.0":
				names = vcard.n.value.__dict__
			else:
				names = dict(zip(vobject.vcard.NAME_ORDER, vcard.n.value.split(";")))

			contact.names = ContactEngine.Name(**names)

			for name in ("nickname", "org", "title", "note", "bday", "photo"):
				field = getattr(vcard, name, None)
				if field:
					if name=="photo":
						if "VALUE" in vcard.photo.params:
							import urllib
							url = urllib.urlopen(vcard.photo.value)
							data = url.read()
							url.close()
						elif "ENCODING" in vcard.photo.params:
							data = vcard.photo.value

						if photo_dir and contact.uuid:
							import os
							path = os.path.join(photo_dir, contact.uuid)
							pfile = file(path, "w")
							pfile.write(data)
							pfile.close()
							contact.photo = path
					elif name=="bday":
						setattr(contact, name, field.value.split("T")[0])
					else:
						setattr(contact, name, unescape(field.value))

			for name in ("tel", "email", "url", "adr"):
				if not getattr(vcard, name, None): continue
				for field in vcard.contents[name]:
					content = contact.add(name)

					if field.params.has_key("TYPE"):
						if name=="tel":
							work = ("WORK" in field.type_paramlist)
							for teltype in ("CELL", "FAX"):
								if teltype in field.type_paramlist:
									content.type = "work_" * work + teltype.lower()
							if not content.type:
								if work:
									content.type = "work"
								else:
									content.type = "home"
						else:
							if "WORK" in field.type_paramlist:
								content.type = "work"
							else:
								content.type = "home"
					else:
						content.type = "home"

					if name=="adr":
						for attr in vobject.vcard.ADDRESS_ORDER:
							setattr(content, attr, getattr(field.value, attr))
					else:
						content.value = field.value

			for imtype in im_types:
				im = getattr(vcard, "X-" + imtype.upper(), None)
				if im:
					for field in vcard.contents[""]:
						content = contact.add("im")
						content

			contact.save()

		except:
			if contact: engine.removeContact(contact.id)

	return contact

def export_vcard(filename, contact):
	try:
		vcard = vobject.vCard()

		vcard.add("n").value = vobject.vcard.Name(**contact.names.__dict__)
		vcard.add("fn").value = format_fn(DISPLAY_FORMAT, **contact.names.__dict__)

		for name in ("nickname", "org", "title", "note", "bday", "photo"):
			field = getattr(contact, name, None)
			if field:
				if name=="photo":
					import urllib
					url = urllib.urlopen(field)
					data = url.read()
					url.close()

					content = vcard.add(name)
					content.encoding_param = "b"
					content.value = data
				elif name=="bday":
					vcard.add(name).value = field
				else:
					vcard.add(name).value = escape(field)

		for name in ("tel", "email", "url", "adr"):
			list = getattr(contact, name+"_list")
			for field in list:
				content = vcard.add(name)
				if name=="adr":
					for attr in vobject.vcard.ADDRESS_ORDER:
						setattr(content.value, attr, getattr(field, attr))
				elif name=="tel":
					content.value = field.value
					type = field.type
					if type in ("home", "work"):
						content.type_paramlist = [type.upper(), "VOICE"]
					else:
						if type.startswith("work_"):
							content.type_paramlist = type.upper().split("_")
						else:
							content.type_paramlist = ["HOME", type.upper()]
				else:
					content.value = field.value
					content.type_paramlist = [field.type.upper()]

		for field in contact.im_list:
			name = "X-" + field.type.upper()
			vcard.add(name).value = field.value

		data = vcard.serialize()

		vfile = file(filename, "a")
		vfile.write(data)
		vfile.close()

		return True
	except:
		return False

def escape(s):
	s = s.replace(",", "\,")
	s = s.replace(";", "\;")
	s = s.replace("\n", "\\n")
	s = s.replace("\r", "\\r")
	s = s.replace("\t", "\\t")
	return s

def unescape(s):
	s = s.replace("\,", ",")
	s = s.replace("\;", ";")
	s = s.replace("\\n", "\n")
	s = s.replace("\\r", "\r")
	s = s.replace("\\t", "\t")
	return s

def entities(s):
	s = s.replace("<", "&lt;")
	s = s.replace(">", "&gt;")
	s = s.replace("&", "&amp;")
	s = s.replace("\"", "&quot;")
	return s

def format_fn(format, **args):
	fullname = format
	for attr in ContactEngine.NAME_ORDER:
		val = args.get(attr, "")
		if not val:
			val = ""
		fullname = fullname.replace("%"+attr[0], val)
	fullname = fullname.replace("  ", " ").strip()
	return fullname

def format_adr(format, **args):
	address = format
	for attr in ContactEngine.ADDRESS_ORDER:
		val = args.get(attr, "")
		if not val:
			val = ""
		elif attr == "city": val += ","
		address = address.replace("%"+attr, val)
	address = address.replace(" ,", "")
	address = address.replace(" \n", "")
	address = address.replace("  ", " ").strip()
	return address

def bday_from_value(value):
	try:
		(y, m, d) = value.split("-", 2)
		if y.isdigit() and m.isdigit() and d.isdigit():
			year = int(y); month = int(m); day = int(d)
			if month >=1 and month <=12:
				if day >= 1 and day <=31:
					return (year, month, day)
	except:
		pass
	return (None, None, None)

def get_pixbuf_of_size(pixbuf, size):
	image_width = pixbuf.get_width()
	image_height = pixbuf.get_height()
	if image_width-size > image_height-size:
		image_height = int(size/float(image_width)*image_height)
		image_width = size
	else:
		image_width = int(size/float(image_height)*image_width)
		image_height = size
	crop_pixbuf = pixbuf.scale_simple(image_width, image_height, gtk.gdk.INTERP_HYPER)
	return crop_pixbuf

def get_crop_pixbuf(pixbuf):
	image_width = pixbuf.get_width()
	image_height = pixbuf.get_height()
	image_xdiff = 0
	image_ydiff = 0
	if image_width > image_height:
		image_xdiff = int((image_width-image_height)/2)
		image_width = image_height
	else:
		image_ydiff = int((image_height-image_width)/2)
		image_height = image_width
	new_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, image_width, image_height)
	new_pixbuf.fill(0x00000000)
	pixbuf.copy_area(image_xdiff, image_ydiff, image_width, image_height, new_pixbuf, 0, 0)
	del pixbuf
	return new_pixbuf

def get_pad_pixbuf(pixbuf, width, height):
	image_width = pixbuf.get_width()
	image_height = pixbuf.get_height()
	x_pos = int((width - image_width)/2)
	y_pos = int((height - image_height)/2)
	new_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, width, height)
	new_pixbuf.fill(0xffff00)
	pixbuf.copy_area(0, 0, image_width, image_height, new_pixbuf, x_pos, y_pos)
	del pixbuf
	return new_pixbuf

def get_pixbuf_of_size_from_file(filename, size):
	try:
		pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
		pixbuf = get_pixbuf_of_size(pixbuf, size)
		return pixbuf
	except:
		return None

def error(text, window=None):
	msg(text, window, type=gtk.MESSAGE_WARNING)

def msg(text, window=None, type=gtk.MESSAGE_INFO):
	dialog = gtk.MessageDialog(window, gtk.DIALOG_MODAL, type, gtk.BUTTONS_CLOSE, text)
	dialog.set_property("use-markup", True)
	dialog.run()
	dialog.destroy()

def browser_load(docslink, window=None):
	try:
		pid = subprocess.Popen(["gnome-open", docslink]).pid
	except:
		try:
			pid = subprocess.Popen(["exo-open", docslink]).pid
		except:
			try:
				pid = subprocess.Popen(["firefox", docslink]).pid
			except:
				try:
					pid = subprocess.Popen(["mozilla", docslink]).pid
				except:
					try:
						pid = subprocess.Popen(["opera", docslink]).pid
					except:
						error(_("Unable to launch a suitable browser."), window)

def find_path(filename):
	dirs = (os.path.join(os.path.split(__file__)[0], filename),
			os.path.join(os.path.split(__file__)[0], "pixmaps", filename),
			os.path.join(os.path.split(__file__)[0], "share", filename),
			os.path.join(__file__.split("/lib")[0], "share", "pixmaps", filename),
			os.path.join(sys.prefix, filename),
			os.path.join(sys.prefix, "share", filename),
			os.path.join(sys.prefix, "share", "arkadas", filename),
			os.path.join(sys.prefix, "share", "pixmaps", filename),
			)
	for dir in dirs:
		if os.path.exists(dir):
			return dir
	return ""
