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

import datetime
import gtk, gobject, pango
# local
from Commons import *
import ContactEntry

order = ["TEL", "EMAIL", "WEB", "IM", "BDAY", "ADR", "WORK_TEL", "WORK_EMAIL", "WORK_WEB", "WORK_ADR"]

class ContactWindow(gtk.Window):

	def __init__(self, parent, entry, edit_mode = False):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		if len(entry.fullname) > 0:
			self.set_title(entry.fullname)
		else:
			self.set_title("Contact")

		self.set_resizable(True)
		self.set_default_size(-1,400)

		if entry.pixbuf != None:
			self.set_icon(get_pixbuf_of_size(entry.pixbuf,128))

		self.tooltips = gtk.Tooltips()

		self.widgets = []

		self.color = gtk.gdk.color_parse("white")

		self.vbox = gtk.VBox(False, 6)
		self.vbox.set_border_width(6)
		self.add(self.vbox)

		# display
		scrolledwindow = gtk.ScrolledWindow()
		scrolledwindow.set_policy(gtk.POLICY_NEVER,gtk.POLICY_AUTOMATIC)
		self.vbox.pack_start(scrolledwindow)

		self.hsizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
		self.vsizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_VERTICAL)

		self.table = gtk.VBox(False, 6)
		self.table.set_border_width(6)
		scrolledwindow.add_with_viewport(self.table)
		scrolledwindow.get_child().modify_bg(gtk.STATE_NORMAL,self.color)
		
		# buttons
		self.buttonbox = gtk.HBox(False, 6)
		self.vbox.pack_end(self.buttonbox, False)

		addButton = gtk.Button("",gtk.STOCK_ADD)
		addButton.set_no_show_all(True)
		addButton.show()
		addButton.get_child().get_child().get_children()[1].hide()
		self.buttonbox.pack_start(addButton, False)

		self.buttonbox.pack_start(gtk.Label())

		editButton = gtk.ToggleButton(gtk.STOCK_EDIT)
		editButton.set_use_stock(True)
		editButton.set_no_show_all(True)
		editButton.show()
		editButton.get_child().get_child().get_children()[1].hide()
		editButton.connect("toggled", self.switch_mode, entry, addButton)
		self.buttonbox.pack_start(editButton, False)

		closeButton = gtk.Button("",gtk.STOCK_CLOSE)
		closeButton.connect_object("clicked", gtk.Widget.destroy, self)
		self.buttonbox.pack_start(closeButton, False)

		# create widgets
		self.build_interface(entry)

		addButton.set_sensitive(edit_mode)
		editButton.set_active(edit_mode)

	def build_interface(self, entry):
		# help-functions
		#---------------
		def add_label(box, text, type):
			def remove_item(button, event):
				if type == "NOTE":
					textbuffer.set_text("")
				else:
					self.widgets.remove(hbox)
					hbox.destroy()
					self.get_toplevel().window.set_cursor(None)
					
			hbox = gtk.HBox(False, 4)

			# caption
			captionbox = gtk.VBox()
			caption = ComboLabel(type)
			caption.button.connect("button_press_event", remove_item)
			captionbox.pack_start(caption, False)
			hbox.pack_start(captionbox, False)
			self.hsizegroup.add_widget(caption)
			self.vsizegroup.add_widget(caption)

			if "ADR" in type:
				# address
				field = AddressField(text)
			elif type == "NOTE":
				# multiline label
				textbuffer = gtk.TextBuffer()
				textbuffer.set_text(text)
				tag_table = textbuffer.get_tag_table()
				tag = gtk.TextTag()
				tag.set_property("foreground", "black")
				tag_table.add(tag)
				textbuffer.apply_tag(tag, textbuffer.get_start_iter(), textbuffer.get_end_iter())
				field = gtk.TextView(textbuffer)
				field.set_wrap_mode(gtk.WRAP_WORD)
			else:
				# entrylabel
				field = EntryLabel(text, type)
				field.set_editable(False)
				self.vsizegroup.add_widget(field)

			hbox.pack_start(field)
			box.add(hbox)
			if not type == "NOTE": self.widgets.append(hbox)
			
		#---------------
		
		self.photohbox = gtk.HBox(False, 2)
		self.emailbox = EventVBox()
		self.workemailbox = EventVBox()
		self.telbox = EventVBox()
		self.worktelbox = EventVBox()
		self.imbox = EventVBox()
		self.workadrbox = EventVBox()
		self.webbox = EventVBox()
		self.workwebbox = EventVBox()
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
			elif type == "WEB":
				self.table.pack_start(self.webbox, False)
			elif type == "WORK_WEB":
				self.table.pack_start(self.workwebbox, False)
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

		self.table.pack_start(self.notebox, False)
		
		# contact photo
		if entry.pixbuf:
			pixbuf = get_pixbuf_of_size(entry.pixbuf,64, False)
			self.hasphoto = True
		else:
			pixbuf = get_pixbuf_of_size_from_file("no-photo.png", 64)
			self.hasphoto = False
		self.photo = ImageButton(pixbuf, self.color, True)
		#self.photo.connect("button_press_event", remove_photo)
		#self.tooltips.set_tip(self.photo,"Click to remove image")		
		self.hsizegroup.add_widget(self.photo)
		self.photohbox.pack_start(self.photo,False)
		
		# big title
		text = "<span size=\"x-large\"><b>%s</b></span>" % (entry.fullname)

		if len(entry.nick) > 0:
			text += " (<big>%s</big>)" % (entry.nick)
		if len(entry.title) > 0:
			text += "\n" + entry.title
		if len(entry.org) > 0:
			text += "\n" + entry.org

		title = gtk.Label()
		title.set_markup(text)
		title.set_alignment(0,0)
		title.set_selectable(True)
		self.photohbox.pack_start(title, True, True, 6)
		self.photohbox.show_all()

		# add widgets
		# tel numbers
		if len(entry.tel) > 0:
			for i in range(len(entry.tel)):
				add_label(self.telbox, entry.tel[i][0], entry.tel[i][1])
		if len(entry.work_tel) > 0:
			for i in range(len(entry.work_tel)):
				add_label(self.worktelbox, entry.work_tel[i][0], "WORK_" + entry.work_tel[i][1])
		# emails
		if len(entry.email) > 0:
			for i in range(len(entry.email)):
				add_label(self.emailbox, entry.email[i], "EMAIL")
		if len(entry.work_email) > 0:
			for i in range(len(entry.work_email)):
				add_label(self.workemailbox, entry.work_email[i], "WORK_EMAIL")
		# web
		if len(entry.url) > 0:
			add_label(self.webbox, entry.url, "WEB")
		if len(entry.work_url) > 0:
			add_label(self.workwebbox, entry.work_url, "WORK_WEB")
		# instant messaging
		if len(entry.im) > 0:
			for i in range(len(entry.im)):
				add_label(self.imbox, entry.im[i][0], entry.im[i][1])
		# address
		if len(entry.address) > 0:
			add_label(self.adrbox, entry.address, "ADR") 
		if len(entry.work_address) > 0:
			add_label(self.workadrbox, entry.work_address, "WORK_ADR")
		# birthday
		try:
			if entry.bday_year:
				date = datetime.date(entry.bday_year, entry.bday_month, entry.bday_day).strftime("%d.%m.%Y")
				add_label(self.bdaybox, "birthday", date, type)
		except: pass

		self.notebox.add(gtk.HSeparator())
		self.notebox.set_spacing(4)
		add_label(self.notebox, entry.note_text, "NOTE")

		self.table.set_no_show_all(True)
		self.table.show()

	#---------------
	# event funtions
	#---------------
	def switch_mode(self, button, entry, widget):
		state = button.get_active()
		widget.set_sensitive(state)

		empty = []
		for child in self.table.get_children():
			if type(child) == EventVBox:
				for hbox in child.get_children():
					if type(hbox) == gtk.HBox:
						caption, field = hbox.get_children()[0].get_children()[0], hbox.get_children()[1]
						caption.set_editable(state)
						if type(field) == EntryLabel:
							field.set_editable(state)
							# remove if empty
							if field.get_text() == "": hbox.destroy() ; continue
						elif type(field) == AddressField:
							field.set_editable(state)
							if field.address == len(field.address) * [""]: hbox.destroy() ; continue
						elif type(field) == gtk.TextView:
							field.set_editable(state)
