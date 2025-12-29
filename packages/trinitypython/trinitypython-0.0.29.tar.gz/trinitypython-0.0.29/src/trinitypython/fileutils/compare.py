from difflib import HtmlDiff
from pathlib import Path
from . import compare_dir

def compare_files(file1, file2, outfile):
    fromlines = Path(file1).read_text().splitlines()
    tolines = Path(file2).read_text().splitlines()
    txt = HtmlDiff(tabsize=4, wrapcolumn=60).make_file(fromlines=fromlines,
                     tolines=tolines, fromdesc=str(file1),
                     todesc=str(file2), context=True)
    Path(outfile).write_text(txt)


def compare_dirs(lft_dir, rt_dir):
    return compare_dir.CompareDir(lft_dir, rt_dir)

