from datetime import datetime
from collections import defaultdict
import inspect

flags = {"show": True}
cntr = defaultdict(int)


def disable_show():
    flags["show"] = False


def enable_show():
    flags["show"] = True


def show():
    if flags["show"] == False:
        return
    tm = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    callee = inspect.currentframe().f_back
    fl = callee.f_code.co_filename
    lno = callee.f_lineno
    cntr[(fl, lno)] += 1
    print(f"{tm} File={fl} Line={lno} Counter={cntr[(fl, lno)]}")
