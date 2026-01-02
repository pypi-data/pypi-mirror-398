# pyright: reportMissingImports=false
import sys, pathlib, logging, os, importlib, datetime, inspect, traceback, requests, multiprocessing
import toml # type: ignore
from packaging import version as packaging_version
from PyQt6 import QtWidgets, QtCore, QtGui

logger = None

# these are return codes... non-0 indicates an error return code
CHECKS_PASSED = 0
BAD_PARAMS = 1
UNKNOWN_OS = 2
PYTHON_VERSION_IS_TOO_LOW = 3
NOT_RUN_FROM_PROJECT_ROOT = 4
CALLER_FILE_NOT_UNDER_CWD = 5
UNEXPECTED_VALUE_ERROR = 6
CALLER_FILE_NOT_IN_EXPECTED_PACKAGE = 7
PACKAGING_NOT_INSTALLED = 8
COULD_NOT_IMPORT_VERSION_FILE = 9
VERSION_FILE_DOES_NOT_CONTAIN_VERSION_LINE = 10
VERSION_FILE_CONTAINS_INVALID_VERSION = 11
VERSION_FILE_TOO_LOW = 12
NOT_IN_VIRTUAL_ENVIRONMENT = 13
IMPORTED_WRONG_VERSION_FILE = 14 
    
def do_start_run_checks(app_name, caller_file_path, package_name='core', return_value=False):
    # checks on the values here, particularly the ones with default args
    if not isinstance(return_value, bool):
        # if the "return_value" param is anything other than Bool this always causes a sys.exit
        stop(f'Bad param for return_value: |{return_value}| type {type(return_value)}. Must be bool.', BAD_PARAMS, False)
    if sys.base_prefix == sys.prefix:
        return stop('This app is not being run in an appropriate activated Python virtual environment', NOT_IN_VIRTUAL_ENVIRONMENT, return_value) 
    if not isinstance(package_name, str):
        return stop(f'Bad param for package_name: |{package_name}| type {type(package_name)}. Must be string.', BAD_PARAMS, return_value)
    if not isinstance(caller_file_path, pathlib.Path):
        return stop(f'Bad param for caller_file_path: |{caller_file_path}| type {type(caller_file_path)}. Must be pathlib.Path.', BAD_PARAMS, return_value)
    if not isinstance(app_name, str):
        return stop(f'Bad param for app_name: |{app_name}| type {type(app_name)}. Must be string.', BAD_PARAMS, return_value)
    # is caller_file_path actually a real file?
    if not caller_file_path.is_file():   
        return stop(f'Bad param for caller_file_path: |{caller_file_path}|. Is not a file.', BAD_PARAMS, return_value)
    if (not sys.platform.startswith('lin')) and (not sys.platform.startswith('win')):
        return stop(f'Can only run on windows or linux platforms currently. This OS is {sys.platform}', UNKNOWN_OS, return_value)
    if sys.version_info.major < 3 or sys.version_info.minor < 10:
        return stop(f'Must be run with Python 10 or higher. This version is {sys.version_info}', PYTHON_VERSION_IS_TOO_LOW, return_value)
    cwd_path = pathlib.Path.cwd()
    if cwd_path.parts[-1] != app_name:
        return stop(f'This app must be run using "python src/{package_name}" from the top-level directory "{app_name}".', NOT_RUN_FROM_PROJECT_ROOT, return_value)
    try:
        relative_path = caller_file_path.relative_to(cwd_path)
    except ValueError as e:
        if 'not in the subpath' in str(e):
            return stop(f'Caller file {caller_file_path} is not under CWD {cwd_path}', CALLER_FILE_NOT_UNDER_CWD, return_value)
        else:
            logging.exception(e)
            return stop(f'Value error {e}', UNEXPECTED_VALUE_ERROR, return_value)
    return CHECKS_PASSED

def stop(msg, error_code, return_value):
    msg = 'FATAL. ' + msg
    if return_value: return error_code, msg
    print(msg, file=sys.stderr)
    sys.exit(error_code)
    
def lib_module_version_check(min_lib_version):
    # 2024-12-07 complete change: version.toml in the root dir is now used
    generic_error_prefix = 'FATAL. Version file "version.toml" in "lib" project root dir: '
    cwd_path = pathlib.Path.cwd()
    try:
        with open(cwd_path.joinpath('version.toml'), 'r') as f:
            version_dict = toml.load(f)
    except BaseException as e:
        print(f'{generic_error_prefix}error loading toml file "version.toml" in "lib" project root dir, exception: {e}')
        return False
    if 'version' not in version_dict:
        print(f'{generic_error_prefix}does not contain key "version"')
        return False
    version_val_as_str = version_dict['version']
    try:
        from packaging import version as packaging_version 
        version = packaging_version.Version(version_val_as_str)
    except BaseException as e:
        # NB as well as a parsing error this would also catch a failure to import packaging_version
        print(f"""{generic_error_prefix}the value for key "version" could not be parsed to a Version object
string value obtained from file |{version_val_as_str}|, exception was {e}""")
        return False
    if version < min_lib_version:
        print(f"""{generic_error_prefix}the lib version is too low!
Min. lib version required: {min_lib_version}. Version found in "version.toml": {version}""")
        return False
    return True

