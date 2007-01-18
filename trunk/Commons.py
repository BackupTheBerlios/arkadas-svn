import gtk

types = {
	"HOME":"Home", "WORK":"Work",
	"BDAY":"Birthday", "URL":"Website",
	"EMAIL":"Email", "IM":"Username",
	"NOTE":"Notes:",
	# address types
	"BOX":"Postbox", "EXTENDED":"Extended",
	"STREET":"Street", "CITY":"City",
	"REGION":"State", "CODE":"ZIP", "COUNTRY":"Country",
	# tel types
	"VOICE":"Landline", "ISDN":"ISDN",
	"CELL":"Mobile", "FAX":"Fax",
	"CAR":"Car", "VIDEO":"Video",
	"PAGER":"Pager", "MODEM":"Modem",
	"BBS":"BBS", "PCS":"PCS",
	# im types
	"X-AIM":"AIM", "X-GADU-GADU":"Gadu-Gadu",
	"X-GROUPWISE":"GroupWise", "X-ICQ":"ICQ",
	"X-IRC":"IRC", "X-JABBER":"Jabber",
	"X-MSN":"MSN", "X-NAPSTER":"Napster",
	"X-YAHOO":"Yahoo", "X-ZEPHYR":"Zephyr",
	}

tel_types = ("VOICE", "ISDN", "CELL", "FAX", "PAGER", "CAR", "VIDEO", "MODEM", "BBS", "PCS")
im_types = ("X-AIM", "X-GADU-GADU", "X-GROUPWISE", "X-ICQ", "X-IRC", "X-JABBER", "X-MSN", "X-NAPSTER", "X-YAHOO", "X-ZEPHYR")
#--------
# widgets
#--------
class CaptionField(gtk.HBox):
	def __init__(self, content):
		gtk.HBox.__init__(self, False, 2)
		self.set_no_show_all(True)

		self.field = None
		self.content = content

		# create type menus
		self.menu = gtk.Menu()
		if self.content.name == "TEL":
			for tel in tel_types:
				menuitem = gtk.MenuItem(types["HOME"] + " " + types[tel])
				menuitem.connect("activate", self.menuitem_click)
				self.menu.append(menuitem)
			for tel in tel_types:
				menuitem = gtk.MenuItem(types["WORK"] + " " +types[tel])
				menuitem.connect("activate", self.menuitem_click)
				self.menu.append(menuitem)
		elif self.content.name.startswith("X-"):
			for text in types.keys():
				if text.startswith("X-"):
					menuitem = gtk.MenuItem(types[text])
					menuitem.connect("activate", self.menuitem_click)
					self.menu.append(menuitem)
		else:
			menuitem = gtk.MenuItem(types["HOME"])
			menuitem.connect("activate", self.menuitem_click)
			self.menu.append(menuitem)
			menuitem = gtk.MenuItem(types["WORK"])
			menuitem.connect("activate", self.menuitem_click)
			self.menu.append(menuitem)
		self.menu.show_all()

		# create label and remove button
		color = gtk.gdk.color_parse("white")

		self.button = gtk.Button()
		self.button.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
		self.button.set_relief(gtk.RELIEF_NONE)
		if not self.content.name == "NOTE": self.pack_start(self.button, False)
		self.labelbox = gtk.EventBox()
		self.labelbox.modify_bg(gtk.STATE_NORMAL, color)
		self.label = gtk.Label()
		self.label.set_alignment(1,0.5)
		self.labelbox.add(self.label)
		self.labelbox.show_all()
		self.pack_start(self.labelbox)

		# create right arrow (only for visual)
		self.arrowbox = gtk.EventBox()
		self.arrowbox.modify_bg(gtk.STATE_NORMAL, color)
		self.arrowbox.connect("button-press-event", self.popup)
		arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)
		arrow.show()
		self.arrowbox.add(arrow)

		if not self.content.name in ("NOTE", "BDAY", "URL"):
			self.pack_start(self.arrowbox, False)
			self.labelbox.connect("button-press-event", self.popup)
			self.arrowbox.connect("button-press-event", self.popup)

		self.parse_paramlist()
		self.set_editable(False)
		self.show()

	def popup(self, *args):
		if self.label.get_property("sensitive"):
			self.menu.popup(None, None, None, 1, 0)

	def set_editable(self, editable):
		self.button.set_property("visible",editable)
		self.arrowbox.set_property("visible",editable)
		self.label.set_sensitive(editable)

	def menuitem_click(self, item):
		paramlist = self.content.type_paramlist
		name = self.content.name
		itemtext = item.get_child().get_text()
		newtype = []

		if itemtext.startswith(types["WORK"]): newtype.append("WORK")
		else: newtype.append("HOME")

		# if phone or im, check types for text
		if name == "TEL" or name.startswith("X-"):
			for key, value in types.iteritems():
				if value == itemtext.replace(types["HOME"], "").replace(types["WORK"], "").strip():
					# if im, change name
					if name.startswith("X-"):
						self.content.name = key
					else:
						newtype.append(key)
					break

		# preserve the other params
		for param in ("INTERNET", "X400", "DOM", "INTL", "POSTAL", "PARCEL", "PREF"):
			if param in paramlist: newtype.append(param)

		self.content.type_paramlist = newtype
		if self.field is not None:
			self.field.content.type_paramlist = newtype
			if self.field.get_text() == self.field.empty_text: self.field.set_text("")
			self.field.set_empty_text()
			self.field.entry.grab_focus()
		self.parse_paramlist()

	def parse_paramlist(self):
		try: paramlist = self.content.type_paramlist
		except: paramlist = []
		name = self.content.name
		text = types["HOME"]

		if "WORK" in paramlist: text = types["WORK"]

		if name.startswith("X-"): text = types[name]
		elif name == "URL": text = types["URL"]
		elif name == "BDAY": text = types["BDAY"]
		elif name == "NOTE": text = types["NOTE"]
		else:
			for tel in tel_types:
				if tel in paramlist:
					if tel == "FAX": text += " " + types["FAX"]
					elif tel == "CELL":
						if "WORK" in paramlist: text += " " + types["CELL"]
						else: text = types["CELL"]

		self.label.set_markup("<b>%s</b>" % (text))

