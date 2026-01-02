# -*- coding: utf-8 -*-

import logging.handlers
import sys, logging, pathlib, subprocess, traceback

import colorlog # type: ignore #@UnusedImport @UnresolvedImport
from concurrent_log_handler import ConcurrentRotatingFileHandler  # type: ignore
import concurrent_log_handler # type: ignore

from constants import *

STANDARD_LOGGING_LOCATION = pathlib.Path(f'{PART2_VAL}/{"ephem" if IS_PRODUCTION else "temp"}/logging')

def configure_logging(logger_name, caller_process='', use_colorlog=True, maxBytes = 1024 * 1024):
    assert type(logger_name) == str, f'|{logger_name}|: type is {type(logger_name)}'
    
    # you are not going to want to have multiple stream handlers... make a suitable mechanism
    # NB this mechanism means that the FIRST call to configure_logging will have the StreamHandler
    if not hasattr(logging, 'stream_handler'):
        if use_colorlog:
            stream_handler = colorlog.StreamHandler()
            # TODO the format pattern should include an indication about whether this is a production run or dev run...
            stream_handler.setFormatter(EnhancedColourFormatter(
                fmt='%(log_color)s%(asctime)s %(levelname)s %(module)s [%(pathname)s %(lineno)d]:\n%(message)s\n', 
                log_colors={
                    'DEBUG':    'white',
                    'INFO':     'white',
                    'WARNING':  'fg_bold_yellow',
                    'ERROR':    'fg_bold_red',
                    'CRITICAL': 'fg_bold_red,bg_white',
                }
                ))
            logger = colorlog.getLogger(logger_name)
        else: 
            stream_handler = logging.StreamHandler(sys.stdout) # make it go to stdout
            stream_handler.setFormatter(EnhancedStdFormatter(
                fmt='%(asctime)s %(levelname)s %(module)s [%(pathname)s %(lineno)d]:\n%(message)s\n'))
            logger = logging.getLogger(logger_name)
        logger.addHandler(stream_handler)
        logging.stream_handler = True
    else:
        logger = colorlog.getLogger(logger_name) # has no StreamHandler
        """
    2023-06-18
    See my answer here: https://stackoverflow.com/questions/2266646/how-to-disable-logging-on-the-standard-error-stream/76499737#76499737
    To prevent "spurious" console output there are 3 possibilities: substitute logging.lastResort, set the parent of a logger
    to None, or give the root logger a handler which does not output to console.
        """
        
    # configure and add file-handler    
    generic_log_dir_path = pathlib.Path(STANDARD_LOGGING_LOCATION)
    """
2023-06-18
The logging framework *automatically* decides that a logger of name "xx.yy" is a child logger of a logger of name "xx".
Thus the 'parent' property of the former will be not the root logger, but logger "xx".

It is a good idea if the directory structure of the log files reflect this hierarchy.
if the name contains dots, this indicates a sequence of directories
e.g. "doc_indexer.user_logger" --> logging should be to directory ".../doc_indexer/user_logger/"
    """
    if '.' in logger_name:
        dirs = logger_name.split('.')
        specific_log_dir_path = generic_log_dir_path.joinpath(*dirs)
    else:
        specific_log_dir_path = generic_log_dir_path.joinpath(logger_name)
    log_file_path = specific_log_dir_path.joinpath(EnhancedStdFormatter.LOG_FILENAME)
    if not log_file_path.parent.is_dir():
        try:
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
        except BaseException as e:
            msg = f"""{caller_process}WARNING: failed to create logging directory, |{log_file_path}|. 
No file-based logging will take place. Exception was |{e}| type {type(e)}"""
            raise Exception(msg)
            return
    file_handler = concurrent_log_handler.ConcurrentRotatingFileHandler(log_file_path, 'a', maxBytes, 10, 'utf-8')
    logger.addHandler(file_handler)
    file_formatter = EnhancedStdFormatter('%(asctime)s - [%(name)s] - %(levelname)s %(module)s [%(pathname)s %(lineno)d]:\n%(message)s')
    file_handler.setFormatter(file_formatter)
    logger.setLevel(logging.INFO)
    # message showing where the user can find the logger files (this message is also output to stdout)
    logger.info(f'{caller_process}Logger created, name |{logger.name}|. File handler log path: {log_file_path}')
    
    return True

    """
2022-08-01
NB it is important to understand that these two logging handlers do not operate independently!
In fact they must be added in this order: 1) stream handler, then 2) file handler... and for example, in the
formatMessage method of the formatter of the first, it can be seen that record.pathname is set to a tweaked version 
of the path string... but this SAME record is then passed to the second handler, with this formatter: so the path 
has already been set to the "tweaked" version.
Also, the time format for the file handler's formatter must be "%(asctime)s", not "%(asctime)s.%(msecs)03d", as the 
format has already been set up for this record. Doing the above actually adds the ms string again. However, in this
second formatter you DO have to stipulate that a decimal point, not a comma, should be used for the ms part!     
    """
        
