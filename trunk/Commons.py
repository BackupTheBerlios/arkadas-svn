import gtk

types = {}
types = {
	'BDAY':'Birthday',
	'WEB':'Homepage',
	'EMAIL':'Email',
	'IM':'Username',
	# address types
	'ADR-0':'Postbox', 'ADR-1':'Extended',
	'ADR-2':'Street', 'ADR-3':'City',
	'ADR-4':'State', 'ADR-5':'Zip', 'ADR-6':'Country',
	# tel types
	'VOICE':'Landline', 'ISDN':'ISDN',
	'CELL':'Mobile', 'CAR':'Car',
	'VIDEO':'Video', 'PAGER':'Pager',
	'FAX':'Fax', 'MODEM':'Modem',
	'BBS':'BBS', 'PCS':'PCS',
	# im types
	'X-AIM':'AIM', 'X-GADU-GADU':'Gadu-Gadu',
	'X-GROUPWISE':'GroupWise', 'X-ICQ':'ICQ',
	'X-IRC':'IRC', 'X-JABBER':'Jabber',
	'X-MSN':'MSN', 'X-NAPSTER':'Napster',
	'X-YAHOO':'Yahoo', 'X-ZEPHYR':'Zephyr',
	}

#--------
# widgets
#--------
class ComboLabel(gtk.HBox):
	def __init__(self, text, type):
		gtk.HBox.__init__(self, False, 2)

		self.set_no_show_all(True)

		if 'X-' in type: text = types[type]


		color = gtk.gdk.color_parse('white')
		self.button = ImageButton(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU), color)
		if not type == 'NOTE': self.pack_start(self.button, False)
		self.labelbox = gtk.EventBox()
		self.labelbox.modify_bg(gtk.STATE_NORMAL, color)
		self.label = gtk.Label()
		self.label.set_markup("<b>%s</b>" % (text))
		self.label.set_alignment(1,0.5)
		if type == 'NOTE': self.label.set_alignment(0,0.5)
		self.labelbox.add(self.label)
		self.labelbox.show_all()
		self.pack_start(self.labelbox)

		self.arrowbox = gtk.EventBox()
		self.arrowbox.modify_bg(gtk.STATE_NORMAL, color)
		self.arrowbox.connect("button-press-event", lambda w,e: self.popup())
		arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)
		arrow.show()
		self.arrowbox.add(arrow)

		self.menu = gtk.Menu()
		# create type menus
		if 'X-' in type:
			for text in types.keys():
				if 'X-' in text:
					item = gtk.MenuItem(types[text])
					item.connect("activate", lambda m: self.set_text(m.get_child().get_text()))
					self.menu.append(item)
		self.menu.show_all()

		if not type == 'NOTE' and not type == 'BDAY':
			self.pack_start(self.arrowbox, False)
			self.labelbox.connect("button-press-event", lambda w,e: self.popup())
			self.arrowbox.connect("button-press-event", lambda w,e: self.popup())

		self.set_editable(False)
		self.show()

	def popup(self):
		if self.label.get_property('sensitive'):
			self.menu.popup(None, None, None, 1, 0)

	def set_editable(self, editable):
		self.button.set_property('visible',editable)
		self.arrowbox.set_property('visible',editable)
		self.label.set_sensitive(editable)

	def set_text(self, text):
		self.label.set_markup("<b>%s</b>" % (text))

class EntryLabel(gtk.Entry):
	def __init__(self, text, empty_text=''):
		gtk.Entry.__init__(self)

		if 'X-' in empty_text: empty_text = 'IM'
		self.empty_text = types.get(empty_text, empty_text)

		self.set_text(text)
		self.set_has_frame(False)
		self.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))

		self.connect("focus-in-event", self.focus_changed, True)
		self.connect("focus-out-event", self.focus_changed, False)

	def set_text(self, text):
		gtk.Entry.set_text(self, text)

	def get_text(self):
		return gtk.Entry.get_text(self)

	def set_editable(self, editable):
		gtk.Entry.set_editable(self, editable)
		self.focus_changed(None, None, not editable)

	def focus_changed(self, widget, event, focus):
		if not self.empty_text == '':
			text = self.get_text().strip()
			if focus:
				if text == self.empty_text:
					self.set_text('')
					self.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
			else:
				if text == '':
					self.set_text(self.empty_text)
					self.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('darkgray'))

