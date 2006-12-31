#!/usr/bin/env python
"""Arkadas, an OS independent Contact-Manager using vCards, written in python and GTK
"""

__author__ = "Paul Johnson"
__email__ = "thrillerator@googlemail.com"
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

import sys, os, urllib, base64, socket, webbrowser
import gtk, gobject, pango
# local
import ContactEntry, ContactWindow

# Test pygtk version
if gtk.pygtk_version < (2, 6, 0):
	sys.stderr.write("requires PyGTK 2.6.0 or newer.\n")
	sys.exit(1)

class ContactList:

	def delete_event(self, widget, event, data=None):
		# Change FALSE to TRUE and the main window will not be destroyed
		# with a "delete_event".
		return False

	def destroy(self, widget, data=None):
		gtk.main_quit()

	def __init__(self):
		socket.setdefaulttimeout(2)

		actions = (
			('NewContact', None, "_New", None, "Create a new contact", None),
			('ShowContact', gtk.STOCK_OPEN, "Sho_w", None, "Show the selected contact", self.showbutton_click),
			('EditContact', gtk.STOCK_EDIT, None, None, "Edit the selected contact", None),
			('DeleteContact', gtk.STOCK_DELETE, None, None, "Delete the selected contact", self.deletebutton_click),
			('Preferences', gtk.STOCK_PREFERENCES, None, None, "Configure the application", None),
			('About', gtk.STOCK_ABOUT, None, None, "About the application", self.about),
			('CopyName', gtk.STOCK_COPY, "_Copy Fullname", None, None, None),
			('CopyEmail', None, "Copy E_mail", None, None, None),
			('CopyNumber', None, "Copy N_umber", None, None, None),
			)

		uiDescription = """
			<ui>
			 <toolbar name="Toolbar">
			  <toolitem action="NewContact"/>
			  <toolitem action="ShowContact"/>
			  <toolitem action="EditContact"/>
			  <toolitem action="DeleteContact"/>
			  <separator name="ST1"/>
			  <toolitem action="Preferences"/>
			 </toolbar>
			 <popup name="Itemmenu">
			  <menuitem action="NewContact"/>
			  <menuitem action="ShowContact"/>
			  <menuitem action="EditContact"/>
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

		# main window
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title('Contactlist')
		self.window.set_resizable(True)
		self.window.set_default_size(300,400)

		self.window.set_icon_name('address-book')
		gtk.window_set_default_icon_name('stock_contact')

		# uimanager
		self.uimanager = gtk.UIManager()
		self.uimanager.add_ui_from_string(uiDescription)
		self.accel_group = self.uimanager.get_accel_group()

		actiongroup = gtk.ActionGroup('Actions')
		actiongroup.add_actions(actions)
		self.uimanager.insert_action_group(actiongroup, 0)

		self.tooltips = gtk.Tooltips()

		main_vbox = gtk.VBox()
		self.window.add(main_vbox)

		# toolbar
		self.toolbar = self.uimanager.get_widget('/Toolbar')
		main_vbox.pack_start(self.toolbar,False,False)

		self.uimanager.get_widget('/Toolbar/NewContact').set_icon_name("contact-new")
		image = self.uimanager.get_widget('/Itemmenu/NewContact').get_children()[1]
		image.set_from_icon_name("contact-new", gtk.ICON_SIZE_MENU)

		self.itemmenu = self.uimanager.get_widget('/Itemmenu')

		contacts_vbox = gtk.VBox(False,6)
		contacts_vbox.set_border_width(6)
		main_vbox.pack_start(contacts_vbox)

		# grouplist
		groups_hbox = gtk.HBox()
		#contacts_vbox.pack_start(groups_hbox,False)

		self.groups_combobox = gtk.combo_box_new_text()
		self.groups_combobox.append_text("All")
		self.groups_combobox.set_active(0)
		self.groups_combobox.set_focus_on_click(False)
		groups_hbox.pack_start(self.groups_combobox)

		self.groupsbutton = gtk.Button('',gtk.STOCK_ADD)
		self.groupsbutton.get_child().get_child().get_children()[1].set_text('')
		groups_hbox.pack_end(self.groupsbutton,False)

		self.tooltips.set_tip(self.groupsbutton,"Add group")

		scrolledwindow1 = gtk.ScrolledWindow()
		scrolledwindow1.unset_flags(gtk.CAN_FOCUS)
		scrolledwindow1.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		scrolledwindow1.set_shadow_type(gtk.SHADOW_IN)
		contacts_vbox.pack_start(scrolledwindow1)

		# contactlist
		self.contactdata = gtk.ListStore(gobject.TYPE_STRING,gtk.gdk.Pixbuf,gobject.TYPE_PYOBJECT)
		self.contactdata.set_sort_func(0,self.sort_contacts,None)
		self.contactdata.set_sort_column_id(0,gtk.SORT_ASCENDING)
		self.contactlist = gtk.TreeView(self.contactdata)
		self.contactlist.set_headers_visible(False)
		self.contactlist.set_rules_hint(True)
		self.contactlist.set_enable_search(True)
		self.contactlist.set_search_equal_func(self.search_contacts)
		scrolledwindow1.add(self.contactlist)

		# contactlist cellrenderers
		celltxt = gtk.CellRendererText()
		celltxt.set_property("ellipsize",pango.ELLIPSIZE_END)
		cellimage = gtk.CellRendererPixbuf()
		column = gtk.TreeViewColumn()
		column.pack_start(celltxt)
		column.pack_end(cellimage,False)
		column.add_attribute(celltxt,"markup",0)
		column.add_attribute(cellimage,"pixbuf",1)
		column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self.contactlist.append_column(column)

		# searchbox
		search_hbox = gtk.HBox()
		contacts_vbox.pack_end(search_hbox,False,True,0)

		self.search_label = gtk.Label()
		self.search_label.set_text_with_mnemonic("_Search:")
		self.search_label.set_padding(6,0)
		search_hbox.pack_start(self.search_label,False,True,0)

		self.search_entry = gtk.Entry()
		self.search_label.set_mnemonic_widget(self.search_entry)
		self.search_entry.set_activates_default(True)
		self.contactlist.set_search_entry(self.search_entry)
		search_hbox.pack_start(self.search_entry)

		# events
		self.contactlist.connect('row_activated', self.contactlist_click)
		self.contactlist.connect('button_press_event', self.contactlist_press)
		self.contactlist.connect('popup_menu', self.contactlist_popup_menu)
		self.contactlist.get_selection().connect('changed', self.contactlist_change)
		self.contactlist_change(self.contactlist.get_selection())
		self.window.connect("delete_event", self.delete_event)
		self.window.connect("destroy", self.destroy)

		self.window.add_accel_group(self.accel_group)
		self.window.show_all()

		self.load_contacts()

	#--------------
	# event funtions
	#--------------
	def showbutton_click(self, widget):
		if self.contactlist.get_selection().count_selected_rows() > 0:
			(model, iter) = self.contactlist.get_selection().get_selected()
			entry = model[iter][2]
			entrywindow = ContactWindow.ContactWindow(self, entry)
			entrywindow.set_title(entry.fullname)
			entrywindow.show_all()

	def deletebutton_click(self, widget):
		if self.contactlist.get_selection().count_selected_rows() > 0:
			(model, iter) = self.contactlist.get_selection().get_selected()
			entry = model[iter][2]
			text = "<big><b>Remove Contact</b></big>\n\n"
			text += "You are about to remove <b>%s</b> from your contactlist.\nDo you want to continue?" % (entry.fullname)
			dialog = gtk.Dialog("Arkadas", self.window,gtk.DIALOG_MODAL)
			dialog.set_size_request(420, -1)
			dialog.set_resizable(False)
			dialog.set_has_separator(False)
			dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, "Delete Contact", gtk.RESPONSE_OK)
			dialoghbox = gtk.HBox()
			dialog.vbox.pack_start(dialoghbox, True, True, 6)
			# dialog image
			dialogimage = gtk.image_new_from_stock(gtk.STOCK_HELP, gtk.ICON_SIZE_DIALOG)
			dialogimage.set_alignment(0.5, 0)
			dialoghbox.pack_start(dialogimage, False, False, 10)
			# dialog label
			dialoglabel = gtk.Label()
			dialoglabel.set_markup(text)
			dialoglabel.set_line_wrap(True)
			dialoghbox.pack_start(dialoglabel)
			dialog.connect('response',self.deletedialog_response, entry)
			dialog.show_all()

	def deletedialog_response(self, dialog, response_id, entry):
		if response_id == gtk.RESPONSE_OK:
			try:
				 os.remove(entry.filename)
				 self.contactdata.remove(entry.iter)
			except:
				pass
		dialog.destroy()

	def contactlist_click(self, treeview, path, column):
		self.showbutton_click(self.uimanager.get_widget('/Toolbar/ShowContact'))

	def contactlist_press(self, widget, event):
		if event.button == 3:
			self.itemmenu.popup(None, None, None, event.button, event.time)

	def contactlist_popup_menu(self, widget):
		self.itemmenu.popup(None, None, None, 3, 0)

	def contactlist_change(self, selection):
		if selection.count_selected_rows() > 0:
			self.uimanager.get_widget('/Toolbar/ShowContact').set_sensitive(True)
			self.uimanager.get_widget('/Itemmenu/ShowContact').show()
			self.uimanager.get_widget('/Toolbar/EditContact').set_sensitive(True)
			self.uimanager.get_widget('/Itemmenu/EditContact').show()
			self.uimanager.get_widget('/Toolbar/DeleteContact').set_sensitive(True)
			self.uimanager.get_widget('/Itemmenu/DeleteContact').show()
			self.uimanager.get_widget('/Itemmenu/CopyName').show()
			self.uimanager.get_widget('/Itemmenu/CopyEmail').show()
			self.uimanager.get_widget('/Itemmenu/CopyNumber').show()
		else:
			self.uimanager.get_widget('/Toolbar/ShowContact').set_sensitive(False)
			self.uimanager.get_widget('/Itemmenu/ShowContact').hide()
			self.uimanager.get_widget('/Toolbar/EditContact').set_sensitive(False)
			self.uimanager.get_widget('/Itemmenu/EditContact').hide()
			self.uimanager.get_widget('/Toolbar/DeleteContact').set_sensitive(False)
			self.uimanager.get_widget('/Itemmenu/DeleteContact').hide()
			self.uimanager.get_widget('/Itemmenu/CopyName').hide()
			self.uimanager.get_widget('/Itemmenu/CopyEmail').hide()
			self.uimanager.get_widget('/Itemmenu/CopyNumber').hide()

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
		aboutdialog.set_name('Arkadas')
		aboutdialog.set_version(__version__)
		aboutdialog.set_comments('An OS independent Contact-Manager using vCards, written in python and GTK.')
		aboutdialog.set_license(__license__)
		aboutdialog.set_authors(['Paul Johnson <thrillerator@googlemail.com>',
									'Erdem Cakir <deejayrdm@gmail.com>'])
		#aboutdialog.set_translator_credits('fr - Floreal M <florealm@gmail.com>\npl - Tomasz Dominikowski <dominikowski@gmail.com>\nde - Paul Johnson <thrillerator@googlemail.com>')
		gtk.about_dialog_set_url_hook(show_website, "http://arkadas.berlios.de")
		aboutdialog.set_website_label("http://arkadas.berlios.de")
		large_icon = gtk.gdk.pixbuf_new_from_file('arkadas.png')
		aboutdialog.set_logo(large_icon)
		aboutdialog.connect('response', close_about)
		aboutdialog.connect('delete_event', close_about)
		aboutdialog.show_all()

	#--------------
	# help funtions
	#--------------
	def load_contacts(self):
		self.contact_dir = os.path.expanduser("~/Contacts")
		if os.path.exists(self.contact_dir) == False:
			os.mkdir(self.contact_dir)

		for file in os.listdir(self.contact_dir):
			if file[-3:] != "vcf": continue

			entry = ContactEntry.Entry()
			entry.filename = os.path.join(self.contact_dir,file)

			if entry.get_dict_from_file(entry.filename):
				entry.get_entries_from_dict()

				markup = "<big><b>%s</b></big>" % (entry.fullname)
				markup_small = "\n<small><b>%s: </b>%s</small>"

				if entry.title != '':
					markup += " <small>(%s)</small>" % (entry.title)

				if len(entry.email) > 0:
					markup += markup_small % ("email","<u>" + entry.email[0] + "</u>")
				elif len(entry.work_email) > 0:
					markup += markup_small % ("email","<u>" + entry.work_email[0] + "</u>")

				if len(entry.tel) > 0:
					markup += markup_small % ("phone",entry.tel[0][0])
				elif len(entry.work_tel) > 0:
					markup += markup_small % ("phone",entry.work_tel[0][0])

				iter = self.contactdata.append([markup,None,entry])
				entry.iter = iter

				if entry.photo != None:
					gobject.idle_add(self.get_image_from_entry, entry)

	def sort_contacts(self, model, iter1, iter2, data):
		entry1 = model[iter1][2] ; entry2 = model[iter2][2]
		f1 = '' ; f2 = ''
		if entry1 and entry2:
			for i in (0,4,3,1,2):
				f1 += entry1.name[i].strip() + ' '
				f2 += entry2.name[i].strip() + ' '
			return cmp(f1.strip().replace('  ',' '),f2.strip().replace('  ',' '))
		return 0

	def search_contacts(self, model, column, key, iter):
		entry = model[iter][2]
		if key.lower() in entry.fullname.lower():
			return False
		return True

	def get_image_from_entry(self, entry):
		if entry.photo_type == "URI":
			try:
				url = urllib.urlopen(entry.photo)
				data = url.read()
				url.close()
			except:
				pass
		elif entry.photo_type == "B64":
			data = base64.decodestring(entry.photo)
		try:
			loader = gtk.gdk.PixbufLoader()
			loader.write(data)
			loader.close()
			pixbuf = loader.get_pixbuf()
		except:
			pass
		entry.pixbuf = self.get_pixbuf_of_size(pixbuf,50)
		self.contactdata[entry.iter][1] = self.get_pixbuf_of_size(pixbuf,50)
		return False

	def get_pixbuf_of_size(self, pixbuf, size):
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

	def get_pixbuf_of_size_from_file(self, filename, size):
		try:
			pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
			pixbuf = self.get_pixbuf_of_size(pixbuf, size)
		except:
			pass
		return pixbuf

	def main(self):
		# All PyGTK applications must have a gtk.main(). Control ends here
		# and waits for an event to occur (like a key press or mouse event).
		gtk.main()

# If the program is run directly or passed as an argument to the python
# interpreter then create a HelloWorld instance and show it
if __name__ == "__main__":
	contacts = ContactList()
	contacts.main()
