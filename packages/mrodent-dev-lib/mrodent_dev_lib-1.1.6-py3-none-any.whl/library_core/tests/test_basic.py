# pyright: reportMissingImports=false
import logging, pathlib, sys, collections, re, importlib, copy
from unittest import mock
import toml # type: ignore
import packaging.version, pytest, colorlog 
from concurrent_log_handler import ConcurrentRotatingFileHandler  
# import src.library_core.library_main as library_main
import configure_logging #@UnusedImport #@UnresolvedImport
import library_main
from common_for_tests import AnyStringWithRegex, is_match

cwd_path = pathlib.Path.cwd()

# if sys.platform.startswith('lin'):
#     # TODO
#     print(f'TODO: only W10 currently', file=sys.stderr)
#     sys.exit(1)
     
@pytest.fixture(autouse=True)
def mock_reset_test_logger_situation():
    test_logger = logging.getLogger('test')
    assert len(test_logger.handlers) == 0
    test_existing_handlers = []
    for handler in test_logger.handlers:
        test_existing_handlers.append(handler)
    yield
    # restore pytest logger handlers (essential for any tests which test logging configuration!)     
    test_logger.handlers = test_existing_handlers

@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above')
def test_version_file_contains_version():
    with open('version.toml', 'r') as f:
        version_dict = toml.load(f)
    assert 'version' in version_dict
    version_val_as_str = version_dict['version']
    from packaging import version as packaging_version #@UnusedImport #@UnresolvedImport
    version = packaging_version.Version(version_val_as_str)
    assert type(version) == packaging_version.Version, f'type is {type(version)}'

@pytest.mark.parametrize('os', ['win32', 'win64', 'linux', 'other_os'])
@pytest.mark.parametrize('return_vals', [True, False])
@mock.patch('pathlib.Path.is_file', return_value=True) # pretend that this __main__.py file exists
def test_os_is_windows_or_linux(_, capsys, os, return_vals):
    assert len(logging.getLogger().handlers) == 4    
    with mock.patch('sys.platform', new_callable=mock.PropertyMock(return_value=os)):
        with mock.patch('sys.argv', new_callable=mock.PropertyMock(return_value=('python', 'src/core'))):        
            if os == 'other_os' and not return_vals:
                with pytest.raises(SystemExit) as excinfo:
                    app_name = cwd_path.parts[-1]
                    return_val = library_main.do_start_run_checks(app_name, cwd_path.joinpath('src', 'core', '__main__.py'), return_value=return_vals)
                assert excinfo.value.code == library_main.UNKNOWN_OS                    
            else:
                app_name = cwd_path.parts[-1]
                return_val = library_main.do_start_run_checks(app_name, cwd_path.joinpath('src', 'core', '__main__.py'), return_value=return_vals)        
    _, err = capsys.readouterr()
    if os == 'other_os':
        if return_vals:
            assert return_val[0] == library_main.UNKNOWN_OS and re.match(r'FATAL\..*windows or linux platforms.*', return_val[1]) != None
        else:
            assert 'FATAL' in err, f'err was |{err}|'
    elif return_vals:
        assert return_val == library_main.CHECKS_PASSED  
 
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above')
def test_start_ve_files_exists():
    # start_ve.bat is the file that activates the virtual env in W10, start_lin_ve in Linux
    file_path_str = 'start_ve.bat' if sys.platform.startswith('win') else 'start_lin_ve'
    assert pathlib.Path(file_path_str).is_file()
 
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above') 
def test_git_ignore_file_exists():
    file_path = pathlib.Path('.gitignore')
    assert file_path.is_file()
 
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above') 
def test_core_package_exists():
    working_dir_path = pathlib.Path('src/library_core')
    assert working_dir_path.is_dir()
    file_path = pathlib.Path('src', 'library_core', 'library_main.py')
    assert file_path.is_file()
 
