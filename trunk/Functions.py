import gtk, subprocess

class ImageButton(gtk.EventBox):
	def __init__(self, image, color = None):
		def hover_image(widget, event):
			self.get_root_window().set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
		def unhover_image(widget, event):
			self.get_root_window().set_cursor(None)

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