class LabelField(gtk.HBox):
	def __init__(self, content, use_content=True):
		gtk.HBox.__init__(self, False)
		self.set_no_show_all(True)

		self.content = content
		self.use_content = use_content
		self.autosize = False

		sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

		self.labelbox = gtk.HBox(False, 2)
		self.pack_start(self.labelbox)
		self.label = gtk.Label()
		self.label.set_selectable(True)
		self.label.set_alignment(0,0.5)
		self.label.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		self.labelbox.pack_start(self.label)
		sizegroup.add_widget(self.labelbox)

		self.entry = gtk.Entry()
		#self.entry.set_has_frame(False)
		self.entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		self.pack_start(self.entry)
		sizegroup.add_widget(self.entry)

		self.show()
		self.label.show()
		self.entry.hide()

		if use_content:
			if self.content.name in ("EMAIL", "URL"):
				if self.content.name  == "EMAIL":
					self.urlbutton = ImageButton(gtk.image_new_from_icon_name("email", gtk.ICON_SIZE_MENU), gtk.gdk.color_parse("white"))
					self.urlbutton.connect("button_press_event", lambda w,e: browser_load("mailto:" + self.content.value, self.get_toplevel()))
				else:
					self.urlbutton = ImageButton(gtk.image_new_from_icon_name("browser", gtk.ICON_SIZE_MENU), gtk.gdk.color_parse("white"))
					self.urlbutton.connect("button_press_event", lambda w,e: browser_load(self.content.value, self.get_toplevel()))
				self.labelbox.pack_end(self.urlbutton, False)
				self.urlbutton.show()

			self.set_text(self.content.value)
			self.set_empty_text()
		else:
			self.set_text(self.content[0])
			self.empty_text = self.content[1]

		self.entry.connect("changed", self.entry_changed)
		self.entry.connect("focus-in-event", self.focus_changed, True)
		self.entry.connect("focus-out-event", self.focus_changed, False)

	def set_empty_text(self):
		if self.content.name.startswith("X-"): type = "IM"
		elif self.content.name == "TEL":
			for param in self.content.type_paramlist:
				if param in tel_types:
					type = param
					break
		else: type = self.content.name.upper()
		self.empty_text = types.get(type, "Empty")

	def set_text(self, text):
		self.label.set_markup("<span foreground=\"black\">%s</span>" % text)
		self.entry.set_text(text)

	def get_text(self):
		text = self.entry.get_text()
		self.set_text(text)
		if self.autosize: self.entry.set_width_chars(len(text))
		return text

	def set_editable(self, editable):
		self.labelbox.set_property("visible", not editable)
		self.entry.set_property("visible", editable)
		self.focus_changed(None, None, not editable)

	def set_autosize(self, autosize):
		self.autosize = autosize
		text = self.get_text().strip()
		if self.autosize: self.entry.set_width_chars(len(text))
		else: self.entry.set_width_chars(-1)

	def entry_changed(self, widget):
		text = self.get_text().strip()
		if self.autosize: self.entry.set_width_chars(len(text))
		if text == self.empty_text: text = ""

		if self.use_content: self.content.value = text
		else: self.content[0] = text

	def focus_changed(self, widget, event, focus):
		text = self.get_text().strip()
		if focus:
			if text == self.empty_text:
				self.set_text("")
				self.entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		else:
			if text == "":
				self.set_text(self.empty_text)
				self.entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("darkgray"))

