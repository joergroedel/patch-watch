#!/bin/bash
#

GIT="/usr/bin/git"
commit=$1

$GIT show -s $commit | grep "Cc: stable@vger.kernel.org" > /dev/null 2>&1

if [ "$?" == "0" ]; then
	echo "stable"
fi

exit 0
