# -*- coding: utf-8 -*-

import sys, os, gc, socket, threading, datetime, ConfigParser

import gtk, gtk.glade, gobject, pango

# Test pygtk version
if gtk.pygtk_version < (2, 8, 0):
	sys.stderr.write("requires PyGTK 2.8.0 or newer.\n")
	sys.exit(1)

import ContactEngine
from Widgets import *
from Commons import *

__author__ = "Paul Johnson"
__email__ = "thrillerator@googlemail.com"
__version__ = "1.7"
__license__ = """Copyright 2007 Paul Johnson <thrillerator@googlemail.com>

Arkadas is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Arkadas is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Arkadas; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

gtk.gdk.threads_init()
socket.setdefaulttimeout(30)

#--------------------
# Class MainWindow
#--------------------
class MainWindow:
	fullscreen = False
	edit = False
	is_new = False
	contact = None

	def __init__(self):
		self.engine = ContactEngine.ContactDB()

		gtk.window_set_default_icon_name("address-book")
		gtk.glade.textdomain("arkadas")
		self.tree = gtk.glade.XML(find_path("arkadas.glade"))

		signals = {}
		for attr in dir(self.__class__):
			signals[attr] = getattr(self, attr)
		self.tree.signal_autoconnect(signals)

		self.tooltips = gtk.Tooltips()
		self.clipboard = gtk.Clipboard()
		self.load_fallbackprefs()
		self.load_prefs()
		self.load_widgets()
		self.build_list()
		self.build_table()
		self.build_prefs()

		self.window.set_app_paintable(True)
		self.window.show_all()

		def load_db():
			self.engine.load(os.path.join(self.data_dir, "contacts.db"))
			self.clear()
			self.load_groups()

		gobject.idle_add(load_db)

	def load_fallbackprefs(self):
		# set config dir
		path = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
		self.config_dir = os.path.join(path, "arkadas")
		if not os.path.exists(self.config_dir): os.mkdir(self.config_dir)
		# set data dir
		path = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
		self.data_dir = os.path.join(path, "arkadas")
		if not os.path.exists(self.data_dir): os.mkdir(self.data_dir)
		# set photo dir
		self.photo_dir = os.path.join(self.data_dir, "images")
		if not os.path.exists(self.photo_dir): os.mkdir(self.photo_dir)

		self.display_format = 0
		self.address_format = 0
		self.sort_format = 0

		self.fullscreen_editing = False
		self.show_separator = True
		self.photo_manip = "center"

		self.display_order = ["tel", "email", "url", "im", "bday", "adr"]
		self.template = ["tel", "email", "url"]

	def load_prefs(self):
		try:
			conf = ConfigParser.ConfigParser()
			conf.read(os.path.join(self.config_dir, "arkadasrc"))

			if conf.has_option("format", "display"):
				self.display_format = conf.getint("format", "display")
			if conf.has_option("format", "sort"):
				self.sort_format = conf.getint("format", "sort")
			if conf.has_option("format", "address"):
				self.address_format = conf.getint("format", "address")

			if conf.has_option("display", "fs_editing"):
				self.fullscreen_editing = conf.getboolean("display", "fs_editing")
			if conf.has_option("display", "show_separator"):
				self.show_separator = conf.getboolean("display", "show_separator")
			if conf.has_option("display", "photo_manip"):
				self.photo_manip = conf.get("display", "photo_manip")

			if conf.has_option("display", "template"):
				self.template = conf.get("display", "template").split(",")
			if conf.has_option("display", "order"):
				self.display_order = conf.get("display", "order").split(",")
		except:
			print "Error while reading settings."

	def save_prefs(self):
		conf = ConfigParser.ConfigParser()

		#conf.add_section("general")

		conf.add_section("format")
		conf.set("format", "display", self.display_format)
		conf.set("format", "sort", self.sort_format)
		conf.set("format", "address", self.address_format)

		conf.add_section("display")
		conf.set("display", "fs_editing", self.fullscreen_editing)
		conf.set("display", "show_separator", self.show_separator)
		conf.set("display", "photo_manip", self.photo_manip)
		conf.set("display", "template", ",".join(self.template))
		conf.set("display", "order", ",".join(self.display_order))

		conf.write(file(os.path.join(self.config_dir, "arkadasrc"), "w"))

	def load_widgets(self):
		self.window = self.tree.get_widget("mainWindow")
		self.groupList = self.tree.get_widget("groupList")
		self.contactList = self.tree.get_widget("contactList")
		self.table = self.tree.get_widget("table")

		self.addCombo = self.tree.get_widget("addCombo")
		self.prevButton = self.tree.get_widget("prevButton")
		self.nextButton = self.tree.get_widget("nextButton")
		self.undoButton = self.tree.get_widget("undoButton")
		self.saveButton = self.tree.get_widget("saveButton")
		self.editButton = self.tree.get_widget("editButton")
		self.namechangeButton = self.tree.get_widget("namechangeButton")

		self.photoBox = self.tree.get_widget("photoBox")
		self.photoImage = self.tree.get_widget("photoImage")

		if not HAVE_VOBJECT:
			self.tree.get_widget("importItem").set_sensitive(False)
			self.tree.get_widget("exportItem").set_sensitive(False)
			self.tree.get_widget("exportItem2").set_sensitive(False)

	def build_list(self):
		dnd = [("STRING", gtk.TARGET_SAME_APP, 0)]

		model = gtk.ListStore(int, str, str)
		#model.set_sort_column_id(1, gtk.SORT_ASCENDING)

		self.groupList.set_model(model)
		self.groupSelection = self.groupList.get_selection()

		# contactlist cellrenderers
		#cellimg = gtk.CellRendererPixbuf()
		#cellimg.set_property("icon-name", "stock_folder")
		celltxt = gtk.CellRendererText()
		celltxt.set_property("ellipsize", pango.ELLIPSIZE_END)
		column = gtk.TreeViewColumn(_("Group"))
		column.set_alignment(0.5)
		#column.pack_start(cellimg, False)
		column.pack_start(celltxt)
		column.add_attribute(celltxt,"text", 1)
		self.groupList.append_column(column)

		self.groupList.set_row_separator_func(lambda m,i: m[i][1]=="")

		self.groupList.enable_model_drag_dest(dnd, gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)

		# events
		self.groupList.connect("row-activated", lambda t,p,v: self.groupaddButton_clicked(edit=True))
		self.groupSelection.connect("changed", self.groupSelection_changed)

		self.contactSelection = self.contactList.get_selection()
		self.contactSelection.set_mode(gtk.SELECTION_MULTIPLE)

		self.contactData = gtk.ListStore(object, str, str)
		self.contactData.set_sort_column_id(2, gtk.SORT_ASCENDING)
		self.contactList.set_model(self.contactData)
		
		def search_func(model, column, key, iter):
			return not (key.lower() in model[iter][1].lower())
		
		self.contactList.set_search_equal_func(search_func)

		# contactlist cellrenderers
		cellimg = gtk.CellRendererPixbuf()
		cellimg.set_property("icon-name", "stock_contact")
		celltxt = gtk.CellRendererText()
		celltxt.set_property("ellipsize", pango.ELLIPSIZE_END)
		column = gtk.TreeViewColumn(_("Name"))
		column.set_alignment(0.5)
		column.pack_start(cellimg, False)
		column.pack_start(celltxt)
		column.add_attribute(celltxt,"text", 1)
		self.contactList.append_column(column)

		self.contactList.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, dnd, gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)

		# events
		self.contactData.connect("row-deleted", self.contactData_changed, None)
		self.contactData.connect("row-inserted", self.contactData_changed)
		self.contactSelection.connect("changed", self.contactSelection_changed)

		self.contactList.grab_focus()

	def build_table(self):
		viewport = self.tree.get_widget("viewport")
		viewport.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

		# create type combo
		model = gtk.ListStore(str, str)

		for name in ("tel", "email", "adr", "url", "im", "bday"):
			model.append([types[name], name])
		self.addCombo.set_model(model)
		cell = gtk.CellRendererText()
		self.addCombo.pack_start(cell)
		self.addCombo.add_attribute(cell, "text", 0)
		self.addCombo.prepend_text(_("Add Field"))
		self.addCombo.set_active(0)

		self.hsizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

		menu = gtk.Menu()
		item = gtk.ImageMenuItem(gtk.STOCK_OPEN)
		item.connect("activate", self.imageopenButton_clicked)
		menu.append(item)
		item = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
		item.connect("activate", self.imageremoveButton_clicked)
		menu.append(item)
		menu.attach_to_widget(self.photoBox, None)
		menu.show_all()

		def photoBox_callbacks(widget, event, type):
			if self.edit:
				if type=="popup":
					menu.popup(None,None,None,event.button,event.time)
				elif type=="enter":
					self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
				elif type=="leave":
					self.window.window.set_cursor(None)

		self.photoBox.connect("button-press-event", photoBox_callbacks, "popup")
		self.photoBox.connect("enter-notify-event", photoBox_callbacks, "enter")
		self.photoBox.connect("leave-notify-event", photoBox_callbacks, "leave")

		#self.photoBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

		# fieldholder

		for name in ("tel", "email", "url", "im", "adr", "bday", "note"):
			setattr(self, name+"box", EventVBox(name, self.hsizegroup, self.show_separator))

		self.adrbox.vbox.set_spacing(4)

		# add fieldholder by order
		for type in self.display_order:
			box = getattr(self, type+"box")
			self.table.pack_start(box, False)

		self.table.pack_start(self.notebox, False)

		# add note field
		scrolledwindow = gtk.ScrolledWindow()
		scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)

		textbuffer = gtk.TextBuffer()
		textview = gtk.TextView(textbuffer)
		textview.set_wrap_mode(gtk.WRAP_WORD)
		textview.set_editable(False)
		textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
		textview.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		textview.set_left_margin(2)
		textview.set_right_margin(2)
		scrolledwindow.add(textview)
		self.notebox.add_field(scrolledwindow)

		self.notebox.hide()
		
		self.modifiedLabel = gtk.Label()
		self.modifiedLabel.set_alignment(1, 1)
		self.modifiedLabel.show()
		self.table.pack_end(self.modifiedLabel)

	def build_prefs(self):
		self.tree.get_widget("formatCombo").set_active(self.display_format)
		self.tree.get_widget("sortCombo").set_active(self.sort_format)
		self.tree.get_widget("addressCombo").set_active(self.address_format)

		self.tree.get_widget("editingCheck").set_active(self.fullscreen_editing)
		self.tree.get_widget("editingCheck").set_active(self.show_separator)

		if self.photo_manip in ("crop", "center"):
			self.tree.get_widget(self.photo_manip+"Radio").set_active(True)
		else:
			self.tree.get_widget("noneRadio").set_active(True)

		model = gtk.ListStore(str, str)
		for item in self.template:
			model.append([types[item], item])

		self.tree.get_widget("templateList").set_model(model)
		column = gtk.TreeViewColumn(None, gtk.CellRendererText(), text=0)
		self.tree.get_widget("templateList").append_column(column)

		self.addfieldMenu = gtk.Menu()
		for name in ("tel", "email", "adr", "url", "im", "bday"):
			item = gtk.MenuItem(types[name])
			item.connect("activate", self.addfieldMenu_clicked, name)
			self.addfieldMenu.append(item)
		self.addfieldMenu.attach_to_widget(self.tree.get_widget("addfieldButton"), None)
		self.addfieldMenu.show_all()

		model = gtk.ListStore(str, str)
		for item in self.display_order:
			model.append([types[item], item])

		self.tree.get_widget("orderList").set_model(model)

		column = gtk.TreeViewColumn(None, gtk.CellRendererText(), text=0)
		self.tree.get_widget("orderList").append_column(column)

	#---------------
	# main funtions
	#---------------
	def load_groups(self):
		model = self.groupList.get_model()
		model.clear()

		model.append([-1, _("All contacts"), ""])
		model.append([0, _("Uncategorized"), ""])
		model.append([0, "", ""])

		for row in self.engine.getGroups():
			model.append(row)

		self.groupSelection.select_path((0,))

	def add_to_list(self, contact, groupadd=False):
		fullname = format_fn(display_formats[self.display_format], **contact.names.__dict__)
		sort_string = format_fn(sort_formats[self.sort_format], **contact.names.__dict__)
		iter = self.contactData.append([contact, fullname, sort_string])

		if groupadd and self.groupSelection.count_selected_rows() > 0:
			(model, g_iter) = self.groupSelection.get_selected()
			id = model[g_iter][0]
			if id > 0:
				self.engine.addToGroup(id, contact.id)

		return iter

	def check_if_changed(self):
		if self.edit and self.contact:
			fullname = format_fn(display_formats[self.display_format], **self.contact.names.__dict__)
			text = "<big><b>%s</b></big>" % _("Save the changes to contact before closing?")
			sec_text = _("If you don't save, changes you made to <b>%s</b> will be permanently lost.") % fullname

			msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE)
			msgbox.set_title("Arkadas")
			msgbox.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)
			msgbox.set_markup(text)
			msgbox.format_secondary_markup(sec_text)

			if msgbox.run() == gtk.RESPONSE_OK:
				self.editButton_clicked(edit=False)
				self.saveButton_clicked()
			elif self.is_new:
				self.engine.removeContact(self.contact)
			msgbox.destroy()

	def parse_contact(self):
		if not self.contact: return

		self.saveButton.set_sensitive(True)
		self.editButton.set_sensitive(True)

		# FIELD - fullname & nickname
		text = "<span size=\"x-large\"><b>%s</b></span>" % format_fn(display_formats[1], **self.contact.names.__dict__)
		if self.contact.hasValue("nickname"):
			text += " (<big>%s</big>)" % self.contact.nickname
		self.tree.get_widget("fullnameLabel").set_markup(text)

		# FIELD - title & org
		if self.contact.hasValue("title"):
			self.tree.get_widget("titleLabel").set_text(self.contact.title)
		if self.contact.hasValue("org"):
			self.tree.get_widget("orgLabel").set_text(self.contact.org)

		for name in ("tel", "email", "url", "im", "adr"):
			contentlist = getattr(self.contact, name+"_list")
			for content in contentlist:
				self.add_label(name, content)

		for field in self.adrbox.vbox:
			field.label.format = address_formats[self.address_format]

		if self.contact.hasValue("bday"):
			self.add_label("bday", self.contact.bday)

		textbuffer = self.notebox.vbox.get_children()[0].get_child().get_buffer()
		if self.contact.hasValue("note"):
			textbuffer.set_text(self.contact.note)
			self.notebox.show()
		else:
			textbuffer.set_text("")
			self.notebox.hide()

		self.table.show()

		# FIELD - photo
		if self.contact.hasValue("photo"):
			try:
				pixbuf = gtk.gdk.pixbuf_new_from_file(self.contact.photo)
				if self.photo_manip == "crop":
					pixbuf = get_crop_pixbuf(pixbuf)
					pixbuf = get_pixbuf_of_size(pixbuf, 64)
				elif self.photo_manip == "center":
					pixbuf = get_pixbuf_of_size(pixbuf, 64)
					pixbuf = get_pad_pixbuf(pixbuf, 64, 64)
				else:
					pixbuf = get_pixbuf_of_size(pixbuf, 64)

				self.has_photo = True
			except:
				pixbuf = get_pixbuf_of_size_from_file(find_path("no-photo.png"), 64)
				self.has_photo = False
		else:
			pixbuf = get_pixbuf_of_size_from_file(find_path("no-photo.png"), 64)
			self.has_photo = False

		self.photoImage.show()
		self.photoImage.set_from_pixbuf(pixbuf)
		
		
		markup = "<small>%s</small>"
		date = datetime.datetime.strptime(self.contact.modified, "%Y-%m-%dT%H:%M:%S")
		text = _("Modified on %s - %s") % (date.strftime("%x"), date.strftime("%X"))
		self.modifiedLabel.set_markup(markup % text)

	def clear(self):
		self.engine.conn.rollback()
		self.contact = None
		self.photoImage.clear()
		self.tree.get_widget("fullnameLabel").set_text("")
		self.tree.get_widget("titleLabel").set_text("")
		self.tree.get_widget("orgLabel").set_text("")
		for name in ("tel", "email", "url", "im", "adr", "bday"):
			for field in getattr(self, name+"box").vbox:
				field.destroy()
		self.table.hide()
		self.addCombo.hide()
		self.saveButton.set_sensitive(False)
		self.editButton.set_sensitive(False)
		gc.collect()

	def add_label(self, name, content):
		def removeButton_clicked(button, field, name, content):
			if name == "bday":
				self.contact.bday = ""
			else:
				self.contact.remove(content)
			field.destroy()

		field = Field(name, content)
		field.removeButton.connect("clicked", removeButton_clicked, field, name, content)

		getattr(self, name+"box").add_field(field)

		return field

	#---------------
	# event funtions
	#---------------
	def delete_event(self, widget, event=None):
		self.check_if_changed()
		self.clear()
		self.save_prefs()
		#sys.exit()
		gtk.main_quit()
		return False

	def newButton_clicked(self, widget):
		self.check_if_changed()
		self.contactSelection.unselect_all()
		self.clear()
		self.is_new = True

		self.contact = self.engine.addContact()

		for name in self.template:
			if name=="bday":
				if self.contact.hasValue("bday"): return
				self.contact.bday = "1950-01-01"
			else:
				self.contact.add(name).value = ""

		self.parse_contact()
		self.editButton_clicked()
		self.namechangeButton_clicked(None)

	def importButton_clicked(self, widget):
		dialog = gtk.FileChooserDialog(title=_("Import Contacts"),action=gtk.FILE_CHOOSER_ACTION_OPEN,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		dialog.set_select_multiple(True)

		filter = gtk.FileFilter()
		filter.set_name(_("vCard Files"))
		filter.add_mime_type("application/vcard")
		filter.add_mime_type("text/x-vcard")
		dialog.add_filter(filter)
		filter = gtk.FileFilter()
		filter.set_name(_("All Files"))
		filter.add_pattern("*")
		dialog.add_filter(filter)

		if dialog.run() == gtk.RESPONSE_OK:
			last = None
			for filename in dialog.get_filenames():
				contacts = import_vcard(filename, self.engine, self.photo_dir)
				if contacts:
					for contact in contacts:
						last = self.add_to_list(contact, True)
				else:
					error(_("There was an error while importing contacts."), self.window)
					dialog.destroy()
					return

			msg(_("Successfully imported contacts."), self.window)

			if last:
				self.contactSelection.unselect_all()
				self.contactSelection.select_iter(last)

		dialog.destroy()

	def exportButton_clicked(self, widget):
		dialog = gtk.FileChooserDialog(title=_("Export Contacts"),
										action=gtk.FILE_CHOOSER_ACTION_SAVE,
										buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))

		dialog.set_default_response(gtk.RESPONSE_OK)

		filter = gtk.FileFilter()
		filter.set_name(_("vCard Files"))
		filter.add_mime_type("application/vcard")
		filter.add_mime_type("text/x-vcard")
		dialog.add_filter(filter)
		filter = gtk.FileFilter()
		filter.set_name(_("All Files"))
		filter.add_pattern("*")
		dialog.add_filter(filter)

		check = gtk.CheckButton(_("Append to file"))
		check.set_active(True)
		dialog.set_extra_widget(check)

		if dialog.run() == gtk.RESPONSE_OK:
			filename = dialog.get_filename()
			if filename:
				if not check.get_active() and os.path.exists(filename): os.remove(filename)
				(model, paths) = self.contactSelection.get_selected_rows()

				for path in paths:
					#FIXME: use id or contact as param
					if not export_vcard(filename, self.engine.getContact(model[path][0])):
						error(_("There was an error while exporting contacts."), self.window)
						dialog.destroy()
						return

				msg(_("Successfully exported contacts."), self.window)

		dialog.destroy()

	def deleteButton_clicked(self, widget):
		selected = self.contactSelection.count_selected_rows() > 0
		many = self.contactSelection.count_selected_rows() > 1
		if selected:
			(model, paths) = self.contactSelection.get_selected_rows()

			if many:
				text = "<big><b>%s</b></big>" % _("Remove Contacts")
				sec_text = _("You are about to remove the selected contacts from your contactlist.\nDo you want to continue?")
			else:
				fullname = model[paths[0]][1]
				text = "<big><b>%s</b></big>" % _("Remove Contact")
				sec_text = _("You are about to remove <b>%s</b> from your contactlist.\nDo you want to continue?") % (fullname)

			msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE)
			msgbox.set_title("Arkadas")
			msgbox.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
			if many:
				msgbox.add_button(_("Delete Contacts"), gtk.RESPONSE_OK)
			else:
				msgbox.add_button(_("Delete Contact"), gtk.RESPONSE_OK)
			msgbox.set_markup(text)
			msgbox.format_secondary_markup(sec_text)

			if msgbox.run() == gtk.RESPONSE_OK:
				self.edit = False
				self.clear()

				iters = []
				for path in paths:
					contact = self.engine.getContact(model[path][0])
					
					image_path = os.path.join(self.photo_dir, contact.uuid)
					if os.path.exists(image_path): os.remove(image_path)
					
					self.engine.removeContact(contact)
					iters.append(model.get_iter(path))

				for iter in iters:
					self.contactData.remove(iter)
				self.contactSelection.select_path((0,))

			msgbox.destroy()

	def removefromButton_clicked(self, widget):
		(model, iter) = self.groupSelection.get_selected()
		group_id = model[iter][0]

		if group_id:
			(model, paths) = self.contactSelection.get_selected_rows()

			iters = []

			for path in paths:
				self.engine.removeFromGroup(group_id, model[path][0].id)
				iters.append(model.get_iter(path))

			for iter in iters:
				self.contactData.remove(iter)

	def fullscreenButton_clicked(self, widget=None):
		hpaned = self.tree.get_widget("hpaned")
		button = self.tree.get_widget("fullscreenButton")
		item = self.tree.get_widget("fullscreenItem1")
		item2 = self.tree.get_widget("fullscreenItem2")
		if self.fullscreen:
			button.set_property("stock-id", gtk.STOCK_FULLSCREEN)
			item.show()
			item2.hide()
		else:
			button.set_property("stock-id", gtk.STOCK_LEAVE_FULLSCREEN)
			item.hide()
			item2.show()
		hpaned.get_child1().set_property("visible", self.fullscreen)
		self.fullscreen = not self.fullscreen
		self.contactData_changed()

	def prefsButton_clicked(self, widget):
		dialog = self.tree.get_widget("prefsDialog")

		self.tree.get_widget("prefNotebook").set_current_page(0)
		dialog.run()

		self.display_format = self.tree.get_widget("formatCombo").get_active()
		self.sort_format = self.tree.get_widget("sortCombo").get_active()

		for row in self.contactData:
			contact = row[0]
			fullname = format_fn(display_formats[self.display_format], **contact.names.__dict__)
			sort_string = format_fn(sort_formats[self.sort_format], **contact.names.__dict__)
			self.contactData[row.iter] = [contact, fullname, sort_string]

		self.address_format = self.tree.get_widget("addressCombo").get_active()

		for field in self.adrbox.vbox:
			field.label.format = address_formats[self.address_format]
			field.label.set_editable(self.edit)

		self.fullscreen_editing = self.tree.get_widget("editingCheck").get_active()
		self.show_separator = self.tree.get_widget("showlineCheck").get_active()

		for opt in ("none", "crop", "center"):
			if self.tree.get_widget(opt+"Radio").get_active():
				self.photo_manip = opt
				break

		model = self.tree.get_widget("templateList").get_model()
		self.template = list(row[1] for row in model)

		model = self.tree.get_widget("orderList").get_model()
		self.display_order = list(row[1] for row in model)

		for name in ("tel", "email", "url", "im", "adr", "bday", "note"):
			self.table.remove(getattr(self, name+"box"))

		for type in self.display_order + ["note"]:
			box = getattr(self, type+"box")
			box.set_separator(self.show_separator)
			self.table.pack_start(box, False)

		self.save_prefs()
		dialog.hide()

	def moveupButton_clicked(self, treeview):
		(model, iter) = treeview.get_selection().get_selected()

		if iter:
			row = model.get_path(iter)[0]
			if row > 0:
				model.move_before(iter, model.get_iter(row-1))

	def movedownButton_clicked(self, treeview):
		(model, iter) = treeview.get_selection().get_selected()

		if iter:
			row = model.get_path(iter)[0]
			if row < len(model)-1:
				model.move_after(iter, model.get_iter(row+1))

	def addfieldMenu_clicked(self, item, name):
		model = self.tree.get_widget("templateList").get_model()
		model.append([types[name], name])

	def addfieldButton_clicked(self, treeview):
		self.addfieldMenu.popup(None, None, None, 1, 0)

	def removefieldButton_clicked(self, treeview):
		(model, iter) = treeview.get_selection().get_selected()

		if iter:
			model.remove(iter)

	def aboutButton_clicked(self, widget):
		aboutdialog = gtk.AboutDialog()
		try:
			aboutdialog.set_transient_for(self.window)
			aboutdialog.set_modal(True)
		except:
			pass
		aboutdialog.set_name("Arkadas")
		aboutdialog.set_version(__version__)
		aboutdialog.set_comments(_("A lightweight GTK+ Contact-Manager."))
		aboutdialog.set_license(__license__)
		aboutdialog.set_authors(["Paul Johnson <thrillerator@googlemail.com>","Erdem Cakir <1988er@gmail.com>"])
		aboutdialog.set_translator_credits("de - Erdem Cakir <1988er@gmail.com>")
		gtk.about_dialog_set_url_hook(lambda d,l: browser_load(l, self.window))
		aboutdialog.set_website("http://arkadas.berlios.de")
		aboutdialog.set_website_label("http://arkadas.berlios.de")
		large_icon = gtk.gdk.pixbuf_new_from_file(find_path("arkadas.png"))
		aboutdialog.set_logo(large_icon)
		aboutdialog.run()
		aboutdialog.destroy()

	def groupaddButton_clicked(self, button=None, edit=False):
		(model, iter) = self.groupSelection.get_selected()

		if edit:
			if iter:
				group = model[iter]
			else: return

			if group[0] in (-1, 0): return

		dialog = gtk.Dialog(None, self.window, gtk.DIALOG_MODAL, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
 		if edit:
 			dialog.set_title(_("Edit Group"))
 			dialog.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
 		else:
 			dialog.set_title(_("Create Group"))
			dialog.add_button(gtk.STOCK_ADD, gtk.RESPONSE_OK)
		dialog.set_default_response(gtk.RESPONSE_OK)

 		table = gtk.Table()
		table.set_row_spacings(2)
		table.set_col_spacings(4)
		table.set_border_width(6)

		label = gtk.Label(_("Group name") + ":")
		label.set_alignment(1, 0.5)
		table.attach(label, 0, 1, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL)
		nameentry = gtk.Entry()
		nameentry.set_activates_default(True)
		if edit: nameentry.set_text(group[1])
		table.attach(nameentry, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL)

		label = gtk.Label(_("Description (optional)") + ":")
		label.set_alignment(1, 0.5)
		table.attach(label, 0, 1, 1, 2, gtk.EXPAND|gtk.FILL, gtk.FILL)
		descentry = gtk.Entry()
		descentry.set_activates_default(True)
		if edit: descentry.set_text(group[2])
		table.attach(descentry, 1, 2, 1, 2, gtk.EXPAND|gtk.FILL, gtk.FILL)

		dialog.vbox.pack_start(table)
		dialog.vbox.show_all()

		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			name = nameentry.get_text()
			desc = descentry.get_text()
			if edit:
				self.engine.editGroup(group[0], name, desc)
				model.set(iter, 1, name, 2, desc)
			else:
				id = self.engine.addGroup(name, desc)
				iter = model.append([id, name, desc])
			self.groupSelection.select_iter(iter)

		dialog.destroy()

	def groupremoveButton_clicked(self, button):
		(model, iter) = self.groupSelection.get_selected()
		if iter:
			group = model[iter]
		else: return

		if group[0] == 0: return

		text = "<big><b>%s</b></big>" % _("Remove Group")
		sec_text = _("You are about to remove the group <b>%s</b>.\nDo you want to continue?") % group[1]

		msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE)
		msgbox.set_title("Arkadas")
		msgbox.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		msgbox.add_button(_("Delete Group"), gtk.RESPONSE_OK)
		msgbox.set_markup(text)
		msgbox.format_secondary_markup(sec_text)

		if msgbox.run() == gtk.RESPONSE_OK:
			self.engine.removeGroup(group[0])
			model.remove(iter)
			self.groupSelection.select_path((0,))

		msgbox.destroy()

	def addCombo_changed(self, combo):
		title, name = combo.get_model()[combo.get_active()]

		if name is None:
			return
		elif name == "bday":
			if self.contact.hasValue("bday"):
				combo.set_active(0)
				return
			self.contact.bday = "1950-01-01"
			field = self.add_label("bday", self.contact.bday)
		else:
			content = self.contact.add(name)
			content.value = ""
			if name in ("tel", "adr"):
				content.type = "home"
			elif name == "im":
				content.type = "aim"
			field = self.add_label(name, content)

		field.set_editable(True)
		field.grab_focus()

		combo.set_active(0)

	def prevButton_clicked(self, button):
		self.goto_contact(-1)

	def nextButton_clicked(self, button):
		self.goto_contact(+1)

	def goto_contact(self, dir):
		try: cur_path = self.contactSelection.get_selected_rows()[1][0][0]
		except: cur_path = None

		if cur_path is not None:
			length = len(self.contactData)
			cur_path += dir
			if cur_path < 0:
				cur_path = length-1
			elif cur_path == length:
				cur_path = 0
			self.contactSelection.unselect_all()
			self.contactSelection.select_path((cur_path,))
			self.contactData_changed()
		elif len(self.contactData) > 0:
			self.contactSelection.select_path((0,))

	def undoButton_clicked(self, button):
		id = self.contact.id
		self.edit = False
		self.editButton_clicked(edit=False)
		self.clear()
		if self.is_new:
			self.engine.removeContact(id)
		else:
			self.contact = self.engine.getContact(id)
			self.parse_contact()
		self.contactData_changed()

	def editButton_clicked(self, button=None, edit=True):
		self.edit = edit

		if self.fullscreen_editing:
			self.fullscreen = not edit
			self.fullscreenButton_clicked()

		self.addCombo.set_property("visible", edit)
		self.prevButton.set_property("visible", not edit)
		self.nextButton.set_property("visible", not edit)
		self.undoButton.set_property("visible", edit)
		self.saveButton.set_property("visible", edit)
		self.editButton.set_property("visible", not edit)
		self.namechangeButton.set_property("visible", edit)
		if edit: self.tree.get_widget("countLabel").set_text("")

		for name in ("tel", "email", "url", "im", "adr"):
			for field in getattr(self, name+"box").vbox:
					field.set_editable(edit)
					if isinstance(field.label, CustomLabel):
						if field.label.get_text() == "":
							self.contact.remove(field.content)
							field.destroy()
					elif isinstance(field.label, AddressField):
						if field.label.content.isEmpty():
							self.contact.remove(field.content)
							field.destroy()

		for field in self.bdaybox.vbox:
			field.set_editable(edit)
			self.contact.bday = field.label.content
			break

		scrolledwindow = self.notebox.vbox.get_children()[0]
		textview = scrolledwindow.get_child()
		textbuffer = textview.get_buffer()

		if edit: scrolledwindow.set_shadow_type(gtk.SHADOW_IN)
		else: scrolledwindow.set_shadow_type(gtk.SHADOW_NONE)

		textview.set_editable(edit)

		self.contact.note = textbuffer.get_text(*textbuffer.get_bounds()).strip()

		if self.contact.hasValue("note") or edit:
			self.notebox.show()
		else:
			self.notebox.hide()
			
	def saveButton_clicked(self, button=None):
		self.editButton_clicked(edit=False)

		if self.contact.save():
			if self.is_new:
				self.add_to_list(self.contact, True)
		else:
			error(_("Unable to save the contact."), self.window)

		self.is_new = False
		self.contactData_changed()	
		
		markup = "<small>%s</small>"
		date = datetime.datetime.strptime(self.contact.modified, "%Y-%m-%dT%H:%M:%S")
		text = _("Modified on %s - %s") % (date.strftime("%x"), date.strftime("%X"))
		self.modifiedLabel.set_markup(markup % text)	

	def imageopenButton_clicked(self, button):
		def update_preview(filechooser):
			filename = filechooser.get_preview_filename()
			pixbuf = get_pixbuf_of_size_from_file(filename, 128)
			preview.set_from_pixbuf(pixbuf)
			filechooser.set_preview_widget_active(pixbuf is not None)
			
		dialog = gtk.FileChooserDialog(title=_("Open Image"),
										action=gtk.FILE_CHOOSER_ACTION_OPEN,
										buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
										
		dialog.set_icon_name("gtk-open")
		dialog.set_default_response(gtk.RESPONSE_OK)
		
		filefilter = gtk.FileFilter()
		filefilter.set_name(_("Images"))
		filefilter.add_pixbuf_formats()
		dialog.add_filter(filefilter)
		filefilter = gtk.FileFilter()
		filefilter.set_name(_("All Files"))
		filefilter.add_pattern("*")
		dialog.add_filter(filefilter)
		
		preview = gtk.Image()
		dialog.set_preview_widget(preview)
		dialog.set_use_preview_label(False)
		dialog.connect("update-preview", update_preview)

		#vbox = gtk.VBox()
		#dialog.set_extra_widget(vbox)

		#vbox.add(gtk.CheckButton(_("Scaledown to 200 Pixel")))
		#vbox.add(gtk.CheckButton(_("Crop image")))
		#vbox.show_all()

		if dialog.run() == gtk.RESPONSE_OK:
			filename = dialog.get_preview_filename()
			try:
				pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
				if self.photo_manip == "crop":
					pixbuf = get_crop_pixbuf(pixbuf)
					pixbuf = get_pixbuf_of_size(pixbuf, 64)
				elif self.photo_manip == "center":
					pixbuf = get_pixbuf_of_size(pixbuf, 64)
					pixbuf = get_pad_pixbuf(pixbuf, 64, 64)
				else:
					pixbuf = get_pixbuf_of_size(pixbuf, 64)
				self.has_photo = True
			except:
				pixbuf = get_pixbuf_of_size_from_file(find_path("no-photo.png"), 64)
				self.has_photo = False

			if self.has_photo:
				self.contact.photo = filename
			self.photoImage.set_from_pixbuf(pixbuf)

		dialog.destroy()
		gc.collect()

	def imageremoveButton_clicked(self, button):
		pixbuf = get_pixbuf_of_size_from_file(find_path("no-photo.png"), 64)
		self.photoImage.set_from_pixbuf(pixbuf)
		self.has_photo = False
		self.contact.photo = ""

	def namechangeButton_clicked(self, button):
		dialog = self.tree.get_widget("namechangeDialog")

		self.nameEntry1 = self.tree.get_widget("nameEntry1")
		self.nameEntry2 = self.tree.get_widget("nameEntry2")
		self.nameEntry3 = self.tree.get_widget("nameEntry3")
		self.nameEntry4 = self.tree.get_widget("nameEntry4").child
		self.nameEntry5 = self.tree.get_widget("nameEntry5").child
		self.nameEntry6 = self.tree.get_widget("nameEntry6")
		self.nameEntry7 = self.tree.get_widget("nameEntry7")
		self.nameEntry8 = self.tree.get_widget("nameEntry8")

		i = 1
		for val in ("given", "additional", "family", "prefix", "suffix"):
			if getattr(self.contact.names, val):
				getattr(self, "nameEntry" + str(i)).set_text(getattr(self.contact.names, val))
			i += 1

		if self.contact.nickname:
			self.nameEntry6.set_text(self.contact.nickname)
		if self.contact.title:
			self.nameEntry7.set_text(self.contact.title)
		if self.contact.org:
			self.nameEntry8.set_text(self.contact.org)

		self.nameEntry1.grab_focus()

		if dialog.run() == gtk.RESPONSE_OK:
			i = 1
			for val in ("given", "additional", "family", "prefix", "suffix"):
				setattr(self.contact.names, val, getattr(self, "nameEntry" + str(i)).get_text())
				i += 1

			self.contact.nickname = self.nameEntry6.get_text().replace("  "," ").strip()
			self.contact.title = self.nameEntry7.get_text().replace("  "," ").strip()
			self.contact.org = self.nameEntry8.get_text().replace("  "," ").strip()

			text = "<span size=\"x-large\"><b>%s</b></span>" % format_fn(display_formats[self.display_format], **self.contact.names.__dict__)
			if self.contact.hasValue("nickname"):
				text += " (<big>%s</big>)" % self.contact.nickname
			self.tree.get_widget("fullnameLabel").set_markup(text)

			if self.contact.hasValue("title"):
				self.tree.get_widget("titleLabel").set_text(self.contact.title)
			if self.contact.hasValue("org"):
				self.tree.get_widget("orgLabel").set_text(self.contact.org)

		dialog.hide()

	def groupList_drag_data_received(self, treeview, drag_context, x, y, selection, info, timestamp):
		data = selection.data

		if data:
			dest_row = treeview.get_dest_row_at_pos(x, y)
			if dest_row:
				if dest_row[1] in (gtk.TREE_VIEW_DROP_INTO_OR_BEFORE, gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
					group_id = treeview.get_model()[dest_row[0]][0]
					if group_id > 0:
						for id in data.split(","):
							if id.isdigit(): self.engine.addToGroup(group_id, id)
						#self.groupSelection.select_path(dest_row[0])
			return True

	def groupSelection_changed(self, selection):
		(model, iter) = selection.get_selected()

		self.contactData.clear()
		if iter:
			for id in self.engine.getList(model[iter][0]):
				contact = self.engine.getContact(id[0])
				if contact is not None:
					self.add_to_list(contact)
			self.contactSelection.select_path((0,))
			
			fakegroup = model[iter][0] in (-1, 0)
			
			self.tree.get_widget("removefromItem").set_property("visible", not fakegroup)
			self.tree.get_widget("removefromItem2").set_property("visible", not fakegroup)
			self.tree.get_widget("separatormenuitemR").set_property("visible", not fakegroup)
			self.tree.get_widget("separatormenuitemR2").set_property("visible", not fakegroup)

	def contactData_changed(self, *args):
		length = len(self.contactData)

		text = ""
		if self.fullscreen:
			try: cur_path = self.contactSelection.get_selected_rows()[1][0][0]
			except: cur_path = None

			if cur_path is not None:
				text = str(cur_path+1) + _(" of ") + str(length)
		else:
			text = str(length)
			if length == 0: text = _("no contacts")
			elif length == 1: text += _(" contact")
			else: text += _(" contacts")

		self.tree.get_widget("countLabel").set_text(text)

	def contactList_drag_data_get(self, treeview, drag_context, selection, info, timestamp):
		(model, paths) = self.contactSelection.get_selected_rows()
		if paths:
			data = ",".join(str(model[path][0].id) for path in paths)
			selection.set_text(data)
			return True

	def contactList_popup(self, widget):
		if self.contactSelection.count_selected_rows() > 0:
			self.tree.get_widget("contactlistMenu").popup(None, None, None, 3, 0)

	def contactList_pressed(self, treeview, event):
 		if event.button == 3:
			if self.contactSelection.count_selected_rows() > 0:
				treeview.grab_focus()
				self.tree.get_widget("contactlistMenu").popup(None, None, None, event.button, event.time)
			return True

	def contactList_clicked(self, *args):
		self.contactSelection_changed(edit=True)

	def contactSelection_changed(self, selection=None, edit=False):
		self.check_if_changed()

		if self.contactSelection.count_selected_rows():
			(model, paths) = self.contactSelection.get_selected_rows()

			if self.contact == model[paths[0]][0]:
				again = True
			else:
				again = False

			if not again:
				self.clear()
				if isinstance(model[paths[0]][0], ContactEngine.Contact):
					self.contact = model[paths[0]][0]
					self.parse_contact()

			if self.contact:
				self.editButton_clicked(edit=edit)
		else:
			self.clear()
			
		self.tree.get_widget("contactMenuitem").set_property("visible", self.contactSelection.count_selected_rows() > 0)

	def main(self):
		#gtk.gdk.threads_enter()
		gtk.main()
		#gtk.gdk.threads_leave()

if __name__ == "__main__":
	app = MainWindow()
	app.main()
