# -*- coding: utf-8 -*-

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
import gtk

from Commons import *

class Field(gtk.EventBox):
	def __init__(self, name, content):
		gtk.EventBox.__init__(self)
		#self.set_flags(gtk.CAN_FOCUS)
		#self.set_above_child(True)
		self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

		#self.connect("focus-out-event", lambda w,e: self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white")))
		#self.connect("focus-in-event", lambda w,e: self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue")))

		self.hbox = gtk.HBox()
		self.hbox.set_no_show_all(True)
		self.add(self.hbox)

		self.content = content

		if isinstance(self.content, ContactEngine.Content):
			if not self.content.type:
				self.content.type = "home"
			if name == "adr":
				self.label = AddressField(self.content)
			else:
				self.label = CustomLabel(self.content.value, (name in ("email", "url")))
		else:
			if name == "bday":
				self.label = BirthdayField(self.content)
			else:
				self.label = CustomLabel(self.content)

		self.hbox.pack_start(self.label, False, padding=4)

		if name != "bday":
			act = None
			model = gtk.ListStore(str, str)
			if name == "tel":
				for val in tel_types:
					if val.startswith("work_"):
						text = "%s (%s)" % (types[val[5:]], types["work"])
					else:
						text = types[val]
					iter = model.append([text, val])
					if val == self.content.type: act = iter
			elif name == "im":
				for val in im_types:
					iter = model.append([types[val], val])
					if val == self.content.type: act = iter
			else:
				for val in ("home", "work"):
					iter = model.append([types[val], val])
					if val == self.content.type: act = iter

			def typeCombo_changed(combo):
				title, self.content.type = combo.get_model()[combo.get_active()]
				self.typeLabel.set_markup("<span foreground=\"dim grey\"><i>%s</i></span>" % title)

			self.typeLabel = gtk.Label()
			self.typeLabel.set_alignment(0, 0)
			self.typeLabel.show()
			self.hbox.pack_start(self.typeLabel, False)

			self.typeCombo = gtk.ComboBox(model)
			cell = gtk.CellRendererText()
			self.typeCombo.pack_start(cell, False)
			self.typeCombo.set_attributes(cell, text=0)

			if act:
				self.typeCombo.set_active_iter(act)
			else:
				self.typeCombo.set_active(0)

			typeCombo_changed(self.typeCombo)
			self.typeCombo.connect("changed", typeCombo_changed)
			self.hbox.pack_start(self.typeCombo, False)

		self.removeButton = gtk.Button()
		self.removeButton.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
		#self.removeButton.set_relief(gtk.RELIEF_NONE)
		self.hbox.pack_start(self.removeButton, False)

		self.label.show()
		self.hbox.show()

	def set_editable(self, editable):
		self.label.set_editable(editable)
		self.removeButton.set_property("visible", editable)
		if hasattr(self, "typeCombo"):
			self.typeLabel.set_property("visible", not editable)
			self.typeCombo.set_property("visible", editable)

		if isinstance(self.content, ContactEngine.Content):
			if self.content.name == "adr":
				self.content = self.label.content
			else:
				self.content.value = self.label.get_text()

	def grab_focus(self):
		if isinstance(self.label,CustomLabel):
			self.label.grab_focus()

class CustomLabel(gtk.HBox):
	def __init__(self, text, link=False):
		gtk.HBox.__init__(self, False)
		self.set_no_show_all(True)

		self.link = link

		self.labelbox = gtk.HBox(False, 2)
		self.pack_start(self.labelbox)

		self.label = gtk.Label()
		self.label.set_selectable(True)
		self.label.set_alignment(0,0.5)
		self.label.show()

		if self.link:
			self.eventbox = gtk.EventBox()
			self.eventbox.set_above_child(True)
			self.eventbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
			self.eventbox.add(self.label)
			self.eventbox.show()
			self.eventbox.connect("button-press-event", self.open_link)
			self.eventbox.connect("enter-notify-event", lambda w,e: self.get_toplevel().window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2)))
			self.eventbox.connect("leave-notify-event", lambda w,e: self.get_toplevel().window.set_cursor(None))
			self.labelbox.pack_start(self.eventbox, False)
		else:
			self.labelbox.add(self.label)

		self.entry = gtk.Entry()
		#self.entry.set_has_frame(False)
		self.entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		self.add(self.entry)

		self.labelbox.show()
		self.entry.hide()
		self.show()

		self.set_text(text)

	def open_link(self, widget, event):
		if event.button == 1:
			url = self.get_text()
			if "@" in url:
				url = "mailto:" + url
			browser_load(url, self.get_toplevel())

	def set_text(self, text):
		if self.link:
			self.label.set_markup("<span foreground=\"blue\"><u>%s</u></span>" % text)
		else:
			self.label.set_markup("<span foreground=\"black\">%s</span>" % text)

		self.entry.set_text(text)

	def get_text(self):
		return self.entry.get_text()

	def set_editable(self, editable):
		self.labelbox.set_property("visible", not editable)
		self.entry.set_property("visible", editable)
		self.set_text(self.entry.get_text())

	def grab_focus(self):
		if self.entry.get_property("visible"): self.entry.grab_focus()
		else: self.label.grab_focus()

