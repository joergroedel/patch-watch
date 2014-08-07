#!/usr/bin/env python
#

import ConfigParser
import subprocess
import sys
import os

config_dir  = '~/.patches/'
config_file = '~/.patches/repos'
git         = '/usr/bin/git'

repo = ''
base = ''
head = ''

config = ConfigParser.RawConfigParser()

def create_config_dir():
	try:
		real_path = os.path.expanduser(config_dir)
		os.mkdir(real_path)
	except OSError:
		pass

def store_config():
	create_config_dir()
	file_name = os.path.expanduser(config_file)
	with open(file_name, 'w') as cfg_file:
		config.write(cfg_file)


def load_config(file_name):
	global repo, head, base
	file_name = os.path.expanduser(file_name)
	config.read(file_name)
	if (not config.has_section(repo)):
		print 'Initializing cache for ' + repo
		config.add_section(repo)
		config.set(repo, 'head', head)
		store_config()

def init_repo(path):
	global git, repo, head, base
	repo = path
	head = subprocess.check_output([git, 'show', '-s', '--format=%H', 'HEAD']).strip()
	load_config(config_file)
	base = config.get(repo, "head").strip()

def do_list():
	global base, head, repo;

	if (base == head):
		return 0;
	output = subprocess.check_output([git, 'log', '--reverse', '--no-merges', base + ".." + head])
	print output
	return 0

def do_update():
	print "Updating base to " + base
	config.set(repo, "head", base)
	store_config()
	return 0

def print_cmds():
	print "Available commands:"
	print "  list           List commits since last update"
	print "  update         Update base to current HEAD"
	print "  help           Show this help text"
	return 0

def main():
	sys.argv.pop(0)

	try:
		init_repo(os.getcwd())
	except ConfigParser.Error:
		print "Error loading config file " + config_file
		return 1

	cmd = "list"

	if (len(sys.argv) >= 1):
		cmd = sys.argv.pop(0)

	if (cmd == 'list'):
		return do_list()
	elif (cmd == 'update'):
		return do_update()
	else:
	 	return print_cmds()

if __name__ == '__main__':
	ret = main()
	if (ret > 255):
		ret = 1
	sys.exit(ret)

