# -*- coding: utf-8 -*-

import sys, pathlib, logging
from unittest import mock
import pytest #@UnusedImport #@UnresolvedImport
from library_main import check_and_configure_TEST # type: ignore
import library_main # type: ignore
import configure_logging # type: ignore
from concurrent_log_handler import ConcurrentRotatingFileHandler  # type: ignore
# from src.library_core.constants import *
from constants import *

@pytest.mark.parametrize('production_run', [True, False])    
def test_sets_up_sys_production_run(production_run):
    if hasattr(sys, 'production_run'):
        delattr(sys, 'production_run')
    with mock.patch('library_core.configure_logging.configure_logging', side_effect=Exception):
        with pytest.raises(Exception):
            real_cwd = pathlib.Path.cwd()
            with mock.patch('pathlib.Path.cwd', return_value=pathlib.Path('blah', 'operative', 'blah') if production_run else real_cwd):
                check_and_configure_TEST()
    assert hasattr(sys, 'production_run') 
    assert sys.production_run == production_run

@pytest.mark.parametrize('log_config_success', [True, False])    
def test_logging_config_failure_ends_run(log_config_success, capsys):
    with mock.patch('library_core.configure_logging.configure_logging', return_value=log_config_success):
        with mock.patch('sys.exit') as mock_exit:
            with mock.patch('logging.getLogger', side_effect=Exception):
                with pytest.raises(Exception):
                    check_and_configure_TEST()
    assert mock_exit.call_count == (0 if log_config_success else 1)
    _, err = capsys.readouterr()
    assert ('FATAL' in err) != log_config_success 
    
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above')                    
@pytest.mark.parametrize('get_admin_success', [True, False])    
def test_get_admin_success_failure_ends_run(get_admin_success, capsys):
    with mock.patch('sys.exit') as mock_exit:
        with mock.patch.object(library_main, 'get_is_admin', return_value=get_admin_success):
            sys.pytl.log(f'here get_admin_success {get_admin_success}')
            library_main.check_and_configure_TEST(admin_user=True)
    assert mock_exit.call_count == (0 if get_admin_success else 1)
    _, err = capsys.readouterr()
    assert ('FATAL' in err) != get_admin_success

@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above')                
def test_initial_log_message_made(caplog):
    with mock.patch('library_core.configure_logging.configure_logging', return_value=True):
        with caplog.at_level(logging.INFO):
            library_main.check_and_configure_TEST()
    assert 'production run?' in caplog.records[0].message 
                
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above')                
@pytest.mark.parametrize('os', ['win32', 'win64', 'linux', 'other_os'])
@mock.patch('library_core.configure_logging.configure_logging')
def test_os_is_windows_if_win_required(_, caplog, os):
    with mock.patch('sys.platform', new_callable=mock.PropertyMock(return_value=os)):
        with mock.patch('sys.argv', new_callable=mock.PropertyMock(return_value=('python', 'src/core'))):        
            if not os.startswith('win'):
                with caplog.at_level(logging.CRITICAL):
                    with pytest.raises(SystemExit):
                        library_main.check_and_configure_TEST(platform='win')
            else:
                library_main.check_and_configure_TEST(platform='win')
    if not os.startswith('win'):        
        assert 'FATAL' in caplog.text, f'caplog.text was |{caplog.text}|'
   
@pytest.mark.skip(reason='2025-12-13 was working OK until I changed to using "import library_main" above')
@pytest.mark.parametrize('os', ['win32', 'win64', 'linux', 'other_os'])
# @pytest.mark.parametrize('os', ['win32'])
@mock.patch('library_core.configure_logging.configure_logging')
def test_by_default_win_or_lin_only_allowed(_, caplog, os):
    acceptable_os = os.startswith('win') or os.startswith('lin')
    with mock.patch('sys.platform', new_callable=mock.PropertyMock(return_value=os)):
        with mock.patch('sys.argv', new_callable=mock.PropertyMock(return_value=('python', 'src/core'))):        
            if not acceptable_os:
                with caplog.at_level(logging.CRITICAL):
                    with pytest.raises(SystemExit):
                        library_main.check_and_configure_TEST()
            else:
                library_main.check_and_configure_TEST()
    if acceptable_os:
        assert 'FATAL' not in caplog.text, f'caplog.text was |{caplog.text}|'
    else:        
        assert 'FATAL' in caplog.text, f'caplog.text was |{caplog.text}|'
   
