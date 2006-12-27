import datetime
import gtk, gobject, pango
import contactentry

order = ['tel', 'email', 'web', 'bday', 'address', 'work_tel', 'work_email', 'work_web', 'work_address', 'note']

class ContactWindow(gtk.Window):

	def __init__(self, parent, entry):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		# main window
		self.set_resizable(True)
		self.set_default_size(-1,400)

		if entry.pixbuf != None:
			self.set_icon(entry.pixbuf)
		else:
			self.set_icon_name("stock_contact")

		self.clipboard = gtk.Clipboard()
		self.tooltips = gtk.Tooltips()

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
		color = parent.contactlist.style_get_property('even-row-color')
		scrolledwindow.get_child().modify_bg(gtk.STATE_NORMAL,color)

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
	def add_label(self, caption_text, text, url=False):
		def copy_to_clipboard(button, text):
			self.clipboard.set_text(text)

		rows = self.table.get_property('n-rows')
		caption = gtk.Label()
		caption.set_markup("<b>%s</b>" % (caption_text))
		caption.set_alignment(1,0)
		self.table.attach(caption, 0, 1, rows, rows+1, gtk.FILL, 0, 2)
		if url:
			labelbutton = gtk.LinkButton(text,text)
			self.tooltips.set_tip(labelbutton,"Click to open!")
		else:
			labelbutton = gtk.Button(text)
			#label.set_ellipsize(pango.ELLIPSIZE_END)
			self.tooltips.set_tip(labelbutton,"Click to copy!")
			labelbutton.connect('clicked',copy_to_clipboard,text)
		labelbutton.set_alignment(0,0)
		labelbutton.set_relief(gtk.RELIEF_NONE)
		self.table.attach(labelbutton, 1, 2, rows, rows+1, gtk.EXPAND|gtk.FILL, gtk.FILL)

		return labelbutton

	def add_separator(self):
		rows = self.table.get_property('n-rows')
		self.table.attach(gtk.HSeparator(), 0, 2, rows, rows+1, gtk.EXPAND|gtk.FILL, 0, 0, 2)

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
		self.table.attach(photo, 0, 1, 0, 1, gtk.FILL, 0, 2, 2)

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
		self.table.attach(big_title, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL, 4)

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
						if entry.email[i] != None: self.add_label("email", entry.email[i], True)
					self.add_separator()
			elif type == 'work_email':
				if len(entry.work_email) > 0:
					for i in range(len(entry.work_email)):
						if entry.work_email[i] != None: self.add_label("work email", entry.work_email[i], True)
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
						caption += "\n"
					if zip and city:
						text += "\n" + zip + " " + city
						caption += "\n"
					if city and state:
						text += " (" + state + ")"
					if country:
						text += "\n" + country
						caption += "\n"
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
					rows = self.table.get_property('n-rows')
					notecaption = gtk.Label()
					notecaption.set_markup("<b>Note:</b>")
					notecaption.set_alignment(0,0)
					self.table.attach(notecaption, 0, 1, rows, rows+1, gtk.FILL, 0, 2)
					noteentry = gtk.Entry()
					noteentry.set_text(entry.note_text)
					noteentry.set_has_frame(False)
					noteentry.set_editable(False)
					self.table.attach(noteentry, 1, 2, rows, rows+1, gtk.EXPAND|gtk.FILL, gtk.FILL, 4)
