__author__ = "Paul Johnson"
__email__ = "thrillerator@googlemail.com"
__version__ = "0.8"
__license__ = """Copyright 2007 Paul Johnson <thrillerator@googlemail.com>

This file is part of Arkadas.

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

import sys, os, vobject
import gtk, gobject, pango

types = {
	"HOME":_("Home"), "WORK":_("Work"),
	"BDAY":_("Birthday"), "URL":_("Website"),
	"EMAIL":"Email", "ADR":_("Address"),
	"IM":_("Username"), "IM2":"Instant Messaging",
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
class MainWindow(gtk.Window):

	def __init__(self, width=200, height=400):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		self.set_title(_("Address Book"))
		self.set_default_size(width, height)
		self.set_position(gtk.WIN_POS_CENTER)
		self.set_geometry_hints(self, width, height)

		gtk.window_set_default_icon_name("address-book")

		self.connect("delete_event", self.delete_event)

		self.vbox = None

		self.build_interface()
		self.show_all()

	def delete_event(self, widget, event, data=None):
		sys.exit()
		return False

	def build_interface(self):
		actions = (
			("NewContact", gtk.STOCK_NEW, None, None, _("Create a new contact"), self.newButton_click),
			("DeleteContact", gtk.STOCK_DELETE, None, None, _("Delete the selected contact"), self.deleteButton_click),
			("Preferences", gtk.STOCK_PREFERENCES, None, None, _("Configure the application"), None),
			("About", gtk.STOCK_ABOUT, None, None, _("About the application"), self.about),
			("CopyName", gtk.STOCK_COPY, _("_Copy Fullname"), None, None, lambda w: self.copy_click(w, "fn")),
			("CopyEmail", None, _("Copy E_mail"), None, None, lambda w: self.copy_click(w, "email")),
			("CopyNumber", None, _("Copy N_umber"), None, None, lambda w: self.copy_click(w, "tel")),
			)

		uiDescription = """
			<ui>
			 <toolbar name="Toolbar">
			  <toolitem action="NewContact"/>
			  <toolitem action="DeleteContact"/>
			  <separator name="ST1"/>
			  <toolitem action="Preferences"/>
			 </toolbar>
			 <popup name="Itemmenu">
			  <menuitem action="NewContact"/>
			  <menuitem action="DeleteContact"/>
			  <separator name="SM1"/>
			  <menuitem action="CopyName"/>
			  <menuitem action="CopyEmail"/>
			  <menuitem action="CopyNumber"/>
			  <separator name="SM2"/>
			  <menuitem action="Preferences"/>
			  <menuitem action="About"/>
			 </popup>
			</ui>
			"""

		# UIManager
		self.uiManager = gtk.UIManager()
		self.uiManager.add_ui_from_string(uiDescription)
		self.add_accel_group(self.uiManager.get_accel_group())

		actionGroup = gtk.ActionGroup("Actions")
		actionGroup.add_actions(actions)
		self.uiManager.insert_action_group(actionGroup, 0)

		self.tooltips = gtk.Tooltips()
		self.clipboard = gtk.Clipboard()

		self.vbox = gtk.VBox()
		self.add(self.vbox)

		# toolbar
		self.toolbar = self.uiManager.get_widget("/Toolbar")
		self.vbox.pack_start(self.toolbar,False,False)

		# paned
		hpaned = gtk.HPaned()
		hpaned.set_border_width(6)
		self.vbox.pack_start(hpaned)

		scrolledwindow = gtk.ScrolledWindow()
		scrolledwindow.unset_flags(gtk.CAN_FOCUS)
		scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		scrolledwindow.set_shadow_type(gtk.SHADOW_IN)
		scrolledwindow.set_size_request(200, -1)
		hpaned.add1(scrolledwindow)

		# contactlist
		self.contactData = gtk.ListStore(str, gobject.TYPE_PYOBJECT)
		self.contactData.set_sort_func(0, sort_contacts, None)
		self.contactData.set_sort_column_id(0, gtk.SORT_ASCENDING)
		self.contactList = gtk.TreeView(self.contactData)
		self.contactList.set_headers_visible(False)
		self.contactList.set_rules_hint(True)
		self.contactList.set_enable_search(True)
		self.contactSelection = self.contactList.get_selection()
		scrolledwindow.add(self.contactList)

		# contactlist cellrenderers
		cellimg = gtk.CellRendererPixbuf()
		cellimg.set_property("icon-name", "stock_contact")
		celltxt = gtk.CellRendererText()
		celltxt.set_property("ellipsize", pango.ELLIPSIZE_END)
		column = gtk.TreeViewColumn()
		column.pack_start(cellimg, False)
		column.pack_start(celltxt)
		column.add_attribute(celltxt,"text", 0)
		column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self.contactList.append_column(column)

		self.vbox.show_all()

		# contactview
		self.contactView = ContactWindow(self)
		self.contactView.hide()
		self.view_visible = False
		hpaned.add2(self.contactView)

		# events
		self.contactList.connect("row-activated", self.contactList_click)
		self.contactList.connect("button-press-event", self.contactList_press)
		self.contactList.connect("popup-menu", self.contactList_popup_menu)
		self.contactSelection.connect("changed", self.contactSelection_change)

		load_contacts(os.path.expanduser("~/Contacts"), self.contactData)

		first_iter = self.contactData.get_iter_first()
		if first_iter is not None:
			self.contactSelection.select_iter(first_iter)

		self.contactList.grab_focus()

	#---------------
	# event funtions
	#---------------
	def view_contact(self, edit = False):
		if self.contactList.get_selection().count_selected_rows() > 0:
			(model, iter) = self.contactList.get_selection().get_selected()
			vcard = model[iter][1]
			if self.contactView.table is not None:
				if self.contactView.saveButton.get_property("visible"):
					text = "<big><b>%s</b></big>" % _("Save the changes to contact before closing?")
					sec_text = _("If you don't save, changes you made to <b>%s</b> will be permanently lost.") % unescape(self.contactView.vcard.fn.value)

					msgbox = gtk.MessageDialog(self, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE)
					msgbox.set_title("Arkadas")
					msgbox.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)
					msgbox.set_markup(text)
					msgbox.format_secondary_markup(sec_text)

					if msgbox.run() == gtk.RESPONSE_OK:
						self.contactView.switch_mode(False, True)
					msgbox.destroy()
				self.contactView.table.destroy()
			self.contactView.build_interface(vcard, edit)
			self.contactView.show_all()

	def newButton_click(self, widget):
		vcard = vobject.vCard()
		vcard.add("n")
		vcard.add("fn")
		vcard.add("tel")
		vcard.add("email")
		vcard.add("url")
		vcard.tel.type_paramlist = ["HOME", "VOICE", "PREF"]
		vcard.email.type_paramlist = ["HOME", "INTERNET", "PREF"]
		vcard.iter = self.contactData.append(["Unbekannt", vcard])
		self.contactSelection.select_iter(vcard.iter)
		self.view_contact(True)
		self.contactView.changeButton_click(None)

	def deleteButton_click(self, widget):
		if self.contactSelection.count_selected_rows() > 0:
			(model, iter) = self.contactSelection.get_selected()
			fullname = model[iter][0]
			filename = model[iter][1].filename

			text = "<big><b>%s</b></big>" % _("Remove Contact")
			sec_text = _("You are about to remove <b>%s</b> from your contactlist.\nDo you want to continue?") % (fullname)

			msgbox = gtk.MessageDialog(self, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE)
			msgbox.set_title("Arkadas")
			msgbox.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, "Delete Contact", gtk.RESPONSE_OK)
			msgbox.set_markup(text)
			msgbox.format_secondary_markup(sec_text)

			if msgbox.run() == gtk.RESPONSE_OK:
				try:
					 os.remove(filename)
					 self.contactData.remove(iter)
				except:
					pass
			msgbox.destroy()

	def about(self, widget):
		def close_about(event, data=None):
			aboutdialog.hide()
			return True

		def show_website(dialog, blah, link):
			webbrowser.open_new(link)

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
		aboutdialog.set_authors(["Paul Johnson <thrillerator@googlemail.com>","Erdem Cakir <deejayrdm@gmail.com>"])
		#aboutdialog.set_translator_credits("de - Paul Johnson <thrillerator@googlemail.com>")
		gtk.about_dialog_set_url_hook(show_website, "http://arkadas.berlios.de")
		aboutdialog.set_website_label("http://arkadas.berlios.de")
		large_icon = gtk.gdk.pixbuf_new_from_file("arkadas.png")
		aboutdialog.set_logo(large_icon)
		aboutdialog.connect("response", close_about)
		aboutdialog.connect("delete_event", close_about)
		aboutdialog.show_all()

	def copy_click(self, widget, name):
		(model, iter) = self.contactList.get_selection().get_selected()
		vcard = model[iter][1]
		value = vcard.getChildValue(name)
		if value is not None:
			if name == "fn": value = unescape(value)
			self.clipboard.set_text(value)

	def contactList_click(self, treeview, path, column):
		self.view_contact(True)

	def contactList_press(self, widget, event):
		if event.button == 3:
			self.uiManager.get_widget("/Itemmenu").popup(None, None, None, event.button, event.time)

	def contactList_popup_menu(self, widget):
		self.uiManager.get_widget("/Itemmenu").popup(None, None, None, 3, 0)

	def contactSelection_change(self, selection):
		x, y, width, height = self.get_allocation()
		if selection.count_selected_rows() > 0:
			self.view_contact()
			if not self.view_visible:
				self.resize(600, height)
				self.contactView.show()
				self.view_visible = True
			self.uiManager.get_widget("/Itemmenu/DeleteContact").show()
			self.uiManager.get_widget("/Itemmenu/CopyName").show()
			self.uiManager.get_widget("/Itemmenu/CopyEmail").show()
			self.uiManager.get_widget("/Itemmenu/CopyNumber").show()
		else:
			if self.view_visible:
				self.resize(200, height)
				self.contactView.hide()
				self.view_visible = False
			self.uiManager.get_widget("/Itemmenu/DeleteContact").hide()
			self.uiManager.get_widget("/Itemmenu/CopyName").hide()
			self.uiManager.get_widget("/Itemmenu/CopyEmail").hide()
			self.uiManager.get_widget("/Itemmenu/CopyNumber").hide()

	def main(self):
		gtk.main()

if __name__ == "__main__":
	app = MainWindow()
	app.main()

#--------------------
# Class ContactWindow
#--------------------
class ContactWindow(gtk.VBox):

	def __init__(self, parent):
		gtk.VBox.__init__(self, False, 6)

		self.new_parent = parent
		self.tooltips = parent.tooltips

		self.vcard = None
		self.table = None
		self.color = gtk.gdk.color_parse("white")

		# display
		self.scrolledwindow = gtk.ScrolledWindow()
		self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		self.pack_start(self.scrolledwindow)

		self.hsizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

		# buttons
		self.buttonbox = gtk.HBox(False, 6)
		self.pack_end(self.buttonbox, False)

		self.addButton = gtk.Button("", gtk.STOCK_ADD)
		self.addButton.set_sensitive(False)
		self.addButton.set_no_show_all(True)
		self.addButton.show()
		self.addButton.get_child().get_child().get_children()[1].hide()
		self.addButton.connect("clicked", self.addButton_click)
		self.buttonbox.pack_start(self.addButton, False)

		self.buttonbox.pack_start(gtk.Label())

		self.saveButton = gtk.Button("", gtk.STOCK_SAVE)
		self.saveButton.set_no_show_all(True)
		self.saveButton.connect("clicked", self.saveButton_click)
		self.buttonbox.pack_start(self.saveButton, False)

		self.editButton = gtk.Button("", gtk.STOCK_EDIT)
		self.editButton.set_no_show_all(True)
		self.editButton.connect("clicked", self.editButton_click)
		self.buttonbox.pack_start(self.editButton, False)

	def build_interface(self, new_vcard, edit=False):
		self.vcard = new_vcard

		self.table = gtk.VBox(False, 10)
		self.table.set_border_width(10)
		self.table.set_no_show_all(True)
		self.scrolledwindow.add_with_viewport(self.table)
		self.scrolledwindow.get_child().modify_bg(gtk.STATE_NORMAL,self.color)

		self.photohbox = gtk.HBox(False, 2)
		self.emailbox = EventVBox()
		self.workemailbox = EventVBox()
		self.telbox = EventVBox()
		self.worktelbox = EventVBox()
		self.imbox = EventVBox()
		self.workadrbox = EventVBox()
		self.urlbox = EventVBox()
		self.adrbox = EventVBox()
		self.bdaybox = EventVBox()
		self.notebox = EventVBox()

		self.table.pack_start(self.photohbox, False)
		self.table.pack_start(gtk.Label())

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

		self.table.pack_start(gtk.Label())
		self.table.pack_start(self.notebox, False)

		# FIELD - photo
		if has_child(self.vcard, "photo"):
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
				pixbuf = get_pixbuf_of_size(loader.get_pixbuf(), 64, True)
				self.hasphoto = True
			except:
				pixbuf = get_pixbuf_of_size_from_file("no-photo.png", 64)
				self.hasphoto = False
		else:
			pixbuf = get_pixbuf_of_size_from_file("no-photo.png", 64)
			self.hasphoto = False

		hbox = gtk.HBox()
		self.hsizegroup.add_widget(hbox)
		self.photohbox.pack_start(hbox,False)

		eventbox = gtk.EventBox()
		eventbox.connect("enter-notify-event", lambda w,e: self.get_toplevel().window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2)))
		eventbox.connect("leave-notify-event", lambda w,e: self.get_toplevel().window.set_cursor(None))
		self.tooltips.set_tip(eventbox, _("Click to change image"))
		hbox.pack_end(eventbox, False)

		photo = gtk.Image()
		photo.set_from_pixbuf(pixbuf)
		eventbox.add(photo)

		titlevbox = gtk.VBox()
		self.photohbox.pack_start(titlevbox, True, True, 2)

		# FIELD - fullname & nickname
		fullname = gtk.Label()
		text = "<span size=\"x-large\"><b>%s</b></span>" % unescape(self.vcard.fn.value)
		if has_child(self.vcard, "nickname"):
			text += " (<big>%s</big>)" % unescape(self.vcard.nickname.value)
		fullname.set_markup(text)
		fullname.set_alignment(0,0)
		fullname.set_selectable(True)
		titlevbox.pack_start(fullname)

		# FIELD - title & org
		text = ""
		org = gtk.Label()
		if has_child(self.vcard, "title"):
			text += unescape(self.vcard.title.value)
		if has_child(self.vcard, "org"):
			text += "\n" + unescape(self.vcard.org.value)
		org.set_text(text)
		org.set_alignment(0,0)
		org.set_selectable(True)
		titlevbox.pack_start(org)

		self.changeButton = gtk.Button()
		self.changeButton.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU))
		self.changeButton.set_no_show_all(True)
		self.changeButton.set_property("visible", edit)
		self.changeButton.connect("clicked", self.changeButton_click)
		self.tooltips.set_tip(self.changeButton, _("Click to change fullname"))
		self.photohbox.pack_start(self.changeButton, False)

		self.photohbox.show_all()

		# FIELD - tel
		self.add_labels_by_name(self.telbox, self.worktelbox, "tel")
		# FIELD - emails
		self.add_labels_by_name(self.emailbox, self.workemailbox, "email")
		# FIELD - web
		if has_child(self.vcard, "url"):
			for child in self.vcard.contents["url"]:
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
		self.notebox.add(gtk.HSeparator())
		self.notebox.set_spacing(4)
		if not has_child(self.vcard, "note"): self.vcard.add("note")
		self.add_label(self.notebox, self.vcard.note)

		self.table.set_no_show_all(True)
		self.table.show()

		self.switch_mode(edit)



	#---------------
	# event funtions
	#---------------
	def addButton_click(self, button):
		# create type menus
		self.addMenu = gtk.Menu()
		for name in ("TEL", "EMAIL", "ADR", "URL", "IM2", "BDAY"):
			if not name in ("BDAY", "IM2"):
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
		elif name == "IM2":
			content = self.vcard.add("x-aim")
			content.type_paramlist = ["HOME"]
			box = self.add_label(self.imbox, content)
		elif name == "BDAY":
			content = self.vcard.add("bday")
			box = self.add_label(self.bdaybox, content)

		caption, field = box.get_children()[0].get_children()[0], box.get_children()[1]
		caption.set_editable(True)
		field.set_editable(True)
		field.grab_focus()

	def saveButton_click(self, button):
		self.switch_mode(False, True)

	def editButton_click(self, button):
		self.switch_mode(True, False)

	def changeButton_click(self, button):
		def add_label(text):
			label = gtk.Label(text)
			label.set_alignment(1, 0.5)
			label.set_padding(4, 0)
			label.set_use_underline(True)
			return label

		def combo_changed(combo):
			index = combo.get_active()
			text = ""
			if index == 0:
				# simple name
				text += entry1.get_text() + " "
				text += entry2.get_text() + " "
				text += entry3.get_text()
			elif index == 1:
				# full name
				text += entry4.get_text() + " "
				text += entry1.get_text() + " "
				text += entry2.get_text() + " "
				text += entry3.get_text() + " "
				text += entry5.get_text()
			elif index == 2:
				# reverse name with comma
				text += entry3.get_text() + ", "
				text += entry1.get_text() + " "
				text += entry2.get_text()
			elif index == 3:
				# reverse name
				text += entry3.get_text() + " "
				text += entry1.get_text() + " "
				text += entry2.get_text()
			testlabel.set_text(text.replace("  ", " ").strip())

		def dialog_response(dialog, response_id):
			if response_id == gtk.RESPONSE_OK:
				combo_changed(combo)

				if not has_child(self.vcard, "n"): self.vcard.add("n")
				self.vcard.n.value.given = entry1.get_text().replace("  "," ").strip()
				self.vcard.n.value.additional = entry2.get_text().replace("  "," ").strip()
				self.vcard.n.value.family = entry3.get_text().replace("  "," ").strip()
				self.vcard.n.value.prefix = entry4.get_text().replace("  "," ").strip()
				self.vcard.n.value.suffix = entry5.get_text().replace("  "," ").strip()

				self.vcard.fn.value = escape(testlabel.get_text())

				if len(entry6.get_text().replace("  "," ").strip()) > 0:
					if not has_child(self.vcard, "nickname"): self.vcard.add("nickname")
					self.vcard.nickname.value = escape(entry6.get_text().replace("  "," ").strip())
				elif has_child(self.vcard, "nickname"): self.vcard.remove(self.vcard.nickname)

				if len(entry7.get_text().replace("  "," ").strip()) > 0:
					if not has_child(self.vcard, "title"): self.vcard.add("title")
					self.vcard.title.value = escape(entry7.get_text().replace("  "," ").strip())
				elif has_child(self.vcard, "title"): self.vcard.remove(self.vcard.title)

				if len(entry8.get_text().replace("  "," ").strip()) > 0:
					if not has_child(self.vcard, "org"): self.vcard.add("org")
					self.vcard.org.value = escape(entry8.get_text().replace("  "," ").strip())
				elif has_child(self.vcard, "org"): self.vcard.remove(self.vcard.org)

				box = self.photohbox.get_children()[1]
				fullname, org = box.get_children()

				text = "<span size=\"x-large\"><b>%s</b></span>" % unescape(self.vcard.fn.value)
				if has_child(self.vcard, "nickname"):
					text += " (<big>%s</big>)" % unescape(self.vcard.nickname.value)
				fullname.set_markup(text)

				text = ""
				if has_child(self.vcard, "title"):
					text += unescape(self.vcard.title.value)
				if has_child(self.vcard, "org"):
					text += "\n" + unescape(self.vcard.org.value)
				org.set_text(text)

			dialog.destroy()

		dialog = gtk.Dialog(_("Change Name"), self.new_parent, gtk.DIALOG_MODAL)
		dialog.set_resizable(False)
		#dialog.set_size_request(420, -1)
		dialog.set_has_separator(False)
		dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_APPLY, gtk.RESPONSE_OK)
		# dialog table
		table = gtk.Table(13, 2)
		table.set_border_width(6)
		dialog.vbox.add(table)

		table.attach(add_label(_("_Given name:")), 0, 1, 0, 1)
		entry1 = gtk.Entry() ; table.attach(entry1, 1, 2, 0, 1)

		table.attach(add_label(_("_Additional names:")), 0, 1, 1, 2)
		entry2 = gtk.Entry() ; table.attach(entry2, 1, 2, 1, 2)

		table.attach(add_label(_("_Family names:")), 0, 1, 2, 3)
		entry3 = gtk.Entry() ; table.attach(entry3, 1, 2, 2, 3)

		table.attach(gtk.Label(), 0, 2, 3, 4)

		table.attach(add_label(_("_Prefixes:")), 0, 1, 4, 5)
		entry4 = gtk.Entry() ; table.attach(entry4, 1, 2, 4, 5)

		table.attach(add_label(_("_Suffixes:")), 0, 1, 5, 6)
		entry5 = gtk.Entry() ; table.attach(entry5, 1, 2, 5, 6)

		table.attach(gtk.Label(), 0, 3, 6, 7)

		table.attach(add_label(_("For_matted name:")), 0, 1, 7, 8)

		combo = gtk.combo_box_new_text()
		combo.append_text(_("Simple Name"))
		combo.append_text(_("Full Name"))
		combo.append_text(_("Reverse Name with Comma"))
		combo.append_text(_("Reverse Name"))
		combo.connect("changed", combo_changed)
		table.attach(combo, 1, 2, 7, 8)

		testlabel = gtk.Entry()
		testlabel.set_editable(False)
		table.attach(testlabel, 1, 2, 8, 9)

		table.attach(gtk.HSeparator(), 0, 2, 9, 10, ypadding=6)

		table.attach(add_label(_("_Nickname:")), 0, 1, 10, 11)
		entry6 = gtk.Entry() ; table.attach(entry6, 1, 2, 10, 11)

		table.attach(add_label(_("_Title/Role:")), 0, 1, 11, 12)
		entry7 = gtk.Entry() ; table.attach(entry7, 1, 2, 11, 12)

		table.attach(add_label(_("_Organization:")), 0, 1, 12, 13)
		entry8 = gtk.Entry() ; table.attach(entry8, 1, 2, 12, 13)

		if has_child(self.vcard, "n"):
			entry1.set_text(self.vcard.n.value.given)
			entry2.set_text(self.vcard.n.value.additional)
			entry3.set_text(self.vcard.n.value.family)
			entry4.set_text(self.vcard.n.value.prefix)
			entry5.set_text(self.vcard.n.value.suffix)
		entry6.set_text(unescape(self.vcard.getChildValue("nickname", "")))
		entry7.set_text(unescape(self.vcard.getChildValue("title", "")))
		entry8.set_text(unescape(self.vcard.getChildValue("org", "")))

		combo.set_active(1)
		combo_changed(combo)

		# events
		dialog.connect("response", dialog_response)
		dialog.show_all()

	def switch_mode(self, state=False, save=False):
		self.addButton.set_sensitive(state)
		self.saveButton.set_property("visible", state)
		self.editButton.set_property("visible", not state)
		self.changeButton.set_property("visible", state)

		if save:
			import os, vobject
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

			if self.hasphoto:
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
						# get caption & field
						caption, field = hbox.get_children()[0].get_children()[0], hbox.get_children()[1]
						caption.set_editable(state)

						if type(field) == LabelField:
							field.set_editable(state)
							# remove empty field
							if field.get_text() == "":
								hbox.destroy()
								continue
							if save:
								new_vcard.add(field.content)
						elif type(field) == AddressField:
							field.set_editable(state)
							# remove empty field
							if str(field.content.value).strip().replace(",", "") == "":
								hbox.destroy()
								continue
							if save:
								new_vcard.add(field.content)
						elif type(field) == gtk.TextView:
							field.set_editable(state)
							textbuffer = field.get_buffer()
							start, end = textbuffer.get_bounds()
							text = textbuffer.get_text(start, end).strip()
							if save and len(text) > 0:
								new_vcard.add("note")
								new_vcard.note.value = escape(text)

		if save:
			try:
				iter = self.vcard.iter
				path = os.path.expanduser("~/Contacts")
				filename = os.path.join(path, unescape(self.vcard.fn.value) + ".vcf")

				if not filename == self.vcard.filename:
					os.remove(self.vcard.filename)

				new_file = open(filename, "w")
				new_file.write(new_vcard.serialize())
				new_file.close()

				self.vcard = new_vcard

				self.vcard.filename = filename
				self.vcard.iter = iter
				self.new_parent.contactData.set(self.vcard.iter, 0, unescape(self.vcard.fn.value), 1, self.vcard)
			except:
				raise

	def add_labels_by_name(self, box, workbox, name):
		if has_child(self.vcard, name):
			for child in self.vcard.contents[name]:
				if "WORK" in child.type_paramlist: self.add_label(workbox, child)
				else: self.add_label(box, child)

	def add_label(self, box, content):
		hbox = gtk.HBox(False, 4)

		# caption
		captionbox = gtk.VBox()
		caption = CaptionField(content)
		caption.removeButton.connect_object("clicked", gtk.Widget.destroy, hbox)
		captionbox.pack_start(caption, False)
		hbox.pack_start(captionbox, False)
		self.hsizegroup.add_widget(caption)

		if content.name == "ADR":
			field = AddressField(content)
		elif content.name == "NOTE":
			# multiline label
			textbuffer = gtk.TextBuffer()
			textbuffer.set_text(unescape(content.value))
			field = gtk.TextView(textbuffer)
			field.set_wrap_mode(gtk.WRAP_WORD)
			field.set_editable(False)
		else:
			# LabelEntry
			field = LabelField(content)
			field.set_editable(False)
			caption.set_field(field)

		hbox.pack_start(field)
		box.add(hbox)
		return hbox

#---------------
# Custom Widgets
#---------------
class CaptionField(gtk.HBox):
	def __init__(self, content):
		gtk.HBox.__init__(self, False, 2)
		self.set_no_show_all(True)

		self.field = None
		self.content = content
		self.sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_VERTICAL)

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

		self.removeButton = gtk.Button()
		self.removeButton.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
		self.removeButton.set_relief(gtk.RELIEF_NONE)
		if not self.content.name == "NOTE": self.pack_start(self.removeButton, False)

		self.labelButton = gtk.Button("")
		self.labelButton.set_relief(gtk.RELIEF_NONE)
		self.labelButton.set_alignment(1,0.5)
		self.pack_start(self.labelButton)

		self.label = gtk.Label()
		self.label.set_alignment(1,0.5)
		self.label.set_sensitive(False)
		self.sizegroup.add_widget(self.label)
		self.pack_start(self.label)

		if not self.content.name in ("NOTE", "BDAY", "URL"):
			self.labelButton.connect("clicked", self.popup)

		self.parse_paramlist()
		self.set_editable(False)
		self.show()

	def popup(self, *args):
		if self.labelButton.get_property("visible"):
			self.menu.popup(None, None, None, 1, 0)

	def set_field(self, field):
		self.field = field
		self.sizegroup.add_widget(field)

	def set_editable(self, editable):
		self.removeButton.set_property("visible", editable)
		if not self.content.name == "NOTE":
			self.labelButton.set_property("visible", editable)
			self.label.set_property("visible", not editable)
		else:
			self.label.set_property("sensitive", editable)
			self.label.show()

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

		self.labelButton.get_child().set_markup("<b>%s</b>" % text)
		self.label.set_markup("<b>%s</b>" % text)

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
		if self.content.name in ("EMAIL", "URL"):
			self.label = gtk.LinkButton("")
			self.label.set_alignment(0,0.5)
			self.label.set_relief(gtk.RELIEF_NORMAL)
			if self.content.name  == "EMAIL":
				self.label.connect("clicked", lambda b: browser_load("mailto:" + self.content.value, self.get_toplevel()))
			else:
				self.label.connect("clicked", lambda b: browser_load(self.content.value, self.get_toplevel()))
			self.link = True
		else:
			self.label = gtk.Label()
			self.label.set_selectable(True)
			self.label.set_alignment(0,0.5)
			self.label.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
			self.link = False

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
		if self.link:
			self.label.set_label(text)
			self.label.set_uri(text)
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

	def grab_focus(self):
		self.street.grab_focus()

class EventVBox(gtk.VBox):
	def __init__(self):
		gtk.VBox.__init__(self)

		self.connect("add", self.add_event)
		self.connect("remove", self.remove_event)

	def add_event(self, container, widget):
		self.show_all()

	def remove_event(self, container, widget):
		if len(self.get_children()) == 0: self.hide_all()

#--------------
# Helpfunctions
#--------------
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

def load_contacts(path, model):
	# make path if dont exists
	if os.path.exists(path) == False: os.mkdir(path)
	# clear all entrys
	model.clear()
	# read all files in folder
	for file in os.listdir(path):
		filename = os.path.join(path, file)
		components = vobject.readComponents(open(filename, "r"))
		while(True):
			try:
				# create vcard-object
				vcard = components.next()
				vcard.filename = filename
				add_to_list(model, vcard)
			except:
				break

def add_to_list(model, vcard):
	# get fullname, else make fullname from name
	if not has_child(vcard, "fn"):
		fn = ""
		n = vcard.n.value.split(";")
		for i in (3,1,2,0,4):
			fn += n[i].strip() + " "
		vcard.add("fn")
		vcard.fn.value = fn.replace("  "," ").strip()
	vcard.iter = model.append([vcard.fn.value, vcard])

# weird sort stuff
def sort_contacts(model, iter1, iter2, data):
	vcard1 = model[iter1][1]
	vcard2 = model[iter2][1]
	if type(vcard1) == vobject.base.Component and type(vcard2) == vobject.base.Component:
		if vcard1.version.value == "3.0":
			f1 = vcard1.n.value.family + " " + vcard1.n.value.given + " " + vcard1.n.value.additional
		else:
			n = vcard1.n.value.split(";")
			f1 = n[0] + " " + n[1] + " " + n[2]

		if vcard2.version.value == "3.0":
			f2 = vcard2.n.value.family + " " + vcard2.n.value.given + " " + vcard2.n.value.additional
		else:
			n = vcard2.n.value.split(";")
			f2 = n[0] + " " + n[1] + " " + n[2]

		return cmp(f1.replace("  "," ").strip(), f2.replace("  "," ").strip())
	else:
		return 0

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
						error_dialog = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, _("Unable to launch a suitable browser."))
						error_dialog.run()
						error_dialog.destroy()

def uuid():
	import os
	pipe = os.popen('uuidgen', 'r')
	if pipe:
		data = pipe.readline().strip("\r\n")
		pipe.close()
	else:
		date = ""
	return data