class AddressField(gtk.Table):
	def __init__(self, address):
		gtk.Table.__init__(self, 4, 2)

		self.set_no_show_all(True)

		self.address = address
		self.widgetlist = 7 * [None]

		self.build_interface()

		self.set_editable(False)
		self.show()

	def build_interface(self):
		for i in range(len(self.address)):
			widget = EntryLabel(self.address[i], types['ADR-' + str(i)])
			widget.set_editable(False)
			if i == 3: widget.set_width_chars(len(widget.get_text()))
			if i == 4: widget.set_width_chars(len(widget.get_text()))
			if i == 5: widget.set_width_chars(len(widget.get_text()))
			widget.connect("changed", self.changed)
			self.widgetlist[i] = widget

		self.attach(self.widgetlist[2], 0, 3, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.widgetlist[0], 0, 3, 1, 2, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.widgetlist[5], 0, 1, 2, 3, gtk.FILL, gtk.FILL)
		self.attach(self.widgetlist[3], 1, 2, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.widgetlist[4], 2, 3, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.widgetlist[6], 0, 3, 3, 4, gtk.EXPAND|gtk.FILL, gtk.FILL)

	def set_editable(self, editable = False):
		for widget in self.widgetlist:
			num = self.widgetlist.index(widget)
			widget.set_editable(editable)
			if editable:
				widget.show()
				if num == 0: widget.set_text(self.address[num])
			else:
				if self.address[num] == '':
					widget.hide()
				else:
					widget.show()
					if num == 0: widget.set_text("Postbox " + self.address[num])

	def changed(self, widget):
		num = self.widgetlist.index(widget)
		text = widget.get_text()
		if num == 0: text = text.replace("Postbox ", "")
		if num == 3: widget.set_width_chars(len(text))
		if num == 4: widget.set_width_chars(len(text))
		if num == 5: widget.set_width_chars(len(text))
		self.address[num] = text.strip()

class ImageButton(gtk.EventBox):
	def __init__(self, image, color = None):
		def hover_image(widget, event):
			self.get_toplevel().window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
		def unhover_image(widget, event):
			self.get_toplevel().window.set_cursor(None)

		gtk.EventBox.__init__(self)
		if color:
			self.modify_bg(gtk.STATE_NORMAL,color)
		self.Image = image
		self.add(self.Image)
		self.connect('enter-notify-event', hover_image)
		self.connect('leave-notify-event', unhover_image)
		self.Image.show()
		self.show()
		self.set_no_show_all(True)
		del image

#----------
# functions
#----------
def get_name_by_type(type):
	if type == 'TEL':
		pass

def get_pixbuf_of_size(pixbuf, size, crop = False):
	image_width = pixbuf.get_width()
	image_height = pixbuf.get_height()
	image_xdiff = 0
	image_ydiff = 0
	if crop:
		if image_width-size > image_height-size:
			image_xdiff = int((image_width-image_height)/2)
			image_width = image_height
		else:
			image_ydiff = int((image_height-image_width)/2)
			image_height = image_width
		new_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, image_width, image_height)
		new_pixbuf.fill(0x00000000)
		pixbuf.copy_area(image_xdiff, image_ydiff, image_width, image_height, new_pixbuf, 0, 0)
		crop_pixbuf = new_pixbuf.scale_simple(size, size, gtk.gdk.INTERP_HYPER)
	else:
		if image_width-size > image_height-size:
			image_height = int(size/float(image_width)*image_height)
			image_width = size
		else:
			image_width = int(size/float(image_height)*image_width)
			image_height = size
		crop_pixbuf = pixbuf.scale_simple(image_width, image_height, gtk.gdk.INTERP_HYPER)
	return crop_pixbuf

def get_pixbuf_of_size_from_file(filename, size):
	try:
		pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
		pixbuf = get_pixbuf_of_size(pixbuf, size)
	except:
		pass
	return pixbuf

def browser_load(docslink, parent = None):
	import subprocess
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
						error_dialog = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, 'Unable to launch a suitable browser.')
						error_dialog.run()
						error_dialog.destroy()
