import time
from .los import *
class pos():
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
class clock():
    def __init__(self, h=0, m=0, s=0):
        self.h = h
        self.m = m
        self.s = s
    def str(self, a='0:0:0'):
        x=a.split(':')
        self.h = int(x[0])
        self.m = int(x[1])
        self.s = int(x[2])
    def put(self):
        return f'{self.h}:{self.m}:{self.s}'
    #更新为实时时间
    def get(self):
        self.h = time.localtime().tm_hour
        self.m = time.localtime().tm_min
        self.s = time.localtime().tm_sec
class date():
    def __init__(self, y=0, m=0, d=0):
        self.y = y
        self.m = m
        self.d = d
    def str(self, a='0-0-0',s='-'):
        x=a.split(s)
        self.y = int(x[0])
        self.m = int(x[1])
        self.d = int(x[2])
    def put(self,s='-'):
        return f'{self.y}{s}{self.m}{s}{self.d}'
    def get(self):
        self.y = time.localtime().tm_year
        self.m = time.localtime().tm_mon
        self.d = time.localtime().tm_mday
class requst():
    def __init__(self):
        pass
    def get(self,url):
        cmd(f"curl {url}")
    def post(self,url,head,data):
        cmd(f"curl -X POST {url} -H \"{head}\" -d \"{data}\"")
