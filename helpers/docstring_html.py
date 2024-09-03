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