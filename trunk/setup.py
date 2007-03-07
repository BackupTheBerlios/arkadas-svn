#!/usr/bin/env python

from distutils.core import setup

setup(name="arkadas",
        version="1.7",
        description="A lightweight GTK+ Contact-Manager.",
        author="Paul Johnson",
        author_email="thrillerator@googlemail.com",
        url="http://arkadas.berlios.de",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: X11 Applications",
            "Intended Audience :: End Users/Desktop",
            "License :: GNU General Public License (GPL)",
            "Operating System :: Linux",
            "Programming Language :: Python",
            "Topic :: Database",
            "Topic :: Desktop Environment",
            "Topic :: Office/Business",
            "Topic :: Utilities"],
        packages = ["Arkadas"],
        scripts = ["arkadas"],
        data_files=[("share/arkadas", ["arkadas.glade", "COPYING", "TODO", "README", "TRANSLATORS"]),
                    ("share/applications", ["arkadas.desktop"]),
                    ("share/pixmaps", ["pixmaps/arkadas.png", "pixmaps/no-photo.png"]),
                    ("share/icons/hicolor/16x16/apps", ["icons/16x16/apps/address-book.png"]),
                    ("share/icons/hicolor/22x22/apps", ["icons/22x22/apps/address-book.png"]),
                    ("share/icons/hicolor/24x24/apps", ["icons/24x24/apps/address-book.png"]),
                    ("share/icons/hicolor/scalable/apps", ["icons/scalable/apps/address-book.svg"]),
                    ("share/locale/de/LC_MESSAGES", ["locale/de/LC_MESSAGES/arkadas.mo"])],
        )
