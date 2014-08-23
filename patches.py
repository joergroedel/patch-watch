#!/usr/bin/env python
#

import ConfigParser
import subprocess
import string
import sys
import sets
import os

config_dir  = '~/.patches/'
config_file = '~/.patches/repos'
filter_file = '~/.patches/filters'
git         = '/usr/bin/git'

commit_file = '~/.patches/commits'

repo = ''
base = ''
head = ''

config = ConfigParser.RawConfigParser()

filters = [ ]
commits = sets.Set()

def load_commits(file_name):
	file_name = os.path.expanduser(file_name)
	if not os.path.isfile(file_name):
		return
	fd = open(file_name, 'r')
	for line in fd:
		line = line.strip().upper()
		commits.add(line)
	fd.close()
	return

def match_commits(commit, subject, markers):
	global commits
	if (len(markers) == 0):
		return False
	commit = commit.upper()
	if commit in commits:
		return False
	for mark in markers:
		if len(mark) != 44:
			continue
		pos = mark.find(':')
		if (pos == -1):
			continue
		tag, ref_commit = mark.split(':', 1)
		if (tag != 'GIT'):
			continue
		if ref_commit in commits:
			return True
	return False

def load_filters(file_name):
	file_name = os.path.expanduser(file_name)
	fd = open(file_name, 'r')
	for line in fd:
		line = line.strip()
		if len(line) < 1 or line[0] == '#':
			continue
		if (not os.path.isfile(line)) or (not os.access(line, os.X_OK)):
			print "Warning: Filter does not exist or is not executable: " + line
			continue
		filters.append(line)
	if (len(filters) == 0):
		print "Warning: No valid filters found"
	fd.close()
	return

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

def parse_markers(output):
	ret = sets.Set([ ])
	lines = output.split('\n')
	for line in lines:
		line    = line.strip()
		markers = line.split(' ')
		for mark in markers:
			mark = mark.strip().upper()
			if (len(mark) > 0):
				ret.add(mark)
	return ret

def apply_filters(commit):
	markers = sets.Set([ ])
	for f in filters:
		output = subprocess.check_output([f, commit]).strip()
		markers.update(parse_markers(output))

	return markers;

def print_commit(commit, subject, markers):
	if (len(markers) == 0):
		return
	mark_str = ''
	for mark in markers:
		mark_str += " [" + mark + "]"
	print "Commit: " + commit + " Subject: " + subject + " Tags: " + mark_str
	return

def do_list():
	global base, head, repo;

	# git log --no-merges --reverse -s --format="%H %s"
	if (base == head):
		return 0;
	output = subprocess.check_output([git, 'log', '--reverse', '--no-merges', '-s', '--format=%H %s', base + ".." + head])
	lines = output.split('\n');
	commits = matches = 0;
	for line in lines:
		line = line.strip();
		if line == '':
			continue
		commits += 1
		commit, subject = line.split(' ', 1);
		markers = apply_filters(commit)
		if match_commits(commit, subject, markers):
			print_commit(commit, subject, markers)
			matches += 1

	print "Commits: " + str(commits) + " Matches: " + str(matches)

	return 0

def do_update():
	print "Updating base to " + head
	config.set(repo, "head", head)
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

	load_filters(filter_file)
	load_commits(commit_file)

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

