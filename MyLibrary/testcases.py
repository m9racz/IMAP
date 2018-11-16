#! /usr/bin/env python3

import IMAPTester
import time

#host = 'lenka.test.com'
host = 'super-test.com'
user = 'beta'
psw = 'a'

username = user + '@' + host


msgs = []
folders = []

def send_email(host, username):
    msg = IMAPTester.Email(host, username, username)
    msg.send()
    time.sleep(1)
    msg.ID = conn.get_msgid_by_subject(msg.subject)
    msg.flags = conn.get_flags(msg.ID)
    count = len(msgs)
    msgs.append(msg)
    return count

# 1. connect to server   
try:
    conn = IMAPTester.IW_connection(host, user, psw)
except Exception as err:
    print("can't connect to server")
    exit()





'''
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
''' 

# 3. set FLAG (\\Flagged & \\Completed)
conn.select()
response = conn.add_flags(b'2','\\Flagged')
print(response)


conn.logout()

# create folder