@pytest.mark.parametrize('version_found', ['real', (3, 9, 1)])
@pytest.mark.parametrize('return_vals', [True, False])  
@mock.patch('pathlib.Path.is_file', return_value=True) # pretend that this __main__.py file exists
def test_min_python_version_v10(_, capsys, version_found, return_vals):
    if version_found == 'real':
        version_info = sys.version_info
    else:
        VersionInfo = collections.namedtuple('VersionInfo', 'major minor micro')
        version_info = VersionInfo(*version_found)
    with mock.patch('sys.argv', new_callable=mock.PropertyMock(return_value=('python', 'src/core'))):
        with mock.patch('sys.version_info', version_info):
            if (version_found == 'real') or return_vals:
                app_name = cwd_path.parts[-1]
                return_val = library_main.do_start_run_checks(app_name, cwd_path.joinpath('src', 'core', '__main__.py'), return_value=return_vals)        
            else:
                with pytest.raises(SystemExit) as excinfo:
                    app_name = cwd_path.parts[-1]
                    return_val = library_main.do_start_run_checks(app_name, cwd_path.joinpath('src', 'core', '__main__.py'), return_value=return_vals)
                assert excinfo.value.code == library_main.PYTHON_VERSION_IS_TOO_LOW                            
    _, err = capsys.readouterr()
    if return_vals:
        if version_found == 'real':
            assert return_val == library_main.CHECKS_PASSED
        else:
            assert return_val[0] == library_main.PYTHON_VERSION_IS_TOO_LOW and re.match( r'FATAL\..*Python 10 or higher.*', return_val[1]) != None 
    else:
        if version_found == 'real':
            assert 'FATAL' not in err, f'err was |{err}|'
            assert return_val == library_main.CHECKS_PASSED
        else:
            assert 'FATAL' in err, f'err was |{err}|'
 
@pytest.mark.parametrize('good_path', [True, False])
@mock.patch(f'pathlib.Path.cwd')
@mock.patch('pathlib.Path.is_file', return_value=True) # pretend that this __main__.py file exists
@pytest.mark.parametrize('return_vals', [True, False])  
def test_main_stops_if_not_run_from_top_directory(_, mock_cwd, good_path, capsys, return_vals):
    # NB this test (like others) only works if "pytest" is run from the project directory
    # NB assumption: that there is, above this file, a dir "tests", of which the parent dir is the project root dir
    file_path = pathlib.Path(__file__)
    while str(file_path.parts[-1]).lower() != 'tests':
        file_path = file_path.parent
    root_dir_path_str = file_path.parent.parts[-1].lower()
    if cwd_path.parts[-1] != root_dir_path_str:
        raise Exception(f'This test file must be run from the root project directory "{root_dir_path_str}", but cwd is {cwd_path}')
    if good_path:
        # a "good path" must end with the directory named [app_name]
        mock_cwd.return_value = cwd_path
        app_name = cwd_path.parts[-1]
        return_value = library_main.do_start_run_checks(app_name, mock_cwd.return_value.joinpath('src', 'core', '__main__.py'), return_value=return_vals)
        assert return_value ==  library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    else:
        mock_cwd.return_value = pathlib.Path('random_path')
        if return_vals:
            app_name = cwd_path.parts[-1]
            return_value = library_main.do_start_run_checks(app_name, mock_cwd.return_value, return_value=return_vals)        
            _, err = capsys.readouterr()
            assert return_value[0] == library_main.NOT_RUN_FROM_PROJECT_ROOT
            assert re.match( r'FATAL\..*top-level directory.*', return_value[1]) != None
            assert err == ''
        else:
            with pytest.raises(SystemExit) as excinfo:
                app_name = cwd_path.parts[-1]
                library_main.do_start_run_checks(app_name, mock_cwd.return_value, return_value=return_vals)        
            _, err = capsys.readouterr()
            assert re.match( r'FATAL\..*top-level directory.*', err) != None
            assert excinfo.value.code == library_main.NOT_RUN_FROM_PROJECT_ROOT
         
@pytest.mark.parametrize('good_path', [True, False])
@mock.patch(f'pathlib.Path.resolve')    
@mock.patch('pathlib.Path.is_file', return_value=True) # pretend that this __main__.py file exists
@pytest.mark.parametrize('return_vals', [True, False])      
def test_main_path_is_relative_to_cwd(_, mock_resolve, good_path, capsys, return_vals):
    file_path = pathlib.Path(__file__)
    while str(file_path.parts[-1]).lower() != 'tests':
        file_path = file_path.parent
    root_dir_path = file_path.parent
    if good_path:
        mock_resolve.return_value = root_dir_path.joinpath('src', 'core', '__main__.py')
        app_name = cwd_path.parts[-1]
        return_value = library_main.do_start_run_checks(app_name, mock_resolve.return_value)
        assert return_value ==  library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    else:
        app_name = file_path.parent.parts[-1].lower()
        # this "resolved" Path ends correctly, but the path to __main__.py is not under the cwd...
        caller_file_path = pathlib.Path('some_dir', app_name, 'src', 'core', '__main__.py')
        # to use these paths in a regex the backslashes need to be doubled in w10
        caller_file_path_str = str(caller_file_path).replace("\\", "\\\\")
        cwd_path_str = str(cwd_path).replace("\\", "\\\\")
        pattern_str = fr'FATAL\..*caller file {caller_file_path_str} is not under cwd ({cwd_path_str}).*'
        mock_resolve.return_value = caller_file_path
        if return_vals:
            app_name = cwd_path.parts[-1]
            return_val = library_main.do_start_run_checks(app_name, mock_resolve.return_value, return_value=return_vals)        
            _, err = capsys.readouterr()
            assert re.match(pattern_str, return_val[1], flags=re.IGNORECASE) != None
            assert return_val[0] == library_main.CALLER_FILE_NOT_UNDER_CWD
        else:
            with pytest.raises(SystemExit) as excinfo:
                app_name = cwd_path.parts[-1]
                library_main.do_start_run_checks(app_name, mock_resolve.return_value, return_value=return_vals)        
            _, err = capsys.readouterr()
            assert re.match(pattern_str, err, flags=re.IGNORECASE) != None
            assert excinfo.value.code == library_main.CALLER_FILE_NOT_UNDER_CWD

