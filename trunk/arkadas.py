# -*- coding: utf-8 -*-

import sys, os, datetime, gc, threading
import gtk, gtk.glade, gobject, pango

# Test pygtk version
if gtk.pygtk_version < (2, 6, 0):
	sys.stderr.write("requires PyGTK 2.6.0 or newer.\n")
	sys.exit(1)

gobject.threads_init()

try:
	import vobject
except ImportError:
	sys.stderr.write("requires vobject.\n")
	sys.exit(1)

import gettext
gettext.install("arkadas", "/usr/share/locale", unicode=1)

__author__ = "Paul Johnson"
__email__ = "thrillerator@googlemail.com"
__version__ = "0.8"
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

types = {
	"HOME":_("Home"), "WORK":_("Work"),
	"BDAY":_("Birthday"), "URL":_("Website"),
	"EMAIL":"Email", "ADR":_("Address"),
	"IM":_("Username"), "IM_CAP":"Instant Messaging",
	"NOTE":_("Notes:"), "TEL":_("Phone"),
	# address types
	"BOX":_("Postbox"), "EXTENDED":_("Extended"),
	"STREET":_("Street"), "CITY":_("City"),
	"REGION":_("State"), "CODE":_("ZIP"), "COUNTRY":_("Country"),
	# tel types
	"VOICE":_("Landline"), "ISDN":_("ISDN"),
	"CELL":_("Mobile"), "FAX":_("Fax"),
	"CAR":_("Car"), "VIDEO":_("Video"),
	"PAGER":_("Pager"), "MODEM":_("Modem"),
	"BBS":_("BBS"), "PCS":_("PCS"),
	# im types
	"X-AIM":"AIM", "X-GADU-GADU":"Gadu-Gadu",
	"X-GROUPWISE":"GroupWise", "X-ICQ":"ICQ",
	"X-IRC":"IRC", "X-JABBER":"Jabber",
	"X-MSN":"MSN", "X-NAPSTER":"Napster",
	"X-YAHOO":"Yahoo", "X-ZEPHYR":"Zephyr",
	}

tel_types = ("VOICE", "ISDN", "CELL", "FAX", "PAGER", "CAR", "VIDEO", "MODEM", "BBS", "PCS")
im_types = ("X-AIM", "X-GADU-GADU", "X-GROUPWISE", "X-ICQ", "X-IRC", "X-JABBER", "X-MSN", "X-NAPSTER", "X-YAHOO", "X-ZEPHYR")

order = ["TEL", "EMAIL", "URL", "IM", "BDAY", "ADR", "WORK_TEL", "WORK_EMAIL", "WORK_ADR"]

