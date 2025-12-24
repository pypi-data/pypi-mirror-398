#!/usr/bin/env bash
A1='2'
A2='21'
B1='41'
B2='61'
WHITE='38;2;255;255;255'
GREEN='38;2;0;255;0'
#
#function pcol(){
#	printf '\x1b[%sm %s\x1b[m\n' $2 $1
#}
#function ptab(){
#	printf '\x1b[%sG %s' $2 $1
#}
#VERSION=$(cat pyproject.toml|rg -i version|tr -d 'version = ')
#PROJ=$(basename $PWD)
#L1="$(printf '%s' "$(ptab "$(pcol '| Project:'     '"$WHITE"' )" '"$A1"' ) $(ptab $(pcol '"| Version:"' '"$WHITE"') '"$B1"')) "
#L2="$(printf '%s' "$(ptab "$(pcol '| Upgrading:'   '"$WHITE"' )" '"$A1"' ))"
#L3="$(printf '%s' "$(ptab "$(pcol '| Tests:'       '"$WHITE"' )" '"$A1"' ) $(ptab $(pcol '"| Result:"' '"$WHITE"') '"$B1"'))"
#L4="$(printf '%s' "$(ptab "$(pcol '| Building:'    '"$WHITE"' )" '"$A1"' ))"
#L5="$(printf '%s' "$(ptab "$(pcol '| GIT:'         '"$WHITE"' )" '"$A1"' ))"
#L6="$(printf '%s' "$(ptab "$(pcol '| Stage:'       '"$WHITE"' )" '"$B1"' ))"
#L7="$(printf '%s' "$(ptab "$(pcol '| Commit:'      '"$WHITE"' )" '"$B1"' ))"
#L8="$(printf '%s' "$(ptab "$(pcol '| Push:'        '"$WHITE"' )" '"$B1"' ))"
##L9=$(printf '%s' "$(ptab $(pcol |PYPI (main):" $WHITE) $A1) $(ptab $(pcol "| Uploading:" $WHITEaaaaa) $B1))"
#printf '%s\n %s\n %s\n %s\n %s\n %s\n%s\n%s\n%s\n' $L{1..9}
#
#A1='2'
#B1='41'
#WHITE='38;2;255;255;255'


VERSION=$(cat pyproject.toml | rg -i version | tr -d 'version = ')
PROJ=$(basename "$PWD")

pip install --upgrade setuptools
pip install --upgrade build
pip install --upgrade twine

python -m unittest &> .STATUS_TESTS
[[ -n $(cat .STATUS_TESTS|rg -i '^OK$') ]] && TESTSTATUS='OK' || TESTSTATUS='FAIL'
rm .STATUS_TESTS
echo $TESTSTATUS

python -m build
git add .
echo "CURRENT VERSION: $VERSION :: TESTS: $TESTSTATUS :: CHANGED: " > .GITCOMMIT_MESSAGE
git status &>> .GITCOMMIT_MESSAGE
git commit -m "$(cat .GITCOMMIT_MESSAGE)"
git push


twine upload  dist/* --verbose  --skip-existing  -u '__token__' -p "$(cat .PYPI_APIKEY)"

printf '\n________________________________________________________________________________\n________________________________________________________________________________\n\n'
