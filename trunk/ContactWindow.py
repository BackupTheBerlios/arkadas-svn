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
from Commons import *
import ContactEntry

order = ['TEL', 'EMAIL', 'WEB', 'IM', 'BDAY', 'ADR', 'WORK_TEL', 'WORK_EMAIL', 'WORK_WEB', 'WORK_ADR']

class ContactWindow(gtk.Window):

	def __init__(self, parent, entry, edit_mode = False):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		if len(entry.fullname) > 0:
			self.set_title(entry.fullname)
		else:
			self.set_title('Contact')

		self.set_resizable(True)
		self.set_default_size(-1,400)

		if entry.pixbuf != None:
			self.set_icon(get_pixbuf_of_size(entry.pixbuf,128))

		self.tooltips = gtk.Tooltips()

		self.widgets = []

		self.color = gtk.gdk.color_parse('white')

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
		scrolledwindow.get_child().modify_bg(gtk.STATE_NORMAL,self.color)
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

		# create widgets
		self.build_interface(entry)

		addButton.set_sensitive(edit_mode)
		editButton.set_active(edit_mode)

	def build_interface(self, entry):
		# help-functions
		#---------------
		def add_label(caption_text, text, type):
			def remove_item(button, event):
				self.widgets.remove([caption, field, urlbutton, type])
				caption.destroy()
				field.destroy()
				if urlbutton is not None: urlbutton.destroy()
				self.get_toplevel().window.set_cursor(None)

			rows = self.table.get_property('n-rows')
			urlbutton = None

			# caption
			caption = ComboLabel(caption_text, type)
			caption.button.connect('button_press_event', remove_item)
			self.table.attach(caption, 0, 1, rows, rows+1, gtk.FILL, gtk.FILL, 4)

			if 'ADR' in type:
				# address
				field = AddressField(text)
			elif type == 'NOTE':
				# multiline label
				textbuffer = gtk.TextBuffer()
				textbuffer.set_text(text)
				field = gtk.TextView(textbuffer)
				field.set_wrap_mode(gtk.WRAP_WORD)
			else:
				# entrylabel
				field = EntryLabel(text, type)
				field.set_editable(False)
				# buttons
				if 'EMAIL' in type or 'WEB' in type:
					if 'EMAIL' in type:
						urlbutton = ImageButton(gtk.image_new_from_icon_name("email", gtk.ICON_SIZE_MENU), self.color)
						urlbutton.connect('button_press_event', lambda w,e: browser_load("mailto:" + text,self))
					elif 'WEB' in type:
						urlbutton = ImageButton(gtk.image_new_from_icon_name("browser", gtk.ICON_SIZE_MENU), self.color)
						urlbutton.connect('button_press_event', lambda w,e: browser_load(text,self))
					self.tooltips.set_tip(urlbutton,"Click to open")
					self.table.attach(urlbutton, 2, 3, rows, rows+1, gtk.FILL, gtk.FILL, 2)

			self.table.attach(field, 1, 2, rows, rows+1, gtk.EXPAND|gtk.FILL, gtk.FILL)
			self.widgets.append([caption, field, urlbutton, type])

		def add_separator():
			rows = self.table.get_property('n-rows')
			seplabel = gtk.Label()
			seplabel.set_size_request(-1,4)
			self.table.attach(seplabel, 0, 3, rows, rows+1, gtk.EXPAND|gtk.FILL, 0)
		#---------------

		# contact photo
		photohbox = gtk.HBox(False,2)
		# contact photo (edit-mode)
		photovbox = gtk.VBox()
		photoremove = ImageButton(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU), self.color)
		photoremove.hide()
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
			if type == 'TEL':
				if len(entry.tel) > 0:
					for i in range(len(entry.tel)):
						caption = "home"
						if entry.tel[i][1]== 'FAX':
							caption += " fax"
						elif entry.tel[i][1]== 'CELL':
							caption = "mobile"
						add_label(caption, entry.tel[i][0], entry.tel[i][1])
					add_separator()
			elif type == 'WORK_TEL':
				if len(entry.work_tel) > 0:
					for i in range(len(entry.work_tel)):
						caption = "work"
						if entry.work_tel[i][1]== 'FAX':
							caption += " fax"
						elif entry.work_tel[i][1]== 'CELL':
							caption += " mobile"
						add_label(caption, entry.work_tel[i][0], "WORK_" + entry.tel[i][1])
					add_separator()
			# emails
			elif type == 'EMAIL':
				if len(entry.email) > 0:
					for i in range(len(entry.email)):
						add_label("home", entry.email[i], type)
					add_separator()
			elif type == 'WORK_EMAIL':
				if len(entry.work_email) > 0:
					for i in range(len(entry.work_email)):
						add_label("work", entry.work_email[i], type)
					add_separator()
			# web
			elif type == 'WEB':
				if len(entry.url) > 0:
					add_label("home page", entry.url, type)
					add_separator()
			elif type == 'WORK_WEB':
				if len(entry.work_url) > 0:
					add_label("work page", entry.work_url, type)
					add_separator()
			# instant messaging
			elif type == 'IM':
				if len(entry.im) > 0:
					for i in range(len(entry.im)):
						add_label("home", entry.im[i][0], entry.im[i][1])
					add_separator()
			# address
			elif 'ADR' in type:
				if 'WORK' in type and len(entry.work_address) > 0:
					add_label("work", entry.work_address, type)
					add_separator()
				elif len(entry.address) > 0:
					add_label("home", entry.address, type)
					add_separator()
			# birthday
			elif type == 'BDAY':
				try:
					if entry.bday_year:
						date = datetime.date(entry.bday_year, entry.bday_month, entry.bday_day).strftime("%d.%m.%Y")
						add_label("birthday", date, type)
						add_separator()
				except: pass

		if len(entry.note_text) > 0:
			rows = self.table.get_property('n-rows')
			self.table.attach(gtk.HSeparator(), 0, 3, rows, rows+1, gtk.EXPAND|gtk.FILL, 0, 0, 2)
			add_label("Note:", entry.note_text, 'NOTE')

		self.table.resize_children()
		self.table.show_all()

	#---------------
	# event funtions
	#---------------
	def switch_mode(self, button, entry, widget):
		state = button.get_active()
		widget.set_sensitive(state)
		empty = []
		for caption, field, urlbutton, etype in self.widgets:
			caption.set_editable(state)
			if type(field) == EntryLabel:
				field.set_editable(state)
				# remove if empty
				if field.get_text() == '': empty.append([caption, field, urlbutton, etype]) ; continue
			elif type(field) == AddressField:
				field.set_editable(state)
				if field.address == len(field.address) * ['']: empty.append([caption, field, urlbutton, etype]) ; continue
			elif type(field) == gtk.TextView:
				field.set_editable(state)
		# remove empty fields
		for caption, field, urlbutton, etype in empty:
			self.widgets.remove([caption, field, urlbutton, etype])
			caption.destroy()
			field.destroy()
			if urlbutton is not None: urlbutton.destroy()
