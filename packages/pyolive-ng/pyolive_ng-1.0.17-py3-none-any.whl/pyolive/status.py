from enum import Enum

class AppStatus(Enum):
    OK = 0
    ERROR = -1
    FIN = 1

class JobStatus(Enum):
    """Status code for job lifecycle"""
    CREATED = 1      # 작업생성
    STARTED = 2      # 작업시작
    RUNNING = 3      # 작업수행중
    ENDED = 4        # 작업종료(정상)
    FINISHED = 5     # 액션트리 종료
    ABORTED = 6      # 작업강제중단
    FAILED = 7       # 작업오류
    RETRY = 8        # 작업오류 재처리