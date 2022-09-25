import sys
sys.path.insert(0,"..")

from commit_m_ver.CommitMsgVerification.enums import *
from commit_m_ver.CommitMsgVerification.commit_m_ver import *

import pytest

def test_initialisation():
    '''
    # no argument
    ver1 = CommitMessageVerification()
    assert ver1.project_directory == '.',"test failed"'''

    '''# argument isn't a directory
    ver2 = CommitMessageVerification('asdfghj')
    assert ver2.project_directory == '.',"test failed"'''

    # appropriate argument
    ver3 = CommitMessageVerification('..')
    assert ver3.project_directory == '..',"test failed"

def test_if_repository():
    ver = CommitMessageVerification('.')
    assert ver.set_repository() == "The path doesn't provide to git repository","test failed"



