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

__version__ = "0.1"
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

import sys, os
import gtk, gobject, pango
# local
from Commons import *
import ContactEntry, ContactWindow

class MainWindow(gtk.Window):

	def __init__(self, width = 200, height = 400):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		self.set_title("Address Book")
		self.set_default_size( width , height )
		self.set_position(gtk.WIN_POS_CENTER)
		self.set_geometry_hints(self, width, height )

		self.set_icon_name("address-book")
		gtk.window_set_default_icon_name("stock_contact")

		self.connect("delete_event", self.delete_event)

		self.vbox = None

		self.build_interface()

	def delete_event(self, widget, event, data=None):
		sys.exit()
		return False

	def build_interface(self):
		actions = (
			("NewContact", gtk.STOCK_NEW, None, None, "Create a new contact", self.newButton_click),
			("DeleteContact", gtk.STOCK_DELETE, None, None, "Delete the selected contact", self.deleteButton_click),
			("Preferences", gtk.STOCK_PREFERENCES, None, None, "Configure the application", None),
			("About", gtk.STOCK_ABOUT, None, None, "About the application", self.about),
			("CopyName", gtk.STOCK_COPY, "_Copy Fullname", None, None, None),
			("CopyEmail", None, "Copy E_mail", None, None, None),
			("CopyNumber", None, "Copy N_umber", None, None, None),
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
		self.contactData = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
		self.contactData.set_sort_func(0, sort_contacts, None)
		self.contactData.set_sort_column_id(0, gtk.SORT_ASCENDING)
		self.contactList = gtk.TreeView(self.contactData)
		self.contactList.set_headers_visible(False)
		self.contactList.set_rules_hint(True)
		self.contactList.set_enable_search(True)
		self.contactList.set_search_equal_func(search_contacts)
		self.contactSelection = self.contactList.get_selection()
		scrolledwindow.add(self.contactList)

		# contactlist cellrenderers
		celltxt = gtk.CellRendererText()
		celltxt.set_property("ellipsize",pango.ELLIPSIZE_END)
		column = gtk.TreeViewColumn()
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
		
		self.contactSelection.select_iter(self.contactData.get_iter_first())
		self.contactList.grab_focus()

	#---------------
	# event funtions
	#---------------
	def view_contact(self, edit = False):
		if self.contactList.get_selection().count_selected_rows() > 0:
			(model, iter) = self.contactList.get_selection().get_selected()
			entry = model[iter][1]
			self.contactView.build_interface(entry, edit)
			self.contactView.show_all()

	def newButton_click(self, widget):
		pass

	def editButton_click(self, widget):
		self.view_contact(True)

	def deleteButton_click(self, widget):
		def dialog_response(dialog, response_id, entry):
			if response_id == gtk.RESPONSE_OK:
				try:
					 os.remove(entry.filename)
					 self.contactData.remove(entry.iter)
				except:
					pass
			dialog.destroy()

		if self.contactSelection.count_selected_rows() > 0:
			(model, iter) = self.contactSelection.get_selected()
			entry = model[iter][1]
			text = "<big><b>Remove Contact</b></big>\n\n"
			text += "You are about to remove <b>%s</b> from your contactlist.\nDo you want to continue?" % (entry.fullname)
			dialog = gtk.Dialog("Arkadas", self, gtk.DIALOG_MODAL)
			dialog.set_size_request(420, -1)
			dialog.set_resizable(False)
			dialog.set_has_separator(False)
			dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, "Delete Contact", gtk.RESPONSE_OK)
			dialoghbox = gtk.HBox()
			dialog.vbox.pack_start(dialoghbox, True, True, 6)
			# dialog image
			dialogimage = gtk.image_new_from_stock(gtk.STOCK_QUESTION, gtk.ICON_SIZE_DIALOG)
			dialogimage.set_alignment(0.5, 0)
			dialoghbox.pack_start(dialogimage, False, False, 10)
			# dialog label
			dialoglabel = gtk.Label()
			dialoglabel.set_markup(text)
			dialoglabel.set_line_wrap(True)
			dialoghbox.pack_start(dialoglabel)
			dialog.connect("response",dialog_response, entry)
			dialog.show_all()

	def contactList_click(self, treeview, path, column):
		self.view_contact()

	def contactList_press(self, widget, event):
		if event.button == 3:
			self.uiManager.get_widget("/Itemmenu").popup(None, None, None, event.button, event.time)

	def contactList_popup_menu(self, widget):
		self.uiManager.get_widget("/Itemmenu").popup(None, None, None, 3, 0)

	def contactSelection_change(self, selection):
		x, y, width, height = self.get_allocation()
		self.view_contact()
		if selection.count_selected_rows() > 0:
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
		aboutdialog.set_comments("A lightweight GTK+ Contact-Manager based on vCards.")
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
	if os.path.exists(path) == False:
		os.mkdir(path)

	model.clear()

	for file in os.listdir(path):
		if file[-3:] != "vcf": continue

		entry = ContactEntry.Entry()

		if entry.get_dict_from_file(os.path.join(path,file)):
			entry.get_entries_from_dict()

			iter = model.append([entry.fullname, entry])
			entry.iter = iter

# weird sort stuff
def sort_contacts(model, iter1, iter2, data):
	entry1 = model[iter1][1] ; entry2 = model[iter2][1]
	f1 = "" ; f2 = ""
	if entry1 and entry2:
		for i in (0,4,3,1,2):
			f1 += entry1.name[i].strip() + " "
			f2 += entry2.name[i].strip() + " "
		return cmp(f1.strip().replace("  "," "),f2.strip().replace("  "," "))
	return 0

def search_contacts(model, column, key, iter):
	fullname = model[iter][0]
	if key.lower() in fullname.lower():
		return False
	return True
