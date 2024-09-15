"""
/***************************************************************************
 SciPyFilters
                                 A QGIS plugin
 Filter collection implemented with SciPy
                              -------------------
        begin                : 2024-03-03
        copyright            : (C) 2024 by Florian Neukirchen
        email                : mail@riannek.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import re

def convert_docstring_to_html(docstring):
    if not docstring:
        return ""
    

    # Ersetzen Sie Fettdruck
    docstring = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', docstring)

    # Ersetzen Sie Kursivdruck
    docstring = re.sub(r'\*(.*?)\*', r'<i>\1</i>', docstring)

    # Einzelne Zeilenumbrüche entfernen, aber doppelte beibehalten
    docstring = re.sub(r'(?<!\n)\n(?!\n)', ' ', docstring)

    # Note
    docstring = re.sub(r'.. note::', '<i>Note:</i>', docstring)

    # Links im Sphinx-Format in HTML umwandeln
    docstring = re.sub(r'`([^<]+)<([^>]+)>`_', r'<a href="\2">\1</a>', docstring)


    return docstring