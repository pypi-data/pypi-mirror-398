from datetime import datetime
from collections import defaultdict

dtfmt = "%Y-%m-%d %H:%M:%S"


class TimerEvent():
    def __init__(self):
        self.start = datetime.now()
        self.fmtstart = self.start.strftime(dtfmt)
        self.stoptm = None
        self.duration = None

    def stop(self):
        self.stoptm = datetime.now()
        self.fmtstop = self.stoptm.strftime(dtfmt)
        self.duration = self.stoptm - self.start


class Timer():
    def __init__(self):
        self.timers = defaultdict(list)

    def start(self, nm):
        self.timers[nm].append(TimerEvent())

    def stop(self, nm):
        self.timers[nm][-1].stop()

    def show(self):
        ar = []
        for nm, tm_list in self.timers.items():
            if len(tm_list) > 1:
                sfx = True
            else:
                sfx = False
            for idx, tm in enumerate(tm_list, start=1):
                if sfx == True:
                    dnm = f"{nm}.{idx}"
                else:
                    dnm = nm
                ar.append([dnm, tm.fmtstart, tm.fmtstop, tm.duration])

        print(f"{'Name'.ljust(30)} {'Duration'.ljust(20)} "
              f"{'Start Time'.ljust(20)} {'End Time'.ljust(20)}")
        print(f"{'=' * 30} {'=' * 20} "
              f"{'=' * 20} {'=' * 20}")
        for row in sorted(ar, key=lambda x: x[3], reverse=True):
            print(f"{row[0].ljust(30)} {str(row[3]).ljust(20)} "
                  f"{str(row[1]).ljust(20)} {str(row[2]).ljust(20)}")


obj = Timer()


def start(nm):
    obj.start(nm)


def stop(nm):
    obj.stop(nm)


def show():
    obj.show()