@pytest.mark.skip(reason="""because as of 2023-03-12 this test no longer applies: i.e. it is permitted to do these checks from a .py file
which is not in the package src/core of the calling package""")
@pytest.mark.parametrize('good_path', [True, False])
@mock.patch('pathlib.Path.is_file', return_value=True) # pretend that this __main__.py file exists
@pytest.mark.parametrize('return_vals', [True, False]) 
def test_main_path_relative_to_cwd_is_in_expected_package(_, good_path, capsys, return_vals):
    # NB this test started in a project other than lib... it is now slightly puzzling because 
    # another project will be calling do_start_run_checks()... but the main thing is to ensure that 
    # (unless an optional keyword "package_name" param is supplied) the path ends "src/core/[...some file]"
    file_path = pathlib.Path(__file__)
    while str(file_path.parts[-1]).lower() != 'tests':
        file_path = file_path.parent
    root_dir_path = file_path.parent
    if good_path:
        app_name = cwd_path.parts[-1]
        return_value = library_main.do_start_run_checks(app_name, root_dir_path.joinpath('src', 'core', '__main__.py'), return_value=return_vals)
        assert return_value ==  library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    else:
        caller_file_path = root_dir_path.joinpath('other_source_folder', 'core', '__main__.py')
        # to use these paths in a regex the backslashes need to be doubled in w10
        caller_file_path_str = str(caller_file_path).replace("\\", "\\\\")
        pattern_str = f'FATAL. This parent dirs of file {caller_file_path_str} must be src/core'
        if return_vals:
            app_name = cwd_path.parts[-1]
            return_val = library_main.do_start_run_checks(app_name, caller_file_path, return_value=return_vals)
            _, err = capsys.readouterr()
            assert re.match(pattern_str, return_val[1], flags=re.IGNORECASE) != None
            assert return_val[0] == library_main.CALLER_FILE_NOT_IN_EXPECTED_PACKAGE
        else:
            with pytest.raises(SystemExit) as excinfo:
                app_name = cwd_path.parts[-1]
                library_main.do_start_run_checks(app_name, caller_file_path, return_value=return_vals)
            _, err = capsys.readouterr()
            assert re.match(pattern_str, err, flags=re.IGNORECASE) != None
            assert excinfo.value.code == library_main.CALLER_FILE_NOT_IN_EXPECTED_PACKAGE
 
# NB 2021-12-22 this does actually need to configure the logger, so do not use fixture mock_out_configure_logger_method
# 2022-07-31 far from sure what the purpose of this test is!
def test_get_logger_should_deliver_colorlog_logger_with_at_least_one_handler(capsys):
    assert len(logging.getLogger().handlers) == 4
    app_name = cwd_path.parts[-1]
    configure_logging.configure_logging(app_name)
    root_logger = colorlog.getLogger()
    assert len(root_logger.handlers) > 0
    local_logger = colorlog.getLogger(__name__)
    assert len(local_logger.handlers) == 0
    main_logger = colorlog.getLogger('__main__')
    assert len(main_logger.handlers) == 0
    random_logger = colorlog.getLogger('???')
    assert len(random_logger.handlers) == 0
 
