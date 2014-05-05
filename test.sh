#!/bin/bash

EXPECTED_ARGS=1
E_BADARGS=65

progname=$(basename $0) 
usage()
{

	cat <<EOF
Usage: test.sh [options]

Run the test runner and optional quality checks

Options:
 --help print this help message
 -e or --with-edx test runner with edx platform tests
 -q or --with-quality run pylint and pep8 on code

EOF
}

SHORTOPTS="eq"
LONGOPTS="help,with-edx,with-quality"

if $(getopt -T >/dev/null 2>&1) ; [ $? = 4 ] ; then # New longopts getopt.
 OPTS=$(getopt -o $SHORTOPTS --long $LONGOPTS -n "$progname" -- "$@")
else # Old classic getopt.
 # Special handling for --help on old getopt.
 case $1 in --help) usage ; exit 0 ;; esac
 OPTS=$(getopt $SHORTOPTS "$@")
fi

if [ $? -ne 0 ]; then
 echo "'$progname --help' for more information" 1>&2
 exit 1
fi

eval set -- "$OPTS"
edx=false
quality=false
while [ $# -gt 0 ]; do
	: debug: $1
	case $1 in
		--help)
			usage
			exit 0
			;;
		-e|--with-edx)
			edx=true
			shift
			;;
		-q|--with-quality)
			quality=true
			shift
			;;
		--)
			shift
			break
			;;
		*)
			echo "Internal Error: option processing error: $1" 1>&2
			exit 1
			;;
	esac
done

if $edx; then
	export XSIFTX_TEST_EDX="yep"
fi
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export XSIFTX_CONFIG="$DIR/xsiftx/tests/config/xsiftx_config.yml"
nosetests --with-coverage --cover-html --cover-package=xsiftx

if $quality; then
	pylint --rcfile=$DIR/.pylintrc xsiftx
	pep8 xsiftx
fi
