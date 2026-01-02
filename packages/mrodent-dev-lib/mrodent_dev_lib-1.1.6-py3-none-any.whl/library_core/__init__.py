# -*- coding: utf-8 -*-
"""This is the core module of project doc_indexer: blah blah blah"""

import pathlib, sys, traceback
frame_list = traceback.extract_stack()
if len(frame_list) > 2:
    path_parts = pathlib.Path(frame_list[2].filename).parts
    sys_platform = sys.platform
    if sys_platform.startswith('win'):
        if len(path_parts) > 2 and path_parts[-3:-1] == ('Scripts', 'pytest.exe'):
            sys.testing_context = True
            sys.path.insert(0, str(pathlib.Path(__file__).parent))
    elif sys_platform.startswith('lin'):
        if len(path_parts) > 2 and path_parts[-3:-1] == ('_pytest', 'config'):
            sys.testing_context = True
            sys.path.insert(0, str(pathlib.Path(__file__).parent))
    else:
        raise Exception(f'OS: |{sys_platform}|!!!')
else:
    raise Exception('Frame list has fewer than 3 frames!!!')
