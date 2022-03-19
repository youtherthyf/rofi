#!/usr/bin/python

from pathlib import Path
import argparse
import json
import sqlite3

# _TODO_ allow configuring paths to any folder
# _TODO_ use pathlib for everything

local_path = "/home/zaraksh/Documents/Code/rofiBookmarks"
local_db_path = Path(local_path, "bookmarks.sqlite")

def update_local_db(dbpath):

    if not dbpath.exists():
        print("Could not update database. Invalid path or profile does not exist")
        return

    print("Updating local database...")

    # Copy firefox's places.sqlite into our own local copy
    local_db_file = open(local_db_path, "wb")
    with open(dbpath, "rb") as dbfile:
        for byte in dbfile:
            local_db_file.write(byte)
    local_db_file.close()

    ## Strip unneeded information from database. Saves space and privacy
    
    # Fetches names of all tables except moz_places and moz_bookmarks    
    get_unneeded_tables = " SELECT name\
                            FROM sqlite_master\
                            WHERE name NOT LIKE '%moz_places%'\
                            AND name NOT LIKE '%moz_bookmarks%'"
    
    # Create the DROP statements.
    statements = []

    db = sqlite3.connect(local_db_path)
    for row in db.execute(get_unneeded_tables):
        (name,) = row
        statement = "DROP TABLE " + name
        statements.append(statement)

    # Drop tables. The try catch is needed because some of commands will drop multiple tables
    # _TODO_ find out why db.execute("DROP TABLE :table", {"table": name}) does not work
    for statement in statements:
        try:
            db.execute(statement)
        except:
            pass

    db.close()

def fetch_data():
    
    db = sqlite3.connect(local_db_path)
    
    # Fetches title, url, and folder-id of all bookmarks
    fetch_bookmarks = " SELECT moz_bookmarks.title,moz_places.url,moz_bookmarks.parent\
                        FROM moz_places\
                        INNER JOIN moz_bookmarks ON moz_places.id=moz_bookmarks.fk"
    
    # Fetches title, folder-id, and id of all folders
    fetch_folders = "   SELECT moz_bookmarks.title,moz_bookmarks.parent,moz_bookmarks.id\
                        FROM moz_bookmarks\
                        WHERE type IS 2\
                        AND parent IS NOT 0"
    
    folders = [] # {"name": string, "parent_key": int, "key": int, "bookmarks": list}
    
    for row in db.execute(fetch_folders):
        (title,parent_key,folder_key) = row
    
        folders.append({
            "name": title,
            "parent_key": parent_key,
            "key": folder_key,
            "bookmarks": []
            })
    
    # Pack bookmarks[] into folders[]
    for row in db.execute(fetch_bookmarks):
        (title,url,parent_key) = row
    
        for folder in folders:
            if folder["key"] is parent_key:
                folder["bookmarks"].append(
                    {
                        "name": title,
                        "url": url
                    }
                )
    
    # Arrange folders into a heirarchy
    for folder in reversed(folders):
        # print(folder["key"], "into", folder["parent_key"])
        for parent in folders:
            # print("----------", parent["key"], "is?", folder["parent_key"])
            if parent["key"] is folder["parent_key"]:
                # print(folder["name"], "into", parent["key"])
                parent["bookmarks"].append(folder)
                folders.pop(folders.index(folder))

    db.close()
    return folders

if __name__ == "__main__":

    # Argparsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", action="store_true",
                        help="Dumps a raw representation of bookmarks")
    parser.add_argument("-u", "--update",
                        help="Update local database using a Firefox profile", metavar="<profile>")

    args = parser.parse_args()

    if args.update:
        dbpath = Path(args.update, "places.sqlite")
        update_local_db(dbpath)
    
    if args.raw:
        print(json.dumps(fetch_data()))

