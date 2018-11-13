import imaplib
import time

host = 'lenka.test.com'
username = 'beta@lenka.test.com'
pw = 'a'


while(1):
    conn = imaplib.IMAP4(host)
    conn.login(username, pw)
    conn.xatom('SELECT "INBOX"')
    conn.xatom('UID SEARCH SINCE 23-Aug-2018')
    conn.xatom('CLOSE')
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    print(conn._simple_command('SELECT', "INBOX"))
    conn.logout()