class EnhancedColourFormatter(colorlog.ColoredFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print milliseconds after decimal point:
        self.default_msec_format = '%s.%03d'
    
    def formatMessage(self, record: logging.LogRecord):
        # tweak: curtail the pathname to show only the path elements from the CWD
        record_path = pathlib.Path(record.pathname)
        cwd_path = pathlib.Path.cwd()
        if record_path.is_relative_to(cwd_path):
            record.pathname = record_path.relative_to(cwd_path)
        # also search for logging being under "lib"
        # TODO do this properly TDD
        lib_dir_path = pathlib.Path(__file__).parent.parent.parent.parent
        if record_path.is_relative_to(lib_dir_path):
            record.pathname = record_path.relative_to(lib_dir_path)
        return super().formatMessage(record)
    
    def formatStack(self, stack_info):
        # 2025-01-22 added to remove the most egregious superfluous stack trace lines
        stack_info_lines = stack_info.splitlines()
        output_lines = []
        also_omit_next = False
        for stack_info_line in stack_info_lines:
            if also_omit_next:
                also_omit_next = False
                continue
            if stack_info_line.endswith('gui_checker_inner_function') or stack_info_line.endswith('executing_func'):
                also_omit_next = True
                continue
            output_lines.append(stack_info_line)
        return super().formatStack('\n'.join(output_lines).strip())


class EnhancedStdFormatter(colorlog.ColoredFormatter):
    LOG_FILENAME = 'rotator_fh.log'
    _LINE_OF_EQUALS = 120 * '='

    """
2022-08-01
NB it is important to understand that these two logging handlers do not operate independently!
In fact they must be added in this order: 1) stream handler, then 2) file handler... and for example, in the
formatMessage method of the formatter of the first, it can be seen that record.pathname is set to a tweaked version 
of the path string... but this SAME record is then passed to the second handler, with this formatter: so the path 
has already been set to the "tweaked" version.
Also, the time format for the file handler's formatter must be "%(asctime)s", not "%(asctime)s.%(msecs)03d", as the 
format has already been set up for this record. Doing the above actually adds the ms string again. However, in this
second formatter you DO have to stipulate that a decimal point, not a comma, should be used for the ms part!     
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print milliseconds after decimal point:
        self.default_msec_format = '%s.%03d'

    def formatMessage(self, record: logging.LogRecord):
        
        # TODO code duplication, see above (added 2023-06-19)
        record_path = pathlib.Path(record.pathname)
        cwd_path = pathlib.Path.cwd()
        if record_path.is_relative_to(cwd_path):
            record.pathname = record_path.relative_to(cwd_path)
        # also search for logging being under "lib"
        # TODO do this properly TDD
        lib_dir_path = pathlib.Path(__file__).parent.parent.parent.parent
        if record_path.is_relative_to(lib_dir_path):
            record.pathname = record_path.relative_to(lib_dir_path)
        # super().formatMessage(record)
        # add lines above and below, and introduce newlines wherever "\\n" found in default output
        one_line_output = self._style.format(record)
        output = one_line_output.replace(r"\n", "\n") # substitute real newlines for newline escape sequences
        return f'{EnhancedStdFormatter._LINE_OF_EQUALS}\n{output}\n{EnhancedStdFormatter._LINE_OF_EQUALS}'
    
    def formatStack(self, stack_info):
        # 2025-01-22 added to remove the most egregious superfluous stack trace lines
        stack_info_lines = stack_info.splitlines()
        output_lines = []
        also_omit_next = False
        for stack_info_line in stack_info_lines:
            if also_omit_next:
                also_omit_next = False
                continue
            if stack_info_line.endswith('gui_checker_inner_function') or stack_info_line.endswith('executing_func'):
                also_omit_next = True
                continue
            output_lines.append(stack_info_line)
        return super().formatStack('\n'.join(output_lines).strip())

