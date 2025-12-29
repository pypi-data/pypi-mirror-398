import difflib
from pathlib import Path
from . import html_template
from typing import List


class CompareDir():
    def __init__(self, lft_dir, rt_dir):
        self.files_only_in_left: List[Path] = []
        self.dirs_only_in_left: List[Path] = []
        self.files_only_in_right: List[Path] = []
        self.dirs_only_in_right: List[Path] = []
        self.__dirs_in_left = set()
        self.__dirs_in_right = set()
        self.__files_in_left = set()
        self.__files_in_right = set()
        self.__files_in_both = set()
        self.__lft_dir = Path(lft_dir)
        self.__rt_dir = Path(rt_dir)
        self.__files_in_both_same = []
        self.__files_in_both_diff = ""
        self.__compare()

    def __load_left(self):
        for fl in self.__lft_dir.rglob("*"):
            if fl.is_dir():
                self.__dirs_in_left |= {str(fl.relative_to(self.__lft_dir))}
            else:
                self.__files_in_left |= {str(fl.relative_to(self.__lft_dir))}

    def __load_right(self):
        for fl in self.__rt_dir.rglob("*"):
            if fl.is_dir():
                self.__dirs_in_right |= {str(fl.relative_to(self.__rt_dir))}
            else:
                self.__files_in_right |= {str(fl.relative_to(self.__rt_dir))}

    def __compare_dirs(self):
        for fl in self.__dirs_in_left - self.__dirs_in_right:
            self.dirs_only_in_left.append(self.__lft_dir / fl)
        for fl in self.__dirs_in_right - self.__dirs_in_left:
            self.dirs_only_in_right.append(self.__rt_dir / fl)

    def __compare_files(self):
        for fl in self.__files_in_left - self.__files_in_right:
            self.files_only_in_left.append(self.__lft_dir / fl)
        for fl in self.__files_in_right - self.__files_in_left:
            self.files_only_in_right.append(self.__rt_dir / fl)
        for fl in self.__files_in_left & self.__files_in_right:
            self.__files_in_both |= {fl}

    def __compare(self):
        self.__load_left()
        self.__load_right()
        self.__compare_dirs()
        self.__compare_files()

    def __gen_html_table(self, lft_txt, rt_txt):
        return difflib.HtmlDiff(tabsize=4, wrapcolumn=60) \
            .make_table(fromlines=lft_txt.splitlines(),
                        tolines=rt_txt.splitlines(),
                        fromdesc=str(self.__lft_dir),
                        todesc=str(self.__rt_dir),
                        context=True)

    def __file_compare(self, dtl_diff_extn):
        for fl in self.__files_in_both:
            fl_pth = self.__lft_dir / fl
            if any([fl_pth.name.endswith(x) for x in dtl_diff_extn]):
                lft_txt = (self.__lft_dir / fl).read_text(errors="ignore")
                rt_txt = (self.__rt_dir / fl).read_text(errors="ignore")
                if lft_txt == rt_txt:
                    self.__files_in_both_same.append(fl)
                else:
                    self.__files_in_both_diff += "<p>" + fl + "<br />"
                    self.__files_in_both_diff += self.__gen_html_table(
                        lft_txt, rt_txt)

    def gen_html_report(self, ofl, dtl_diff_extn):
        self.__file_compare(dtl_diff_extn)

        out = html_template.diff_hdr
        out += f"<p><b>Files present only in {self.__lft_dir}</b><br />"
        out += "<br />".join(sorted([str(x.relative_to(self.__lft_dir)) for x in
                                     self.files_only_in_left]))
        out += "<p>"
        out += f"<p><b>Files present only in {self.__rt_dir}</b><br />"
        out += "<br />".join(sorted([str(x.relative_to(self.__rt_dir)) for x in
                                     self.files_only_in_right]))
        out += "<p>"
        out += f"<p><b>Directories present only in {self.__lft_dir}</b><br />"
        out += "<br />".join(sorted([str(x.relative_to(self.__lft_dir)) for x in
                                     self.dirs_only_in_left]))
        out += "<p>"
        out += f"<p><b>Directories present only in {self.__rt_dir}</b><br />"
        out += "<br />".join(sorted([str(x.relative_to(self.__rt_dir)) for x in
                                     self.dirs_only_in_right]))
        out += "<p>"
        xtn_lst = ",".join(dtl_diff_extn)
        out += "<p><b>Files present in both directores and are same</b><br />"
        out += f"<b>Looking for extensions - {xtn_lst}</b><br />"
        out += "<br />".join(sorted(self.__files_in_both_same))
        out += "<p>"
        out += "<p><b>Files present in both directores and are " \
               "different</b><br />"
        out += f"<b>Looking for extensions - {xtn_lst}</b><br />"
        out += self.__files_in_both_diff
        out += "<p>"
        out += html_template.diff_trl
        Path(ofl).write_text(out, errors="ignore")
