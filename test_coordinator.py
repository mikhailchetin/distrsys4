from coordinator import Coordinator
import sys


class TestFailedException(Exception):
    pass


def test(info, master, backup, number, description):
    if info.master != master:
        sys.stderr.write("Wrong master: expected %s, got %s\n" % (master, info.master))
        raise TestFailedException(description)
    if info.backup != backup:
        sys.stderr.write("Wrong backup: expected %s, got %s\n" % (backup, info.backup))
        raise TestFailedException(description)
    if info.number != number:
        sys.stderr.write("Wrong view number: expected %s, got %s\n" % (number, info.number))
        raise TestFailedException(description)

    sys.stderr.write("Test passed: %s\n" % description)


def main():
    service = Coordinator()
    longDelay = service.deadPings * 2
    srv1 = "http://localhost:10001"
    srv2 = "http://localhost:10002"
    srv3 = "http://localhost:10003"
    currentView = 0

    try:
        # no ready servers
        if service.master() is not None:
            raise TestFailedException("no ready servers")
        sys.stderr.write("Test passed: no ready servers\n")

        # first master
        for i in range(longDelay):
            info = service.ping(0, srv1)
            if info.number == currentView + 1:
                break
            service.tick()
        currentView += 1
        test(info, srv1, None, currentView, "first master")

        # first backup
        for i in range(longDelay):
            service.ping(currentView, srv1)
            info = service.ping(0, srv2)
            if info.number == currentView + 1:
                break
            service.tick()
        currentView += 1
        test(info, srv1, srv2, currentView, "first backup")

        # master fails, backup should take over
        service.ping(2, srv1)
        for i in range(longDelay):
            info = service.ping(2, srv2)
            if info.number == currentView + 1:
                break
            service.tick()
        currentView += 1
        test(info, srv2, None, currentView, "backup takes over")

        # first server restarts, should become backup
        for i in range(longDelay):
            service.ping(currentView, srv2)
            info = service.ping(0, srv1)
            if info.number == currentView + 1:
                break
            service.tick()
        currentView += 1
        test(info, srv2, srv1, currentView, "restarted server becomes backup")

        # master fails, third server appears,
        # backup should become master, new server - backup
        service.ping(currentView, srv2)
        for i in range(longDelay):
            service.ping(currentView, srv1)
            info = service.ping(0, srv3)
            if info.number == currentView + 1:
                break
            service.tick()
        currentView += 1
        test(info, srv1, srv3, currentView, "spare server becomes backup")

        # master quickly restarts, should not be master anymore
        service.ping(currentView, srv1)
        for i in range(longDelay):
            service.ping(0, srv1)
            info = service.ping(currentView, srv3)
            if info.number == currentView + 1:
                break
            service.tick()
        currentView += 1
        test(info, srv3, srv1, currentView, "master reboots")

        # set up a number with just 3 as master,
        # to prepare for the next test.
        for i in range(longDelay):
            info = service.ping(currentView, srv3)
            service.tick()
        currentView += 1
        test(info, srv3, None, currentView, "master only")

        # backup appears but master does not ack
        for i in range(longDelay):
            service.ping(0, srv1)
            info = service.ping(currentView, srv3)
            if info.number == currentView + 1:
                break
            service.tick()
        currentView += 1
        test(info, srv3, srv1, currentView, "master doesn't ack")

        # master didn't ack and dies
        # check that backup is not promoted
        for i in range(longDelay):
            info = service.ping(currentView, srv1)
            if info.number == currentView + 1:
                break
            service.tick()
        test(info, srv3, srv1, currentView, "do not promote backup")

        # master finally acks
        for i in range(longDelay):
            service.ping(currentView, srv3)
            info = service.ping(currentView, srv1)
            if info.number == currentView + 1:
                break
            service.tick()
        test(info, srv3, srv1, currentView, "master acks")

        # backup suddenly restarts
        # should become backup anew
        for i in range(longDelay):
            service.ping(currentView, srv3)
            info = service.ping(0, srv1)
            if info.number == currentView + 1:
                break
            service.tick()
        currentView += 1
        test(info, srv3, srv1, currentView, "backup reboots")

    except TestFailedException as e:
        sys.stderr.write("Test failed: %s\n" % e)


if __name__ == "__main__":
    main()