#--------------------
# Class MainWindow
#--------------------
class MainWindow:
	fullscreen = False
	import_mode = False
	edit = False
	is_new = False
	vcard = None
	photodatatype = None

	def __init__(self):
		gtk.window_set_default_icon_name("address-book")
		self.tree = gtk.glade.XML(find_path("arkadas.glade"))

		signals = {}
		for attr in dir(self.__class__):
			signals[attr] = getattr(self, attr)
		self.tree.signal_autoconnect(signals)

		self.tooltips = gtk.Tooltips()
		self.clipboard = gtk.Clipboard()
		self.load_prefs()
		self.load_widgets()
		self.build_list()
		self.build_table()
		self.clear()

		self.window.show_all()

		args = sys.argv[1:]
		if len(args) > 0:
			for arg in args:
				self.import_contact(arg, True)

		if not len(self.contactData) > 0:
			self.import_mode = False
			self.tree.get_widget("revertButton").hide()
			gobject.idle_add(self.load_contacts)

	def load_prefs(self):
		# set fallback config dir
		path = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
		self.config_dir = os.path.join(path, "arkadas")
		if not os.path.exists(self.config_dir): os.mkdir(self.config_dir)
		# set fallback contact dir
		self.contact_dir = os.path.join(self.config_dir, "contacts")

	def load_widgets(self):
		self.window = self.tree.get_widget("mainWindow")
		self.contactList = self.tree.get_widget("contactList")
		self.table = self.tree.get_widget("table")

		self.addButton = self.tree.get_widget("addButton")
		self.undoButton = self.tree.get_widget("undoButton")
		self.saveButton = self.tree.get_widget("saveButton")
		self.editButton = self.tree.get_widget("editButton")
		self.imagechangeButton = self.tree.get_widget("imagechangeButton")
		self.imageremoveButton = self.tree.get_widget("imageremoveButton")
		self.namechangeButton = self.tree.get_widget("namechangeButton")

		self.photoImage = self.tree.get_widget("photoImage")

	def build_list(self):
		self.contactSelection = self.contactList.get_selection()
		self.contactSelection.set_mode(gtk.SELECTION_MULTIPLE)

		self.contactData = gtk.ListStore(str, str, gobject.TYPE_PYOBJECT)
		self.contactData.set_sort_column_id(1, gtk.SORT_ASCENDING)
		self.contactList.set_model(self.contactData)

		# contactlist cellrenderers
		cellimg = gtk.CellRendererPixbuf()
		cellimg.set_property("icon-name", "stock_contact")
		celltxt = gtk.CellRendererText()
		celltxt.set_property("ellipsize", pango.ELLIPSIZE_END)
		column = gtk.TreeViewColumn()
		column.pack_start(cellimg, False)
		column.pack_start(celltxt)
		column.add_attribute(celltxt,"text", 0)
		self.contactList.append_column(column)

		# events
		self.contactData.connect("row-deleted", self.contactData_change, None)
		self.contactData.connect("row-inserted", self.contactData_change)
		self.contactSelection.connect("changed", self.contactSelection_change)

		self.contactList.grab_focus()

	def build_table(self):
		viewport = self.tree.get_widget("viewport")
		viewport.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

		# create type menus
		self.addMenu = gtk.Menu()
		for name in ("TEL", "EMAIL", "ADR", "URL", "IM_CAP", "BDAY"):
			if not name in ("BDAY", "IM_CAP", "URL"):
				menuitem = gtk.MenuItem(types[name])
				menuitem.connect("activate", self.addMenu_itemclick, "HOME", name)
				self.addMenu.append(menuitem)
				menuitem = gtk.MenuItem(types[name] + " (" + types["WORK"] + ")")
				menuitem.connect("activate", self.addMenu_itemclick, "WORK", name)
				self.addMenu.append(menuitem)
			else:
				menuitem = gtk.MenuItem(types[name])
				menuitem.connect("activate", self.addMenu_itemclick, "", name)
				self.addMenu.append(menuitem)
		self.addMenu.show_all()

		self.hsizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

		# fieldholder
		self.photobox = self.tree.get_widget("photobox")
		self.emailbox = EventVBox()
		self.workemailbox = EventVBox()
		self.telbox = EventVBox()
		self.worktelbox = EventVBox()
		self.imbox = EventVBox()
		self.workadrbox = EventVBox()
		self.urlbox = EventVBox()
		self.adrbox = EventVBox()
		self.bdaybox = EventVBox()
		self.notebox = gtk.VBox(False, 6)

		# add fieldholder by order
		for type in order:
			# tel numbers
			if type == "TEL":
				self.table.pack_start(self.telbox, False)
			elif type == "WORK_TEL":
				self.table.pack_start(self.worktelbox, False)
			# emails
			elif type == "EMAIL":
				self.table.pack_start(self.emailbox, False)
			elif type == "WORK_EMAIL":
				self.table.pack_start(self.workemailbox, False)
			# web
			elif type == "URL":
				self.table.pack_start(self.urlbox, False)
			# instant messaging
			elif type == "IM":
				self.table.pack_start(self.imbox, False)
			# address
			elif type == "ADR":
				self.table.pack_start(self.adrbox, False)
			elif type == "WORK_ADR":
				self.table.pack_start(self.workadrbox, False)
			# birthday
			elif type == "BDAY":
				self.table.pack_start(self.bdaybox, False)

		self.table.pack_start(self.notebox)

		# add photobuttons & titlelabel
		hbox = self.tree.get_widget("hbox2")
		self.hsizegroup.add_widget(hbox)

	#---------------
	# main funtions
	#---------------
	def load_contacts(self):
		self.contactData.clear()
		# read all files in folder
		for curfile in os.listdir(self.contact_dir):
			filename = os.path.join(self.contact_dir, curfile)
			# create vcard-object
			components = vobject.readComponents(file(filename, "r"))
			for vcard in components:
				try:
					vcard.filename = filename
					self.add_to_list(vcard)
				except:
					break
		self.contactSelection.select_path((0,))
		return False

	def add_to_list(self, vcard):
		# get fullname, else make fullname from name
		if vcard.version.value == "3.0":
			sort_string = vcard.n.value.family + " " + vcard.n.value.given + " " + vcard.n.value.additional
		else:
			n = vcard.n.value.split(";")
			sort_string = n[0] + " " + n[1] + " " + n[2]
			if not has_child(vcard, "fn"):
				fn = ""
				for i in (3,1,2,0,4):
					fn += n[i].strip() + " "
				vcard.add("fn")
				vcard.fn.value = fn.replace("  "," ").strip()
		sort_string = sort_string.replace("  "," ").strip()
		vcard.iter = self.contactData.append([unescape(vcard.fn.value), sort_string, vcard])

	def import_contact(self, filename, add=False):
		if not self.import_mode:
			self.check_if_changed()
			self.contactData.clear()
			self.import_mode = True
			self.tree.get_widget("revertButton").show()

		try:
			components = vobject.readComponents(file(filename, "r"))
			for vcard in components:
				vcard.filename = filename
				vcard.iter = None
				self.add_to_list(vcard)
				self.contactSelection.select_iter(vcard.iter)
				if add:
					vcard.filename = None
					self.saveButton_clicked()
		except:
			error_dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, _("Unable to load the contact."))
			error_dialog.run()
			error_dialog.destroy()
			self.clear()

	def check_if_new(self):
		if self.is_new:
			self.is_new = False
			self.contactData.remove(self.vcard.iter)
			self.editButton_clicked(edit=False)
			self.clear()
			return True
		else:
			return False

	def check_if_changed(self):
		if self.edit and self.vcard is not None:
			text = "<big><b>%s</b></big>" % _("Save the changes to contact before closing?")
			sec_text = _("If you don't save, changes you made to <b>%s</b> will be permanently lost.") % unescape(self.vcard.fn.value)

			msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE)
			msgbox.set_title("Arkadas")
			msgbox.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)
			msgbox.set_markup(text)
			msgbox.format_secondary_markup(sec_text)

			if msgbox.run() == gtk.RESPONSE_OK:
				self.editButton_clicked(edit=False)
				self.saveButton_clicked()
			msgbox.destroy()

	def view_contact(self, edit = False):
		if self.contactSelection.count_selected_rows() > 0:
			(model, paths) = self.contactSelection.get_selected_rows()
			vcard = model[paths[0]][2]

			self.check_if_new()
			self.check_if_changed()
			self.clear()
			self.load_contact(vcard, edit)

	def load_contact(self, new_vcard, edit=False):
		self.vcard = new_vcard

		self.saveButton.set_sensitive(True)
		self.editButton.set_sensitive(True)

		self.has_photo = True

		# FIELD - fullname & nickname
		text = "<span size=\"x-large\"><b>%s</b></span>" % unescape(self.vcard.fn.value)
		if has_child(self.vcard, "nickname"):
			text += " (<big>%s</big>)" % unescape(self.vcard.nickname.value)
		self.tree.get_widget("fullnameLabel").set_markup(text)

		# FIELD - title & org
		if has_child(self.vcard, "title"):
			self.tree.get_widget("titleLabel").set_text(unescape(self.vcard.title.value))
		if has_child(self.vcard, "org"):
			self.tree.get_widget("orgLabel").set_text(unescape(self.vcard.org.value))

		# FIELD - tel
		self.add_labels_by_name(self.telbox, self.worktelbox, "tel")
		# FIELD - emails
		self.add_labels_by_name(self.emailbox, self.workemailbox, "email")
		# FIELD - web
		if has_child(self.vcard, "url"):
			for child in self.vcard.contents["url"]:
				if not child.value.startswith("http://"):
					child.value = "http://" + child.value
				self.add_label(self.urlbox, child)
		# FIELD - instant messaging
		for im in im_types:
			if has_child(self.vcard, im.lower()):
				for child in self.vcard.contents[im.lower()]:
					self.add_label(self.imbox, child)
		# FIELD - address
		self.add_labels_by_name(self.adrbox, self.workadrbox, "adr")
		# FIELD - birthday
		if has_child(self.vcard, "bday"):
			for child in self.vcard.contents["bday"]:
				self.add_label(self.bdaybox, child)

		# FIELD - note
		if not has_child(self.vcard, "note"): self.vcard.add("note")
		if not len(self.notebox.get_children()) > 0:
			sep = gtk.HSeparator() ; sep.show()
			self.notebox.pack_start(sep, False)
			self.add_label(self.notebox, self.vcard.note)
		else:
			textview = self.notebox.get_children()[1].get_children()[1].get_child()
			textview.get_buffer().set_text(unescape(self.vcard.note.value))
		self.notebox.show_all()

		self.editButton_clicked(edit=edit)

		self.table.show()

		# FIELD - photo
		def load_photo():
			pixbuf = None
			if has_child(self.vcard, "photo"):
				self.photoImage.show()
				data = None
				# load data or decode data
				if "VALUE" in self.vcard.photo.params:
					try:
						import urllib
						url = urllib.urlopen(self.vcard.photo.value)
						data = url.read()
						url.close()
					except:
						pass
					self.photodata = self.vcard.photo.value
					self.photodatatype = "URI"
				elif "ENCODING" in self.vcard.photo.params:
					data = self.vcard.photo.value
					self.photodata = self.vcard.photo.value
					self.photodatatype = "B64"
				# try to load photo
				try:
					loader = gtk.gdk.PixbufLoader()
					loader.write(data)
					loader.close()
					pixbuf = get_pixbuf_of_size(loader.get_pixbuf(), 64)
					self.has_photo = True
				except:
					self.has_photo = False
			else:
				self.has_photo = False

			self.photoImage.set_from_pixbuf(pixbuf)

		gobject.idle_add(load_photo)

	def clear(self):
		self.vcard = None
		self.photoImage.clear()
		self.tree.get_widget("fullnameLabel").set_text("")
		self.tree.get_widget("titleLabel").set_text("")
		self.tree.get_widget("orgLabel").set_text("")
		for box in self.table.get_children():
			if type(box) == EventVBox:
				for child in box.get_children():
					child.destroy()
		self.table.hide()
		self.addButton.hide()
		self.saveButton.set_sensitive(False)
		self.editButton.set_sensitive(False)
		gc.collect()

	def add_labels_by_name(self, box, workbox, name):
		if has_child(self.vcard, name):
			for child in self.vcard.contents[name]:
				if child.params.has_key("TYPE"):
					if "WORK" in child.type_paramlist: self.add_label(workbox, child)
					else: self.add_label(box, child)
				else:
					child.type_paramlist = ["HOME"]
					self.add_label(box, child)

	def add_label(self, box, content):
		hbox = gtk.HBox(False, 6)

		try:
			paramlist = content.type_paramlist
		except:
			paramlist = []

		# caption
		captionbox = gtk.VBox()
		caption = CaptionField(content.name, paramlist)
		caption.removeButton.connect_object("clicked", gtk.Widget.destroy, hbox)
		captionbox.pack_start(caption, False)
		hbox.pack_start(captionbox, False)
		self.hsizegroup.add_widget(caption)

		if content.name == "ADR":
			field = AddressField(content)
		elif content.name == "BDAY":
			field = BirthdayField(content, self.tooltips)
		elif content.name == "NOTE":
			# multiline label
			scrolledwindow = gtk.ScrolledWindow()
			scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
			scrolledwindow.set_shadow_type(gtk.SHADOW_IN)

			textbuffer = gtk.TextBuffer()
			textbuffer.set_text(unescape(content.value))
			textview = gtk.TextView(textbuffer)
			textview.set_wrap_mode(gtk.WRAP_WORD)
			textview.set_editable(False)
			textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
			textview.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
			scrolledwindow.add(textview)
			field = scrolledwindow
		else:
			# LabelEntry
			field = LabelField(content)
			field.set_editable(False)
			caption.field = field

		hbox.add(field)
		box.add(hbox)
		return hbox

	#---------------
	# event funtions
	#---------------
	def delete_event(self, widget, event=None):
		self.check_if_changed()
		#sys.exit()
		gtk.main_quit()
		return False

	def newButton_clicked(self, widget):
		vcard = vobject.vCard()
		vcard.add("n")
		vcard.add("fn")
		vcard.add("tel")
		vcard.add("email")
		vcard.add("url")
		vcard.tel.type_paramlist = ["HOME", "VOICE", "PREF"]
		vcard.email.type_paramlist = ["HOME", "INTERNET", "PREF"]
		vcard.serialize()
		vcard.filename = None
		vcard.iter = self.contactData.append([_("Unnamed"), "", vcard])
		self.contactSelection.unselect_all()
		self.contactSelection.select_iter(vcard.iter)
		self.view_contact(True)
		self.is_new = True
		self.undoButton.hide()
		self.namechangeButton_clicked(None)

	def openButton_clicked(self, widget):
		dialog = gtk.FileChooserDialog(title=_("Open Contacts"),action=gtk.FILE_CHOOSER_ACTION_OPEN,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		dialog.set_select_multiple(True)
		dialog.set_extra_widget(gtk.CheckButton(_("Import to contactlist")))
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
			for filename in dialog.get_filenames():
				self.import_contact(filename, dialog.get_extra_widget().get_active())

		dialog.destroy()

	def deleteButton_clicked(self, widget):
		selected = self.contactSelection.count_selected_rows() > 0
		many = self.contactSelection.count_selected_rows() > 1
		if selected and not self.check_if_new():
			(model, paths) = self.contactSelection.get_selected_rows()

			if many:
				text = "<big><b>%s</b></big>" % _("Remove Contacts")
				sec_text = _("You are about to remove the selected contacts from your contactlist.\nDo you want to continue?")
			else:
				fullname = model[paths[0]][0]
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
				iters = []
				for path in paths:
					iters.append(model.get_iter(path))
				for iter in iters:
					filename = model[iter][2].filename
					try:
						os.remove(filename)
						self.contactData.remove(iter)
						self.contactSelection.select_path((0,))
					except:
						pass
			msgbox.destroy()

	def fullscreenButton_clicked(self, widget):
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

	def prefsButton_clicked(self, widget):
		pass

	def copyButton_clicked(self, widget, name):
		(model, paths) = self.contactSelection.get_selected_rows()
		vcard = model[paths[0]][2]
		value = vcard.getChildValue(name)
		if value is not None:
			if name == "fn": value = unescape(value)
			self.clipboard.set_text(value)

	def importButton_clicked(self, widget):
		(model, paths) = self.contactSelection.get_selected_rows()
		for path in paths:
			vcard = model[path][2]
			vcard.filename = None
			self.saveButton_clicked()

	def exportButton_clicked(self, widget):
		pass

	def aboutButton_clicked(self, widget):
		aboutdialog = gtk.AboutDialog()
		try:
			aboutdialog.set_transient_for(self.window)
			aboutdialog.set_modal(True)
		except:
			pass
		aboutdialog.set_name("Arkadas")
		aboutdialog.set_version(__version__)
		aboutdialog.set_comments(_("A lightweight GTK+ Contact-Manager based on vCards."))
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

	def revertButton_clicked(self, widget):
		self.check_if_changed()
		self.import_mode = False
		widget.hide()
		self.load_contacts()

	def addButton_clicked(self, button):
		self.addMenu.popup(None, None, None, 3, 0)

	def addMenu_itemclick(self, item, nametype, name):
		if name == "TEL":
			content = self.vcard.add("tel")
			content.type_paramlist = [nametype, "VOICE"]
			if nametype == "HOME": box = self.add_label(self.telbox, content)
			elif nametype == "WORK": box = self.add_label(self.worktelbox, content)
		elif name == "EMAIL":
			content = self.vcard.add("email")
			content.type_paramlist = [nametype, "INTERNET"]
			if nametype == "HOME": box = self.add_label(self.emailbox, content)
			elif nametype == "WORK": box = self.add_label(self.workemailbox, content)
		elif name == "ADR":
			content = self.vcard.add("adr")
			content.type_paramlist = [nametype, "POSTAL", "PARCEL"]
			if nametype == "HOME": box = self.add_label(self.adrbox, content)
			elif nametype == "WORK": box = self.add_label(self.workadrbox, content)
		elif name == "URL":
			content = self.vcard.add("url")
			box = self.add_label(self.urlbox, content)
		elif name == "IM_CAP":
			content = self.vcard.add("x-aim")
			content.type_paramlist = ["HOME"]
			box = self.add_label(self.imbox, content)
		elif name == "BDAY":
			content = self.vcard.add("bday")
			content.value = "1950-01-01"
			box = self.add_label(self.bdaybox, content)

		caption, field = box.get_children()[0].get_children()[0], box.get_children()[1]
		caption.set_editable(True)
		field.set_editable(True)
		field.grab_focus()

	def prevButton_clicked(self, button):
		try:
			cur_path = self.contactData.get_path(self.vcard.iter)[0]
		except:
			cur_path = None

		self.contactSelection.unselect_all()
		if cur_path is not None:
			if cur_path > 0:
				self.contactSelection.select_path((cur_path-1,))
				return
		self.contactSelection.select_path((len(self.contactData)-1,))

	def nextButton_clicked(self, button):
		try:
			cur_path = self.contactData.get_path(self.vcard.iter)[0]
		except:
			cur_path = None

		self.contactSelection.unselect_all()
		if cur_path is not None:
			if cur_path < len(self.contactData)-1:
				self.contactSelection.select_path((cur_path+1,))
				return
		self.contactSelection.select_path((0,))

	def undoButton_clicked(self, button):
		vcard = self.vcard
		self.clear()
		self.load_contact(vcard)

	def editButton_clicked(self, button=None, edit=True):
		self.edit = edit
		self.addButton.set_property("visible", edit)
		self.undoButton.set_property("visible", edit)
		self.saveButton.set_property("visible", edit)
		self.editButton.set_property("visible", not edit)
		self.imagechangeButton.set_property("visible", edit)
		self.imageremoveButton.set_property("visible", edit and self.has_photo)
		self.namechangeButton.set_property("visible", edit)

		if not self.has_photo:
			if edit:
				pixbuf = get_pixbuf_of_size_from_file(find_path("no-photo.png"), 64)
				self.photoImage.set_from_pixbuf(pixbuf)
			else:
				self.photoImage.clear()

		for child in self.table.get_children():
			if type(child) == EventVBox:
				for hbox in child.get_children():
					if type(hbox) == gtk.HBox:
						# get caption & field
						caption, field = hbox.get_children()[0].get_children()[0], hbox.get_children()[1]
						caption.set_editable(edit)
						if type(field) == LabelField:
							field.set_editable(edit)
							# remove empty field
							if field.get_text() == "":
								hbox.destroy()
								continue
						elif type(field) == AddressField:
							field.set_editable(edit)
							# remove empty field
							if str(field.content.value).strip().replace(",", "") == "":
								hbox.destroy()
								continue
						elif type(field) == BirthdayField:
							field.set_editable(edit)

		scrolledwindow = self.notebox.get_children()[1].get_children()[1]
		textview = scrolledwindow.get_child()
		if edit: scrolledwindow.set_shadow_type(gtk.SHADOW_IN)
		else: scrolledwindow.set_shadow_type(gtk.SHADOW_NONE)

		textview.set_left_margin(2 * edit)
		textview.set_right_margin(2 * edit)
		textview.set_editable(edit)

	def saveButton_clicked(self, button=None):
		if len(unescape(self.vcard.fn.value)) > 0:
			self.editButton_clicked(edit=False)
			self.is_new = False
			new_vcard = vobject.vCard()
			new_vcard.add("prodid").value = "Arkadas 1.0"
			if has_child(self.vcard, "uid"):
				new_vcard.add("uid").value = uuid()

			if self.vcard.version.value == "3.0":
				new_vcard.add(self.vcard.n)
			else:
				n = self.vcard.n.value.split(";")
				new_vcard.add("n")
				new_vcard.n.value = vobject.vcard.Name(n[0], n[1], n[2], n[3], n[4])
			new_vcard.add(self.vcard.fn)
			if has_child(self.vcard, "nickname"):
				new_vcard.add(self.vcard.nickname)
			if has_child(self.vcard, "org"):
				new_vcard.add(self.vcard.org)
			if has_child(self.vcard, "title"):
				new_vcard.add(self.vcard.title)

			if self.has_photo:
				photo = new_vcard.add("photo")
				if self.photodatatype == "URI":
					photo.value_param = "URI"
				else:
					photo.encoding_param = "b"
				photo.value = self.photodata

			for name in ("label", "mailer", "tz", "geo", "role", "logo", "agent",\
						  "categories", "sort-string", "sound", "class", "key", ):
				if has_child(self.vcard, name):
					new_vcard.add(self.vcard.contents[name][0])

			for child in self.table.get_children():
				if type(child) == EventVBox:
					for hbox in child.get_children():
						if type(hbox) == gtk.HBox:
							field = hbox.get_children()[1]
							new_vcard.add(field.content)

			textview = self.notebox.get_children()[1].get_children()[1].get_child()
			textbuffer = textview.get_buffer()
			start, end = textbuffer.get_bounds()
			text = textbuffer.get_text(start, end).strip()
			if len(text) > 0:
				new_vcard.add("note")
				new_vcard.note.value = escape(text)

			try:
				iter = self.vcard.iter
				filename = os.path.join(self.contact_dir, unescape(self.vcard.fn.value) + ".vcf")

				if self.vcard.filename is not None:
					if not filename == self.vcard.filename:
						if not self.vcard.filename.startswith(self.contact_dir):
							filename = self.vcard.filename
						else:
							os.remove(self.vcard.filename)

				new_file = file(filename, "w")
				new_file.write(new_vcard.serialize())
				new_file.close()

				self.vcard = new_vcard

				self.vcard.filename = filename
				self.vcard.iter = iter
				if self.vcard.iter is not None:
					sort_string = self.vcard.n.value.family + " " + self.vcard.n.value.given + " " + self.vcard.n.value.additional
					self.contactData[self.vcard.iter][0] = unescape(self.vcard.fn.value)
					self.contactData[self.vcard.iter][1] = sort_string
					self.contactData[self.vcard.iter][2] = self.vcard
			except:
				pass
		else:
			errordialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, _("Can't save, please enter a name."))
			errordialog.run()
			errordialog.destroy()

	def imagechangeButton_clicked(self, button):
		def update_preview(filechooser):
			filename = filechooser.get_preview_filename()
			pixbuf = None
			try:
				pixbuf = gtk.gdk.PixbufAnimation(filename).get_static_image()
				width = pixbuf.get_width()
				height = pixbuf.get_height()
				if width > height:
					pixbuf = pixbuf.scale_simple(128, int(float(height)/width*128), gtk.gdk.INTERP_HYPER)
				else:
					pixbuf = pixbuf.scale_simple(int(float(width)/height*128), 128, gtk.gdk.INTERP_HYPER)
			except:
				pass
			if pixbuf == None:
				pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, 1, 8, 128, 128)
				pixbuf.fill(0x00000000)
			preview.set_from_pixbuf(pixbuf)
			have_preview = True
			filechooser.set_preview_widget_active(have_preview)
			del pixbuf

		dialog = gtk.FileChooserDialog(title=_("Open Image"),action=gtk.FILE_CHOOSER_ACTION_OPEN,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		filter = gtk.FileFilter()
		filter.set_name(_("Images"))
		filter.add_pixbuf_formats()
		dialog.add_filter(filter)
		filter = gtk.FileFilter()
		filter.set_name(_("All Files"))
		filter.add_pattern("*")
		dialog.add_filter(filter)
		preview = gtk.Image()
		dialog.set_preview_widget(preview)
		dialog.set_use_preview_label(False)
		dialog.connect("update-preview", update_preview)
		dialog.set_default_response(gtk.RESPONSE_OK)

		if dialog.run() == gtk.RESPONSE_OK:
			filename = dialog.get_preview_filename()
			try:
				imagefile = file(filename, "r")
				data = imagefile.read()
				imagefile.close()

				loader = gtk.gdk.PixbufLoader()
				loader.write(data)
				loader.close()
				pixbuf = get_pixbuf_of_size(loader.get_pixbuf(), 64)

				self.photodata = data
				self.photodatatype = "B64"
				self.imageremoveButton.show()
				self.has_photo = True
			except:
				pixbuf = get_pixbuf_of_size_from_file(find_path("no-photo.png"), 64)
				self.imageremoveButton.hide()
				self.has_photo = False
			self.photoImage.set_from_pixbuf(pixbuf)

		dialog.destroy()
		gc.collect()

	def imageremoveButton_clicked(self, button):
		pixbuf = get_pixbuf_of_size_from_file(find_path("no-photo.png"), 64)
		self.photoImage.set_from_pixbuf(pixbuf)
		self.has_photo = False
		button.hide()

	def namechangeButton_clicked(self, button):
		def combo_changed(combo):
			index = combo.get_active()
			text = ""
			if index == 0:
				# simple name
				text += nameEntry1.get_text() + " "
				text += nameEntry2.get_text() + " "
				text += nameEntry3.get_text()
			elif index == 1:
				# full name
				text += nameEntry4.get_text() + " "
				text += nameEntry1.get_text() + " "
				text += nameEntry2.get_text() + " "
				text += nameEntry3.get_text() + " "
				text += nameEntry5.get_text()
			elif index == 2:
				# reverse name with comma
				text += nameEntry3.get_text() + ", "
				text += nameEntry1.get_text() + " "
				text += nameEntry2.get_text()
			elif index == 3:
				# reverse name
				text += nameEntry3.get_text() + " "
				text += nameEntry1.get_text() + " "
				text += nameEntry2.get_text()
			testEntry.set_text(text.replace("  ", " ").strip())

		dialog = self.tree.get_widget("namechangeDialog")
		dialog.set_default_response(gtk.RESPONSE_OK)

		combo = self.tree.get_widget("nameCombo")
		combo.set_active(1)
		combo.connect("changed", combo_changed)

		testEntry = self.tree.get_widget("testEntry")
		testEntry.connect("focus-in-event", lambda w,e: combo_changed(combo))

		nameEntry1 = self.tree.get_widget("nameEntry1")
		nameEntry2 = self.tree.get_widget("nameEntry2")
		nameEntry3 = self.tree.get_widget("nameEntry3")
		nameEntry4 = self.tree.get_widget("nameEntry4").child
		nameEntry5 = self.tree.get_widget("nameEntry5").child
		nameEntry6 = self.tree.get_widget("nameEntry6")
		nameEntry7 = self.tree.get_widget("nameEntry7")
		nameEntry8 = self.tree.get_widget("nameEntry8")

		if has_child(self.vcard, "n"):
			nameEntry1.set_text(self.vcard.n.value.given)
			nameEntry2.set_text(self.vcard.n.value.additional)
			nameEntry3.set_text(self.vcard.n.value.family)
			nameEntry4.set_text(self.vcard.n.value.prefix)
			nameEntry5.set_text(self.vcard.n.value.suffix)
		nameEntry6.set_text(unescape(self.vcard.getChildValue("nickname", "")))
		nameEntry7.set_text(unescape(self.vcard.getChildValue("title", "")))
		nameEntry8.set_text(unescape(self.vcard.getChildValue("org", "")))

		combo_changed(combo)
		nameEntry1.grab_focus()

		if dialog.run() == gtk.RESPONSE_OK:
			combo_changed(combo)

			if not has_child(self.vcard, "n"): self.vcard.add("n")
			self.vcard.n.value.given = nameEntry1.get_text().replace("  "," ").strip()
			self.vcard.n.value.additional = nameEntry2.get_text().replace("  "," ").strip()
			self.vcard.n.value.family = nameEntry3.get_text().replace("  "," ").strip()
			self.vcard.n.value.prefix = nameEntry4.get_text().replace("  "," ").strip()
			self.vcard.n.value.suffix = nameEntry5.get_text().replace("  "," ").strip()

			self.vcard.fn.value = escape(testEntry.get_text())

			if len(nameEntry6.get_text().replace("  "," ").strip()) > 0:
				if not has_child(self.vcard, "nickname"): self.vcard.add("nickname")
				self.vcard.nickname.value = escape(nameEntry6.get_text().replace("  "," ").strip())
			elif has_child(self.vcard, "nickname"): self.vcard.remove(self.vcard.nickname)

			if len(nameEntry7.get_text().replace("  "," ").strip()) > 0:
				if not has_child(self.vcard, "title"): self.vcard.add("title")
				self.vcard.title.value = escape(nameEntry7.get_text().replace("  "," ").strip())
			elif has_child(self.vcard, "title"): self.vcard.remove(self.vcard.title)

			if len(nameEntry8.get_text().replace("  "," ").strip()) > 0:
				if not has_child(self.vcard, "org"): self.vcard.add("org")
				self.vcard.org.value = escape(nameEntry8.get_text().replace("  "," ").strip())
			elif has_child(self.vcard, "org"): self.vcard.remove(self.vcard.org)

			text = "<span size=\"x-large\"><b>%s</b></span>" % unescape(self.vcard.fn.value)
			if has_child(self.vcard, "nickname"):
				text += " (<big>%s</big>)" % unescape(self.vcard.nickname.value)
			self.tree.get_widget("fullnameLabel").set_markup(text)

			if has_child(self.vcard, "title"):
				self.tree.get_widget("titleLabel").set_text(unescape(self.vcard.title.value))
			if has_child(self.vcard, "org"):
				self.tree.get_widget("orgLabel").set_text(unescape(self.vcard.org.value))
		else:
			self.check_if_new()

		dialog.hide()

	def contactData_change(self, model, path, iter):
		text = str(len(self.contactData))
		if text == 0: text = _("no contacts")
		elif text == 1: text += _(" contact")
		else: text += _(" contacts")
		self.tree.get_widget("countLabel").set_text(text)

	def contactList_clicked(self, *args):
		self.view_contact(True)

	def contactSelection_change(self, selection):
		selected = (self.contactSelection.count_selected_rows() > 0)

		self.tree.get_widget("contactMenuitem").set_property("visible", selected)
		self.tree.get_widget("importItem").set_property("visible", self.import_mode)

		if selected:
			self.view_contact()
		else:
			self.clear()

	def main(self):
		gtk.gdk.threads_enter()
		gtk.main()
		gtk.gdk.threads_leave()

#---------------
# Custom Widgets
#---------------
class CaptionField(gtk.HBox):
	def __init__(self, name, paramlist):
		gtk.HBox.__init__(self, False, 2)
		self.set_no_show_all(True)

		self.field = None
		self.content_name = name
		self.paramlist = paramlist

		# create type menus
		self.menu = gtk.Menu()
		if self.content_name == "TEL":
			for tel in tel_types:
				menuitem = gtk.MenuItem(types["HOME"] + " " + types[tel])
				menuitem.connect("activate", self.menuitem_click)
				self.menu.append(menuitem)
			for tel in tel_types:
				menuitem = gtk.MenuItem(types["WORK"] + " " +types[tel])
				menuitem.connect("activate", self.menuitem_click)
				self.menu.append(menuitem)
		elif self.content_name.startswith("X-"):
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

		self.removeButton = gtk.Button()
		self.removeButton.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
		self.removeButton.set_relief(gtk.RELIEF_NONE)
		if not self.content_name == "NOTE": self.pack_start(self.removeButton, False)

		self.labelButton = gtk.Button("")
		self.labelButton.set_relief(gtk.RELIEF_NONE)
		self.labelButton.set_alignment(1,0.5)
		self.pack_start(self.labelButton)

		self.label = gtk.Label()
		self.label.set_alignment(1,0.5)
		self.pack_start(self.label)

		if not self.content_name in ("NOTE", "BDAY", "URL"):
			self.labelButton.connect("clicked", self.popup)

		self.parse_paramlist()
		self.set_editable(False)
		self.show()

	def popup(self, *args):
		if self.labelButton.get_property("visible"):
			self.menu.popup(None, None, None, 1, 0)

	def set_editable(self, editable):
		self.removeButton.set_property("visible", editable)
		if not self.content_name == "NOTE":
			self.labelButton.set_property("visible", editable)
			self.label.set_property("visible", not editable)
		else:
			self.labelButton.hide()
			self.label.show()

		if self.field is not None:
			self.field.content.name = self.content_name
			self.field.content.type_paramlist = self.paramlist
			if self.field.get_text() == self.field.empty_text: self.field.set_text("")
			self.field.set_empty_text()
			self.field.entry.grab_focus()

	def menuitem_click(self, item):
		itemtext = item.get_child().get_text()
		newtype = []

		if itemtext.startswith(types["WORK"]): newtype.append("WORK")
		else: newtype.append("HOME")

		# if phone or im, check types for text
		if self.content_name == "TEL" or self.content_name.startswith("X-"):
			for key, value in types.iteritems():
				if value == itemtext.replace(types["HOME"], "").replace(types["WORK"], "").strip():
					# if im, change name
					if self.content_name.startswith("X-"):
						self.content_name = key
					else:
						newtype.append(key)
					break

		# preserve the other params
		for param in ("INTERNET", "X400", "DOM", "INTL", "POSTAL", "PARCEL", "PREF"):
			if param in self.paramlist: newtype.append(param)

		self.paramlist = newtype
		self.parse_paramlist()

	def parse_paramlist(self):
		text = types["HOME"]

		if "WORK" in self.paramlist: text = types["WORK"]

		if self.content_name.startswith("X-"): text = types[self.content_name]
		elif self.content_name == "BDAY": text = types["BDAY"]
		elif self.content_name == "URL": text = types["URL"]
		elif self.content_name == "NOTE": text = types["NOTE"]
		else:
			for tel in tel_types:
				if tel in self.paramlist:
					if tel == "FAX": text += " " + types["FAX"]
					elif tel == "CELL":
						if "WORK" in self.paramlist: text += " " + types["CELL"]
						else: text = types["CELL"]

		self.labelButton.get_child().set_markup("<b>%s</b>" % text)
		if self.content_name == "NOTE":
			self.label.set_markup("<span foreground=\"black\"><b>%s</b></span>" % text)
		else:
			self.label.set_markup("<span foreground=\"dim grey\"><b>%s</b></span>" % text)

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

		if use_content:
			if self.content.name in ("EMAIL", "URL"):
				self.eventbox = gtk.EventBox()
				self.eventbox.set_above_child(True)
				self.eventbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
				self.eventbox.add(self.label)
				self.eventbox.show()
				self.eventbox.connect("button-press-event", self.open_link)
				self.eventbox.connect("enter-notify-event", lambda w,e: self.get_toplevel().window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2)))
				self.eventbox.connect("leave-notify-event", lambda w,e: self.get_toplevel().window.set_cursor(None))
				self.link = True
				self.labelbox.pack_start(self.eventbox, False)
			else:
				self.link = False
				self.labelbox.add(self.label)
		else:
			self.link = False
			self.labelbox.add(self.label)

		sizegroup.add_widget(self.labelbox)

		self.entry = gtk.Entry()
		#self.entry.set_has_frame(False)
		self.entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		self.add(self.entry)
		sizegroup.add_widget(self.entry)

		self.show()
		self.label.show()
		self.entry.hide()

		if use_content:
			self.set_text(self.content.value)
			self.set_empty_text()
		else:
			self.set_text(self.content[0])
			self.empty_text = self.content[1]

		self.entry.connect("changed", self.entry_changed)
		self.entry.connect("focus-in-event", self.focus_changed, True)
		self.entry.connect("focus-out-event", self.focus_changed, False)

	def open_link(self, widget, event):
		if event.button == 1:
			url = self.get_text()
			if self.content.name  == "EMAIL":
				url = "mailto:" + url
			browser_load(url, self.get_toplevel())

	def set_empty_text(self):
		if self.content.name.startswith("X-"): type = "IM"
		elif self.content.name == "TEL":
			type = None
			for param in self.content.type_paramlist:
				if param in tel_types:
					type = param
					break
			if type is None: type =  "VOICE"
		else: type = self.content.name.upper()
		self.empty_text = types.get(type, "Empty")

	def set_text(self, text):
		if self.link:
			self.label.set_markup("<span foreground=\"blue\"><u>%s</u></span>" % text)
		else:
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

		text = self.get_text().strip()
		if self.use_content: self.content.value = text
		else: self.content[0] = text

	def set_autosize(self, autosize):
		self.autosize = autosize
		text = self.get_text().strip()
		if self.autosize: self.entry.set_width_chars(len(text))
		else: self.entry.set_width_chars(-1)

	def grab_focus(self):
		if self.entry.get_property("visible"): self.entry.grab_focus()
		else: self.label.grab_focus()

	def entry_changed(self, widget):
		text = self.get_text().strip()
		if self.autosize: self.entry.set_width_chars(len(text))
		if text == self.empty_text: text = ""

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

