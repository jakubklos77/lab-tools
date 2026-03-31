#!/home/jakub/bin/run-in-terminal
#!/usr/bin/env python

import shutil
import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))

# Load JSON
with open(os.path.join(script_dir, "../data/adb_pull.json"), 'r') as file:
    json = json.load(file)
if not json:
    raise Exception("JSON not found or malformed")

# Get dirs
source = json['source']
dest = json['dest']

# Process paths
for path in json['paths']:

    # Source, dest dir
    sourcedir = source + path
    destdir = dest + path

    # Create
    os.makedirs(destdir, exist_ok=True)

    # Debug
    #print('copy ' + sourcedir + ' ' + destdir)

    # Pull
    try:
        print(f'copying {sourcedir} {destdir}',  end = '')
        shutil.copytree(sourcedir, destdir, dirs_exist_ok = True)
        print("")
    except Exception as error:
        print(", error", error)
