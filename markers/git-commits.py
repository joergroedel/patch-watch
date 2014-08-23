#!/usr/bin/env python
#

import subprocess
import string
import sys

git = '/usr/bin/git'

def check_commit(commit):
	try:
		full_commit = subprocess.check_output([git, 'show', '-s', '--format=%H', commit],stderr=subprocess.STDOUT).strip()
	except subprocess.CalledProcessError:
		return

	print "git:"+full_commit
	return

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
			check_commit(token)
	return

def main():
	global git

	sys.argv.pop(0)
	if len(sys.argv) < 1:
		return 1
	commit = sys.argv.pop(0)

	try:
		lines = subprocess.check_output([git, 'show', '-s', commit], stderr=subprocess.STDOUT).split('\n')
	except subprocess.CalledProcessError:
		return 1

	body = False
	for line in lines:
		line = line.strip()
		if line == '':
			body = True
			continue
		if not body:
			continue
		check_line(line)

	return 0


if __name__ == '__main__':
	ret = main()
	if (ret > 255):
		ret = 1
	sys.exit(ret)
