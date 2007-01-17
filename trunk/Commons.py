import gtk

types = {
	"HOME":"home", "HOME_CAP":"Home",
	"WORK":"work", "WORK_CAP":"Work",
	"BDAY":"Birthday", "BDAY_CAP":"birthday", 
	"WEB":"Homepage", "WEB_CAP":"page",
	"EMAIL":"Email", "IM":"Username",
	"NOTE":"Note",
	# address types
	"ADR-0":"Postbox", "ADR-1":"Extended",
	"ADR-2":"Street", "ADR-3":"City",
	"ADR-4":"State", "ADR-5":"Zip", "ADR-6":"Country",
	# tel types
	"VOICE":"Landline", "ISDN":"ISDN",
	"CELL":"Mobile", "CELL_CAP":"mobiles",
	"FAX":"Fax", "FAX_CAP":"fax",
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
	
tel_types = ("VOICE", "ISDN", "CELL", "CAR", "VIDEO", "PAGER", "FAX", "MODEM", "BBS", "PCS")
#--------
# widgets
#--------
class ComboLabel(gtk.HBox):
	def __init__(self, type):
		gtk.HBox.__init__(self, False, 2)

		self.set_no_show_all(True)
		
		menuitems = []
		
		text, menutype = self.text_by_type(type)
		
		self.menu = gtk.Menu()
		# create type menus
		if menutype == "":
			menuitems = [types["HOME_CAP"], types["WORK_CAP"]]
		elif menutype == "TEL":
			menuitems = [types["HOME_CAP"], types["WORK_CAP"]]
			submenu = gtk.Menu()
			submenu2 = gtk.Menu()
			for tel in tel_types:
				menuitem = gtk.MenuItem(types[tel])
				menuitem2 = gtk.MenuItem(types[tel])
				menuitem.connect("activate", self.menuitem_click, type, False)
				menuitem2.connect("activate", self.menuitem_click, type, False, True)
				submenu.append(menuitem)
				submenu2.append(menuitem2)	
		elif menutype == "X-":
			for text in types.keys():
				if "X-" in text:
					menuitems.append(types[text])
					
		for itemtext in menuitems:
			menuitem = gtk.MenuItem(itemtext)
			if menutype == "TEL" and itemtext == types["HOME_CAP"]: menuitem.set_submenu(submenu)
			elif menutype == "TEL": menuitem.set_submenu(submenu2)
			if not menutype == "TEL": menuitem.connect("activate", self.menuitem_click, type, True)
			self.menu.append(menuitem)	
				
		self.menu.show_all()
		
		color = gtk.gdk.color_parse("white")
		self.button = gtk.Button() #ImageButton(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU), color)
		self.button.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
		self.pack_start(self.button, False)
		self.labelbox = gtk.EventBox()
		self.labelbox.modify_bg(gtk.STATE_NORMAL, color)
		self.label = gtk.Label()
		self.label.set_markup("<b>%s</b>" % (text))
		self.label.set_alignment(1,0.5)
		self.labelbox.add(self.label)
		self.labelbox.show_all()
		self.pack_start(self.labelbox)

		self.arrowbox = gtk.EventBox()
		self.arrowbox.modify_bg(gtk.STATE_NORMAL, color)
		self.arrowbox.connect("button-press-event", self.popup)
		arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)
		arrow.show()
		self.arrowbox.add(arrow)

		if not type == "NOTE" and not type == "BDAY":
			self.pack_start(self.arrowbox, False)
			self.labelbox.connect("button-press-event", self.popup)
			self.arrowbox.connect("button-press-event", self.popup)

		self.set_editable(False)
		self.show()

	def popup(self, *args):
		if self.label.get_property("sensitive"):
			self.menu.popup(None, None, None, 1, 0)

	def set_editable(self, editable):
		self.button.set_property("visible",editable)
		self.arrowbox.set_property("visible",editable)
		self.label.set_sensitive(editable)

	def set_text(self, text):
		self.label.set_markup("<b>%s</b>" % (text))
	
	def get_text(self):
		return self.label.get_text()
		
	def get_type(self):
		return self.etype

	def menuitem_click(self, item, type, main=False, work=False):
		itemtext = item.get_child().get_text()
		if main and itemtext == types["WORK_CAP"]:
			type = "WORK_" + type
		elif not main:
			for key, value in types.iteritems():
				if value == itemtext:
					type = key
					break
			if work: type = "WORK_" + type
		text, menutype = self.text_by_type(type)
		self.set_text(text)
		
	def text_by_type(self, type):
		self.etype = type
		menutype = ""
		text = types["HOME"]
		if "WORK" in type: text = types["WORK"]
		if "WEB" in type: text += " " + types["WEB_CAP"]
		elif "X-" in type: text = types[type] ; menutype = "IM"
		elif type == "BDAY": text = types["BDAY_CAP"]
		elif type == "NOTE": text = types["NOTE"] + ":"
		else:
			for tel in tel_types:
				if tel in type: 
					menutype = "TEL"
					if tel == "FAX": text += " " + types["FAX_CAP"]
					elif tel == "CELL": text = types["CELL_CAP"]
					elif type == "WORK_CELL": text += " " + types["CELL_CAP"]
		return text, menutype
		