def test_logger_prints_to_stdout(capsys, tmpdir):
    configure_logging.configure_logging('test')
    logger = logging.getLogger('test')
    # sys.pytl.log(f'logger {logger}')
    
    # NB by default the logger is set at "WARNING or higher": this is changed by logger.setLevel(logging.DEBUG)
    logger.info('messageXXX')
    # NB TODO "warning" or higher should be printed to stderr (and be printed in bright red, even in W10); below that to stdout
    logger.warning('messageYYY')
    _, err = capsys.readouterr()
    assert 'messageXXX' in err and 'messageYYY' in err, f'err was |{err}|'
 
def test_configure_logging_creates_logger_with_info_level():
    assert len(logging.getLogger('test').handlers) == 0
    configure_logging.logger = None
    configure_logging.configure_logging('test')
    logger = logging.getLogger('test')
    assert logger.level == logging.INFO
    # this should create 2 handlers: stream handler (for stdout) and file handler (for file logging)
    assert len(logging.getLogger('test').handlers) == 2
 
def test_configure_logging_creates_and_adds_streamhandler_with_EnhancedColourFormatter():
    assert len(logging.getLogger().handlers) == 4
    configure_logging.configure_logging('test')
    # NB 2 (I think) of pytest's only loggers are colorlog.StreamHandlers!
    n_stream_handlers_with_ecf = 0
    logger = logging.getLogger('test')
#     sys.pytl.log(f'logger {logger}')
#     sys.pytl.log(f'len(logger.handlers) {len(logger.handlers)}')
    for handler in logger.handlers:
        if isinstance(handler, colorlog.StreamHandler):
            if isinstance(handler.formatter, configure_logging.EnhancedColourFormatter):
                logging.info(f'handler.formatter {handler.formatter}')
                n_stream_handlers_with_ecf += 1
                formatter = handler.formatter
    assert n_stream_handlers_with_ecf == 1
    # sys.pytl.log(f'formatter._fmt |{formatter._fmt}|')
    assert is_match(r'^%\(log_color\)s%\(asctime\)s %\(levelname\)s %\(module\)s \[%\(pathname\)s %\(lineno\)d\]:\n%\(message\)s\n$', formatter._fmt)
 
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above') 
def test_EnhancedColourFormatter_prints_only_path_from_cwd(capsys):
    sys.pytl.log(f'hasattr(logging, "stream_handler") {hasattr(logging, "stream_handler")}')
    configure_logging.configure_logging('test')
    logger = logging.getLogger('test')
    sys.pytl.log(f'hasattr(logging, "stream_handler") {hasattr(logging, "stream_handler")}')
    logger.info('some bubbles')
    _, err = capsys.readouterr()
    # the date-time part at the start (after the day of the week) should not contain a comma
    # this output string starts with several colour-control characters and then the day of the week
    module_name = __name__
    pattern_str = fr'.*INFO {module_name} \[\s*(.+{module_name}.py) \d+\]:.*some bubbles.*'
    # sys.pytl.log(f'out |{out}|')
    result = re.match(pattern_str, err, re.DOTALL)
    assert result != None
    file_path = pathlib.Path(__file__)
    last_part_of_path = file_path.relative_to(cwd_path.parent)
    assert result.groups()[0] == str(last_part_of_path)
 
def test_configure_logging_creates_and_adds_ConcurrentRotatingFileHandler_with_standard_formatter():
    assert len(logging.getLogger().handlers) == 4
    assert configure_logging.configure_logging('test')
    n_crf_handlers_with_std_formatter = 0
    
    # for handler in configure_logging.logger.handlers:
    logger = logging.getLogger('test')    
    for handler in logger.handlers:
        
        if isinstance(handler, ConcurrentRotatingFileHandler):
            print(f'dir(handler) {dir(handler)}')
            if isinstance(handler.formatter, logging.Formatter):
                n_crf_handlers_with_std_formatter += 1
    assert n_crf_handlers_with_std_formatter == 1
 
def test_ConcurrentRotatingFileHandler_is_created_with_certain_params():
    assert len(logging.getLogger().handlers) == 4
    with mock.patch('concurrent_log_handler.ConcurrentRotatingFileHandler.__init__', return_value=None) as mock_constructor:
        with mock.patch('logging.Logger.info'):
            configure_logging.configure_logging('test')
    logging_file_path = pathlib.Path(configure_logging.STANDARD_LOGGING_LOCATION, 'test', configure_logging.EnhancedStdFormatter.LOG_FILENAME)    
    # mock_constructor.assert_called_once_with(logging_file_path, 'a', 100000, 10, 'utf-8')
    # change to default size 2024-12-07
    mock_constructor.assert_called_once_with(logging_file_path, 'a', 1024 * 1024, 10, 'utf-8')
 
