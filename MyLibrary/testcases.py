#! /usr/bin/env python3

import IMAPTester
import time

#host = 'lenka.test.com'
host = 'super-test.com'
user = 'beta'
psw = 'a'

username = user + '@' + host




# connect to server   
try:
    conn = IMAPTester.IW_connection(host, user, psw)
except Exception as err:
    print("can't connect to server")
    exit()

#send test MSG
msg1 = IMAPTester.email(host, username, username)
msg1.send()
time.sleep(1)
msg1.ID = conn.get_msgid_by_subject(msg1.subject)


#conn.logout()

# create folder
