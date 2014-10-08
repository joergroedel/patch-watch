#!/usr/bin/env python
#

import ConfigParser
import subprocess
import string
import json
import sys
import sets
import os

config_dir   = '~/.patches/'
config_file  = '~/.patches/repos'
watches_file = '~/.patches/config'
filter_file  = '~/.patches/filters'
git          = '/usr/bin/git'

commit_file = '~/.patches/commits'

repo = ''
base = ''
head = ''

config = ConfigParser.RawConfigParser();
watches = ConfigParser.RawConfigParser();

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
		ref_commit = ref_commit.upper()
		tag        = tag.upper()
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

def load_watches(file_name, watches):
	file_name = os.path.expanduser(file_name);
	if not os.path.isfile(file_name):
		return;
	watches.read(file_name);
	return;

def store_watches(file_name, watches):
	create_config_dir();
	file_name = os.path.expanduser(file_name)
	with open(file_name, 'w') as cfg_file:
		watches.write(cfg_file);
	return;

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
			mark = mark.strip()
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

def make_dict(commit, subject, markers):
	d = dict();
	d['id']      = commit;
	d['subject'] = subject;
	tags  = list();
	refs  = list();
	paths = list();
	for mark in markers:
		pos = mark.find(':');
		if (pos == -1):
			tags.append(mark.strip());
			continue;
		t, v = mark.split(':', 1);
		if t == 'git':
			refs.append(v);
		elif t == 'path':
			paths.append(v);
	d['tags'] = tags;
	d['refs'] = refs;
	d['paths'] = paths;
	return d;

def process_commits(lines, progress=False):
	data = list();

	current = 0;
	number  = len(lines);
	for line in lines:
		if progress:
			current += 1;
			percent = float(current) / float(number);
			message = '\rProcessing {c}/{n} ({p:.2%} done)'.format(c=current, n=number, p=percent);
			print message,

		line = line.strip();
		if line == '':
			continue
		commit, subject = line.split(' ', 1);
		markers = apply_filters(commit);
		data.append(make_dict(commit, subject, markers));

	return data;

def do_list():
	global base, head, repo;

	# git log --no-merges --reverse -s --format="%H %s"
	if (base == head):
		return 0;
	output = subprocess.check_output([git, 'log', '--reverse', '--no-merges', '-s', '--format=%H %s', base + ".." + head])
	lines = output.split('\n');

	print json.dumps(process_commits(lines));

	return 0

def write_db_file(file_name, data):
	file_name = os.path.expanduser(file_name);
	with open(file_name, 'w') as db_file:
		json.dump(data, db_file, indent=8);
	return;

def read_db_file(file_name):
	file_name = os.path.expanduser(file_name);
	with open(file_name, 'r') as db_file:
		data = json.load(db_file);
	return data;

def do_init(argv):
	if len(argv) != 2:
		print "Init needs 2 arguments: name base";
		return 1;

	name = argv.pop(0);
	base = argv.pop(0);

	if (watches.has_section(name)):
		print name + " already exists";
		return 1;

	db_file = config_dir + name + '.json'
	output = subprocess.check_output([git, 'log', '--format=%H %s', base + '~1..' + base]);
	data = process_commits(output.split('\n'));
	write_db_file(db_file, data);

	watches.add_section(name);
	watches.set(name, 'database', db_file)

	store_watches(watches_file, watches);

	return 0;

def do_update(argv):

	if len(argv) < 1:
		print "Update needs database as parameter"
		return 1;
	name = argv.pop(0);

	head = 'HEAD';
	if len(argv) > 0:
		head = argv.pop(0);

	if not watches.has_section(name):
		print "Unknown database: " + name;
		return 1;

	db_file = watches.get(name, 'database');
	data = read_db_file(db_file);
	last_commit = data[len(data)-1]['id'];

	output = subprocess.check_output([git, 'log', '--reverse', '--no-merges', '-s', '--format=%H %s', last_commit + ".." + head])
	ndata = process_commits(output.split('\n'), progress=True);

	write_db_file(db_file, data + ndata);

	return 0;

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
	load_watches(watches_file, watches);

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
		return do_update(sys.argv)
	elif (cmd == 'init'):
		return do_init(sys.argv);
	else:
	 	return print_cmds()

if __name__ == '__main__':
	ret = main()
	if (ret > 255):
		ret = 1
	sys.exit(ret)