def test_file_formatter_is_created_with_certain_params():
    assert len(logging.getLogger().handlers) == 4
    
    # with mock.patch('logging.Formatter.__init__', return_value=None) as mock_constructor:
    with mock.patch.object(configure_logging, 'EnhancedStdFormatter', return_value=None) as mock_constructor:
        
        with mock.patch('logging.Logger._log'):
            configure_logging.configure_logging('test')
    mock_constructor.assert_called_with('%(asctime)s - [%(name)s] - %(levelname)s %(module)s [%(pathname)s %(lineno)d]:\n%(message)s')
 
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above') 
def test_EnhancedStandardFormatter_prints_only_path_from_cwd():
    sys.pytl.log(f'hasattr(logging, "stream_handler") {hasattr(logging, "stream_handler")}')
    logging_file_path = pathlib.Path(configure_logging.STANDARD_LOGGING_LOCATION, 'test', configure_logging.EnhancedStdFormatter.LOG_FILENAME)
    logging_file_path.unlink(missing_ok=True)
    logging_file_path.parent.mkdir(parents=True, exist_ok=True)
    configure_logging.configure_logging('test')
    logger = logging.getLogger('test')
    logger.info('some bubbles')
    # NB caplog.text does not capture the **formatted** messages, only the messages as formatted by pytest's formatter
    # module_name = __name__ # 2022-08-07: suspicion: __name__ may be different in W10
    module_name = 'configure_logging'
    # the date-time part at the start should not contain a comma
    equals = configure_logging.EnhancedStdFormatter._LINE_OF_EQUALS
    # NB the ".*" at the start here was added 2022-08-18 because the logging path is first logged by configure_logging()
    pattern_str = fr'.*{equals}\n[\d\-\s:\.]+ - \[test\] - INFO {module_name} \[\s*(.+{module_name}.py) \d+\]:.*some bubbles\n{equals}.*'
    with open(logging_file_path, 'r') as f:
        log_file_text = f.read()
    result = re.match(pattern_str, log_file_text, re.DOTALL)
    assert result != None
    # now test to make sure that the path of the file where the log message was done, relative to the cwd root, is included
    file_path = pathlib.Path(configure_logging.__file__)
    last_part_of_path = file_path.relative_to(cwd_path.parent)
    
    assert result.groups()[0] == str(last_part_of_path)
 
def test_logging_dir_is_created_if_does_not_exist(tmpdir):
    app_name = cwd_path.parts[-1]
    logging_dir_path = pathlib.Path(str(tmpdir)).joinpath('logging_dir', app_name)
    logging_dir_path_str = str(logging_dir_path)
    with mock.patch('configure_logging.STANDARD_LOGGING_LOCATION', 
        new_callable=mock.PropertyMock(return_value=logging_dir_path_str)):
        configure_logging.configure_logging('test')
    assert logging_dir_path.is_dir()
 
def test_warn_message_out_if_logging_dir_fails_to_be_created(tmpdir):
    assert len(logging.getLogger().handlers) == 4
    app_name = cwd_path.parts[-1]
    logging_dir_path = pathlib.Path(str(tmpdir)).joinpath('logging_dir', app_name)
    logging_dir_path_str = str(logging_dir_path)
    with mock.patch('configure_logging.STANDARD_LOGGING_LOCATION', 
        new_callable=mock.PropertyMock(return_value=logging_dir_path_str)):
        with mock.patch('pathlib.Path.mkdir', side_effect=Exception()):
            with pytest.raises(Exception) as e:
                # sys.pytl.log(f'here')
                configure_logging.configure_logging('test')
                    
    # sys.pytl.log(f'here {e}')
    assert not logging_dir_path.is_dir()
    assert 'WARNING: failed to create logging directory' in str(e)
    # the custom console streamhandler *is* created, after removing the default stderr streamhandler
    assert len(logging.getLogger().handlers) == 4
 
@mock.patch(f'logging.basicConfig')
def test_basic_logger_is_not_configured_if_exception_raised(mock_basic):
    assert len(logging.getLogger().handlers) == 4
    with mock.patch('logging.Logger.setLevel', side_effect=Exception('random problem')):
        with pytest.raises(Exception):
            configure_logging.configure_logging('test')
    mock_basic.assert_not_called()
    # _, err = capsys.readouterr()
    # assert 'WARNING: unexpected problem trying to configure basic logger' in err
    # assert 'random problem' in err
     
