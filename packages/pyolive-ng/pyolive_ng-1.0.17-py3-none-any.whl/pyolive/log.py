import os
import sys
import socket
import queue
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Optional
from .config import Config


def get_log_level(level_str: str) -> int:
    if level_str == 'info':
        level = logging.INFO
    elif level_str == 'warn':
        level = logging.WARNING
    elif level_str == 'error':
        level = logging.ERROR
    else:
        level = logging.DEBUG
    return level


class AgentLog:
    def __init__(self, agent: str):
        self.agent: str = agent
        self.log_queue: queue.Queue = queue.Queue()
        self.listener: Optional[logging.handlers.QueueListener] = None
        self.logger: Optional[logging.Logger] = None
        self.home: Optional[str] = None  # _get_log_name()에서 Config.ATHENA_HOME 사용
        
        self._init_logger()

    def _init_logger(self) -> None:
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')

        config = Config('athena-agent.yaml')
        level: int = get_log_level(config.get_value('log/level'))
        count: int = self._get_log_count(config.get_value('log/rotate'))
        size: int = self._get_log_bytes(config.get_value('log/size'))
        name: str = self._get_log_name()

        file_handler = RotatingFileHandler(filename=name, maxBytes=size, backupCount=count)
        file_handler.setFormatter(formatter)

        self.listener = logging.handlers.QueueListener(self.log_queue, file_handler)
        self.listener.start()

        queue_handler = logging.handlers.QueueHandler(self.log_queue)

        self.logger = logging.getLogger(self.agent)
        self.logger.setLevel(level)
        self.logger.addHandler(queue_handler)
        self.logger.propagate = False

    def get_logger(self) -> logging.Logger:
        return self.logger

    def close(self) -> None:
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _get_log_count(self, rotate_str: str) -> int:
        return int(rotate_str)

    def _get_log_bytes(self, size_str: str) -> int:
        i = size_str.find('kb')
        if i > 0:
            return int(size_str[:i]) * 1024
        i = size_str.find('mb')
        if i > 0:
            return int(size_str[:i]) * 1024 * 1024
        i = size_str.find('gb')
        if i > 0:
            return int(size_str[:i]) * 1024 * 1024 * 1024
        return 0

    def _get_log_name(self) -> str:
        # 런타임에 환경변수 다시 읽기
        athena_home_env = os.getenv("ATHENA_HOME")
        athena_home = athena_home_env if athena_home_env else Config.ATHENA_HOME
        
        path = os.path.join(athena_home, 'logs', 'agent')
        os.makedirs(path, exist_ok=True)
        file = self.agent + '@' + socket.gethostname() + '.log'
        log_path = os.path.join(path, file)
        
        return log_path


class AppLog:
    def __init__(self, app: str, devel: bool = False):
        self.app: str = app
        self.devel: bool = devel
        self.home: Optional[str] = None  # _get_or_create_logger()에서 Config.ATHENA_HOME 사용
        
        self.logger: logging.Logger = self._get_or_create_logger()

    def _get_or_create_logger(self) -> logging.Logger:
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s #(%(thread)s) %(message)s')

        if not self.devel:
            logger = logging.getLogger(self.app)
            if not logger.handlers:
                config = Config('athena-app.yaml')
                level: int = get_log_level(config.get_value('log/level'))
                date_fmt: str = config.get_value('log/path').strip('{}')
                # 런타임에 환경변수 다시 읽기
                athena_home_env = os.getenv("ATHENA_HOME")
                athena_home = athena_home_env if athena_home_env else Config.ATHENA_HOME
                path: str = os.path.join(athena_home, 'logs', 'app')
                file: str = self.app + '@' + socket.gethostname() + '.log'

                file_handler = CustomTimedRotatingFileHandler(path, file, date_fmt)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                logger.setLevel(level)
                logger.propagate = False
        else:
            # devel=True일 때도 파일 로그 생성 (stdout과 함께)
            logger = logging.getLogger(self.app)
            logger.setLevel(logging.DEBUG)
            
            # 기존 핸들러가 있으면 제거 (중복 방지)
            if logger.handlers:
                logger.handlers.clear()
            
            # stdout 핸들러 추가
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(logging.DEBUG)  # 핸들러 레벨 명시적 설정
            stdout_handler.setFormatter(formatter)
            logger.addHandler(stdout_handler)
            
            # 파일 핸들러도 추가 (develop_mode에서도 로그 파일 생성)
            try:
                # 런타임에 환경변수 다시 읽기 (여러 방법 시도)
                athena_home_env = os.getenv("ATHENA_HOME")
                if not athena_home_env:
                    # 환경변수가 없으면 Config에서 가져오기
                    athena_home = Config.ATHENA_HOME
                else:
                    athena_home = athena_home_env
                
                # pywork 로그는 agent 디렉토리에, 그 외는 app 디렉토리에 생성
                if self.app == "pywork":
                    log_subdir = "agent"
                else:
                    log_subdir = "app"
                
                # 경로 검증 및 생성
                path: str = os.path.join(athena_home, 'logs', log_subdir)
                try:
                    os.makedirs(path, exist_ok=True)
                    # 디렉토리 쓰기 권한 확인
                    if not os.access(path, os.W_OK):
                        raise PermissionError(f"No write permission for log directory: {path}")
                except (OSError, PermissionError) as e:
                    # 디렉토리 생성 실패 시 현재 작업 디렉토리 사용
                    path = os.path.join(os.getcwd(), 'logs', log_subdir)
                    os.makedirs(path, exist_ok=True)
                
                file: str = self.app + '@' + socket.gethostname() + '.log'
                log_path = os.path.join(path, file)
                
                # 파일 핸들러 생성 및 설정
                file_handler = RotatingFileHandler(
                    filename=log_path,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=3
                )
                file_handler.setLevel(logging.DEBUG)  # 핸들러 레벨 명시적 설정
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                
                # 파일 핸들러가 제대로 추가되었는지 확인
                file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
                if not file_handlers:
                    raise RuntimeError(f"File handler was not added to logger: {logger.name}")
                
            except Exception as e:
                # 파일 로그 생성 실패 시 stderr에 경고 출력 (개발 모드에서만)
                print(f"Warning: Failed to create log file handler: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
            
            logger.propagate = False

        return logger

    def get_logger(self) -> logging.Logger:
        return self.logger
    
    def close(self) -> None:
        """로그 파일 핸들러를 명시적으로 flush하고 종료"""
        if self.logger:
            # 모든 파일 핸들러를 flush
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    try:
                        handler.flush()
                    except Exception:
                        pass


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        base_dir: str,
        filename: str,
        date_format: str,
        when: str = 'midnight',
        interval: int = 1,
        backupCount: int = 0
    ):
        self.base_dir: str = base_dir
        self.date_format: str = date_format
        self.filename: str = filename
        self.update_log_dir()
        log_filename: str = os.path.join(self.log_dir, filename)
        super().__init__(log_filename, when=when, interval=interval, backupCount=backupCount)

    def update_log_dir(self) -> None:
        current_time: str = datetime.now().strftime(self.date_format)
        self.log_dir: str = os.path.join(self.base_dir, current_time)
        os.makedirs(self.log_dir, exist_ok=True)

    def doRollover(self) -> None:
        self.update_log_dir()
        self.baseFilename = os.path.join(self.log_dir, self.filename)
        super().doRollover()