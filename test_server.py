import xmlrpclib
import sys


class TestFailedException(Exception):
    pass


def test(condition, description):
    if not condition:
        raise TestFailedException()
    sys.stderr.write("Test passed: %s\n" % description)


def main():
    # before running test, please ensure that modules
    # are running on the following addresses:
    coord_name = "http://localhost:10000"
    srv1_name = "http://localhost:10001"
    srv2_name = "http://localhost:10002"

    coordinator = xmlrpclib.ServerProxy(coord_name, allow_none=True)
    server1 = xmlrpclib.ServerProxy(srv1_name, allow_none=True)
    server2 = xmlrpclib.ServerProxy(srv2_name, allow_none=True)
    longDelay = 10

    try:
        # first master
        for i in range(longDelay):
            coordinator.tick()
            server1.tick()
        test(coordinator.master() == srv1_name, "first master")
        server1.put("a", "aaa")
        test(server1.get("a") == "aaa", "first master")

        # first backup
        for i in range(longDelay):
            coordinator.tick()
            server1.tick()
            server2.tick()
        test(coordinator.master() == srv1_name, "first backup")
        server1.put("b", "bbb")
        test(server1.get("b") == "bbb", "first backup")

        # master fails
        for i in range(longDelay):
            coordinator.tick()
            server2.tick()
        test(coordinator.master() == srv2_name, "master fails")
        test(server2.get("a") == "aaa", "master fails")
        test(server2.get("b") == "bbb", "master fails")

        # ex-master restarts
        for i in range(longDelay):
            coordinator.tick()
            server1.tick()
            server2.tick()
        test(coordinator.master() == srv2_name, "ex-master restarts")

        # oh no! network partition
        # client sees server2, but coordinator does not
        for i in range(longDelay):
            coordinator.tick()
            server1.tick()
        test(coordinator.master() == srv1_name, "network partition")
        test(server1.get("a") == "aaa", "network partition")
        test(server1.get("b") == "bbb", "network partition")
        try:
            server2.put("c", "ccc")
            raise TestFailedException("Must throw!")
        except xmlrpclib.Fault, fault:
            pass # ok

    except TestFailedException as e:
        sys.stderr.write("Test failed: %s\n" % e)


if __name__ == "__main__":
    main()