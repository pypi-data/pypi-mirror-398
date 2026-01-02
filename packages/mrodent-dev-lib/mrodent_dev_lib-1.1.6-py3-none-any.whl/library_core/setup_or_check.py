"""
2025-12-19
Purpose of this file: 
When setting up a new project, run this file in a given directory and, after making various checks, it will 
install the starting components for a new project. 

There are 4 prerequisites: 
- there must be no parameters, except "--h": help
- the python available must be >= 3.10 
- the OS must be Linux or W10
- the name (lower-cased) of the directory where this script is being run must include the string "workspace"

"""
import logging
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s()\n%(message)s\n'  # Custom format)
)
import sys
if len(sys.argv) > 1:
    helpscript = """
The purpose of this script is to set up basic utility files in a new (or existing) project directory and 
also to create a virtual environment where it should be (on "partition2"). It should work in Linux or W10,
and should create files which will mean the project can be run in either OS

**How to run**:
Run with no parameters, in a directory with "workspace" in the name (lower-cased): it will ask you the name 
of the project you want to create.
It will not interfere with expected files if it finds they already exist.
NB it assumes that "python" is a recognised executable in both Win and Lin: in Linux due to a symlink which 
may be local or system-wide (typically for /usr/bin/python3)
"""
    if len(sys.argv) == 2 and sys.argv[1] == '--h':
        print(helpscript)
    else:
        logging.error(f'FATAL. This file must be run with no parameters or "--h"', file=sys.stderr)
    sys.exit()

py_major_version = sys.version_info[0] 
py_minor_version = sys.version_info[1] 
if py_major_version < 3 or py_minor_version < 10:
    logging.error(f'FATAL. This file must be run in Python 3.10 or higher', file=sys.stderr)
    sys.exit()

platform_lc = sys.platform.lower()
if not platform_lc.startswith('lin') and not platform_lc.startswith('win'):
    logging.error(f'FATAL. Cannot run this in OS |{sys.platform}| - only Linux or W10')
    sys.exit()

IS_LINUX = platform_lc.startswith('lin')
import pathlib
cwd = pathlib.Path.cwd()
# logging.info(f'+++ str(CWD.stem) |{str(cwd.stem)}|')
if 'workspace' not in cwd.stem.lower():
    logging.error(f'FATAL. This must be run in a directory containing the string "workspace"')
    sys.exit()

print(f'Enter project name:')
while True:
    project_name = input()
    if ' ' in project_name:
        logging.warning(f'WARN. The project name cannot contain spaces. Try again')
    else:
        break

logging.info(f'project name |{project_name}|')
# if this already exists as a file: error
target_root_dir_path = cwd.joinpath(project_name) 
if target_root_dir_path.is_file():
    logging.error(f'FATAL. This |{project_name}| is a file in this directory')
    sys.exit()

# if this doesn't exist: make new directory
if target_root_dir_path.exists():
    logging.info(f'Project {project_name}| already exists as directory... continuing to set up where expected files are missing')
    
else:

    logging.info(f'... trying to create project root dir ... ')
    try:
        target_root_dir_path.mkdir()
    except BaseException as e:
        logging.exception(f'FATAL. This |{project_name}| could not be created as as directory')
        sys.exit()
    logging.info(f'project root dir created')

# path to venv must be PART2/apps/Python/virtual_envs/[directory]
import os
part2_env_var_name = 'PART2'
part2_env_var_val = os.environ.get(part2_env_var_name)
if part2_env_var_val is None:
    logging.error(f'FATAL. No environment variable "{part2_env_var_name}" was found')
    sys.exit()

ve_part2_path_parts = ['apps', 'Python', 'virtual_envs']
ve_part2_path = pathlib.Path(f'{part2_env_var_val}/').joinpath(*ve_part2_path_parts)
# logging.info(f'+++ ve_part2_path {ve_part2_path}')
if ve_part2_path.is_file():
    logging.error(f'FATAL. Expected path to directory containing virtual envs is a file: {ve_part2_path}')
    sys.exit()
if not ve_part2_path.exists():
    # ... try to create
    try:
        ve_part2_path.mkdir(parents=True, exist_ok=True)
    except BaseException as e:
        logging.exception(f'FATAL. Path to directory containing virtual envs could not be created')
        sys.exit()

# we need to use or create a new venv called dev_[xxx]
dev_ve_name = 'dev_' + project_name
target_dev_ve_path = ve_part2_path.joinpath(dev_ve_name)
if target_dev_ve_path.is_file():
    logging.error(f'FATAL. Target path to directory to contain dev virtual env is a file: {target_dev_ve_path}')
    sys.exit()

if target_dev_ve_path.exists():
    logging.info(f'A directory already exists at {target_dev_ve_path} - assuming this is a regular venv')
else:
    logging.info(f'... trying to create the dev venv for this project at {target_dev_ve_path}\nCan take a few seconds...')
    from venv import create
    try:
        create(target_dev_ve_path, with_pip=True)
    except BaseException as e:
        logging.exception(f'FATAL. Error creating venv at {target_dev_ve_path}')
        sys.exit()