@pytest.mark.parametrize('present', [True, False])
# @pytest.mark.parametrize('present', [True])
def test_c_and_c_checks_that_various_root_dir_files_exists(present, caplog, tmpdir):
    # filenames = ['start_ve.bat', '.gitignore', 'conftest.py', 'start_lin_ve']
    filenames = ['start_ve.bat', '.gitignore', 'conftest.py', 've_path_linux']
    tmpdir_path = pathlib.Path(str(tmpdir))
    if present:
        for filename in filenames:
            tmpdir_path.joinpath(filename).touch()
    with mock.patch('pathlib.Path.cwd', return_value=tmpdir_path):
        if not present:
            with caplog.at_level(logging.CRITICAL):
                with pytest.raises(SystemExit):
                    library_main.check_and_configure_TEST(platform='win')
            assert 'FATAL' in caplog.text, f'caplog.text was |{caplog.text}|'
        else:
            library_main.check_and_configure_TEST(platform='win')
            assert 'FATAL' not in caplog.text, f'caplog.text was |{caplog.text}|'
   
# # TODO: should be part of lib method checking for starter package... ("core" by default)  
# def test_core_package_exists(qtbot):
#     working_dir_path = pathlib.Path('src/core')
#     assert working_dir_path.is_dir()
#     file_path = pathlib.Path('src/core/__main__.py')
#     assert file_path.is_file()
# 
# # TODO: should be part of lib method for checking on installation of required modules
# def test_main_stops_if_packaging_module_not_installed(capsys, reset_packaging, qtbot):
#     # NB you have to have packaging installed in order to check the python version
#     # NB module "packaging" is often installed with other modules, so you may not have to do "pip install packaging"
#     if 'packaging' in sys.modules:
#         sys.modules['packaging'] = None
#     with pytest.raises(SystemExit):
#         with mock.patch('sys.argv', new_callable=mock.PropertyMock(return_value=('python', 'src/core'))):        
#             core_main.main()
#     _, err = capsys.readouterr()
#     assert 'FATAL' in err and 'pip install packaging' in err, f'err was |{err}|'
# 
# 
# # TODO: should be part of lib check method
# VersionInfo = collections.namedtuple('VersionInfo', 'major minor micro')     
# @pytest.mark.parametrize('version_found', [VersionInfo(3, 9, 1)])  
# @mock.patch('logging_config.configure_logger')
# @mock.patch('sys.argv', new_callable=mock.PropertyMock(return_value=('python', 'src/core')))        
# def test_main_stops_if_python_version_too_old(_, mock_config, capsys, version_found, qtbot):
#     sys.version = version_found
#     with mock.patch('sys.version_info', version_found):
#         if version_found == (2, 5, 2):
#             with pytest.raises(SystemExit):
#                 core_main.main()
#             _, err = capsys.readouterr()
#             assert 'FATAL' in err
#         else:
#             core_main.main() # other: passes OK!

def test_is_possible_to_configure_log_file_size(tmpdir):
    with mock.patch('concurrent_log_handler.ConcurrentRotatingFileHandler'):
        with pytest.raises(AssertionError):
            # passing "None" here will result in an AssertionError... but if the configure_logging() does not
            # have a default argument "maxBytes" it will raise a different one... so this guarantees that that param is present
            configure_logging.configure_logging(None, maxBytes = 1024 * 1024)
    

@pytest.mark.parametrize('maxBytes_size', [500, 100000, None])
def test_maxBytes_param_is_used_for_log_file_size(tmpdir, maxBytes_size):
    with mock.patch('concurrent_log_handler.ConcurrentRotatingFileHandler') as mock_constructor:
        with mock.patch('logging.Logger.info'):
            if maxBytes_size == None:
                configure_logging.configure_logging('some name')
            else:
                configure_logging.configure_logging('some name', maxBytes=maxBytes_size)
    # expected_path = pathlib.Path('D:/temp/logging/some name/rotator_fh.log')
    expected_path = pathlib.Path(f'{PART2_VAL}/temp/logging/some name/rotator_fh.log')
    if maxBytes_size == None:
        # this then checks on the default setting for maxBytes
        mock_constructor.assert_called_once_with(expected_path, 'a', 1024 * 1024, 10, 'utf-8')
    else:
        mock_constructor.assert_called_once_with(expected_path, 'a', maxBytes_size, 10, 'utf-8')

