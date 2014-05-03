if [[ "$1" == "--with-edx" ]]; then
	export XSIFTX_TEST_EDX="yep"
fi
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export XSIFTX_CONFIG="$DIR/xsiftx/tests/config/xsiftx_config.yml"
nosetests --with-coverage --cover-html --cover-package=xsiftx