"""
2022-08-21
This class is intended to detect whether an instance of this script is already running.
Used like this:
    sic = lib_main.SingleInstanceChecker(__name__)
    if sic.already_running():
        print(f'FATAL. ...
"""        
class SingleInstanceChecker:
    def __init__(self, id):
        # NB the "id" here should be unique: a filename like "__main__.py" will I think risk a confusion 
        # between processes 
        assert type(id) == str
        pid = os.getpid()
        if sys.platform.startswith('win'):
            # NB an attempt to import this in Linux (for example during testing) will raise ModuleNotFoundError
            # NB needs pip install pywin32 
            import win32api, winerror, win32event # type: ignore
            self.mutexname = id
            self.lock = win32event.CreateMutex(None, False, self.mutexname)
            last_error = win32api.GetLastError()
            # logging.info(f'A PID {pid} {datetime.datetime.now()} self.mutexname |{self.mutexname}| win32api.GetLastError() {last_error}')
            self.running = (last_error == winerror.ERROR_ALREADY_EXISTS)
            # logging.info(f'B PID {pid} {datetime.datetime.now()} self.mutexname |{self.mutexname}| win32api.GetLastError() {win32api.GetLastError()}')
        else:
            # NB an attempt to import this in W10 (for example during testing) will raise ModuleNotFoundError
            # NB needs pip install fcntl 
            import fcntl
            self.lock = open(f"/tmp/instance_{id}.lock", 'wb')
            try:
                fcntl.lockf(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.running = False
            except IOError:
                self.running = True

    def already_running(self):
        return self.running
        
    def __del__(self):
        if self.lock:
            try:
                if sys.platform.startswith('win'):
                    try:
                        import win32api # type: ignore
                    except ImportError as e:
                        # raised 2022-09-09 during pytest testing
                        if 'likely shutting down' in str(e):
                            return
                    win32api.CloseHandle(self.lock)
                elif sys.platform.startswith('lin'):
                    # TODO how to deal with self.lock == True in Linux? does it just "close handle" automatically?
                    pass
                else:
                    # TODO in Linux this raised an Exception
                    os.close(self.lock)
            except Exception as e:
                logging.exception(e)
        
if __name__ == '__main__':
    msg = f'*** this file, |{__file__}|, is not meant to be run independently: the lib module is for importing from other projects'
    print(msg, file=sys.stderr)
    raise Exception(msg)
    
if __name__ == 'library_core.library_main':
    pass
    # TODO in fact most stuff should happen here ... but on 2023-05-23 there are 
    # about 6 live projects which use "library_core": I don't want to interfere with these, so instead:
    
# not all projects involve QT, so don't include in "check_and_configure"
def check_qt_version():
    # from PyQt5 import QtCore
    from PyQt6 import QtCore
    qt_version = int(QtCore.QSysInfo.productVersion())  
    min_qt_version = 10
    # logger.info(f'qt_version {qt_version}, min_qt_version {min_qt_version}')
    if qt_version < min_qt_version:
        msg = f'FATAL. QT version must be {min_qt_version} or higher but is {qt_version}'
        if logger != None:
            logger.critical(msg)
        else:
            print(msg, file=sys.stderr)
        sys.exit()
    
def custom_excepthook(exc_type, exc_value, exc_traceback):
    if hasattr(sys, 'pytl'):
        sys.pytl.log(f'exc_type {exc_type}, exc_value {exc_value}, exc_traceback {exc_traceback}')
    # allow Ctrl-C to have effect as normal...
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical('Uncaught exception', exc_info=(exc_type, exc_value, exc_traceback))

def custom_unraisablehook(*args):
    """
2023-05-23 NB still not sure when this is raised: normally appears to be one param, of "undefined class!" 
UnraisableHookArgs, which has various attributes, see below    
    """
    stack_trace = ''.join(traceback.format_stack())
    """
    arg 0: |UnraisableHookArgs(exc_type=<class 'NameError'>, exc_value=NameError("name 'logger' is not defined"), 
    exc_traceback=<traceback object at 0x0000025B185BB700>, err_msg=None, 
    object=<function thread_check.<locals>.pseudo_decorator.<locals>.gui_checker_inner_function at 0x0000025B150AB400>)| 
    type <class 'UnraisableHookArgs'>
    """
    # NB arg.__class__.__qualname__ is "UnraisableHookArgs"... but this is also said to be "undefined"!
    if len(args) == 1 and 'UnraisableHookArgs' in str(type(args[0])):
        hook_args = args[0]
        sys.excepthook(hook_args.exc_type, hook_args.exc_value, hook_args.exc_traceback)
        logger.critical(f'Unraisable hook called, with single arg of type sys.UnraisableHookArgs\n' 
            + f'err_msg={hook_args.err_msg}\nobject={hook_args.object} type {type(hook_args.object)}\nstack trace:\n{stack_trace}')
    else:    
        logger.critical(f'Unraisable hook called, args {args}\nstack trace:\n{stack_trace}')
        for i, arg in enumerate(args):
            logger.info(f'arg {i}: |{arg}| type {type(arg)}')
    
def get_is_admin():
    if sys.platform.startswith('win'):
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0 
    else:
        logger.info(f'os.environ.get("SUDO_UID") {os.environ.get("SUDO_UID")}')
        return os.environ.get('SUDO_UID') == '1000'

def check_and_configure(min_lib_version=None, platform='linux_or_w10', min_python_version_str='3.9', single_instance=True, 
        pyqt=True, admin_user=False):
    cwd_path = pathlib.Path.cwd()
    sys.production_run = 'operative' in str(cwd_path)
    # you want to set up logging as early as poss...
    try:
        import library_core.configure_logging
        caller_appname = cwd_path.name
        if not library_core.configure_logging.configure_logging(caller_appname):
            print(f'FATAL. Logger configuration failed', file=sys.stderr)
            sys.exit()
    except BaseException as e:
        print(f'FATAL. Logger configuration failed, exception: {e}', file=sys.stderr)
        logging.exception('')
        sys.exit()
    global logger
    # NB I thought for a bit that you have to call colorlog.getLogger() to get a colour log... but this seems to deliver a colour log:
    logger = logging.getLogger(caller_appname)
    # logger.info(f'production run? {sys.production_run}') # TODO should be used for configuring logger path... #@UndefinedVariable
    if hasattr(sys, 'pytl'):
        sys.pytl.log(f'here admin_user {admin_user}')
    if admin_user:
        if hasattr(sys, 'pytl'):
            sys.pytl.log('here')
        if not get_is_admin():
            if hasattr(sys, 'pytl'):
                sys.pytl.log('here')
            # print(f'FATAL. Must be run as "admin"/"elevated" user', file=sys.stderr)
            logger.error(f'FATAL. Must be run as "admin"/"elevated" user')
            sys.exit()
    if hasattr(sys, 'pytl'):
        sys.pytl.log('here')
    # hooks    
    sys.excepthook = custom_excepthook
    sys.unraisablehook = custom_unraisablehook
    # does this caller project have a version file under /src?
    SOURCE_DIR_NAME = 'src'
    caller_src_dir_path = cwd_path.joinpath(SOURCE_DIR_NAME)
    # NB this is also a kind of check that the CWD is the root directory: a directory with "src" directory under it
    if not caller_src_dir_path.exists():
        logger.critical(f'FATAL. Caller CWD does not have a directory "{SOURCE_DIR_NAME}" under root dir. NB project must be run from project root directory')
        sys.exit()
    if caller_src_dir_path.is_file():
        logger.critical(f'FATAL. {caller_src_dir_path} is a file but should be a dir')
        sys.exit()
    caller_file_path = pathlib.Path(inspect.stack()[1].filename) 
    # logger.info(f'caller_file_path |{caller_file_path}|')
    if not caller_file_path.is_relative_to(cwd_path): 
        logger.critical(f'FATAL. Caller file |{caller_file_path}| is not relative to CWD |{cwd_path}|. NB project must be run from project root directory')
        sys.exit()


    # 2024-12-07 vast amounts of this stuff to do with "importing the version file" are no longer relevant: 
    # "version.toml" in the root directory is now used... at least in project "lib"
    # TODO URGENT posssibly though this relates to the versioning of the user projects themselves (i.e. which use "lib") ...?
    # ON TODAY'S DATE: "organiser" and "doc_indexer" have (correctly) "version.toml" and no "version.py"
    # ... BUT: sysadmin has src/version_file.py ! Oh dear, this must be changed TODO URGENT

    # we can be pretty sure at this point that the name of the last directory of the CWD is the caller_appname 
    sys.path.insert(0, str(caller_src_dir_path))    
    VERSION_FILE_STEM = 'version_file'
    if VERSION_FILE_STEM in sys.modules:
        logger.critical(f'FATAL. sys.modules already contains a key "{VERSION_FILE_STEM}"')
        sys.exit()
    try:
        caller_version_file_mod = importlib.import_module(VERSION_FILE_STEM)
    except ModuleNotFoundError:
        logger.critical(f'FATAL. Module not found trying to import caller version file |{VERSION_FILE_STEM}| under {caller_src_dir_path}')
        sys.exit()
    except BaseException:
        logger.exception(f'FATAL. Trying to import caller version file |{VERSION_FILE_STEM}| under {caller_src_dir_path}')
        sys.exit()
    sys.modules['caller_version_file_mod'] = sys.modules[VERSION_FILE_STEM]
    del  sys.modules[VERSION_FILE_STEM]
    caller_version_file_path = pathlib.Path(caller_version_file_mod.__file__)
    if caller_version_file_path.parent != caller_src_dir_path:
        logger.critical(f'FATAL. The version file imported as the caller version file is not under {caller_src_dir_path}: its path is {caller_version_file_path}')
        sys.exit()
    VERSION_ATTRIB_NAME = 'version'
    if not hasattr(caller_version_file_mod, VERSION_ATTRIB_NAME):
        logger.critical(f'FATAL. Caller version file |{VERSION_FILE_STEM}| under {caller_src_dir_path} does not contain "{VERSION_ATTRIB_NAME}" attribute')
        sys.exit()
    # the version of the caller project must be checked and a means found to "return" it to the caller project
    caller_version_str = getattr(caller_version_file_mod, VERSION_ATTRIB_NAME)
    version_type = type(caller_version_str)
    if version_type != str:
        logger.critical(f'FATAL. Caller version attribute |{VERSION_ATTRIB_NAME}| in file {caller_version_file_path}, i.e. {caller_version_str}, is wrong class: {version_type}')
        sys.exit()
    try:
        caller_version = packaging_version.parse(caller_version_str)
    except BaseException:
        logger.critical(f'FATAL. Could not parse lib version string |{caller_version_str}| to get packaging version')
        sys.exit()
    # now we have to check that this imported mod is indeed the version_file.py belonging to this lib project, not to the caller project.
    # first find "lib" directory above here
    this_file_path = pathlib.Path(__file__)
    # logger.info(f'this_file_path.parts {this_file_path.parts}')
    lib_module_root_dir_path = None
    for i, part in enumerate(reversed(this_file_path.parts)):
        if part.lower() == 'lib':
            # NB we are counting ***backwards*** with the counter variable, i
            lib_module_root_dir_path = pathlib.Path(*this_file_path.parts[:-i])
            break
    if lib_module_root_dir_path == None:
        logger.critical(f'FATAL. Unable to determine the root dir of the "lib" module from path of this file: {this_file_path}')
        sys.exit()
    lib_module_src_dir_path = lib_module_root_dir_path.joinpath(SOURCE_DIR_NAME)
    if not lib_module_src_dir_path.is_dir():
        logger.critical(f'FATAL. Root dir of the "lib" module does not seem to have a dir at {lib_module_src_dir_path}')
        sys.exit()
    """ make it possible to import src\version_file.py in the *** lib *** module
    NB because this is placed at the start of sys.path, the attempt to import version_file.py should use that of the lib
    project (if there is such a file), rather than (already imported) version_file.py of the caller project (but this is checked later)
    """
    sys.path.insert(0, str(lib_module_src_dir_path))    
    try:
        lib_version_file_mod = importlib.import_module(VERSION_FILE_STEM)
    except ModuleNotFoundError:
        logger.critical(f'FATAL. Module not found trying to import lib version file |{VERSION_FILE_STEM}| under {lib_module_src_dir_path}')
        sys.exit()
    except BaseException:
        logger.exception(f'FATAL. Trying to import lib version file |{VERSION_FILE_STEM}| under {lib_module_src_dir_path}')
        sys.exit()
    sys.modules['lib_version_file_mod'] = sys.modules[VERSION_FILE_STEM]
    del  sys.modules[VERSION_FILE_STEM]
    lib_version_file_path = pathlib.Path(lib_version_file_mod.__file__)
    if lib_version_file_path.parent != lib_module_src_dir_path:
        logger.critical(f'FATAL. The version file imported as the lib version file is not under {lib_module_src_dir_path}: its path is {lib_version_file_path}')
        sys.exit()
    lib_version_str = getattr(lib_version_file_mod, VERSION_ATTRIB_NAME)
    version_type = type(lib_version_str)
    if version_type != str:
        logger.critical(f'FATAL. Lib version attribute in file is wrong class: {version_type}')
        sys.exit()
    try:
        lib_version = packaging_version.parse(lib_version_str)
    except BaseException:
        logger.critical(f'FATAL. Could not parse lib version string |{lib_version_str}| to get packaging version')
        sys.exit()
    if min_lib_version == None:
        # logger.info('OK, caller is unconcerned with version of lib module')
        pass
    else:
        if type(min_lib_version) != packaging_version.Version:
            logger.critical(f'FATAL. Min lib version required is not packaging.version.Version but type {type(min_lib_version)}')
            sys.exit()
        
        if lib_version < min_lib_version:
            logger.critical(f'FATAL. Lib version must be {min_lib_version} at minimum but is {lib_version}')
            sys.exit()
        # logger.info(f'version of lib is OK...')
    
    # logger.info(f'check OS...')    
    if platform == 'linux_or_w10':
        if (not sys.platform.startswith('lin')) and (not sys.platform.startswith('win')):
            logger.critical(f'FATAL. Disallowed OS: must be Linux or W10 but is {sys.platform}')
            sys.exit()
    elif platform != None and not sys.platform.startswith(platform):
        logger.critical(f'FATAL. Disallowed OS: must start with "{platform}" but is {sys.platform}')
        sys.exit()
    # platform=None will effectively disable any checks
    # logger.info(f'check certain required files...')
    
    filenames = ['start_ve.bat', '.gitignore', 'conftest.py', 'start_lin_ve']
    for filename in filenames:
        file_path = cwd_path.joinpath(filename)
        if not file_path.is_file():
            logger.critical(f'FATAL. File {file_path} is not a file')
            sys.exit()
            
    """        
To make sure that all external Python modules have been installed in the project VE, it is I think a good idea
to import all .py files in the project. This relies on them having all the import statements at the top of the file 
(i.e. rather than in pieces of conditionally executed code) as far as possible. Sometimes a given module may occasionally only be
needed in W10 and not in Linux, but this will be rare, and will be fine: if a sys.platform == .. test is done in the file
    
First, before anything else, make it possible to import "thread_check" (decorator) from the constants in "from constants import *"
If you don't do this first, the import of all files which do "from constants import *" and then use the decorator will fail    
    """ 
    constants_file_path = caller_file_path.parent.joinpath('constants.py')
    if constants_file_path.is_file():
        try:
            constants_module = importlib.import_module(constants_file_path.stem)
        except BaseException:
            logger.exception(f'FATAL. Trying to import constants.py file |{constants_file_path}|')
            sys.exit()
        constants_module.thread_check = thread_check
        # also make ***this*** library module available to the constants module
        constants_module.library_main = importlib.import_module(f'{this_file_path.parent.name}.{this_file_path.stem}')
        
    
    for py_file_path in caller_src_dir_path.glob('**/*.py'):
        # logger.info(f'--> found {py_file_path} stem |{py_file_path.stem}|')
        if py_file_path.stem in sys.modules:
            module = sys.modules[py_file_path.stem]
            if hasattr(module, '__file__'):
                module_path = pathlib.Path(module.__file__)
                if module_path == py_file_path:
                    # logger.info(f'======= file {py_file_path} has already been imported: skipping')
                    continue
            else:
                continue 
            msg = f"""FATAL. There is already a key for {py_file_path.stem} in sys.modules, with path |{module_path}|,
...but the one to be imported is |{py_file_path}|"""
            logger.critical(msg)
            sys.exit()
        sys.path.insert(0, str(py_file_path.parent))
        try:
            imported_module = importlib.import_module(py_file_path.stem)
        except ModuleNotFoundError as e:
            logger.exception(f'FATAL. Module not found, name |{e.name}|, trying to import caller project .py file |{py_file_path}|')
            sys.exit()
        except BaseException:
            logger.exception(f'FATAL. Trying to import caller project .py file |{py_file_path}|')
            sys.exit()
        del sys.path[0]
        imported_module_path = pathlib.Path(imported_module.__file__)
        if imported_module_path != py_file_path: 
            logger.critical(f'FATAL. An import of a .py file went wrong: tried to import |{py_file_path}| but the resultant module has path {imported_module_path}')
            sys.exit()
        del sys.modules[py_file_path.stem]
        
    # logger.info(f'check that python version is acceptable... sys.version_info {sys.version_info}\ndir {dir(sys.version_info)}\ntype {type(sys.version_info)}')
    # logger.info(f'check that python version is acceptable...')
    python_version = packaging_version.Version(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')
    min_python_version = packaging_version.Version(min_python_version_str)
    # logger.info(f'python_version {python_version}')
    if python_version < min_python_version:
        logger.critical(f'FATAL. Project is running Python {python_version} but the minimum Python version is {min_python_version}')
        sys.exit()

    if single_instance:          
        # logger.info(f'check that instance of this project is not already running...')
        sic = SingleInstanceChecker(caller_appname)
        if sic.already_running():
            logger.critical(f'FATAL. Another instance of this script {caller_appname} appears to be running.')
            sys.exit()
            
    if pyqt:
        # logger.info(f'check that PyQT version is high enough...')
        # from PyQt5 import QtCore
        from PyQt6 import QtCore
        qt_version = int(QtCore.QSysInfo.productVersion())  
        min_qt_version = 10
        if qt_version < min_qt_version:
            logger.critical(f'FATAL. QT version must be {min_qt_version} or higher but is {qt_version}')
            sys.exit()
    # TODO sys.argv should also be examined here... and the results returned 
    return {'caller_version': caller_version} 

# decorator for methods
# NB this has to be in its own file in order to be imported by a variety of other files
# NB in the event of a hang (or a situation which is not a hang but the design of the app means it's impossible to close it), 
# and if you press Ctrl-C repeatedly in the console, you eventually get a KeyboardInterrupt... but I don't think it's possible
# to "catch" this

# NB 2024-04-14 realised that this check on the gui thread status seemingly only happens AT THE END OF THE METHOD! ... is this right???
# def thread_check(gui_thread: bool):
def thread_check(gui_thread):
    # if gui_thread is None:
    #     logger.info(f'+++ A', stack_info=True)

    def pseudo_decorator(func):
        if not callable(func):
            # major coding error 
            raise Exception(f'func is type {type(func)}')
        def gui_checker_inner_function(*args, **kwargs):
            try:
                func.stack_trace = None
                if QtWidgets.QApplication == None: # under what circs might this happen???
                    return None
                if QtWidgets.QApplication.instance() != None: 
                    app_thread = QtWidgets.QApplication.instance().thread()
                    curr_thread = QtCore.QThread.currentThread()
                    # None means we don't check the GUI status of the thread
                    if gui_thread != None:
                        if (curr_thread == app_thread) != gui_thread:
                            err_msg = f'method {func.__qualname__} should have been called in {"GUI thread" if gui_thread else "non-GUI thread"}'
                            if logger != None:
                                logger.error(err_msg, stack_info=True)
                            # NB  would be such a major coding error that fatal exception is raised: QT5 likely to crash soon afterwards if this happens ...
                            raise Exception(err_msg)
                def executing_func(*args, **kwargs):
                    func.stack_trace  = ''.join(traceback.format_stack())
                    thread_check.stack_trace  = ''.join(traceback.format_stack())
                    thread_check.func = func
                    return func(*args, **kwargs)
                if QtWidgets.QApplication.instance() == None: 
                    error_msg = f'thread-checked function {func} - function is being run with no QApplication instance!'
                    logger.error(error_msg)
                    raise Exception(error_msg)
                return executing_func(*args, **kwargs)        
            except BaseException as e:
                msg = f'stack trace:\n{func.stack_trace}\n'
                if logger == None:
                    print(msg, file=sys.stderr)
                else:
                    logger.exception(msg, stack_info=True)
                # NB a KeyboardInterrupt on the DOS screen from which the app was launched, will not be "seen"
                # until you put focus back on the app (from the DOS screen)... but when you do this will stop the app: 
                if isinstance(e, KeyboardInterrupt):
                    sys.exit()
                raise e
        return gui_checker_inner_function
    return pseudo_decorator

# min_lib_version=None means "any version of lib"
def check_and_configure_TEST(min_lib_version=None, platform='linux_or_w10', min_python_version_str='3.9', single_instance=True, 
        pyqt=True, admin_user=False):
    cwd_path = pathlib.Path.cwd()
    sys.production_run = 'operative' in str(cwd_path)
    # you want to set up logging as early as poss...
    import library_core.configure_logging
    caller_appname = cwd_path.name
    if not library_core.configure_logging.configure_logging(caller_appname):
        print(f'FATAL. Logger configuration failed', file=sys.stderr)
        sys.exit()
    if hasattr(sys, 'pytl'):
        sys.pytl.log(f'here admin_user {admin_user}')
    if hasattr(sys, 'pytl'):
        sys.pytl.log('here')
    global logger
    if hasattr(sys, 'pytl'):
        sys.pytl.log('here')
    # NB I thought for a bit that you have to call colorlog.getLogger() to get a colour log... but this seems to deliver a colour log:
    try:
        logger = logging.getLogger(caller_appname)
    except BaseException as e:
        if hasattr(sys, 'pytl'):
            sys.pytl.log(f'e {e} type {type(e)}')
        raise e
    if hasattr(sys, 'pytl'):
        sys.pytl.log('here')
    logger.info(f'production run? {sys.production_run}') # TODO should be used for configuring logger path...
    if hasattr(sys, 'pytl'):
        sys.pytl.log('here')
    if admin_user:
        if hasattr(sys, 'pytl'):
            sys.pytl.log(f'here get_is_admin() {get_is_admin()}')
        if not get_is_admin():
            if hasattr(sys, 'pytl'):
                sys.pytl.log('here')
            logger.critical(f'FATAL. Must be run as "admin"/"elevated" user')
            if hasattr(sys, 'pytl'):
                sys.pytl.log('here')
            sys.exit()
    if platform == 'linux_or_w10':
        if (not sys.platform.startswith('lin')) and (not sys.platform.startswith('win')):
            logger.critical(f'FATAL. Disallowed OS: must be Linux or W10 but is {sys.platform}')
            sys.exit()
    elif platform != None and not sys.platform.startswith(platform):
        logger.critical(f'FATAL. Disallowed OS: must start with "{platform}" but is {sys.platform}')
        sys.exit()
    filenames = ['start_ve.bat', '.gitignore', 'conftest.py', 've_path_linux']
    for filename in filenames:
        file_path = cwd_path.joinpath(filename)
        if not file_path.is_file():
            logger.critical(f'FATAL. File {file_path} is not a file')
            sys.exit()

# 2025-12-13 not sure what this next stuff is about    
    
# 
#     # hooks    
#     sys.excepthook = custom_excepthook
#     sys.unraisablehook = custom_unraisablehook
#     # does this caller project have a version file under /src?
#     SOURCE_DIR_NAME = 'src'
#     caller_src_dir_path = cwd_path.joinpath(SOURCE_DIR_NAME)
#     # NB this is also a kind of check that the CWD is the root directory: a directory with "src" directory under it
#     if not caller_src_dir_path.exists():
#         logger.critical(f'FATAL. Caller CWD does not have a directory "{SOURCE_DIR_NAME}" under root dir. NB project must be run from project root directory')
#         sys.exit()
#     if caller_src_dir_path.is_file():
#         logger.critical(f'FATAL. {caller_src_dir_path} is a file but should be a dir')
#         sys.exit()
#     caller_file_path = pathlib.Path(inspect.stack()[1].filename) 
#     # logger.info(f'caller_file_path |{caller_file_path}|')
#     if not caller_file_path.is_relative_to(cwd_path): 
#         logger.critical(f'FATAL. Caller file |{caller_file_path}| is not relative to CWD |{cwd_path}|. NB project must be run from project root directory')
#         sys.exit()
#     # we can be pretty sure at this point that the name of the last directory of the CWD is the caller_appname 
#         
#     """ make it possible to import src\version_file.py
#     NB because this is placed at the start of sys.path, the attempt to import version_file.py should use that of the caller
#     project (if there is such a file), rather than version_file.py of the lib project (but this is checked later)
#     """
#     sys.path.insert(0, str(caller_src_dir_path))    
#     VERSION_FILE_STEM = 'version_file'
#     if VERSION_FILE_STEM in sys.modules:
#         logger.critical(f'FATAL. sys.modules already contains a key "{VERSION_FILE_STEM}"')
#         sys.exit()
#     try:
#         caller_version_file_mod = importlib.import_module(VERSION_FILE_STEM)
#     except ModuleNotFoundError:
#         logger.critical(f'FATAL. Module not found trying to import caller version file |{VERSION_FILE_STEM}| under {caller_src_dir_path}')
#         sys.exit()
#     except BaseException:
#         logger.exception(f'FATAL. Trying to import caller version file |{VERSION_FILE_STEM}| under {caller_src_dir_path}')
#         sys.exit()
#     sys.modules['caller_version_file_mod'] = sys.modules[VERSION_FILE_STEM]
#     del  sys.modules[VERSION_FILE_STEM]
#     caller_version_file_path = pathlib.Path(caller_version_file_mod.__file__)
#     if caller_version_file_path.parent != caller_src_dir_path:
#         logger.critical(f'FATAL. The version file imported as the caller version file is not under {caller_src_dir_path}: its path is {caller_version_file_path}')
#         sys.exit()
#     VERSION_ATTRIB_NAME = 'version'
#     if not hasattr(caller_version_file_mod, VERSION_ATTRIB_NAME):
#         logger.critical(f'FATAL. Caller version file |{VERSION_FILE_STEM}| under {caller_src_dir_path} does not contain "{VERSION_ATTRIB_NAME}" attribute')
#         sys.exit()
#     # the version of the caller project must be checked and a means found to "return" it to the caller project
#     caller_version_str = getattr(caller_version_file_mod, VERSION_ATTRIB_NAME)
#     version_type = type(caller_version_str)
#     if version_type != str:
#         logger.critical(f'FATAL. Caller version attribute |{VERSION_ATTRIB_NAME}| in file {caller_version_file_path}, i.e. {caller_version_str}, is wrong class: {version_type}')
#         sys.exit()
#     try:
#         caller_version = packaging_version.parse(caller_version_str)
#     except BaseException:
#         logger.critical(f'FATAL. Could not parse lib version string |{caller_version_str}| to get packaging version')
#         sys.exit()
#     # now we have to check that this imported mod is indeed the version_file.py belonging to this lib project, not to the caller project.
#     # first find "lib" directory above here
#     this_file_path = pathlib.Path(__file__)
#     # logger.info(f'this_file_path.parts {this_file_path.parts}')
#     lib_module_root_dir_path = None
#     for i, part in enumerate(reversed(this_file_path.parts)):
#         if part.lower() == 'lib':
#             # NB we are counting ***backwards*** with the counter variable, i
#             lib_module_root_dir_path = pathlib.Path(*this_file_path.parts[:-i])
#             break
#     if lib_module_root_dir_path == None:
#         logger.critical(f'FATAL. Unable to determine the root dir of the "lib" module from path of this file: {this_file_path}')
#         sys.exit()
#     lib_module_src_dir_path = lib_module_root_dir_path.joinpath(SOURCE_DIR_NAME)
#     if not lib_module_src_dir_path.is_dir():
#         logger.critical(f'FATAL. Root dir of the "lib" module does not seem to have a dir at {lib_module_src_dir_path}')
#         sys.exit()
# 
#     # logger.info('check version of lib module:')
#     """ make it possible to import src\version_file.py in the *** lib *** module
#     NB because this is placed at the start of sys.path, the attempt to import version_file.py should use that of the lib
#     project (if there is such a file), rather than (already imported) version_file.py of the caller project (but this is checked later)
#     """
#     sys.path.insert(0, str(lib_module_src_dir_path))    
#     try:
#         lib_version_file_mod = importlib.import_module(VERSION_FILE_STEM)
#     except ModuleNotFoundError:
#         logger.critical(f'FATAL. Module not found trying to import lib version file |{VERSION_FILE_STEM}| under {lib_module_src_dir_path}')
#         sys.exit()
#     except BaseException:
#         logger.exception(f'FATAL. Trying to import lib version file |{VERSION_FILE_STEM}| under {lib_module_src_dir_path}')
#         sys.exit()
#     sys.modules['lib_version_file_mod'] = sys.modules[VERSION_FILE_STEM]
#     del  sys.modules[VERSION_FILE_STEM]
#     lib_version_file_path = pathlib.Path(lib_version_file_mod.__file__)
#     if lib_version_file_path.parent != lib_module_src_dir_path:
#         logger.critical(f'FATAL. The version file imported as the lib version file is not under {lib_module_src_dir_path}: its path is {lib_version_file_path}')
#         sys.exit()
#     lib_version_str = getattr(lib_version_file_mod, VERSION_ATTRIB_NAME)
#     version_type = type(lib_version_str)
#     if version_type != str:
#         logger.critical(f'FATAL. Lib version attribute in file is wrong class: {version_type}')
#         sys.exit()
#     try:
#         lib_version = packaging_version.parse(lib_version_str)
#     except BaseException:
#         logger.critical(f'FATAL. Could not parse lib version string |{lib_version_str}| to get packaging version')
#         sys.exit()
#     if min_lib_version == None:
#         # logger.info('OK, caller is unconcerned with version of lib module')
#         pass
#     else:
#         if type(min_lib_version) != packaging_version.Version:
#             logger.critical(f'FATAL. Min lib version required is not packaging.version.Version but type {type(min_lib_version)}')
#             sys.exit()
#         
#         if lib_version < min_lib_version:
#             logger.critical(f'FATAL. Lib version must be {min_lib_version} at minimum but is {lib_version}')
#             sys.exit()
#         # logger.info(f'version of lib is OK...')
#     
#     # logger.info(f'check OS...')    
#     if platform == 'linux_or_w10':
#         if (not sys.platform.startswith('lin')) and (not sys.platform.startswith('win')):
#             logger.critical(f'FATAL. Disallowed OS: must be Linux or W10 but is {sys.platform}')
#             sys.exit()
#     elif platform != None and not sys.platform.startswith(platform):
#         logger.critical(f'FATAL. Disallowed OS: must start with "{platform}" but is {sys.platform}')
#         sys.exit()
#     # platform=None will effectively disable any checks
#     # logger.info(f'check certain required files...')
#     
#     filenames = ['start_ve.bat', '.gitignore', 'conftest.py', 'start_lin_ve']
#     for filename in filenames:
#         file_path = cwd_path.joinpath(filename)
#         if not file_path.is_file():
#             logger.critical(f'FATAL. File {file_path} is not a file')
#             sys.exit()
#             
#     """        
# To make sure that all external Python modules have been installed in the project VE, it is I think a good idea
# to import all .py files in the project. This relies on them having all the import statements at the top of the file 
# (i.e. rather than in pieces of conditionally executed code) as far as possible. Sometimes a given module may occasionally only be
# needed in W10 and not in Linux, but this will be rare, and will be fine: if a sys.platform == .. test is done in the file
#     
# First, before anything else, make it possible to import "thread_check" (decorator) from the constants in "from constants import *"
# If you don't do this first, the import of all files which do "from constants import *" and then use the decorator will fail    
#     """ 
#     constants_file_path = caller_file_path.parent.joinpath('constants.py')
#     if constants_file_path.is_file():
#         try:
#             constants_module = importlib.import_module(constants_file_path.stem)
#         except BaseException:
#             logger.exception(f'FATAL. Trying to import constants.py file |{constants_file_path}|')
#             sys.exit()
#         constants_module.thread_check = thread_check
#         # also make ***this*** library module available to the constants module
#         constants_module.library_main_submodule = importlib.import_module(f'{this_file_path.parent.name}.{this_file_path.stem}')
#         
#     
#     for py_file_path in caller_src_dir_path.glob('**/*.py'):
#         # logger.info(f'--> found {py_file_path} stem |{py_file_path.stem}|')
#         if py_file_path.stem in sys.modules:
#             module = sys.modules[py_file_path.stem]
#             module_path = pathlib.Path(module.__file__)
#             if module_path == py_file_path:
#                 # logger.info(f'======= file {py_file_path} has already been imported: skipping')
#                 continue 
#             msg = f"""FATAL. There is already a key for {py_file_path.stem} in sys.modules, with path |{module_path}|,
# ...but the one to be imported is |{py_file_path}|"""
#             logger.critical(msg)
#             sys.exit()
#         sys.path.insert(0, str(py_file_path.parent))
#         try:
#             imported_module = importlib.import_module(py_file_path.stem)
#         except ModuleNotFoundError as e:
#             logger.exception(f'FATAL. Module not found, name |{e.name}|, trying to import caller project .py file |{py_file_path}|')
#             sys.exit()
#         except BaseException:
#             logger.exception(f'FATAL. Trying to import caller project .py file |{py_file_path}|')
#             sys.exit()
#         del sys.path[0]
#         imported_module_path = pathlib.Path(imported_module.__file__)
#         if imported_module_path != py_file_path: 
#             logger.critical(f'FATAL. An import of a .py file went wrong: tried to import |{py_file_path}| but the resultant module has path {imported_module_path}')
#             sys.exit()
#         del sys.modules[py_file_path.stem]
#         
#     # logger.info(f'check that python version is acceptable... sys.version_info {sys.version_info}\ndir {dir(sys.version_info)}\ntype {type(sys.version_info)}')
#     # logger.info(f'check that python version is acceptable...')
#     python_version = packaging_version.Version(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')
#     min_python_version = packaging_version.Version(min_python_version_str)
#     # logger.info(f'python_version {python_version}')
#     if python_version < min_python_version:
#         logger.critical(f'FATAL. Project is running Python {python_version} but the minimum Python version is {min_python_version}')
#         sys.exit()
# 
#     if single_instance:          
#         # logger.info(f'check that instance of this project is not already running...')
#         sic = SingleInstanceChecker(caller_appname)
#         if sic.already_running():
#             logger.critical(f'FATAL. Another instance of this script {caller_appname} appears to be running.')
#             sys.exit()
#             
#     if pyqt:
#         # logger.info(f'check that PyQT version is high enough...')
#         from PyQt5 import QtCore
#         qt_version = int(QtCore.QSysInfo.productVersion())  
#         min_qt_version = 10
#         if qt_version < min_qt_version:
#             logger.critical(f'FATAL. QT version must be {min_qt_version} or higher but is {qt_version}')
#             sys.exit()
#     # TODO sys.argv should also be examined here... and the results returned 
#     return {'caller_version': caller_version} 


# TODO needs TDD

def request_call(verb, *args, **kwargs):
    DEFAULT_REQUESTS_TIMEOUT = (5, 15)
    LINE_OF_DASHES = 100 * '-'
    if 'timeout' not in kwargs:
        kwargs['timeout'] = DEFAULT_REQUESTS_TIMEOUT
    try:
        response = requests.request(verb, *args, **kwargs)
    except BaseException as exception:
        logger_found = False
        msg1 = f'verb: |{verb}|\nargs {args}\nkwargs {kwargs}\nLOWER STACK:\n{LINE_OF_DASHES}'
        try:
            logger.exception(msg1)
            logger_found = True
            logger.error(f'{LINE_OF_DASHES} LOWER STACK ENDS\n')
        except AttributeError:
            print(f'\n\n*** request_call: WARNING:\nlogger not set up as global variable in {__file__}\n', file=sys.stderr)
            print(msg1, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            print(f'{LINE_OF_DASHES} LOWER STACK ENDS\n', file=sys.stderr)
        raw_tb = traceback.extract_stack()
        if 'data' in kwargs and len(kwargs['data']) > 500: # anticipate giant data string
            kwargs['data'] = f'{kwargs["data"][:500]}...'
        msg2 = f'UPPER STACK:\n{LINE_OF_DASHES}:\n' + ''.join(traceback.format_list(raw_tb[:-1])) + f'{LINE_OF_DASHES} UPPER STACK ENDS\n'
        logger.error(msg2) if logger_found else print(msg2, file=sys.stderr) 
        return (False, exception)
    return (True, response)


# 2025-12-13 not sure what this next stuff is about

# def interruptible_request_call(verb, *args, **kwargs):
#     DEFAULT_REQUESTS_TIMEOUT = (5, 15)
#     LINE_OF_DASHES = 100 * '-'
#     if 'timeout' not in kwargs:
#         kwargs['timeout'] = DEFAULT_REQUESTS_TIMEOUT
#     
#     queue = multiprocessing.SimpleQueue()
#     def func(queue):
#     
#         try:
#             response = requests.request(verb, *args, **kwargs)
#         except BaseException as exception:
#             
#             logger.exception(f'verb: |{verb}|\nargs {args}\nkwargs {kwargs}\nLOWER STACK:\n{LINE_OF_DASHES}')
#             logger.error(f'{LINE_OF_DASHES} LOWER STACK ENDS\n')
#             raw_tb = traceback.extract_stack()
#             if 'data' in kwargs and len(kwargs['data']) > 500: # anticipate giant data string
#                 kwargs['data'] = f'{kwargs["data"][:500]}...'
#             msg = f'UPPER STACK:\n{LINE_OF_DASHES}:\n' + ''.join(traceback.format_list(raw_tb[:-1])) + f'{LINE_OF_DASHES} UPPER STACK ENDS\n'
#             logger.error(msg) 
#             # return (False, exception)
#             queue.put((False, exception))
#         
#         # return (True, response)
#         queue.put((True, response))
#     
#     logger.info('here')
#     process = multiprocessing.Process(target=func, args=queue)
#     logger.info('here')
#     process.start()
#     logger.info('here')
#     returned_val = queue.get()
#     logger.info(f'returned_val {returned_val}')

    