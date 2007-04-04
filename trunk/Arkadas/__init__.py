# -*- coding: utf-8 -*-

# Copyright © 2006-2007 Paul Johnson <thrillerator@googlemail.com>
#
# This file is part of Arkadas.
#
# Arkadas is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Arkadas is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Arkadas; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA

import socket
socket.setdefaulttimeout(30)

import gtk

# Test pygtk version
if gtk.pygtk_version < (2, 8, 0):
	sys.stderr.write("requires PyGTK 2.8.0 or newer.\n")
	sys.exit(1)
	
gtk.gdk.threads_init()

import gtk.glade
gtk.glade.textdomain("arkadas")
	
import gettext
gettext.install("arkadas", "/usr/share/locale", unicode=1)

if __name__ == "__main__":
	import MainWindow
	app = MainWindow.MainWindow()
	app.main()