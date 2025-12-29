from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter


class FileInfo():
    def __init__(self, fl):
        self.fl = Path(fl)
        self.stat = self.fl.stat()
        self.mtime = datetime.fromtimestamp(self.stat.st_mtime)
        self.fmttime = self.mtime.strftime("%Y-%m-%d %H:%M:%S")
        self.size = self.stat.st_size
        self.parent = str(self.fl.parent)
        self.get_size_in_human_form()
        self.details = [self.fl, self.size, self.size_human, self.mtime,
                        self.fmttime]

    def get_size_in_human_form(self):
        if self.size > 1000000000:
            self.size_human = f"{self.size / 1000000000} GB"
        elif self.size > 1000000:
            self.size_human = f"{self.size / 1000000} MB"
        elif self.size > 1000:
            self.size_human = f"{self.size / 1000} KB"
        else:
            self.size_human = f"{self.size} Bytes"


class DirInfo():
    def __init__(self, dr):
        self.__dr = Path(dr)
        self.__files = []
        self.__load_files()

    def __load_files(self):
        for fl in self.__dr.rglob("*"):
            if fl.is_file():
                self.__files.append(FileInfo(fl))

    def sort_by_time(self):
        return [x.details for x in sorted(self.__files, key=lambda y: y.mtime)]

    def sort_by_size(self):
        return [x.details for x in sorted(self.__files, key=lambda y: y.size,
                                          reverse=True)]

    def modified_within(self, mins):
        reftm = datetime.now() - timedelta(minutes=mins)
        return [x.details for x in sorted(self.__files, key=lambda y: y.mtime,
                                          reverse=True) if x.mtime > reftm]

    def modified_before(self, mins):
        reftm = datetime.now() - timedelta(minutes=mins)
        return [x.details for x in sorted(self.__files, key=lambda y: y.mtime,
                                          reverse=True) if x.mtime < reftm]

    def sort_by_file_count(self):
        return sorted(list(Counter([x.parent for x in self.__files]).items()),
                      key=lambda x: x[1], reverse=True)
