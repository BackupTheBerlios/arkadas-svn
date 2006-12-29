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

import datetime, webbrowser
import gtk, gobject, pango
# local
import ContactEntry

order = ['tel', 'email', 'web', 'bday', 'address', 'work_tel', 'work_email', 'work_web', 'work_address', 'note']

class ContactWindow(gtk.Window):

	def __init__(self, parent, entry):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		# main window
		self.set_resizable(True)
		self.set_default_size(-1,400)

		if entry.pixbuf != None:
			self.set_icon(entry.pixbuf)

		self.clipboard = gtk.Clipboard()
		self.tooltips = gtk.Tooltips()

		self.even_color = parent.contactlist.style_get_property('even-row-color')
		self.odd_color = parent.contactlist.style_get_property('odd-row-color')
		self.hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND1)

		vbox1 = gtk.VBox(False, 6)
		vbox1.set_border_width(6)
		self.add(vbox1)

		scrolledwindow = gtk.ScrolledWindow()
		scrolledwindow.set_policy(gtk.POLICY_NEVER,gtk.POLICY_AUTOMATIC)
		vbox1.pack_start(scrolledwindow)

		self.table = gtk.Table()
		self.table.set_border_width(6)
		scrolledwindow.add_with_viewport(self.table)
		#scrolledwindow.get_child().set_shadow_type(gtk.SHADOW_NONE)
		scrolledwindow.get_child().modify_bg(gtk.STATE_NORMAL,self.even_color)

		hbox1 = gtk.HBox(False, 6)
		vbox1.pack_end(hbox1, False)

		noticelabel = gtk.Label()
		#noticelabel.set_text("Click on items to copy or open!")
		noticelabel.set_alignment(0,0.5)
		hbox1.pack_start(noticelabel)

		editbutton = gtk.Button('',gtk.STOCK_EDIT)
		editbutton.get_child().get_child().get_children()[1].set_text('')
		hbox1.pack_start(editbutton,False)

		closebutton = gtk.Button('',gtk.STOCK_CLOSE)
		hbox1.pack_end(closebutton,False)

		self.make_widgets(entry)

		# events
		closebutton.connect_object("clicked", gtk.Widget.destroy, self)

	#--------------
	# help funtions
	#--------------
	def add_label(self, caption_text, text, url=False, mail=False):
		def copy_to_clipboard(widget, event, text):
			self.clipboard.set_text(text)
		def open_url(widget, event, text, mail=False):
			if not mail:
				webbrowser.open_new(text)
			else:
				webbrowser.open_new("mailto:" + text)
		def hover_image(widget, event):
			self.window.set_cursor(self.hand_cursor)
		def unhover_image(widget, event):
			self.window.set_cursor(None)

		rows = self.table.get_property('n-rows')
		# caption
		caption = gtk.Label()
		caption.set_markup("<b>%s</b>" % (caption_text))
		caption.set_alignment(1,0)
		self.table.attach(caption, 0, 1, rows, rows+1, gtk.FILL, gtk.FILL, 6, 2)
		hbox = gtk.HBox(False, 2)
		# label
		label = gtk.Label(text)
		label.set_alignment(0,0)
		label.set_selectable(True)
		hbox.pack_start(label)
		# buttons
		eventbox1 = gtk.EventBox()
		eventbox1.modify_bg(gtk.STATE_NORMAL,self.even_color)
		copyimage = gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU)
		eventbox1.add(copyimage)
		eventbox1.connect('button_press_event', copy_to_clipboard, text)
		eventbox1.connect('enter-notify-event', hover_image)
		eventbox1.connect('leave-notify-event', unhover_image)
		hbox.pack_end(eventbox1, False)
		if url or mail:
			eventbox2 = gtk.EventBox()
			eventbox2.modify_bg(gtk.STATE_NORMAL,self.even_color)
			if mail:
				urlimage = gtk.image_new_from_icon_name("email", gtk.ICON_SIZE_MENU)
			else:
				urlimage = gtk.image_new_from_icon_name("browser", gtk.ICON_SIZE_MENU)
			eventbox2.add(urlimage)
			eventbox2.connect('button_press_event', open_url, text, mail)
			eventbox2.connect('enter-notify-event', hover_image)
			eventbox2.connect('leave-notify-event', unhover_image)
			hbox.pack_start(eventbox2, False)
		self.table.attach(hbox, 1, 2, rows, rows+1, gtk.EXPAND|gtk.FILL, gtk.FILL, 0, 2)
		return caption, label

	def add_separator(self):
		rows = self.table.get_property('n-rows')
		self.table.attach(gtk.HSeparator(), 0, 3, rows, rows+1, gtk.EXPAND|gtk.FILL, 0, 0, 2)

	#--------------
	# create the widgets
	#--------------
	def make_widgets(self, entry):
		# contact photo
		photo = gtk.Image()
		if entry.pixbuf != None:
			photo.set_from_pixbuf(entry.pixbuf)
		photo.set_alignment(1,0.5)
		photo.set_flags('can-focus')
		self.table.attach(photo, 0, 1, 0, 1, gtk.FILL, 0, 6, 4)

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
		self.table.attach(big_title, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL)

		self.add_separator()

		# add widgets in order
		for type in order:
			# tel numbers
			if type == 'tel':
				if len(entry.tel) > 0:
					for i in range(len(entry.tel)):
						if entry.tel[i] != None: self.add_label("home", entry.tel[i])
					self.add_separator()
			elif type == 'work_tel':
				if len(entry.work_tel) > 0:
					for i in range(len(entry.work_tel)):
						if entry.work_tel[i] != None: self.add_label("work", entry.work_tel[i])
					self.add_separator()
			# emails
			elif type == 'email':
				if len(entry.email) > 0:
					for i in range(len(entry.email)):
						if entry.email[i] != None: self.add_label("email", entry.email[i], True, True)
					self.add_separator()
			elif type == 'work_email':
				if len(entry.work_email) > 0:
					for i in range(len(entry.work_email)):
						if entry.work_email[i] != None: self.add_label("work email", entry.work_email[i], True, True)
					self.add_separator()
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
					self.add_label(caption, text)
					self.add_separator()
			# web
			elif type == 'web':
				if len(entry.url) > 0:
					self.add_label("web", entry.url, True)
				if len(entry.videoconference) > 0:
					self.add_label("video", entry.videoconference, True)
				if len(entry.url) > 0 or len(entry.videoconference) > 0:
					self.add_separator()
			elif type == 'work_web':
				if len(entry.work_url) > 0:
					self.add_label("work", entry.work_url, True)
				if len(entry.work_videoconference) > 0:
					self.add_label("work", entry.work_videoconference, True)
				if len(entry.work_url) > 0 or len(entry.work_videoconference) > 0:
					self.add_separator()
			# birthday
			elif type == 'bday':
				try:
					if entry.bday_year:
						date = datetime.date(entry.bday_year, entry.bday_month, entry.bday_day).strftime("%d.%m.%Y")
						self.add_label("birthday", date)
						self.add_separator()
				except: pass
			elif type == 'note':
				if len(entry.note_text) > 0:
					notecaption, notelabel = self.add_label("Note:", entry.note_text)
					notecaption.set_alignment(0,0)
					notelabel.set_line_wrap(True)
