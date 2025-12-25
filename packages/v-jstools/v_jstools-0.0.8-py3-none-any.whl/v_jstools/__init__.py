# coding=utf-8
import shutil
import os
import sys
import time
import json
import tempfile
def extractall(self, path=None, members=None, pwd=None):
    if members is None: members = self.namelist()
    path = os.getcwd() if path is None else os.fspath(path)
    for zipinfo in members:
        try:    _zipinfo = zipinfo.encode('cp437').decode('gbk')
        except: _zipinfo = zipinfo.encode('utf-8').decode('utf-8')
        print('[*] unpack...', _zipinfo)
        if _zipinfo.endswith('/') or _zipinfo.endswith('\\'):
            myp = os.path.join(path, _zipinfo)
            if not os.path.isdir(myp):
                os.makedirs(myp)
        else:
            myp = os.path.join(path, _zipinfo)
            youp = os.path.join(path, zipinfo)
            self.extract(zipinfo, path)
            if myp != youp:
                os.rename(youp, myp)
import zipfile
zipfile.ZipFile.extractall = extractall

import os
import shutil
import platform
import subprocess

def open_folder(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

def encbytefile(bytecode, password):
    def make_qequence(password):
        import re
        import hashlib
        if type(password) == str: password = password.encode()
        p = password
        r = b''
        for i in range(256):
            d = hashlib.md5(p)
            c = d.hexdigest().encode()
            r += c
            p = c
        r = r.decode()
        l = re.findall('..', r)
        l = list(map(lambda i:int(i,16), l))
        return l
    sequence = make_qequence(password)
    title = []
    for i, c in enumerate(bytecode[:4096*8]):
        title.append(c ^ sequence[i%len(sequence)])
    bytecode = bytes(title) + bytecode[4096*8:]
    return bytecode

def unpack(password):
    print('[*] unpack...')
    if not password: 
        print('[*] no password.')
        return
    localpath = os.path.split(__file__)[0]
    zfile = os.path.join(localpath, 'v_jstools.zip')
    tfile = os.path.join(localpath, 'temp.zip')
    if os.path.isfile(tfile): os.remove(tfile)
    with open(zfile, 'rb') as f1:
        with open(tfile, 'wb') as f2:
            f2.write(encbytefile(f1.read(), password.encode()))
    tpath = os.path.join(localpath, 'v_jstools')
    try:
        zf = zipfile.ZipFile(tfile)
        zf.extractall(path = tpath)
        zf.close()
        open_folder(tpath)
    except:
        if os.path.isdir(tpath):
            shutil.rmtree(tpath)
        print('[*] error password.')
        return

def execute():
    argv = sys.argv
    print('v_jstools :::: [ {} ]'.format(' '.join(argv)))
    if len(argv) == 1:
        print('[unpack]:  v_jstools unpack')
        return
    if len(argv) > 1:
        if argv[1] == 'unpack':
            password = None
            if len(argv) > 2:
                password = argv[2]
            unpack(password)
        return