class LabelEntry(gtk.HBox):
	def __init__(self, text, type, empty_text="Empty"):
		gtk.HBox.__init__(self, False)

		self.set_no_show_all(True)

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
		self.entry.set_has_frame(False)
		self.entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		self.pack_start(self.entry, False)
		sizegroup.add_widget(self.entry)

		self.entry.connect("focus-in-event", self.focus_changed, True)
		self.entry.connect("focus-out-event", self.focus_changed, False)

		if "EMAIL" in type or "WEB" in type:
			if "EMAIL" in type:
				self.urlbutton = ImageButton(gtk.image_new_from_icon_name("email", gtk.ICON_SIZE_MENU), gtk.gdk.color_parse("white"))
				self.urlbutton.connect("button_press_event", lambda w,e: browser_load("mailto:" + text, self.get_toplevel()))
			elif "WEB" in type:
				self.urlbutton = ImageButton(gtk.image_new_from_icon_name("browser", gtk.ICON_SIZE_MENU), gtk.gdk.color_parse("white"))
				self.urlbutton.connect("button_press_event", lambda w,e: browser_load(text, self.get_toplevel()))
			self.labelbox.pack_end(self.urlbutton, False)
			self.urlbutton.show()

		self.show()
		self.label.show()
		self.entry.hide()

		self.set_text(text)

		type = type.replace("WORK_", "")
		if "X-" in type: empty_text = "IM"
		self.empty_text = types.get(type, empty_text)

	def set_text(self, text):
		self.label.set_markup("<span foreground=\"black\">%s</span>" % text)
		self.entry.set_text(text)

	def get_text(self):
		text = self.entry.get_text()
		self.set_text(text)
		return text
	
	def set_editable(self, editable):
		self.labelbox.set_property("visible", not editable)
		self.entry.set_property("visible", editable)
		self.focus_changed(None, None, not editable)

	def focus_changed(self, widget, event, focus):
		if not self.empty_text == "":
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
	def __init__(self, address, type):
		gtk.Table.__init__(self, 4, 2)

		self.set_no_show_all(True)

		self.etype = type
		self.address = address
		self.widgetlist = 7 * [None]

		self.build_interface()

		self.set_editable(False)
		self.show()

	def build_interface(self):
		for i in range(len(self.address)):
			widget = LabelEntry(self.address[i], "", types["ADR-" + str(i)])
			widget.set_editable(False)
			if i == 3 or i == 4 or i == 5: widget.entry.set_width_chars(len(widget.get_text()))
			widget.entry.connect("changed", self.changed, widget)
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
				if self.address[num] == "":
					widget.hide()
				else:
					widget.show()
					if num == 0: widget.set_text("Postbox " + self.address[num])

	def changed(self, widget, parent):
		num = self.widgetlist.index(parent)
		text = parent.get_text()
		if num == 0: text = text.replace("Postbox ", "")
		if num == 3 or num == 4 or num == 5: widget.set_width_chars(len(text))
		self.address[num] = text.strip()

	def set_type(self, type):
		self.etype = type
	
	def get_type(self):
		return self.etype

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
def get_name_by_type(type):
	if type == "TEL":
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
						error_dialog = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, "Unable to launch a suitable browser.")
						error_dialog.run()
						error_dialog.destroy()
