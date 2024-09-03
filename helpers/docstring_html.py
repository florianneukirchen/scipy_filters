import re

def convert_docstring_to_html(docstring):
    if not docstring:
        return ""
    
 # Bullet list
    def replace_bullet_list(match):
        items = match.group(0)
        items = re.sub(r'^\s*\*\s+(.*)$', r'<li>\1</li>', items, flags=re.MULTILINE)
        return f"<ul>\n{items}\n</ul>"

    # Ersetzen Sie Bullet-Listen
    docstring = re.sub(r'((?:^\s*\*\s+.*$\n?)+)', replace_bullet_list, docstring, flags=re.MULTILINE)


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