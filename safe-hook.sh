#!/bin/bash

python3=$(command -v python3)

if [[ ${python3} == '' ]]
then
	echo "python3 not installed"
	exit 0
fi

pip3=$(command -v pip3)

if [[ ${pip3} == '' ]]
then
	echo "pip3 not installed"
	exit 0
fi


mustPyModuleInstalled() {
	pip3 show $1>/dev/null 2>&1
	if [[ $? -eq 0 ]]; then
		echo "$1 installed"
		return
	fi

	pip3 install $1
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

python3 safe-hook.py $@