# now create lin_ve_path
lin_path_str = f'${part2_env_var_name}/{"/".join(ve_part2_path_parts)}/{dev_ve_name}/bin/activate\n'
lin_ve_path_file_path = target_root_dir_path.joinpath('lin_ve_path')
if not lin_ve_path_file_path.exists():
    path_file_path_forwardslash_version = str(lin_ve_path_file_path).replace('\\', '/')
    with open(path_file_path_forwardslash_version, 'w') as f:
        target_ve_path_forwardslash_version = str(target_dev_ve_path).replace('\\', '/')
        f.write(lin_path_str)
    extra_msg = '' if IS_LINUX else ' - when in Linux make this executable' 
    logging.info(f'Created start ve file for Lin at {lin_ve_path_file_path}{extra_msg}')
    if IS_LINUX:
        # ... make executable
        import subprocess
        subprocess.run(['chmod', 'u+x', lin_ve_path_file_path])

# now create win_ve_path.bat
win_path_str = f'%{part2_env_var_name}%/{"/".join(ve_part2_path_parts)}/{dev_ve_name}/Scripts/activate\n'\
    .replace('/', '\\')
win_ve_path_file_path = target_root_dir_path.joinpath('win_ve_path.bat')
if not win_ve_path_file_path.exists():
    path_file_path_backslash_version = str(win_ve_path_file_path).replace('/', '\\')
    with open(path_file_path_backslash_version, 'w') as f:
        target_ve_path_backslash_version = str(target_dev_ve_path).replace('/', '\\')
        f.write(win_path_str)
    logging.info(f'Created start ve file for Win at {win_ve_path_file_path}')

# create the run_[xxx].py file
run_project_file_path = target_root_dir_path.joinpath(f'run_{project_name}.py')
if not run_project_file_path.exists():
    # NB this assumes that there is a "src" dir and under that a "core" dir and under that a file "start.py"
    # not always the case ... but can be tweaked, copied and tweaked, etc. as required
    run_text = """#!./python

import subprocess, pathlib, sys, os

try:
    platform_lc = sys.platform.lower()    
    if platform_lc.startswith('lin'):
        import tempfile
        with open('lin_ve_path', 'r') as f:
            contents = f.read()
        commands = [contents.strip(), f'python src/core/start.py']
        with tempfile.NamedTemporaryFile(suffix = '.sh', mode= 'w') as tmp:
            tmp.write('\n'.join(commands))
            tmp.flush()
            execute_file = ['/bin/bash', tmp.name]
            subprocess.run(['chmod', 'u+x', tmp.name], check=True)
            subprocess.run(execute_file, check=True)
    elif platform_lc.startswith('win'):
        subprocess.run(r'win_ve_path.bat && python src/core/start.py', universal_newlines=True, check=True)
    else:
        print(f'FATAL. Cannot be run in operating system {sys.platform}', file=sys.stderr)
except BaseException as e:
    import logging
    print(f'FATAL. Exception: {e}', file=sys.stderr)
    logging.exception('')
"""
    with open(run_project_file_path, 'w') as f:
        f.write(run_text)
    if IS_LINUX:
        # ... make executable
        import subprocess
        subprocess.run(['chmod', 'u+x', lin_ve_path_file_path])
    else:
        logging.info(f'TODO when in Linux this run file, {run_project_file_path}, should be made executable')

# make version.toml if it doesn't exist
version_toml_file_path = target_root_dir_path.joinpath(f'version.toml')
if not run_project_file_path.exists():
    with open(version_toml_file_path, 'w') as f:
        f.write('version="0.0.0"') # the first commit with a git tag will set this to something meaningful

# make pyt.bat (for Win) and pyt (for Lin)
pyt_bat_file_path = target_root_dir_path.joinpath(f'pyt.bat')
if not pyt_bat_file_path.exists():
    pyt_bat_text = """@echo off
REM this passes on the command line args (including "..\lib\pyt.py" to the python utility in project lib)
python ..\lib\pyt.py %*
"""
    with open(pyt_bat_file_path, 'w') as f:
        f.write(pyt_bat_text)

pyt_sh_file_path = target_root_dir_path.joinpath(f'pyt.sh')
if not pyt_sh_file_path.exists():
    pyt_sh_text = """# this passes on the command line args (including "..\lib\pyt.py" to the python utility in project lib)
python ../lib/pyt.py "$@"
"""
    with open(pyt_sh_file_path, 'w') as f:
        f.write(pyt_sh_text)
        
    if IS_LINUX:
        # ... make executable
        import subprocess
        subprocess.run(['chmod', 'u+x', pyt_sh_file_path])
    else:
        logging.info(f'TODO when in Linux this pyt.sh file, {pyt_sh_file_path}, should be made executable')


# make config.toml, initially with one setting, the min "lib" (i.e. mrodent-dev-lib/mrodent-lib) version
config_toml_file_path = target_root_dir_path.joinpath(f'config.toml')
if not config_toml_file_path.exists():
    with open(config_toml_file_path, 'w') as f:
        f.write('min_lib_project_version="1.1.0"')

# finally, a starter .gitignore
gitignore_text = """
*.pyc 
*.txt 
requirements.txt 
**/tmp 
**/temp
/.settings
.project
.pydevproject
*.log
*.tmp
*.diff
/.pytest_cache/
*/target/*
**/target/**
"""
gitignore_file_path = target_root_dir_path.joinpath(f'.gitignore')
if not gitignore_file_path.exists():
    with open(gitignore_file_path, 'w') as f:
        f.write(gitignore_text)

"""
2025-12-19
NB currently this is agnostic about whether a .git dir or .git file (pointing to a remote repo) is present ...
"""