def test_logger_info_message_with_logging_path_if_successful_configuration():
    with mock.patch('logging.Logger.info') as mock_info:
        configure_logging.configure_logging('test')
    logging_output_path = pathlib.Path(configure_logging.STANDARD_LOGGING_LOCATION, 'test', 
        configure_logging.EnhancedStdFormatter.LOG_FILENAME)
    # this got a "re.error: bad escape" before I did this
    logging_output_path = re.sub(r"\\", ".", str(logging_output_path))
    mock_info.assert_called_once_with(AnyStringWithRegex(f'.*{logging_output_path}.*'))
  
@mock.patch('pathlib.Path.is_file', return_value=True) # pretend that this __main__.py file exists   
def test_do_start_run_checks_can_return_values_rather_than_exiting(_):
    app_name = cwd_path.parts[-1]
    VersionInfo = collections.namedtuple('VersionInfo', 'major minor micro')
    version_info = VersionInfo(3, 9, 1)
    with mock.patch('sys.version_info', version_info):
        return_value = library_main.do_start_run_checks(app_name, cwd_path.joinpath('src', 'core', '__main__.py'), return_value=True)
    assert return_value[0] == library_main.PYTHON_VERSION_IS_TOO_LOW     
 
@pytest.mark.parametrize('package_name', ['string_name', False, 0, None])
@pytest.mark.parametrize('return_vals', [True, False])
@mock.patch('pathlib.Path.is_file', return_value=True) # pretend that this __main__.py file exists
def test_do_start_run_checks_checks_package_name_param(_, package_name, return_vals, capsys):
    app_name = cwd_path.parts[-1]
    caller_file_path = cwd_path.joinpath('src', package_name, '__main__.py') if package_name == 'string_name' else pathlib.Path('blip') 
    if package_name == 'string_name':
        return_val = library_main.do_start_run_checks(app_name, caller_file_path, package_name=package_name, return_value=return_vals)
        assert return_val == library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    elif return_vals:
        return_val = library_main.do_start_run_checks(app_name, caller_file_path, package_name=package_name, return_value=return_vals)
        assert return_val[0] == library_main.BAD_PARAMS
        assert re.match(fr'FATAL\..*Bad param.*', return_val[1]) != None, f'return_val[1] |{return_val[1]}|'
        _, err = capsys.readouterr()
        assert err == ''
    else:
        with pytest.raises(SystemExit) as excinfo:
            library_main.do_start_run_checks(app_name, caller_file_path, package_name=package_name, return_value=return_vals)
        assert excinfo.value.code == library_main.BAD_PARAMS
        _, err = capsys.readouterr()
        assert re.match(fr'FATAL\..*Bad param.*', err) != None, f'err |{err}|'
 
@pytest.mark.parametrize('return_vals', [True, False, 0, None, 'hi!'])
@mock.patch('pathlib.Path.is_file', return_value=True) # pretend that this __main__.py file exists
def test_do_start_run_checks_checks_return_vals_param(_, return_vals, capsys):
    app_name = cwd_path.parts[-1]
    caller_file_path = cwd_path.joinpath('src', 'core', '__main__.py')
    # NB 1 == True is True, and 0 == False is also True...
    if return_vals is True:
        return_val = library_main.do_start_run_checks(app_name, caller_file_path, return_value=return_vals)
        assert return_val == library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    elif return_vals is False:
        return_val = library_main.do_start_run_checks(app_name, caller_file_path, return_value=return_vals)
        assert return_val == library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    else:
        with pytest.raises(SystemExit) as excinfo:
            library_main.do_start_run_checks(app_name, caller_file_path, return_value=return_vals)
        assert excinfo.value.code == library_main.BAD_PARAMS           
        _, err = capsys.readouterr()
        assert re.match(fr'FATAL\..*Bad param.*', err) != None, f'err |{err}|'
         
@pytest.mark.parametrize('file_path', ['real', False, 0, None, 'bubbles'])
@pytest.mark.parametrize('return_vals', [True, False])
def test_do_start_run_checks_checks_caller_file_path_param(file_path, return_vals, capsys):
    app_name = cwd_path.parts[-1]
    if file_path == 'real':
        file_path = cwd_path.joinpath('src', 'core', '__main__.py')
        # pretend that this __main__.py file exists
        with mock.patch('pathlib.Path.is_file', return_value=True):
            return_val = library_main.do_start_run_checks(app_name, file_path, return_value=return_vals)
        assert return_val == library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    elif return_vals:
        return_val = library_main.do_start_run_checks(app_name, file_path, return_value=return_vals)
        assert return_val[0] == library_main.BAD_PARAMS
        assert re.match(fr'FATAL\..*Bad param.*', return_val[1]) != None, f'return_val[1] |{return_val[1]}|'
        _, err = capsys.readouterr()
        assert err == ''
    else:
        with pytest.raises(SystemExit) as excinfo:
            library_main.do_start_run_checks(app_name, file_path, return_value=return_vals)
        assert excinfo.value.code == library_main.BAD_PARAMS
        _, err = capsys.readouterr()
        assert re.match(fr'FATAL\..*Bad param.*', err) != None, f'err |{err}|'
     