class AddressField(gtk.HBox):
	def __init__(self, content):
		gtk.HBox.__init__(self)

		self.set_no_show_all(True)

		self.content = content

		self.build_interface()

		self.set_editable(False)
		self.show()

	def build_interface(self):
		self.label = gtk.Label()
		self.label.set_alignment(0,0.5)
		self.label.set_selectable(True)
		self.add(self.label)

		self.table = gtk.Table()
		self.add(self.table)

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

		self.table.attach(self.street, 0, 3, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.table.attach(self.box, 0, 3, 1, 2, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.table.attach(self.country, 0, 3, 3, 4, gtk.EXPAND|gtk.FILL, gtk.FILL)

		# american
		self.table.attach(self.city, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
		self.table.attach(self.region, 1, 2, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.table.attach(self.code, 2, 3, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)

		# german, french
		#self.table.attach(self.code, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
		#self.table.attach(self.city, 1, 2, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)
		#self.table.attach(self.region, 2, 3, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)

	def set_editable(self, editable = False):
		self.label.set_property("visible", not editable)
		self.table.set_property("visible", editable)

		for widget in self.table.get_children():
			if type(widget) == LabelField:
				widget.set_editable(editable)

		self.content.value.box = self.box.content[0]
		self.content.value.extended = self.extended.content[0]
		self.content.value.street = self.street.content[0]
		self.content.value.city = self.city.content[0]
		self.content.value.region = self.region.content[0]
		self.content.value.code = self.code.content[0]
		self.content.value.country = self.country.content[0]

		self.label.set_text(str(self.content.value))

	def grab_focus(self):
		self.street.grab_focus()

class BirthdayField(gtk.HBox):
	def __init__(self, content, tooltips):
		gtk.HBox.__init__(self)

		self.content = content
		self.tooltips = tooltips

		self.build_interface()
		self.show_all()

		self.set_editable(False)

	def build_interface(self):
		self.label = gtk.Label()
		self.label.set_alignment(0,0.5)
		self.label.set_selectable(True)
		self.add(self.label)

		self.datebox = gtk.HBox()
		self.add(self.datebox)

		self.day = gtk.SpinButton(gtk.Adjustment(1, 1, 31, 1, 7), 1, 0)
		self.day.set_numeric(True)
		self.day.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		self.tooltips.set_tip(self.day, _('Day'))
		self.datebox.pack_start(self.day, False)

		self.month = gtk.SpinButton(gtk.Adjustment(1, 1, 12, 1, 3), 1, 0)
		self.month.set_numeric(True)
		self.month.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		self.tooltips.set_tip(self.month, _('Month'))
		self.datebox.pack_start(self.month, False)

		self.year = gtk.SpinButton(gtk.Adjustment(1950, 1900, 2100, 1, 10), 1, 0)
		self.year.set_numeric(True)
		self.year.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		self.tooltips.set_tip(self.year, _('Year'))
		self.datebox.pack_start(self.year, False)

		year, month, day = bday_from_value(self.content.value)

		if year is not None:
			self.day.set_value(day)
			self.month.set_value(month)
			self.year.set_value(year)

	def set_editable(self, editable):
		year = self.year.get_value_as_int()
		month = self.month.get_value_as_int()
		day = self.day.get_value_as_int()

		date = datetime.date(year, month, day)

		self.content.value = date.isoformat()
		self.label.set_markup("<span foreground=\"black\">%s</span>" % date.strftime("%x"))

		self.label.set_property("visible", not editable)
		self.datebox.set_property("visible", editable)

class EventVBox(gtk.VBox):
	def __init__(self):
		gtk.VBox.__init__(self)

		self.set_no_show_all(True)

		self.connect("add", self.add_event)
		self.connect("remove", self.remove_event)

	def add_event(self, container, widget):
		self.show()
		widget.show_all()

	def remove_event(self, container, widget):
		if len(self.get_children()) == 0: self.hide()

#--------------
# Helpfunctions
#--------------
def escape(s):
	s = s.replace(",", "\,")
	s = s.replace(";", "\;")
	s = s.replace("\n", "\\n")
	s = s.replace("\r", "\\r")
	s = s.replace("\t", "\\t")
	return s

def unescape(s):
	s = s.replace("\,", ",")
	s = s.replace("\;", ";")
	s = s.replace("\\n", "\n")
	s = s.replace("\\r", "\r")
	s = s.replace("\\t", "\t")
	return s

def entities(s):
	s = s.replace("<", "&lt;")
	s = s.replace(">", "&gt;")
	s = s.replace("&", "&amp;")
	s = s.replace("\"", "&quot;")
	return s

def bday_from_value(value):
	try:
		(y, m, d) = value.split("-", 2)
		d = d.split("T")
		if y.isdigit() and m.isdigit() and d[0].isdigit():
			year = int(y); month = int(m); day = int(d[0])
			if month >=1 and month <=12:
				if day >= 1 and day <=31:
					return (year, month, day)
	except:
		pass
	return (None, None, None)

def has_child(vcard, childName, childNumber = 0):
	try:
		return len(str(vcard.getChildValue(childName, "", childNumber))) > 0
	except:
		return False

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
						error_dialog = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, _("Unable to launch a suitable browser."))
						error_dialog.run()
						error_dialog.destroy()

def find_path(filename):
	dirs = (os.path.join(sys.prefix, filename),
			os.path.join(sys.prefix, "share", filename),
			os.path.join(sys.prefix, "share", "arkadas", filename),
			os.path.join(sys.prefix, "share", "pixmaps", filename),
			os.path.join(os.path.split(__file__)[0], filename),
			os.path.join(os.path.split(__file__)[0], "pixmaps", filename),
			os.path.join(os.path.split(__file__)[0], "share", filename),
			os.path.join(__file__.split("/lib")[0], "share", "pixmaps", filename),)
	for dir in dirs:
		if os.path.exists(dir):
			return dir
	return ""

def uuid():
	pipe = os.popen("uuidgen", "r")
	if pipe:
		data = pipe.readline().strip("\r\n")
		pipe.close()
	else:
		data = ""
	return data

if __name__ == "__main__":
	app = MainWindow()
	app.main()
