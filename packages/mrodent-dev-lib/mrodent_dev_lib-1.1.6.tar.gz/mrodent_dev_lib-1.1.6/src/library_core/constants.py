import pathlib, sys, os

# get project name
path_parts = pathlib.Path(__file__).parts
PROJECT_NAME = path_parts[-2]
# print(f'>>> PROJECT_NAME |{PROJECT_NAME}|') # i.e. "lib" 

# get type of run
IS_PRODUCTION = None
for path_part in path_parts[:-2]:
  lc_path_part = path_part.lower()
  if 'operative' in lc_path_part:
    IS_PRODUCTION = True
  elif 'workspace' in lc_path_part:
    IS_PRODUCTION = False
if IS_PRODUCTION is None:
  print(f'FATAL. Neither "operative" nor "workspace" found in path parts: {path_parts[:-2]}', file=sys.stderr)
  sys.exit()

# get PART2 env var value
part2_env_var_name = 'PART2'
PART2_VAL = os.environ.get(part2_env_var_name)
if PART2_VAL == None:
  print(f'FATAL. Environment variable |{part2_env_var_name}| not set', file=sys.stderr)
  sys.exit()
# print(f'>>> env var |{PART2_VAL}|')

# get git OS
lc_os_name = sys.platform.lower()
IS_LINUX = None
if lc_os_name.startswith('lin'):
  IS_LINUX = True
elif lc_os_name.startswith('win'):
  IS_LINUX = False
if IS_LINUX == None:
  print(f'FATAL. Cannot operate in OS {sys.platform}', file=sys.stderr)
  sys.exit()
