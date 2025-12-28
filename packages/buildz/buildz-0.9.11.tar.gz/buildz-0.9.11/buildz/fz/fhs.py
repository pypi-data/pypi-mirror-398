#coding=utf-8

import hashlib
import os
#计算文件hash值
def fhash(fp, hm="sha256", blk_sz = 10240):
	if type(hm) == str:
		hm = getattr(hashlib, hm)()
	with open(fp, 'rb') as f:
		while True:
			bs = f.read(blk_sz)
			if len(bs)==0:
				break
			hm.update(bs)
	return hm.hexdigest()

pass
def bs_hash(bs, fhm):
	obj = fhm()
	obj.update(bs)
	return obj.hexdigest()

pass
def fhashs(fp, blk_size = 10240, max_read = -1, hm = "sha256"):
	if type(hm) == str:
		fhm = getattr(hashlib, hm)
	else:
		fhm = hm
	hashs = []
	if not os.path.isfile(fp) or max_read==0:
		return hashs
	size = 0
	bs = b""
	reads = 0
	mark_read = True
	with open(fp, 'rb') as f:
		while len(bs)>0 or mark_read:
			if max_read>0 and size>=max_read:
				break
			read_size = blk_size
			if max_read>0:
				read_size = min(max_read-size, blk_size)
			if mark_read:
				curr = f.read(read_size)
				if len(curr)==0:
					mark_read = False
				else:
					bs += curr
			if len(bs)>=read_size or not mark_read:
				tmp = bs[:read_size]
				bs = bs[read_size:]
				size+=read_size
				hashs.append(bs_hash(tmp, fhm))
	return hashs
	
