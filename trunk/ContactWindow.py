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

import datetime
import gtk, gobject, pango
# local
from Functions import *
import ContactEntry

order = ['tel', 'email', 'web', 'im', 'bday', 'address', 'work_tel', 'work_email', 'work_web', 'work_address', 'note']

class ContactWindow(gtk.Window):

	def __init__(self, parent, entry, edit_mode = False):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		self.set_resizable(True)
		self.set_default_size(-1,400)

		if entry.pixbuf != None:
			self.set_icon(get_pixbuf_of_size(entry.pixbuf,128))

		self.tooltips = gtk.Tooltips()

		self.even_color = parent.contactList.style_get_property('even-row-color')
		self.odd_color = parent.contactList.style_get_property('odd-row-color')

		self.vbox = gtk.VBox(False, 6)
		self.vbox.set_border_width(6)
		self.add(self.vbox)

		# display
		scrolledwindow = gtk.ScrolledWindow()
		scrolledwindow.set_policy(gtk.POLICY_NEVER,gtk.POLICY_AUTOMATIC)
		self.vbox.pack_start(scrolledwindow)

		self.table = gtk.Table()
		self.table.set_border_width(6)
		scrolledwindow.add_with_viewport(self.table)
		scrolledwindow.get_child().modify_bg(gtk.STATE_NORMAL,self.even_color)

		# buttons
		self.buttonbox = gtk.HBox(False, 6)
		self.vbox.pack_end(self.buttonbox, False)

		addButton = gtk.Button('',gtk.STOCK_ADD)
		addButton.set_no_show_all(True)
		addButton.show()
		addButton.get_child().get_child().get_children()[1].hide()
		self.buttonbox.pack_start(addButton, False)

		self.buttonbox.pack_start(gtk.Label())

		editButton = gtk.ToggleButton(gtk.STOCK_EDIT)
		editButton.set_use_stock(True)
		editButton.set_no_show_all(True)
		editButton.show()
		editButton.get_child().get_child().get_children()[1].hide()
		editButton.connect("toggled", self.switch_mode, entry, addButton)
		self.buttonbox.pack_start(editButton, False)

		closeButton = gtk.Button('',gtk.STOCK_CLOSE)
		closeButton.connect_object("clicked", gtk.Widget.destroy, self)
		self.buttonbox.pack_start(closeButton, False)

		addButton.set_sensitive(edit_mode)
		editButton.set_active(edit_mode)

		# create widgets
		self.build_interface(entry, edit_mode)

	def build_interface(self, entry, edit_mode = False):
		# help-functions
		#---------------
		def add_label(caption_text, text, url = False, mail = False, multiline = False):
			def open_url(widget, event, text, mail = False):
				if not mail:
					browser_load(text, self)
				else:
					browser_load("mailto:" + text, self)

			rows = self.table.get_property('n-rows')

			# caption
			caption = gtk.Label()
			caption.set_markup("<b>%s</b>" % (caption_text + text.count('\n') * "\n"))
			caption.set_alignment(1,0.5)
			self.table.attach(caption, 0, 1, rows, rows+1, gtk.FILL, gtk.FILL, 6, 2)

			if multiline:
				# multiline label
				textbuffer = gtk.TextBuffer()
				textbuffer.set_text(text)
				textview = gtk.TextView(textbuffer)
				self.table.attach(textview, 1, 2, rows, rows+1, gtk.EXPAND|gtk.FILL, gtk.FILL, 0, 2)
				return caption, textview
			else:
				# label
				label = gtk.Entry()
				label.set_text(text)
				label.set_editable(edit_mode)
				label.set_has_frame(edit_mode)
				self.table.attach(label, 1, 2, rows, rows+1, gtk.EXPAND|gtk.FILL, gtk.FILL, 0, 2)
				# buttons
				if url or mail:
					if mail:
						urlbutton = ImageButton(gtk.image_new_from_icon_name("email", gtk.ICON_SIZE_MENU), self.even_color)
					else:
						urlbutton = ImageButton(gtk.image_new_from_icon_name("browser", gtk.ICON_SIZE_MENU), self.even_color)
					self.tooltips.set_tip(urlbutton,"Click to open")
					urlbutton.connect('button_press_event', open_url, text, mail)
					self.table.attach(urlbutton, 2, 3, rows, rows+1, gtk.EXPAND|gtk.FILL, gtk.FILL, 2)
				return caption, label

		def add_separator():
			rows = self.table.get_property('n-rows')
			seplabel = gtk.Label()
			seplabel.set_size_request(-1,5)
			self.table.attach(seplabel, 0, 3, rows, rows+1, gtk.EXPAND|gtk.FILL, 0)
		#---------------

		# contact photo
		photohbox = gtk.HBox(False,2)
		# contact photo (edit-mode)
		photovbox = gtk.VBox()
		photoremove = ImageButton(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU), self.even_color)
		if not edit_mode: photoremove.hide()
		self.tooltips.set_tip(photoremove,"Click to remove image")
		#photoremove.connect('button_press_event', copy_to_clipboard, text)
		photovbox.pack_start(photoremove, False)
		photohbox.pack_start(photovbox, False)

		viewport = gtk.Viewport()
		photohbox.pack_start(viewport,False)
		photo = gtk.Image()
		if entry.pixbuf:
			photo.set_from_pixbuf(get_pixbuf_of_size(entry.pixbuf,64, False))
			hasphoto = True
		else:
			photo.set_from_file('no-photo.png')
			hasphoto = False
		photo.set_padding(6, 6)
		photo.set_alignment(1, 0.5)
		photo.set_flags('can-focus')
		viewport.add(photo)

		self.table.attach(photohbox, 0, 1, 0, 1, gtk.FILL, 0, 6, 4)

		# big title
		text = "<span size=\"x-large\"><b>%s</b></span>" % (entry.fullname)

		if len(entry.nick) > 0:
			text += "\n<big>%s</big>" % (entry.nick)
		if len(entry.title) > 0:
			text += "\n" + entry.title
		if len(entry.org) > 0:
			text += " at " + entry.org

		big_title = gtk.Label()
		big_title.set_markup(text)
		big_title.set_alignment(0,0)
		big_title.set_selectable(True)
		#big_title.set_ellipsize(pango.ELLIPSIZE_END)
		self.table.attach(big_title, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL, 0, 6)

		add_separator()

		# add widgets in order
		for type in order:
			# tel numbers
			if type == 'tel':
				if len(entry.tel) > 0:
					for i in range(len(entry.tel)):
						caption = "home"
						if entry.tel[i][1]== 'FAX':
							caption += " fax"
						elif entry.tel[i][1]== 'CELL':
							caption = "mobile"
						add_label(caption, entry.tel[i][0])
					add_separator()
			elif type == 'work_tel':
				if len(entry.work_tel) > 0:
					for i in range(len(entry.work_tel)):
						caption = "work"
						if entry.work_tel[i][1]== 'FAX':
							caption += " fax"
						elif entry.work_tel[i][1]== 'CELL':
							caption += " mobile"
						add_label(caption, entry.work_tel[i][0])
					add_separator()
			# emails
			elif type == 'email':
				if len(entry.email) > 0:
					for i in range(len(entry.email)):
						add_label("email", entry.email[i], True, True)
					add_separator()
			elif type == 'work_email':
				if len(entry.work_email) > 0:
					for i in range(len(entry.work_email)):
						add_label("work email", entry.work_email[i], True, True)
					add_separator()
			# web
			elif type == 'web':
				if len(entry.url) > 0:
					add_label("web", entry.url, True)
				if len(entry.videoconference) > 0:
					add_label("video", entry.videoconference, True)
				if len(entry.url) > 0 or len(entry.videoconference) > 0:
					add_separator()
			elif type == 'work_web':
				if len(entry.work_url) > 0:
					add_label("work", entry.work_url, True)
				if len(entry.work_videoconference) > 0:
					add_label("work", entry.work_videoconference, True)
				if len(entry.work_url) > 0 or len(entry.work_videoconference) > 0:
					add_separator()
			# instant messaging
			elif type == 'im':
				if len(entry.im) > 0:
					for i in range(len(entry.im)):
						add_label("im", entry.im[i][0], True)
					add_separator()
			# address
			elif 'address' in type:
				caption = None
				if 'work' in type and len(entry.work_address) > 0:
					(pobox, extended, street, city, state, zip, country) = entry.work_address
					caption = "work"
				elif len(entry.address) > 0:
					(pobox, extended, street, city, state, zip, country) = entry.address
					caption = "home"
				if caption:
					text = ""
					if street:
						text += street
					if pobox:
						text += "\nPostbox " + pobox
					if zip and city:
						text += "\n" + zip + " " + city
					if city and state:
						text += " (" + state + ")"
					if country:
						text += "\n" + country
					add_label(caption, text, multiline = True)
					add_separator()
			# birthday
			elif type == 'bday':
				try:
					if entry.bday_year:
						date = datetime.date(entry.bday_year, entry.bday_month, entry.bday_day).strftime("%d.%m.%Y")
						add_label("birthday", date)
						add_separator()
				except: pass
			elif type == 'note':
				if len(entry.note_text) > 0:
					rows = self.table.get_property('n-rows')
					self.table.attach(gtk.HSeparator(), 0, 3, rows, rows+1, gtk.EXPAND|gtk.FILL, 0, 0, 2)
					notecaption, notetextview = add_label("Note:", entry.note_text, multiline = True)
					notecaption.set_alignment(0,0)
					notetextview.set_wrap_mode(gtk.WRAP_WORD)

		self.table.resize_children()
		self.table.show_all()

	#---------------
	# event funtions
	#---------------
	def switch_mode(self, button, entry, widget):
		state = button.get_active()
		widget.set_sensitive(state)
		for child in self.table.get_children():
			if child.__class__== gtk.Entry:
				child.set_editable(state)
				child.set_has_frame(state)
