#!/bin/bash
#

GIT="/usr/bin/git"
commit=$1

$GIT show -s $commit | grep -i fix > /dev/null 2>&1

if [ "$?" == "0" ]; then
	exit 1
fi

exit 0
