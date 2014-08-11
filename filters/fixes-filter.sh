#!/bin/bash
#

GIT="/usr/bin/git"
commit=$1

$GIT show -s $commit | grep -i fix > /dev/null 2>&1

if [ "$?" == "0" ]; then
	echo "fix"
fi

exit 0
