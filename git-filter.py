#!/usr/bin/env python
#

import subprocess
import string
import sys

git = '/usr/bin/git'

def check_line(line):
	tokens = line.split(' ');
	for token in tokens:
		token = token.strip(' \t\r:;.,<>[]()-_=+~')
		if (len(token) < 8):
			continue
		is_hash = True
		for c in token:
			f = string.find(string.hexdigits, c)
			if f == -1:
				is_hash = False
				break
		if is_hash:
			print token
	return

def main():
	global git

	for line in sys.stdin:
		line = line.strip()
		check_line(line)

	return 0


if __name__ == '__main__':
	ret = main()
	if (ret > 255):
		ret = 1
	sys.exit(ret)
