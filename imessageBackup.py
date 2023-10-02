import sqlite3
import re
import subprocess
import os

archivePath = "/Users/ryder/Desktop/iMessage Archives"

subprocess.run(f"rm -rf '{archivePath}'", shell = True)
subprocess.run(f"mkdir -p '{archivePath}'", shell = True)
subprocess.run(f"imessage-exporter --export-path '{archivePath}' -f html -c compatible", shell = True)

contactsPath1 = "/Users/ryder/Library/Application Support/AddressBook/Sources/339586BA-F4F9-4626-83FD-199F8D24E8E8/AddressBook-v22.abcddb"
contactsPath2 = "/Users/ryder/Library/Application Support/AddressBook/Sources/FC9D18F9-3669-4B22-9362-16C015471A47/AddressBook-v22.abcddb" # apparently some can be duplicated across databases??? why
nameRegex = r"\b(.+)(?=.*\1\s)" #r"\b([a-zA-Z0-9_ &'/\(\)-]+)\b(?=.*\s\1\s)"
fullAMERNumRegex = r"1[0-9]{10}"
noCountryCodeAMERRegex = r"[^1\s][0-9]{9}\s"
intlNumberRegex = r"[0-9]{11,}"
stupidCodesRegex = r"[0-9]{3,4} [0-9]{3,4} "
processedNumsRegex = r"\+[0-9]{10,}"
numToNameMap = {}

def SQLintoDict(contactsPath):
    connection = sqlite3.connect(contactsPath)
    crsr = connection.cursor()

    sqlReadStrForIndex = "SELECT ZSTRINGFORINDEXING FROM ZABCDCONTACTINDEX"
    crsr.execute(sqlReadStrForIndex)
    ans = crsr.fetchall() # individual string is ans[i][0]

    for entry in ans:
        entry = entry[0]
        name = re.search(nameRegex, entry); name = name.group(); name = name.replace("/", " or ")
        number = re.search(fullAMERNumRegex, entry)
        if number != None:
            number = "+" + number.group()
        else:
            number = re.search(intlNumberRegex, entry)
            if number != None:
                number = "+" + number.group()
            else:
                number = re.search(noCountryCodeAMERRegex, entry) # regex matching must go in this order
                if number != None:
                    number = "+1" + number.group()[:-1] # assuming american numbers are default
                else:
                    number = re.search(stupidCodesRegex, entry); number = number.group()
                    number = number[:(len(number) // 2 - 1)]

        numToNameMap[number] = name
    
    connection.close()
    return numToNameMap

SQLintoDict(contactsPath1)
SQLintoDict(contactsPath2)

htmlFiles = os.path.abspath(archivePath)
for file in os.listdir(htmlFiles): # file is string ending in ".html"
    src = os.path.join(htmlFiles, file)

    matchesList = re.findall(processedNumsRegex, file)
    for number in matchesList:
        try:
            asName = numToNameMap[number]
            file = file.replace(number, asName)
        except:
            pass

    dst = os.path.join(htmlFiles, file)
    os.rename(src, dst)