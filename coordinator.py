from SimpleXMLRPCServer import SimpleXMLRPCServer


class Info:
    def __init__(self, master, backup, viewNumber):
        self.master = master
        self.backup = backup
        self.number = viewNumber


class Coordinator:
    deadPings = 5

    def __init__(self):
        self.info = Info(None, None, 0)
        self.freeServers = []
        #times till death
        self.freeServersTimes = []
        self.backupTime = self.deadPings
        self.masterTime = self.deadPings
        self.dataCopied = False
        self.validView = True

    def ping(self, viewNumber, server):
        if server not in [self.info.master, self.info.backup]:
            if server not in self.freeServers:
                self.freeServers.append(server)
                self.freeServersTimes.append(self.deadPings)
            self.freeServersTimes[self.freeServers.index(server)] = self.deadPings
            flag = False
            if not self.info.backup:
                if self.validView:
                    self.replace_backup()
                    flag = True
            if not self.info.master:
                if self.validView:
                    self.replace_master()
                    flag = True
            if flag:
                self.validView = False
                self.info.number += 1
        else:
            if viewNumber == self.info.number:
                if server == self.info.master:
                    self.validView = True
                    self.masterTime = self.deadPings
                    if self.info.backup:
                        self.dataCopied = True
                else:
                    self.backupTime = self.deadPings
            elif viewNumber == 0:
                if server == self.info.master:
                    if self.validView and self.dataCopied:
                        self.freeServers.append(server)
                        self.freeServersTimes.append(self.deadPings)
                        self.replace_master()
                        self.validView = False
                        self.info.number += 1
                else:
                    if self.validView:
                        self.freeServers.append(server)
                        self.freeServersTimes.append(self.deadPings)
                        self.replace_backup()
                        self.validView = False
                        self.info.number += 1
        return self.info

    def master(self):
        return self.info.master

    def backup(self):
        return self.info.backup

    def replace_backup(self):
        self.dataCopied = False
        if len(self.freeServers):
            self.info.backup = self.freeServers.pop()
            self.backupTime = self.freeServersTimes.pop()
            return True
        else:
            self.info.backup = None
            self.backupTime = self.deadPings
            return False

    def replace_master(self):
        if self.info.backup:
            self.info.master = self.info.backup
            self.masterTime = self.backupTime
            self.info.backup = None
            self.backupTime = self.deadPings
            self.replace_backup()
            return True
        else:
            if len(self.freeServers):
                self.replace_backup()
                self.replace_master()
                return True
            else:
                self.info.master = None
                self.masterTime = self.deadPings
                return False

    def tick(self):
        if self.info.backup and self.backupTime:
            self.backupTime -= 1
        if self.info.master and self.masterTime:
            self.masterTime -= 1
        if self.backupTime == 0:
            if self.validView:
                self.replace_backup()
                self.validView = False
                self.info.number += 1
        if self.masterTime == 0:
            if self.validView:
                self.replace_master()
                self.validView = False
                self.info.number += 1
        for i in xrange(len(self.freeServersTimes)):
            self.freeServersTimes[i] -= 1
            if self.freeServersTimes[i] == 0:
                self.freeServers.pop(i)
                self.freeServersTimes.pop(i)


def main():
    server = SimpleXMLRPCServer(("localhost", 10000), allow_none=True)
    server.register_instance(Coordinator())
    server.serve_forever()


if __name__ == "__main__":
    main()

