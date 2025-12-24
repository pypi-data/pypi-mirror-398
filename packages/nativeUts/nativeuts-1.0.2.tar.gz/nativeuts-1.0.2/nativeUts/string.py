from forbiddenfruit import curse
import os
from pathlib import Path
import re
import posixpath


#============================  STRING
def only_numbers(self):
    return "".join([x for x in self if x in "0123456789"])

def usToNumber(self):
    return float(self.replace(",",""))

def brToNumber(self):
    num = re.sub(r"R|r|\$", "", self)
    num = num.replace(".","")
    num = num.replace(",",".")
    return float(num.strip() or '0')

def joinPath(self,*paths):
    return os.path.join(self, *paths)

def joinUrl(self,*paths):
    return posixpath.join(self, *paths)

def fileName(self,extension=True):
    if extension:
        return os.path.basename(self)
    return Path(self).stem

def isEmail(self):
    r = re.compile(r'^[\w-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$')
    return bool(r.match(self))

def isLike(self,pattern):
    r = re.compile(f"^{pattern}$")
    return bool(r.match(self))

def regx(self,pattern):
    return re.findall(pattern,self)


curse(str, "only_numbers", only_numbers)
curse(str, "usToNumber", usToNumber)
curse(str, "brToNumber", brToNumber)
curse(str, "isEmail", isEmail)
curse(str, "joinPath", joinPath)
curse(str, "joinUrl", joinUrl)
curse(str, "fileName", fileName)
curse(str, "isLike", isLike)
curse(str, "regx", regx)