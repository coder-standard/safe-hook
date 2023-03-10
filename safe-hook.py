# coding=utf-8

import platform
import requests
import os
import sys
from distutils.spawn import find_executable
import logging
import getopt
import shutil
import re
import pathlib
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

globalFlag = True
opts, args = getopt.getopt(sys.argv[1:], "-l-v", ["local", 'version'])
for opt_name, opt_value in opts:
    if opt_name in ("-l", "--local"):
        globalFlag = False
    if opt_name in ("-v", "--version"):
        print("The version is v1.1.0")
        exit()

if not globalFlag:
    logging.info("local mode")


gitLeaksVersion = '8.16.0'


def get_host_architecture():
    if re.match(r'i.86', platform.machine()):
        logging.critical('unsupported machine:', platform.machine)
        return ''
    elif platform.machine() == 'x86_64' or platform.machine() == 'AMD64':
        host_arch = 'x64'
    elif platform.machine() == 'aarch64':
        host_arch = 'arm64'
    elif platform.machine().startswith('arm'):
        host_arch = platform.machine()
    else:
        host_arch = 'x32'

    return host_arch


def download(url: str, fname: str):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))

    with open(fname, 'wb') as file, tqdm(
            desc=fname,
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


def download_git_leaks(work_root):
    system_id = platform.system().lower()

    ext = 'tar.gz'

    if system_id == 'windows':
        ext = 'zip'

    dl_url = 'https://github.com/gitleaks/gitleaks/releases/download/v{0}/gitleaks_{0}_{1}_{2}.{3}'.format(
        gitLeaksVersion, system_id, get_host_architecture(), ext)

    logging.info('gitleaks url is ' + dl_url)

    dl_file = 'gitleaks_{}.{}'.format(gitLeaksVersion, ext)
    dl_file = os.path.join(work_root, dl_file)

    download(dl_url, dl_file)

    if system_id == 'windows':
        exit_code = os.system('unzip -o -d {} {}'.format(work_root, dl_file))
    else:
        exit_code = os.system('tar xvf {} -C {}'.format(dl_file, work_root))

    if exit_code >> 8 != 0:
        sys.exit()


gitBin = find_executable('git')
if gitBin is None:
    logging.critical('no git installed')
    exit(1)

workDir = os.getcwd()

if not os.path.isdir(os.path.join(workDir, ".git")):
    if not globalFlag:
        logging.warning("not git root")


if globalFlag:
    initTemplateDir = os.popen("git config --global init.templateDir").read().strip()
    if len(initTemplateDir) == 0:
        initTemplateDir = os.path.join(os.path.expanduser("~"), ".git-template")
        if not os.path.isdir(initTemplateDir):
            os.makedirs(initTemplateDir)
        if not os.path.isdir(initTemplateDir):
            logging.critical("no file %s", initTemplateDir)
            exit(1)
        os.popen("git config --global init.templateDir " + initTemplateDir)

    initTemplateDir = os.popen("git config --global init.templateDir").read().strip()
    if len(initTemplateDir) == 0:
        logging.critical("valid  init.templateDir")
        exit(1)

    logging.info("init.templateDir is %s", initTemplateDir)
    hooksDir = os.path.join(initTemplateDir, "hooks")
else:
    hooksDir = os.path.join(workDir, ".git", "hooks")

if not os.path.isdir(hooksDir):
    os.makedirs(hooksDir)

preCommitFile = os.path.join(hooksDir, "pre-commit")

hasInstalled = False

if not os.path.isfile(preCommitFile):
    with open(preCommitFile, 'a', encoding='utf-8') as f:
        f.write("#!/bin/sh\n")

safeHookPreCommitFilename = 'safe-hook-pre-commit.sh'
safeHookPreCommandFileRelPath = "./.git/hooks/" + safeHookPreCommitFilename

with open(preCommitFile, 'r', encoding='utf-8') as f:
    line = f.readline()
    if not line:
        with open(preCommitFile, 'a', encoding='utf-8') as f2:
            f2.write("#!/bin/sh\n")
    else:
        if line.strip() != "#!/bin/sh":
            logging.critical("need /bin/sh flag")
            exit(1)
        while True:
            line = f.readline()
            if not line:
                break
            line = line.strip()
            if line == safeHookPreCommandFileRelPath:
                hasInstalled = True
                break

os.popen("chmod +x " + preCommitFile)

if hasInstalled:
    logging.critical("has installed")
    exit(0)

gitLeaksBin = find_executable('gitleaks')

if gitLeaksBin is None:
    root = os.path.join(str(pathlib.Path.home()), '.safe-hooks')
    if not os.path.isdir(root):
        os.makedirs(root)
    gitLeaksBin = os.path.join(root, 'gitleaks')
    if platform.system().lower() == 'windows':
        gitLeaksBin += ".exe"
    if not os.path.isfile(gitLeaksBin):
        logging.info('no gitleaks found. try install it')
        download_git_leaks(root)

print('gitleaks path is {}'.format(gitLeaksBin))

safeHookPreCommitFileContent = '''# -*- coding: utf-8 -*

if [ "${1}x" == "1x" ]; then
    echo "skip gitleask"
else
    if [ -f ".gitleaks.toml" ]; then
      {0} protect --staged -v
    else
      {0} protect --staged -v -c .git/hooks/gitleaks.toml
    fi
fi
'''.format(pathlib.PurePath(gitLeaksBin).as_posix(), '{SKIP}')

safeHookPreCommitFile = os.path.join(hooksDir, safeHookPreCommitFilename)
with open(safeHookPreCommitFile, 'wb') as f:
    f.write(safeHookPreCommitFileContent.encode())

os.popen("chmod +x " + safeHookPreCommitFile)
shutil.copyfile(os.path.join(workDir, ".gitleaks.toml"), os.path.join(hooksDir, "gitleaks.toml"))
with open(preCommitFile, 'a', encoding='utf-8') as f:
    f.write("\n" + safeHookPreCommandFileRelPath + "\n")

logging.info("install hooks success")