class AddressField(gtk.HBox):
	def __init__(self, content):
		gtk.HBox.__init__(self)

		self.content = content
		self.format = address_formats[0]
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

		for val in ContactEngine.ADDRESS_ORDER:
			setattr(self, val, gtk.Entry())
			if getattr(self.content, val):
				getattr(self, val).set_text(getattr(self.content, val))

		i = 0
		for val in ("street", "extended", "box", "city", "region", "code", "country"):
			label = gtk.Label(types[val] + ":")
			label.set_alignment(0, 0.5)
			self.table.attach(label, 0, 1, i, i+1, gtk.EXPAND|gtk.FILL, gtk.FILL)
			self.table.attach(getattr(self, val), 1, 2, i, i+1, gtk.EXPAND|gtk.FILL, gtk.FILL)
			i += 1

		self.table.attach(gtk.HSeparator(), 0, 2, i, i+1, gtk.EXPAND|gtk.FILL, gtk.FILL, ypadding=2)


		self.table.show_all()

	def set_editable(self, editable = False):
		self.label.set_property("visible", not editable)
		self.table.set_property("visible", editable)

		for widget in self.table.get_children():
			if isinstance(widget, gtk.Entry):
				widget.set_editable(editable)

		for val in ContactEngine.ADDRESS_ORDER:
			setattr(self.content, val, getattr(self, val).get_text().strip())

		text = format_adr(self.format,**self.content.__dict__)
		self.label.set_markup("<span foreground=\"black\">%s</span>" % text)

	def grab_focus(self):
		self.street.grab_focus()

class BirthdayField(gtk.HBox):
	def __init__(self, content):
		gtk.HBox.__init__(self)

		self.set_no_show_all(True)

		self.content = content
		self.tooltips = gtk.Tooltips()

		self.build_interface()

		self.set_editable(False)
		self.show()

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

		self.datebox.show_all()

		year, month, day = bday_from_value(self.content)

		if year:
			self.day.set_value(day)
			self.month.set_value(month)
			self.year.set_value(year)

	def set_editable(self, editable):
		year = self.year.get_value_as_int()
		month = self.month.get_value_as_int()
		day = self.day.get_value_as_int()

		date = datetime.date(year, month, day)

		self.content = date.isoformat()
		self.label.set_markup("<span foreground=\"black\">%s</span>" % date.strftime("%x"))

		self.label.set_property("visible", not editable)
		self.datebox.set_property("visible", editable)

class EventVBox(gtk.HBox):
	def __init__(self, name, sizegroup=None):
		gtk.HBox.__init__(self)
		self.set_no_show_all(True)

		self.sname = name
		self.sizegroup = sizegroup

		# caption
		self.caption = gtk.Label()
		self.caption.set_markup("<span foreground=\"dim grey\"><b>%s:</b></span>" % types[name])
		self.caption.set_alignment(1, 0)
		self.pack_start(self.caption, False)

		sep = gtk.VSeparator()
		sep.show()
		self.pack_start(sep, False, padding=4)

		self.vbox = gtk.VBox()
		self.add(self.vbox)

		self.vbox.connect("remove", self.remove_event)

	def add_field(self, widget):
		if len(self.vbox.get_children()) == 0 and self.sizegroup:
			self.sizegroup.add_widget(self.caption)
		self.vbox.add(widget)
		self.vbox.show()
		self.caption.show()
		self.show()
		widget.show_all()

	def remove_event(self, container, widget):
		if not len(container.get_children()):
			if self.sizegroup: self.sizegroup.remove_widget(self.caption)
			self.hide()
