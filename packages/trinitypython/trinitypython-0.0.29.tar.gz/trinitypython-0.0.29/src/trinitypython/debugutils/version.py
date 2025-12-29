import pkg_resources
from datetime import datetime
from pathlib import Path
import json


def _get_current_package_dict():
    ar = [str(x).split()[:2] for x in pkg_resources.working_set]
    return {x[0]: x[1] for x in ar}


def _get_file_list(app, fldr):
    return list(Path(fldr).glob(f"{app}_package*.json"))


def _get_latest_file(app, fldr):
    return sorted(_get_file_list(app, fldr))[-1]


def _load_file(fl):
    return json.loads(Path(fl).read_text())


def save(app, fldr):
    tm = datetime.now().strftime("%Y%m%d_%H%M%S")
    ofl = Path(fldr) / f"{app}_package_{tm}.json"
    ofl.write_text(json.dumps(_get_current_package_dict(), indent=2))


def _compare_dict(new, old):
    out = {}
    out['added'] = {x: new[x] for x in set(new.keys()) - set(old.keys())}
    out['removed'] = {x: old[x] for x in set(old.keys()) - set(new.keys())}
    out['modified'] = {x: new[x] for x in set(new.keys()) & set(old.keys())
                       if new[x] != old[x]}
    return out


def _print_diff(cur_pkg, prev_pkg):
    diff = _compare_dict(cur_pkg, prev_pkg)
    for typ in sorted(diff.keys()):
        if diff[typ]:
            print(f"  {typ} -->")
            print("\n".join([f"    {k} = {v}" for k, v in diff[typ].items()]))


def compare(app, fldr):
    prev_pkg = _load_file(_get_latest_file(app, fldr))
    cur_pkg = _get_current_package_dict()
    _print_diff(cur_pkg, prev_pkg)


def timeline(app, fldr):
    cur_pkg = _get_current_package_dict()
    nm = "Current"
    for fl in sorted(_get_file_list(app, fldr), reverse=True):
        prev_pkg = _load_file(fl)
        print(f"\n{nm}")
        _print_diff(cur_pkg, prev_pkg)
        cur_pkg = prev_pkg
        tm = fl.name.replace(f"{app}_package_", "").split(".")[0]
        nm = datetime.strptime(tm, "%Y%m%d_%H%M%S").isoformat()
