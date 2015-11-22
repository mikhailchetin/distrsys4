import xmlrpclib
import sys
from SimpleXMLRPCServer import SimpleXMLRPCServer


class Server():
    def __init__(self, name, coord_name):
        self.coordinator = xmlrpclib.ServerProxy(coord_name)
        self.name = name
        self.viewNumber = 0
        self.storage = {}

    def additem(self, key, value):
        self.storage[key] = value

    def tick(self):
        newView = self.coordinator.ping(self.viewNumber, self.name)['number']
        if self.viewNumber != newView:
            for key, value in self.storage.items():
                self.put_backup(key, value)
            self.viewNumber = self.coordinator.ping(newView, self.name)['number']

    def put(self, key, value):
        print "My name is ", self.name
        print "I put key ", key, " and value ", value, " inside me"
        if self.coordinator.master() and self.name == self.coordinator.master():
            self.additem(key, value)
            self.put_backup(key, value)
        else:
            raise Exception()

    def put_backup(self, key, value):
        if self.coordinator.backup() and not self.name == self.coordinator.backup():
            backup = xmlrpclib.ServerProxy(self.coordinator.backup())
            backup.additem(key, value)

    def get(self, key):
        return self.storage[key]


def main():
    server = SimpleXMLRPCServer((sys.argv[1], int(sys.argv[2])), allow_none=True)
    server.register_instance(Server('http://' + sys.argv[1] + ':' + sys.argv[2], "http://localhost:10000"))
    server.serve_forever()

if __name__ == "__main__":
    main()