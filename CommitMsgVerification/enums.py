from enum import Enum

class CommitMessage(str, Enum):
    FIX = 1
    FEAT = 2
    MAJOR = 3
    
    @staticmethod
    def get_max_by_value(enum1, enum2):
        return enum1 if enum1.value > enum2.value else enum2

# enum1 = CommitMessage.FIX
# enum2 = CommitMessage.FEAT
# print(CommitMessage.get_max_by_value(enum1, enum2).name)