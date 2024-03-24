#!/usr/bin/python3

import os
import subprocess
import glob
from xml.dom.minidom import *

i_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "i18n"))
os.chdir(i_path)
print(os.getcwd())
result = subprocess.run(["pylupdate5", "scipy_filters.pro"])
print(result.stdout)


for fn in glob.glob('*.ts'):
    dom = parse(fn)
    contexts = dom.getElementsByTagName("context")
    contexts[0].getElementsByTagName("name")[0].firstChild.data = "ScipyFiltersPlugin"

    parent = contexts[0].parentNode

    for ctx in contexts[1:]:
        messages = ctx.getElementsByTagName("message")
        for msg in messages:
            contexts[0].appendChild(msg)
        parent.removeChild(ctx)


    with open(fn, "w") as f:
        dom.writexml(f)



