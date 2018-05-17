from xmlrpclib import ServerProxy, Fault
from cmd import Cmd
from random import choice
from string import lowercase
from server import Node,UNHANDLED  
from threading import Thread
from time import sleep
import sys
HEAD_START = 0.1
SECRET_LENGTH = 10000000
def randomString(length):
    chars = []
    letters = lowercase[:26]
    while length > 0:
        length -= 1
        chars.append(choice(letters))
    return ''.join(chars)
class Client(Cmd):
    prompt = '> '
    def __init__(self, url, dirname, urlfile):
        Cmd.__init__(self)
        self.secret = randomString(SECRET_LENGTH)
        n = Node(url, dirname, self.secret)
        t = Thread(target = n._start)
        t.setDaemon(1)
        t.start()
        sleep(HEAD_START)
        self.server = ServerProxy(url)
        for line in open(urlfile):
            line = line.strip()
            self.server.hello(line)
    def do_fetch(self, arg):
        try:
            self.server.fetch(arg,self.secret)
        except Fault,f:
            if f.faultCode != UNHANDLED: raise
            print "The file isn't found",arg
    def do_exit(self,arg):
        print
        sys.exit()
    do_EOR = do_exit
def main():
    client = Client('master', ./, refprofile)
    client.cmdloop()
if __name__ == '__main__':main()