class AddressField(gtk.Table):
	def __init__(self, content):
		gtk.Table.__init__(self)

		self.set_no_show_all(True)

		self.content = content

		self.build_interface()

		self.set_editable(False)
		self.show()

	def build_interface(self):
		self.box = LabelField([self.content.value.box, types["BOX"]], False)
		self.extended = LabelField([self.content.value.extended, types["EXTENDED"]], False)
		self.street = LabelField([self.content.value.street, types["STREET"]], False)
		self.city = LabelField([self.content.value.city, types["CITY"]], False)
		self.region = LabelField([self.content.value.region, types["REGION"]], False)
		self.code = LabelField([self.content.value.code, types["CODE"]], False)
		self.country = LabelField([self.content.value.country, types["COUNTRY"]], False)

		self.city.set_autosize(True)
		self.region.set_autosize(True)
		self.code.set_autosize(True)


		self.attach(self.street, 0, 3, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.box, 0, 3, 1, 2, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.country, 0, 3, 3, 4, gtk.EXPAND|gtk.FILL, gtk.FILL)

		# american
		self.attach(self.city, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
		self.attach(self.region, 1, 2, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.attach(self.code, 2, 3, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)

		# german, french
		#self.attach(self.code, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
		#self.attach(self.city, 1, 2, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)
		#self.attach(self.region, 2, 3, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)

	def set_editable(self, editable = False):
		for widget in self.get_children():
			if type(widget) == LabelField:
				widget.set_editable(editable)
				if editable:
					widget.show()
				else:
					if widget.get_text().strip() == "":
						widget.hide()
					else:
						widget.show()


		if not editable:
			self.content.value.box = self.box.content[0]
			self.content.value.extended = self.extended.content[0]
			self.content.value.street = self.street.content[0]
			self.content.value.city = self.city.content[0]
			self.content.value.region = self.region.content[0]
			self.content.value.code = self.code.content[0]
			self.content.value.country = self.country.content[0]


class EventVBox(gtk.VBox):
	def __init__(self):
		gtk.VBox.__init__(self)

		self.connect("add", self.add_event)
		self.connect("remove", self.remove_event)

	def add_event(self, container, widget):
		self.show_all()

	def remove_event(self, container, widget):
		if len(self.get_children()) == 0: self.hide_all()

class ImageButton(gtk.EventBox):
	def __init__(self, image, color = None, from_pixbuf=False):
		def hover_image(widget, event):
			self.get_toplevel().window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
		def unhover_image(widget, event):
			self.get_toplevel().window.set_cursor(None)

		gtk.EventBox.__init__(self)
		if color:
			self.modify_bg(gtk.STATE_NORMAL,color)
		if from_pixbuf:
			self.Image = gtk.Image()
			self.Image.set_from_pixbuf(image)
		else:
			self.Image = image
		self.add(self.Image)
		self.connect("enter-notify-event", hover_image)
		self.connect("leave-notify-event", unhover_image)
		self.Image.show()
		self.show()
		self.set_no_show_all(True)
		del image

#----------
# functions
#----------
def escape(s):
	s = s.replace(',', '\,')
	s = s.replace(';', '\;')
	s = s.replace('\n', '\\n')
	s = s.replace('\r', '\\r')
	s = s.replace('\t', '\\t')
	return s

def unescape(s):
	s = s.replace('\,', ',')
	s = s.replace('\;', ';')
	s = s.replace('\\n', '\n')
	s = s.replace('\\r', '\r')
	s = s.replace('\\t', '\t')
	return s

def entities(s):
	s = s.replace('<', '&lt;')
	s = s.replace('>', '&gt;')
	s = s.replace('&', '&amp;')
	s = s.replace('"', '&quot;')
	return s

def bday_from_value(value):
	try:
		(y, m, d) = value.split("-", 2)
		d = d.split('T')
		if y.isdigit() and m.isdigit() and d[0].isdigit():
			year = int(y); month = int(m); day = int(d[0])
			if month >=1 and month <=12:
				if day >= 1 and day <=31:
					return (year, month, day)
	except:
		pass
	return (None, None, None)

def has_child(vcard, childName, childNumber = 0):
	return len(str(vcard.getChildValue(childName, "", childNumber))) > 0

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
						error_dialog = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, "Unable to launch a suitable browser.")
						error_dialog.run()
						error_dialog.destroy()