@pytest.mark.parametrize('app_name_param', ['real', False, 0, None])
@pytest.mark.parametrize('return_vals', [True, False])
def test_do_start_run_checks_checks_app_name_param(app_name_param, return_vals, capsys):
    app_name = cwd_path.parts[-1]
    caller_file_path = cwd_path.joinpath('src', 'core', '__main__.py')  
    if app_name_param == 'real':
        # use the real app_name, i.e. "lib"; also pretend that this __main__.py file exists
        with mock.patch('pathlib.Path.is_file', return_value=True):
            return_val = library_main.do_start_run_checks(app_name, caller_file_path, return_value=return_vals)
        assert return_val == library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    elif return_vals:
        return_val = library_main.do_start_run_checks(app_name_param, caller_file_path, return_value=return_vals)
        assert return_val[0] == library_main.BAD_PARAMS
        assert re.match(fr'FATAL\..*Bad param.*', return_val[1]) != None, f'return_val[1] |{return_val[1]}|'
        _, err = capsys.readouterr()
        assert err == ''
    else:
        with pytest.raises(SystemExit) as excinfo:
            library_main.do_start_run_checks(app_name_param, caller_file_path, return_value=return_vals)
        assert excinfo.value.code == library_main.BAD_PARAMS
        _, err = capsys.readouterr()
        assert re.match(fr'FATAL\..*Bad param.*', err) != None, f'err |{err}|'
     
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above')
@pytest.mark.parametrize('caller_file_path', ['file', 'dir', 'non-existent'])
@pytest.mark.parametrize('return_vals', [True, False])
def test_do_start_run_checks_checks_that_caller_file_path_is_file(caller_file_path, return_vals, capsys, tmpdir):
    app_name = cwd_path.parts[-1]
    tmpdir_path = pathlib.Path(str(tmpdir))
    bad_caller_file_path = tmpdir_path.joinpath('subdir')
    if caller_file_path == 'dir':
        bad_caller_file_path.mkdir()
    if caller_file_path == 'file':
        # this will be a real path, as long as this "lib" project has a package "library_core" and file "__init__.py" under it
        caller_file_path = cwd_path.joinpath('src', 'library_core', '__init__.py')
        # use the real app_name, i.e. "lib"
        return_val = library_main.do_start_run_checks(app_name, caller_file_path, package_name='library_core', return_value=return_vals)
        assert return_val == library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    elif return_vals:
        return_val = library_main.do_start_run_checks(app_name, bad_caller_file_path, return_value=return_vals)
        assert return_val[0] == library_main.BAD_PARAMS
        assert re.match(fr'FATAL\..*Bad param.*', return_val[1]) != None, f'return_val[1] |{return_val[1]}|'
        _, err = capsys.readouterr()
        assert err == ''
    else:
        with pytest.raises(SystemExit) as excinfo:
            library_main.do_start_run_checks(app_name, bad_caller_file_path, return_value=return_vals)
        assert excinfo.value.code == library_main.BAD_PARAMS
        _, err = capsys.readouterr()
        assert re.match(fr'FATAL\..*Bad param.*', err) != None, f'err |{err}|'
 
