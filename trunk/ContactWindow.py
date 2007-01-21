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

import gtk, gobject, pango
from Commons import *

order = ["TEL", "EMAIL", "URL", "IM", "BDAY", "ADR", "WORK_TEL", "WORK_EMAIL", "WORK_ADR"]

class ContactWindow(gtk.VBox):

	def __init__(self, parent):
		gtk.VBox.__init__(self, False, 6)

		self.new_parent = parent
		self.tooltips = parent.tooltips

		self.vcard = None
		self.table = None
		self.color = gtk.gdk.color_parse("white")

		# display
		self.scrolledwindow = gtk.ScrolledWindow()
		self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		self.pack_start(self.scrolledwindow)

		self.hsizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

		# buttons
		self.buttonbox = gtk.HBox(False, 6)
		self.pack_end(self.buttonbox, False)

		self.addButton = gtk.Button("", gtk.STOCK_ADD)
		self.addButton.set_sensitive(False)
		self.addButton.set_no_show_all(True)
		self.addButton.show()
		self.addButton.get_child().get_child().get_children()[1].hide()
		self.addButton.connect("clicked", self.addButton_click)
		self.buttonbox.pack_start(self.addButton, False)

		self.buttonbox.pack_start(gtk.Label())

		self.saveButton = gtk.Button("", gtk.STOCK_SAVE)
		self.saveButton.set_no_show_all(True)
		self.saveButton.connect("clicked", self.saveButton_click)
		self.buttonbox.pack_start(self.saveButton, False)

		self.editButton = gtk.Button("", gtk.STOCK_EDIT)
		self.editButton.set_no_show_all(True)
		self.editButton.connect("clicked", self.editButton_click)
		self.buttonbox.pack_start(self.editButton, False)

	def build_interface(self, new_vcard, edit=False):
		self.vcard = new_vcard

		self.table = gtk.VBox(False, 10)
		self.table.set_border_width(10)
		self.table.set_no_show_all(True)
		self.scrolledwindow.add_with_viewport(self.table)
		self.scrolledwindow.get_child().modify_bg(gtk.STATE_NORMAL,self.color)

		self.photohbox = gtk.HBox(False, 2)
		self.emailbox = EventVBox()
		self.workemailbox = EventVBox()
		self.telbox = EventVBox()
		self.worktelbox = EventVBox()
		self.imbox = EventVBox()
		self.workadrbox = EventVBox()
		self.urlbox = EventVBox()
		self.adrbox = EventVBox()
		self.bdaybox = EventVBox()
		self.notebox = EventVBox()

		self.table.pack_start(self.photohbox, False)
		self.table.pack_start(gtk.Label())

		for type in order:
			# tel numbers
			if type == "TEL":
				self.table.pack_start(self.telbox, False)
			elif type == "WORK_TEL":
				self.table.pack_start(self.worktelbox, False)
			# emails
			elif type == "EMAIL":
				self.table.pack_start(self.emailbox, False)
			elif type == "WORK_EMAIL":
				self.table.pack_start(self.workemailbox, False)
			# web
			elif type == "URL":
				self.table.pack_start(self.urlbox, False)
			# instant messaging
			elif type == "IM":
				self.table.pack_start(self.imbox, False)
			# address
			elif type == "ADR":
				self.table.pack_start(self.adrbox, False)
			elif type == "WORK_ADR":
				self.table.pack_start(self.workadrbox, False)
			# birthday
			elif type == "BDAY":
				self.table.pack_start(self.bdaybox, False)

		self.table.pack_start(gtk.Label())
		self.table.pack_start(self.notebox, False)

		# FIELD - photo
		if has_child(self.vcard, "photo"):
			data = None
			# load data or decode data
			if "VALUE" in self.vcard.photo.params:
				try:
					import urllib
					url = urllib.urlopen(self.vcard.photo.value)
					data = url.read()
					url.close()
				except:
					pass
				self.photodatatype = "URI"
			elif "ENCODING" in self.vcard.photo.params:
				data = self.vcard.photo.value
				self.photodatatype = "B64"
			# try to load photo
			try:
				loader = gtk.gdk.PixbufLoader()
				loader.write(data)
				loader.close()
				pixbuf = get_pixbuf_of_size(loader.get_pixbuf(), 64, True)
				self.hasphoto = True
			except:
				pixbuf = get_pixbuf_of_size_from_file("no-photo.png", 64)
				self.hasphoto = False
		else:
			pixbuf = get_pixbuf_of_size_from_file("no-photo.png", 64)
			self.hasphoto = False
		if self.hasphoto: self.photodata = data

		hbox = gtk.HBox()
		self.hsizegroup.add_widget(hbox)
		self.photohbox.pack_start(hbox,False)
		self.photo = ImageButton(pixbuf, self.color, True)
		#self.photo.connect("button_press_event", remove_photo)
		self.tooltips.set_tip(self.photo, _("Click to change image"))
		hbox.pack_end(self.photo, False)

		titlevbox = gtk.VBox()
		self.photohbox.pack_start(titlevbox, True, True, 2)

		# FIELD - fullname & nickname
		fullname = gtk.Label()
		text = "<span size=\"x-large\"><b>%s</b></span>" % unescape(self.vcard.fn.value)
		if has_child(self.vcard, "nickname"):
			text += " (<big>%s</big>)" % unescape(self.vcard.nickname.value)
		fullname.set_markup(text)
		fullname.set_alignment(0,0)
		fullname.set_selectable(True)
		titlevbox.pack_start(fullname)

		# FIELD - title & org
		text = ""
		org = gtk.Label()
		if has_child(self.vcard, "title"):
			text += unescape(self.vcard.title.value)
		if has_child(self.vcard, "org"):
			text += "\n" + unescape(self.vcard.org.value)
		org.set_text(text)
		org.set_alignment(0,0)
		org.set_selectable(True)
		titlevbox.pack_start(org)

		self.changeButton = gtk.Button()
		self.changeButton.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU))
		self.changeButton.set_no_show_all(True)
		self.changeButton.set_property("visible", edit)
		self.changeButton.connect("clicked", self.changeButton_click)
		self.tooltips.set_tip(self.changeButton, _("Click to change fullname"))
		self.photohbox.pack_start(self.changeButton, False)

		self.photohbox.show_all()

		# FIELD - tel
		self.add_labels_by_name(self.telbox, self.worktelbox, "tel")
		# FIELD - emails
		self.add_labels_by_name(self.emailbox, self.workemailbox, "email")
		# FIELD - web
		if has_child(self.vcard, "url"):
			for child in self.vcard.contents["url"]:
				self.add_label(self.urlbox, child)
		# FIELD - instant messaging
		for im in im_types:
			if has_child(self.vcard, im.lower()):
				for child in self.vcard.contents[im.lower()]:
					self.add_label(self.imbox, child)
		# FIELD - address
		self.add_labels_by_name(self.adrbox, self.workadrbox, "adr")
		# FIELD - birthday
		if has_child(self.vcard, "bday"):
			for child in self.vcard.contents["bday"]:
				self.add_label(self.bdaybox, child)

		# FIELD - note
		self.notebox.add(gtk.HSeparator())
		self.notebox.set_spacing(4)
		if not has_child(self.vcard, "note"): self.vcard.add("note")
		self.add_label(self.notebox, self.vcard.note)

		self.table.set_no_show_all(True)
		self.table.show()

		self.switch_mode(edit)



	#---------------
	# event funtions
	#---------------
	def addButton_click(self, button):
		# create type menus
		self.addMenu = gtk.Menu()
		for name in ("TEL", "EMAIL", "ADR", "URL", "IM2", "BDAY"):
			if not name in ("BDAY", "IM2"):
				menuitem = gtk.MenuItem(types[name])
				menuitem.connect("activate", self.addMenu_itemclick, "HOME", name)
				self.addMenu.append(menuitem)
				menuitem = gtk.MenuItem(types[name] + " (" + types["WORK"] + ")")
				menuitem.connect("activate", self.addMenu_itemclick, "WORK", name)
				self.addMenu.append(menuitem)
			else:
				menuitem = gtk.MenuItem(types[name])
				menuitem.connect("activate", self.addMenu_itemclick, "", name)
				self.addMenu.append(menuitem)
		self.addMenu.show_all()
		self.addMenu.popup(None, None, None, 3, 0)

	def addMenu_itemclick(self, item, nametype, name):
		if name == "TEL":
			content = self.vcard.add("tel")
			content.type_paramlist = [nametype, "VOICE"]
			if nametype == "HOME": box = self.add_label(self.telbox, content)
			elif nametype == "WORK": box = self.add_label(self.worktelbox, content)
		elif name == "EMAIL":
			content = self.vcard.add("email")
			content.type_paramlist = [nametype, "INTERNET"]
			if nametype == "HOME": box = self.add_label(self.emailbox, content)
			elif nametype == "WORK": box = self.add_label(self.workemailbox, content)
		elif name == "ADR":
			content = self.vcard.add("adr")
			content.type_paramlist = [nametype, "POSTAL", "PARCEL"]
			if nametype == "HOME": box = self.add_label(self.adrbox, content)
			elif nametype == "WORK": box = self.add_label(self.workadrbox, content)
		elif name == "URL":
			content = self.vcard.add("url")
			box = self.add_label(self.urlbox, content)
		elif name == "IM2":
			content = self.vcard.add("x-aim")
			content.type_paramlist = ["HOME"]
			box = self.add_label(self.imbox, content)
		elif name == "BDAY":
			content = self.vcard.add("bday")
			box = self.add_label(self.bdaybox, content)

		caption, field = box.get_children()[0].get_children()[0], box.get_children()[1]
		caption.set_editable(True)
		field.set_editable(True)
		field.grab_focus()

	def saveButton_click(self, button):
		self.switch_mode(False, True)

	def editButton_click(self, button):
		self.switch_mode(True, False)

	def changeButton_click(self, button):
		def add_label(text):
			label = gtk.Label(text)
			label.set_alignment(1, 0.5)
			label.set_padding(4, 0)
			label.set_use_underline(True)
			return label

		def combo_changed(combo):
			index = combo.get_active()
			text = ""
			if index == 0:
				# simple name
				text += entry1.get_text() + " "
				text += entry2.get_text() + " "
				text += entry3.get_text()
			elif index == 1:
				# full name
				text += entry4.get_text() + " "
				text += entry1.get_text() + " "
				text += entry2.get_text() + " "
				text += entry3.get_text() + " "
				text += entry5.get_text()
			elif index == 2:
				# reverse name with comma
				text += entry3.get_text() + ", "
				text += entry1.get_text() + " "
				text += entry2.get_text()
			elif index == 3:
				# reverse name
				text += entry3.get_text() + " "
				text += entry1.get_text() + " "
				text += entry2.get_text()
			testlabel.set_text(text.replace("  ", " ").strip())

		def dialog_response(dialog, response_id):
			if response_id == gtk.RESPONSE_OK:
				combo_changed(combo)

				if not has_child(self.vcard, "n"): self.vcard.add("n")
				self.vcard.n.value.given = entry1.get_text().replace("  "," ").strip()
				self.vcard.n.value.additional = entry2.get_text().replace("  "," ").strip()
				self.vcard.n.value.family = entry3.get_text().replace("  "," ").strip()
				self.vcard.n.value.prefix = entry4.get_text().replace("  "," ").strip()
				self.vcard.n.value.suffix = entry5.get_text().replace("  "," ").strip()

				self.vcard.fn.value = escape(testlabel.get_text())

				if len(entry6.get_text().replace("  "," ").strip()) > 0:
					if not has_child(self.vcard, "nickname"): self.vcard.add("nickname")
					self.vcard.nickname.value = escape(entry6.get_text().replace("  "," ").strip())
				elif has_child(self.vcard, "nickname"): self.vcard.remove(self.vcard.nickname)

				if len(entry7.get_text().replace("  "," ").strip()) > 0:
					if not has_child(self.vcard, "title"): self.vcard.add("title")
					self.vcard.title.value = escape(entry7.get_text().replace("  "," ").strip())
				elif has_child(self.vcard, "title"): self.vcard.remove(self.vcard.title)

				if len(entry8.get_text().replace("  "," ").strip()) > 0:
					if not has_child(self.vcard, "org"): self.vcard.add("org")
					self.vcard.org.value = escape(entry8.get_text().replace("  "," ").strip())
				elif has_child(self.vcard, "org"): self.vcard.remove(self.vcard.org)

				box = self.photohbox.get_children()[1]
				fullname, org = box.get_children()

				text = "<span size=\"x-large\"><b>%s</b></span>" % unescape(self.vcard.fn.value)
				if has_child(self.vcard, "nickname"):
					text += " (<big>%s</big>)" % unescape(self.vcard.nickname.value)
				fullname.set_markup(text)

				text = ""
				if has_child(self.vcard, "title"):
					text += unescape(self.vcard.title.value)
				if has_child(self.vcard, "org"):
					text += "\n" + unescape(self.vcard.org.value)
				org.set_text(text)

			dialog.destroy()

		dialog = gtk.Dialog(_("Change Name"), self.new_parent, gtk.DIALOG_MODAL)
		dialog.set_resizable(False)
		#dialog.set_size_request(420, -1)
		dialog.set_has_separator(False)
		dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_APPLY, gtk.RESPONSE_OK)
		# dialog table
		table = gtk.Table(13, 2)
		table.set_border_width(6)
		dialog.vbox.add(table)

		table.attach(add_label(_("_Given name:")), 0, 1, 0, 1)
		entry1 = gtk.Entry() ; table.attach(entry1, 1, 2, 0, 1)

		table.attach(add_label(_("_Additional names:")), 0, 1, 1, 2)
		entry2 = gtk.Entry() ; table.attach(entry2, 1, 2, 1, 2)

		table.attach(add_label(_("_Family names:")), 0, 1, 2, 3)
		entry3 = gtk.Entry() ; table.attach(entry3, 1, 2, 2, 3)

		table.attach(gtk.Label(), 0, 2, 3, 4)

		table.attach(add_label(_("_Prefixes:")), 0, 1, 4, 5)
		entry4 = gtk.Entry() ; table.attach(entry4, 1, 2, 4, 5)

		table.attach(add_label(_("_Suffixes:")), 0, 1, 5, 6)
		entry5 = gtk.Entry() ; table.attach(entry5, 1, 2, 5, 6)

		table.attach(gtk.Label(), 0, 3, 6, 7)

		table.attach(add_label(_("For_matted name:")), 0, 1, 7, 8)

		combo = gtk.combo_box_new_text()
		combo.append_text(_("Simple Name"))
		combo.append_text(_("Full Name"))
		combo.append_text(_("Reverse Name with Comma"))
		combo.append_text(_("Reverse Name"))
		combo.connect("changed", combo_changed)
		table.attach(combo, 1, 2, 7, 8)

		testlabel = gtk.Entry()
		testlabel.set_editable(False)
		table.attach(testlabel, 1, 2, 8, 9)

		table.attach(gtk.HSeparator(), 0, 2, 9, 10, ypadding=6)

		table.attach(add_label(_("_Nickname:")), 0, 1, 10, 11)
		entry6 = gtk.Entry() ; table.attach(entry6, 1, 2, 10, 11)

		table.attach(add_label(_("_Title/Role:")), 0, 1, 11, 12)
		entry7 = gtk.Entry() ; table.attach(entry7, 1, 2, 11, 12)

		table.attach(add_label(_("_Organization:")), 0, 1, 12, 13)
		entry8 = gtk.Entry() ; table.attach(entry8, 1, 2, 12, 13)

		if has_child(self.vcard, "n"):
			entry1.set_text(self.vcard.n.value.given)
			entry2.set_text(self.vcard.n.value.additional)
			entry3.set_text(self.vcard.n.value.family)
			entry4.set_text(self.vcard.n.value.prefix)
			entry5.set_text(self.vcard.n.value.suffix)
		entry6.set_text(unescape(self.vcard.getChildValue("nickname", "")))
		entry7.set_text(unescape(self.vcard.getChildValue("title", "")))
		entry8.set_text(unescape(self.vcard.getChildValue("org", "")))

		combo.set_active(1)
		combo_changed(combo)

		# events
		dialog.connect("response", dialog_response)
		dialog.show_all()

	def switch_mode(self, state=False, save=False):
		self.addButton.set_sensitive(state)
		self.saveButton.set_property("visible", state)
		self.editButton.set_property("visible", not state)
		self.changeButton.set_property("visible", state)

		if save:
			import os, vobject
			new_vcard = vobject.vCard()
			if self.vcard.version.value == "3.0":
				new_vcard.add(self.vcard.n)
			else:
				n = self.vcard.n.value.split(";")
				new_vcard.add("n")
				new_vcard.n.value = vobject.vcard.Name(n[0], n[1], n[2], n[3], n[4])
			new_vcard.add(self.vcard.fn)

			if self.hasphoto:
				photo = new_vcard.add("photo")
				if self.photodatatype == "URI":
					photo.value_param = "URI"
				else:
					photo.encoding_param = "b"
				photo.value = self.photodata

		for child in self.table.get_children():
			if type(child) == EventVBox:
				for hbox in child.get_children():
					if type(hbox) == gtk.HBox:
						# get caption & field
						caption, field = hbox.get_children()[0].get_children()[0], hbox.get_children()[1]
						caption.set_editable(state)

						if type(field) == LabelField:
							field.set_editable(state)
							# remove empty field
							if field.get_text() == "":
								hbox.destroy()
								continue
							if save:
								new_vcard.add(field.content)
						elif type(field) == AddressField:
							field.set_editable(state)
							# remove empty field
							if str(field.content.value).strip().replace(",", "") == "":
								hbox.destroy()
								continue
							if save:
								new_vcard.add(field.content)
						elif type(field) == gtk.TextView:
							field.set_editable(state)
							textbuffer = field.get_buffer()
							start_iter = textbuffer.get_start_iter()
							end_iter = textbuffer.get_end_iter()
							text = textbuffer.get_text(start_iter, end_iter).strip()
							if save and len(text) > 0:
								new_vcard.add("note")
								new_vcard.note.value = escape(text)

		if save:
			try:
				iter = self.vcard.iter
				path = os.path.expanduser("~/Contacts")
				filename = os.path.join(path, unescape(self.vcard.fn.value) + ".vcf")

				if not filename == self.vcard.filename:
					os.remove(self.vcard.filename)

				new_file = open(filename, "w")
				new_file.write(new_vcard.serialize())
				new_file.close()

				self.vcard = new_vcard

				self.vcard.filename = filename
				self.vcard.iter = iter
				self.new_parent.contactData.set(self.vcard.iter, 0, unescape(self.vcard.fn.value), 1, self.vcard)
			except:
				raise

	def add_labels_by_name(self, box, workbox, name):
		if has_child(self.vcard, name):
			for child in self.vcard.contents[name]:
				if "WORK" in child.type_paramlist: self.add_label(workbox, child)
				else: self.add_label(box, child)

	def add_label(self, box, content):
		hbox = gtk.HBox(False, 4)

		# caption
		captionbox = gtk.VBox()
		caption = CaptionField(content)
		caption.removeButton.connect_object("clicked", gtk.Widget.destroy, hbox)
		captionbox.pack_start(caption, False)
		hbox.pack_start(captionbox, False)
		self.hsizegroup.add_widget(caption)

		if content.name == "ADR":
			field = AddressField(content)
		elif content.name == "NOTE":
			# multiline label
			textbuffer = gtk.TextBuffer()
			textbuffer.set_text(unescape(content.value))
			field = gtk.TextView(textbuffer)
			field.set_wrap_mode(gtk.WRAP_WORD)
			field.set_editable(False)
		else:
			# LabelEntry
			field = LabelField(content)
			field.set_editable(False)
			caption.field = field

		hbox.pack_start(field)
		box.add(hbox)
		return hbox
