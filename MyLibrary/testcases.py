#! /usr/bin/env python3

import IMAPTester
import time

#host = 'lenka.test.com'
host = 'super-test.com'
user = 'user'
psw = 'a'

username = user + '@' + host
PublicMail = "public-folders@" + host

msgs = []
folders = []

def send_email(host, to):
    msg = IMAPTester.Email(host, to, username)
    msg.send()
    time.sleep(1)
    msg.ID = conn.get_msgid_by_subject(msg.subject)
    msg.flags = conn.get_flags(msg.ID)
    count = len(msgs)
    msgs.append(msg)
    return count


def test_subscribe(folder):
    '''subscribe folder return True if is this folder in LSUB list
    '''
    returncode = False
    try:
        conn.subscribe(folder)
    except:
        print("ERROR!!!", err)
        return False
    lsub = conn.lsub()
    for item in lsub[1]:
        item = item[7:].decode().replace('"','')
        if folder == item:
            returncode = True
    return returncode

def test_unsubscribe(folder):
    '''unsubscribe folder return True if is not this folder in LSUB list
    '''
    returncode = True
    try:
        conn.unsubscribe(folder)
    except:
        print("ERROR!!!", err)
        return False
    lsub = conn.lsub()
    for item in lsub[1]:
        item = item[7:].decode().replace('"','')
        if folder == item:
            returncode = False
    return returncode

def test_xlist(folder = "INBOX", pattern = "*", expected = ["INBOX/SUB1-1","INBOX/SUB1-2"]):
    xlist = conn.xlist(folder,pattern)[1]
    count = 0
    list_fail = []
    xlist_name = []
    
    for folder in xlist:
        folder = folder.decode().split(" ")
        xlist_name.append(folder[-1].replace('"','').upper())
    
    for item in expected:
        item = item.upper()
        if item in xlist_name:
            count += 1
        else:
            list_fail.append(item)
    if count == len(expected):
        return True#, list_fail, folder, pattern
    else:
        return False#, list_fail, folder, pattern
       # print("TEST - Xlist pattern - FAIL ",list_fail," folder: ",folder, "pattern: ",pattern)

# 1. connect to server   
try:
    conn = IMAPTester.IW_connection(host, user, psw)
except Exception as err:
    print("can't connect to server")
    exit()


# 2. send test email = SEND, RECEIVE, SEARCH
try:
    msgid = send_email(host, username)
    if (msgs[msgid]).ID == -1:
        print("[ERROR]  receive / search this msg: %s" % (msgs[msgid]).subject)
    else:
        print("[OK]  send / receive / search")
except ConnectionRefusedError as err:
    print("[ERROR]  send msg")
    print(err)


# 3. set FLAG (\\Flagged & \\Completed)
#select INBOX folder
conn.select() 
# + \\flagged
if conn.add_flag(((msgs[msgid]).ID),'\\Flagged'):
    print("[OK]  +flag \\flagged")
else:
    print("[ERROR]  +flag \\flagged")
# + $Completed
if conn.add_flag(((msgs[msgid]).ID),'$Completed'):
    print("[OK]  +flag $Completed")
else:
    print("[ERROR]  +flag $Completed")
(msgs[msgid]).flags = conn.get_flags((msgs[msgid]).ID)


# 4. create folder
folder_tree = ['INBOX/sub1-1','INBOX/sub1-2','myfolder1', 'myfolder2', 'myfolder1/sub1-1', 'myfolder1/sub1-2', 'myfolder2/sub2-1', 'myfolder2/sub2-2']
fail = True
for folder in folder_tree:
    if conn.create_folder(folder):
        folders.append(folder)
        time.sleep(1)
    else:
        if conn.select(folder)[0] == "OK":
            print("[WARNING]  folder already exists: " ,folder)
            folders.append(folder)
            fail = False
        else:
            print("[ERROR]  create folder: " ,folder)
            fail = False
if fail:
    print("[OK]  create folders")


# 5. test case sensitivity - folder rename
if conn.create_folder(folders[0].capitalize()):
    print("[ERROR] case sensitivity - FOLDERS")
else:
    print("[OK]  case sensitivity Folders")


# 6. test rename folder
if conn.rename_folder(folders[-1], (folders[-1] + "-new")):
    print("[OK]  rename folder")
    folders[-1] = folders[-1].replace(folders[-1], (folders[-1] + "-new"))
else:
    print("[ERROR] rename folder")

# 7. test subscribe and unsubscribe folder
#send msg tu public - cant del this msg hust for create public INBOX
IMAPTester.Email(host, PublicMail, username).send()
TestFolders = [folders[0], folders[-1], "Public/INBOX", "Public/inbox", "Public/Inbox"]
fail = True
for folder in TestFolders:
    if not test_subscribe(folder):
        print("[ERROR]  subscribe folder: " ,folder)
        fail = False
    if not test_unsubscribe(folder):
        print("[ERROR]  unsubscribe folder: " ,folder)
        fail = False        
if fail:
    print("[OK]  subscribe/unsubscribe folders")

# 8. Xlist tests
testcase = [["", "INBOX/%", ["INBOX/SUB1-1","INBOX/SUB1-2"]],["", "inbox/%", ["INBOX/SUB1-1","INBOX/SUB1-2"]],["", "Inbox/%", ["INBOX/SUB1-1","INBOX/SUB1-2"]],["INBOX/", "*", ["INBOX/SUB1-1","INBOX/SUB1-2"]],["myfolder1", "*", ["MYFOLDER1/SUB1-1","MYFOLDER1/SUB1-2"]],["", "*", folders],["", "%", ["MYFOLDER1","MYFOLDER2","INBOX"]]]

fail = True
for case in testcase:
    if not test_xlist(folder=case[0], pattern=case[1],expected=case[2]):
        print("[ERROR]  XLIST (folder, pattern, expected): " ,case)
        fail = False
    
if fail:
    print("[OK]  XLIST")





#delete all created msgs
fail = True
for msg in msgs:
    if not conn.delete_message(msg.ID, msg.folder):
        print("[ERROR]  delete msg: " ,msg)
        fail = False
if fail:
    print("[OK]  delete msgs")
    msgs = []

#delete all created folders
fail = True
for folder in folders:
    if not conn.delete_folder(folder):
        print("[ERROR]  delete folder: " ,folder)
        fail = False
if fail:
    print("[OK]  delete folders")
    folders = []

conn.logout()