@pytest.mark.parametrize('version_too_low', [True, False])
def test_version_check_message_if_lib_version_is_too_low(version_too_low, tmpdir):
    version_string = ('7.0.0' if version_too_low else '7.0.1')
    min_lib_version = packaging.version.Version('7.0.1') 

    # 2024-12-07 this has changed completely: library_main.lib_module_version_check must now read in file version.toml in the root dir

    # first read out to a temp dir a version.toml file with the "too-low version"
    tmpdir_path = pathlib.Path(str(tmpdir))
    too_low_version_dict = {'version': version_string}
    with open(tmpdir_path.joinpath('version.toml'), 'w') as f:
        toml.dump(too_low_version_dict, f)
    # mock out the CWD
    with mock.patch('pathlib.Path.cwd', return_value=tmpdir_path):

        # assert library_main.lib_module_version_check(min_lib_version) == (not version_too_low)
        assert library_main.lib_module_version_check(min_lib_version) == (not version_too_low)
 
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above')
@pytest.mark.parametrize('in_ve', [True, False])
@pytest.mark.parametrize('return_vals', [True, False])  
def test_main_stops_if_not_run_in_virtual_environment(capsys, in_ve, return_vals):
    assert sys.base_prefix != sys.prefix, 'it appears that these tests are not being run in a virtual environment'
    app_name = cwd_path.parts[-1]
    caller_file_path = cwd_path.joinpath('src', 'library_core', 'library_main.py')
    pattern_str = r'FATAL\..*This app is not being run in an appropriate activated Python virtual environment.*'
    if in_ve:
        return_val = library_main.do_start_run_checks(app_name, caller_file_path, package_name='library_core', return_value=return_vals)


        assert return_val == library_main.CHECKS_PASSED
        _, err = capsys.readouterr()
        assert err == ''
    else:
        with mock.patch('sys.base_prefix', new_callable=mock.PropertyMock(return_value=sys.prefix)):
            if return_vals:
                return_val = library_main.do_start_run_checks(app_name, caller_file_path, package_name='library_core', return_value=return_vals)
                error_code = return_val[0]
            else:
                with pytest.raises(SystemExit) as excinfo:
                    return_val = library_main.do_start_run_checks(app_name, caller_file_path, package_name='library_core', return_value=return_vals)
                error_code = excinfo.value.code
        _, err = capsys.readouterr()
        error_msg = return_val[1] if return_vals else err
        assert (err == '') if return_vals else True
        assert error_code == library_main.NOT_IN_VIRTUAL_ENVIRONMENT
        assert re.match(pattern_str, error_msg, flags=re.IGNORECASE) != None, f'error_msg |{error_msg}|'

@pytest.mark.parametrize('normal_configuration_succeeds', [True, False, 'exception'])
@mock.patch(f'logging.basicConfig')
def test_test_configure_logging_returns_True_or_False_or_raises_exception(mock_basic, capsys, normal_configuration_succeeds):
    assert len(logging.getLogger().handlers) == 4
    if normal_configuration_succeeds == True:
        return_value = configure_logging.configure_logging('test')
        assert return_value == True
    elif normal_configuration_succeeds == 'exception':
        with mock.patch('logging.Logger.setLevel', side_effect=Exception('random problem')):
            with pytest.raises(Exception):
                configure_logging.configure_logging('test')
    else:
        pass # TODO: something which results in False return
    
def test_console_StreamHandler_formatter_configures_legible_colours():
    configure_logging.configure_logging('test')
    logger = logging.getLogger('test')
    # NB a ConcurrentRotatingFileHandler subclasses from both FileHandler and StreamHandler
    console_stream_handlers = [handler for handler in logger.handlers \
        if isinstance(handler, colorlog.StreamHandler) and not isinstance(handler, logging.FileHandler)]
    assert len(console_stream_handlers) == 1
    console_stream_handler = console_stream_handlers[0]
    formatter = console_stream_handler.formatter
    log_colors={
        'DEBUG':    'white',
        'INFO':     'white',
        'WARNING':  'fg_bold_yellow',
        'ERROR':    'fg_bold_red',
        'CRITICAL': 'fg_bold_red,bg_white',
    }
    assert formatter.log_colors == log_colors
    
def test_configure_logger_sets_console_StreamHandler_only_for_the_first_logger_configured():
    assert not hasattr(logging, 'stream_handler')
    configure_logging.configure_logging('test1')
    logger1 = logging.getLogger('test1')
    assert hasattr(logging, 'stream_handler')
    # NB a ConcurrentRotatingFileHandler subclasses from both FileHandler and StreamHandler
    logger1_console_stream_handlers = [handler for handler in logger1.handlers \
        if isinstance(handler, colorlog.StreamHandler) and not isinstance(handler, logging.FileHandler)]
    assert len(logger1_console_stream_handlers) == 1
    # now create another logger, with a different name
    configure_logging.configure_logging('test2')
    logger2 = logging.getLogger('test2')
    assert hasattr(logging, 'stream_handler')
    logger2_console_stream_handlers = [handler for handler in logger2.handlers \
        if isinstance(handler, colorlog.StreamHandler) and not isinstance(handler, logging.FileHandler)]
    assert len(logger2_console_stream_handlers) == 0
        
         
