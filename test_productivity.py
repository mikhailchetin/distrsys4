import xmlrpclib
import os
import datetime
from threading import Thread

N = 1000


def test_master(coordinator, server1, storage):
    server1.clear_storage() #to make sure storage is clean before testing
    start = datetime.datetime.now()
    for i in xrange(N):
        coordinator.tick()
        server1.tick()
        server1.put(storage[i][0], storage[i][1])
    end = datetime.datetime.now()
    total_time = 60 * end.minute + end.second + end.microsecond * 1e-6 - 60 * start.minute - start.second - start.microsecond * 1e-6
    print total_time, "seconds for", N, "queries"
    print int(N/total_time), "queries per second by master only"


def test_master_backup(coordinator, server1, server2, storage):
    server1.clear_storage()
    server2.clear_storage()
    start = datetime.datetime.now()
    for i in xrange(N):
        coordinator.tick()
        server1.tick()
        server2.tick()
        server1.put(storage[i][0], storage[i][1])
    end = datetime.datetime.now()
    total_time = 60 * end.minute + end.second + end.microsecond * 1e-6 - 60 * start.minute - start.second - start.microsecond * 1e-6
    print total_time, "seconds for", N, "queries"
    print int(N/total_time), "queries per second by master with backup"
    server1.clear_storage()
    server2.clear_storage()


def tick_server(server1):
    server1.tick()


def send_put_requests(server1, storage):
    start = datetime.datetime.now()
    for i in xrange(2 * N, 3 * N):
        #debug message to make sure master is getting put requests simultaneously with copying data to backup
        #print "Sending put request", storage[i][0]
        server1.put(storage[i][0], storage[i][1])
    end = datetime.datetime.now()
    total_time = 60 * end.minute + end.second + end.microsecond * 1e-6 - 60 * start.minute - start.second - start.microsecond * 1e-6
    print total_time, "seconds for", N, "queries"
    print int(N/total_time), "queries per second by master copying to backup"


def test_copy(coordinator, server1, server2, storage):
    server1.clear_storage()
    server2.clear_storage()

    #filling storage in master, backup is absent
    for i in xrange(2 * N):#filling with 2N pairs to make sure copying will be longer
        coordinator.tick()
        server1.tick()
        server1.put(storage[i][0], storage[i][1])

    #backup appears
    server2.tick()

    #this thread calls tick for master, which invokes copying data to new backup
    thread1 = Thread(target=tick_server, args=[server1])

    #meanwhile, this thread calls function invoking many put requests to master
    thread2 = Thread(target=send_put_requests, args=(server1, storage))

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

def main():
    # before running test, please ensure that modules
    # are running on the following addresses:
    coord_name = "http://localhost:10000"
    srv1_name = "http://localhost:10001"
    srv2_name = "http://localhost:10002"

    coordinator = xmlrpclib.ServerProxy(coord_name)
    server1 = xmlrpclib.ServerProxy(srv1_name)
    server2 = xmlrpclib.ServerProxy(srv2_name)

    #generating keys and values beforehand to avoid spending time on this during testing
    storage = [
        [os.urandom(4).encode('hex'), os.urandom(4).encode('hex')] for i in xrange(3 * N)
    ]

    test_master(coordinator, server1, storage)
    test_master_backup(coordinator, server1, server2, storage)
    test_copy(coordinator, server1, server2, storage)

if __name__ == "__main__":
    main()