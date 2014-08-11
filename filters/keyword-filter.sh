#!/bin/bash
#

GIT="/usr/bin/git"
commit=$1

function match_keyword {
	match=$1
	tag=$2

	$GIT show -s $commit | grep -i "$match" > /dev/null 2>&1
	if [ "$?" == "0" ]; then
		echo $tag
	fi
}

match_keyword "fix" "fix"
match_keyword "Cc: stable@vger.kernel.org" "stable"
match_keyword "CVE " "CVE SEC"

exit 0
