import sys
sys.path.insert(0,"..")

from CommitMsgVerification.enums import *
from CommitMsgVerification.commit_m_ver import *

import pytest

def test_initialisation():
    # no argument
    ver1 = CommitMessageVerification()
    assert ver1.project_directory == '.',"test failed"

    '''# argument isn't a directory
    ver2 = CommitMessageVerification('-p', 'asdfghj')
    assert ver2.project_directory == '.',"test failed"'''

    # appropriate argument
    ver3 = CommitMessageVerification('-p', '..')
    assert ver3.project_directory == '..',"test failed"

def test_if_repository():
    ver1 = CommitMessageVerification('-p', '.')
    assert ver1.set_repository() == None,"test failed"

    ver2 = CommitMessageVerification('-p', '..')
    assert ver2.set_repository() == "The path doesn't provide to git repository","test failed"



