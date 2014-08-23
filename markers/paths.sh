#!/bin/bash
#

GIT="/usr/bin/git"
DIFFSTAT="/usr/bin/diffstat"
commit=$1

for path in `$GIT show -p $commit | diffstat -p1 -l`; do
	echo "PATH:$path"
done
