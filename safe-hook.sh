#!/bin/bash

python3full=$(command -v python3)

if [[ ${python3full} != '' ]]
then
  # fix default python3 on windows
  version=`${python3full}  -V 2>&1 | awk '{print $2}' | awk -F '.' '{print $1}'`
  if [[ "${version}x" != "2" && "${version}x" != "3" ]]
  then
    python3full=$(command -v python)
  fi
fi

if [[ ${python3full} == '' ]]
then
	echo "python3 not installed"
	exit 0
fi

version=`${python3full}  -V 2>&1 | awk '{print $2}' | awk -F '.' '{print $1}'`

if [[ "${version}" != "3" ]]
then
	echo "python3 not installed"
	exit 0
fi

pip3full=$(command -v pip3)

if [[ ${pip3full} == '' ]]
then
	echo "pip3 not installed"
	exit 0
fi


mustPyModuleInstalled() {
	${pip3full} show $1>/dev/null 2>&1
	if [[ $? -eq 0 ]]; then
		echo "$1 installed"
		return
	fi

	${pip3full} install $1
	if [[ $? -ne 0 ]]; then
		echo "install $1 failed, abort"
		exit 1
	else
		echo "install $1 success"
	fi
}


mustPyModuleInstalled requests
mustPyModuleInstalled tqdm

if [[ ! -f safe-hook.py ]]; then
	git clone git@github.com:coder-standard/safe-hook.git
	cd safe-hook 
fi

${python3full} safe-hook.py $@
