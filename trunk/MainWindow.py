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

import sys, os, vobject
import gtk, gobject, pango
from Commons import *
import ContactWindow

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

	def delete_event(self, widget, event, data=None):
		sys.exit()
		return False

	def build_interface(self):
		actions = (
			("NewContact", gtk.STOCK_NEW, None, None, _("Create a new contact"), self.newButton_click),
			("DeleteContact", gtk.STOCK_DELETE, None, None, _("Delete the selected contact"), self.deleteButton_click),
			("Preferences", gtk.STOCK_PREFERENCES, None, None, _("Configure the application"), None),
			("About", gtk.STOCK_ABOUT, None, None, _("About the application"), self.about),
			("CopyName", gtk.STOCK_COPY, _("_Copy Fullname"), None, None, None),
			("CopyEmail", None, _("Copy E_mail"), None, None, None),
			("CopyNumber", None, _("Copy N_umber"), None, None, None),
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
		self.contactView = ContactWindow.ContactWindow(self)
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
		vcard.tel.type_paramlist = ["HOME", "VOICE"]
		vcard.email.type_paramlist = ["HOME"]
		vcard.url.type_paramlist = ["HOME", "INTERNET"]
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

#--------------
# help funtions
#--------------
def load_contacts(path, model):
	# make path if dont exists
	if os.path.exists(path) == False: os.mkdir(path)
	# clear all entrys
	model.clear()
	# read all files in folder
	for file in os.listdir(path):
		filename = os.path.join(path, file)
		components = vobject.readComponents(open(filename, "r"), False, True, True)
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
	f1 = "" ; f2 = ""
	try:
		f1 += vcard1.n.value.family
		f1 += " " + vcard1.n.value.given
		f2 += vcard2.n.value.family
		f2 += " " + vcard2.n.value.given
		return cmp(f1.strip().replace("  "," "),f2.strip().replace("  "," "))
	except:
		return 1
