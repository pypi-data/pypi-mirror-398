#coding=utf-8

class Stack:
    def __getitem__(self, i):
        if i>=0:
            n = self.base+i
        else:
            n = self.last+i
        if n<self.base or n>=self.last:
            raise IndexError("index out of range")
        if n<0:
            raise Exception("up N<0")
            n+=self.size
        elif n>=self.size:
            raise Exception("up N>sz")
            n-=self.size
        return self.stack[n]
        if i == 0:
            return self.stack[self.base]
        elif i==-1:
            n = self.last-1
            if n<0:
                n+=self.size
            return self.stack[n]
        else:
            raise Exception("unsupport")
    def __init__(self, size):
        self.stack = [None]*size
        self.base = 0
        self.last = 0
        self.size = size
    def pop(self, i):
        if i==0:
            obj = self.stack[self.base]
            self.base+=1
            if self.base>self.last:
                raise Exception("unsupport X1")
            if self.base>=self.size:
                raise Exception("unsupport B")
                self.base -=self.size
        elif i==-1:
            self.last -=1 
            if self.base>self.last:
                raise Exception("unsupport X1")
            if self.last<0:
                raise Exception("unsupport A")
                self.last+=self.size
            obj = self.stack[self.last]
        else:
            raise Exception("unsupport")
        return obj
    def __len__(self):
        n = self.last - self.base
        if n<0:
            raise Exception("unsupport N1")
            n+=self.size
        elif n>=self.size:
            raise Exception("unsupport N2")
            n -= self.size
        return n
    def append(self, obj):
        self.stack[self.last]=obj
        self.last+=1
        if self.last>=self.size:
            raise Exception("unsupport C")
            self.last-=self.size

pass