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

import datetime, base64, urllib
import gtk, gobject, pango
# local
from Commons import *
import ContactEntry

order = ["TEL", "EMAIL", "URL", "IM", "BDAY", "ADR", "WORK_TEL", "WORK_EMAIL", "WORK_ADR"]

class ContactWindow(gtk.VBox):

	def __init__(self, parent):
		gtk.VBox.__init__(self, False, 6)

		self.tooltips = parent.tooltips

		self.table = None
		self.color = gtk.gdk.color_parse("white")

		# display
		self.scrolledwindow = gtk.ScrolledWindow()
		self.scrolledwindow.set_policy(gtk.POLICY_NEVER,gtk.POLICY_AUTOMATIC)
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
		self.buttonbox.pack_start(self.addButton, False)

		self.buttonbox.pack_start(gtk.Label())

		self.saveButton = gtk.Button("", gtk.STOCK_SAVE)
		self.saveButton.set_no_show_all(True)
		self.buttonbox.pack_start(self.saveButton, False)

		self.editButton = gtk.Button("", gtk.STOCK_EDIT)
		self.editButton.set_no_show_all(True)
		self.buttonbox.pack_start(self.editButton, False)

	def build_interface(self, vcard, edit=False):
		# help-functions
		#---------------
		def add_labels_by_name(box, workbox, name):
			if has_child(vcard, name):
				for child in vcard.contents[name]:
					if "WORK" in child.type_paramlist: add_label(workbox, child)
					else: add_label(box, child)

		def add_label(box, content):
			def remove_item(button):
					hbox.destroy()

			hbox = gtk.HBox(False, 4)

			# caption
			captionbox = gtk.VBox()
			caption = CaptionField(content)
			caption.button.connect("clicked", remove_item)
			captionbox.pack_start(caption, False)
			hbox.pack_start(captionbox, False)
			self.hsizegroup.add_widget(caption)

			if content.name == "ADR":
				field = AddressField(content)
			elif content.name == "NOTE":
				# multiline label
				textbuffer = gtk.TextBuffer()
				textbuffer.set_text(content.value)
				tag_table = textbuffer.get_tag_table()
				tag = gtk.TextTag()
				tag.set_property("foreground", "black")
				tag_table.add(tag)
				textbuffer.apply_tag(tag, textbuffer.get_start_iter(), textbuffer.get_end_iter())
				field = gtk.TextView(textbuffer)
				field.set_wrap_mode(gtk.WRAP_WORD)
				field.set_editable(False)
			else:
				# LabelEntry
				field = LabelField(content)
				field.set_editable(False)

			hbox.pack_start(field)
			box.add(hbox)

		#---------------
		self.addButton.set_sensitive(edit)
		self.addButton.connect("clicked", self.addButton_click, vcard)
		self.saveButton.set_property("visible", edit)
		self.saveButton.connect("clicked", self.saveButton_click, vcard)
		self.editButton.set_property("visible", not edit)
		self.editButton.connect("clicked", self.editButton_click, vcard)

		if self.table is not None: self.table.destroy()
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
		if has_child(vcard, "photo"):
			date = None
			if "VALUE" in vcard.photo.params:
				try:
					url = urllib.urlopen(vcard.photo.value)
					data = url.read()
					url.close()
				except:
					pass
			elif "ENCODING" in vcard.photo.params:
				data = vcard.photo.value
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

		hbox = gtk.HBox()
		self.hsizegroup.add_widget(hbox)
		self.photohbox.pack_start(hbox,False)
		self.photo = ImageButton(pixbuf, self.color, True)
		#self.photo.connect("button_press_event", remove_photo)
		self.tooltips.set_tip(self.photo,"Click to change image")
		hbox.pack_end(self.photo, False)

		titlevbox = gtk.VBox()
		self.photohbox.pack_start(titlevbox, True, True, 2)

		# FIELD - fullname & nickname
		fullname = gtk.Label()
		text = "<span size=\"x-large\"><b>%s</b></span>" % vcard.fn.value
		if has_child(vcard, "nickname"):
			text += " (<big>%s</big>)" % (vcard.nickname.value)
		fullname.set_markup(text)
		fullname.set_alignment(0,0)
		fullname.set_selectable(True)
		titlevbox.pack_start(fullname)

		# FIELD - title & org
		text = ""
		org = gtk.Label()
		if has_child(vcard, "title"):
			text += vcard.title.value
		if has_child(vcard, "org"):
			text += "\n" + vcard.org.value
		org.set_text(text)
		org.set_alignment(0,0)
		org.set_selectable(True)
		titlevbox.pack_start(org)

		self.photohbox.show_all()

		# FIELD - tel
		add_labels_by_name(self.telbox, self.worktelbox, "tel")
		# FIELD - emails
		add_labels_by_name(self.emailbox, self.workemailbox, "email")
		# FIELD - web
		if has_child(vcard, "url"):
			for child in vcard.contents["url"]:
				add_label(self.urlbox, child)
		# FIELD - instant messaging
		for im in im_types:
			if has_child(vcard, im.lower()):
				for child in vcard.contents[im.lower()]:
					add_label(self.imbox, child)
		# FIELD - address
		#add_labels_by_name(self.adrbox, "adr")
		#add_labels_by_name(self.workadrbox, "adr", True)
		# FIELD - birthday
		if has_child(vcard, "bday"):
			for child in vcard.contents["bday"]:
				add_label(self.bdaybox, child)

		# FIELD - note
		self.notebox.add(gtk.HSeparator())
		self.notebox.set_spacing(4)
		if not has_child(vcard, "note"): vcard.add("note")
		add_label(self.notebox, vcard.note)

		self.table.set_no_show_all(True)
		self.table.show()

	#---------------
	# event funtions
	#---------------
	def addButton_click(self, button, vcard):
		pass

	def saveButton_click(self, button, vcard):
		self.switch_mode(vcard, False)

	def editButton_click(self, button, vcard):
		self.switch_mode(vcard, True)

	def switch_mode(self, vcard, state=False):
		self.addButton.set_sensitive(state)
		self.saveButton.set_property("visible", state)
		self.editButton.set_property("visible", not state)

		for child in self.table.get_children():
			if type(child) == EventVBox:
				for hbox in child.get_children():
					if type(hbox) == gtk.HBox:
						# get caption & field
						caption, field = hbox.get_children()[0].get_children()[0], hbox.get_children()[1]
						caption.set_editable(state)
						# remove empty field
						if type(field) == LabelField:
							field.set_editable(state)
							if field.get_text() == "": hbox.destroy() ; continue
						elif type(field) == gtk.TextView:
							field.set_editable(state)


	def namedialog(self, button, event, vcard):
		pass
