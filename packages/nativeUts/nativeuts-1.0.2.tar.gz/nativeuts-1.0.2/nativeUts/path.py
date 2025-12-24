from forbiddenfruit import curse
import os
from pathlib import Path
import glob
import shutil

#============================  PATH

def clear(self,only_files=False):
    if only_files:
        files = glob.glob(os.path.join(self, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
    else:
        shutil.rmtree(self)
        os.makedirs(self, exist_ok=True)

curse(Path, "clear", clear)

