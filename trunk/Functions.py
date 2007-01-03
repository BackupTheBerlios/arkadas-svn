import gtk, subprocess

class EntryLabel(gtk.Entry):
	def __init__(self, text):
		gtk.Entry.__init__(self)

		self.type = None
		self.set_text(text)

		self.connect("focus-in-event", self.focus_changed, True)
		self.connect("focus-out-event", self.focus_changed, False)

	def set_text(self, text):
		gtk.Entry.set_text(self, text)

	def get_text(self):
		return gtk.Entry.get_text(self)

	def set_type(self, caption_type, type):
		self.type = type
		self.caption_type = caption_type

	def get_type(self):
		return self.type

	def set_editable(self, editable):
		gtk.Entry.set_editable(self, editable)
		gtk.Entry.set_has_frame(self, editable)
		if editable: self.focus_changed(None, None, False)
		else: self.focus_changed(None, None, True)

	def focus_changed(self, widget, event, focus):
		text = self.get_text().strip()
		if focus:
			if text.startswith('(') and self.type is not None:
				self.set_text('')
		else:
			if text == '' and self.type is not None:
				self.set_text("(%s)" % self.caption_type)

class AddressField(gtk.Table):
	def __init__(self, address):
		gtk.Table.__init__(self, 4, 2)

		self.set_no_show_all(True)

		self.address_name = ("Postbox", "Extended", "Street", "City", "State", "Zip", "Country")
		self.address = address
		self.widgetlist = 7 * [None]

		self.build_interface()

		self.set_editable(False)
		self.show()

	def build_interface(self):
		for i in range(len(self.address)):
			widget = EntryLabel(self.address[i])
			widget.set_editable(False)
			widget.set_type(self.address_name[i],'adr')
			if i == 5: widget.set_width_chars(len(widget.get_text()))
			widget.connect("changed", self.changed)
			self.widgetlist[i] = widget

		self.attach(self.widgetlist[2], 0, 2, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.widgetlist[0], 0, 2, 1, 2, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.widgetlist[5], 0, 1, 2, 3, gtk.FILL, gtk.FILL)
		self.attach(self.widgetlist[3], 1, 2, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.widgetlist[6], 0, 2, 3, 4, gtk.EXPAND|gtk.FILL, gtk.FILL)

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
