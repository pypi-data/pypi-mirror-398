import base64
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union

@dataclass
class JobContext:
    regkey: str = ''
    topic: str = ''
    action_id: int = 0
    action_ns: str = ''
    action_app: str = 'ovm_hello_py'
    action_params: str = ''
    job_id: str = ''
    job_hostname: str = ''
    job_seq: int = 0
    timestamp: int = 0
    filenames: List[str] = field(default_factory=list)
    msgbox: Dict[str, Union[str, int]] = field(default_factory=dict)
    msglist: List[str] = field(default_factory=list)

    def __init__(self, message: Optional[Dict[str, Union[str, int, list, dict]]] = None, devel: bool = False):
        if not devel and message is not None:
            self.regkey = message['regkey']
            self.topic = message['topic']
            self.action_id = int(message['action_id'])
            self.action_ns = message['action_ns']
            self.action_app = message['action_app']
            self.action_params = message['action_params']
            self.job_id = message['job_id']
            self.job_hostname = message['job_hostname']
            self.job_seq = int(message['job_seq'])
            self.timestamp = int(message['timestamp'])
            self.filenames = message['filenames'][:]
            self.msgbox = message['msgbox']
            self.msglist = []
        else:
            self.regkey = ''
            self.topic = ''
            self.action_id = 0
            self.action_ns = ''
            self.action_app = 'ovm_pytest'
            self.action_params = ''
            self.job_id = ''
            self.job_hostname = ''
            self.job_seq = 0
            self.timestamp = 0
            self.filenames = []
            self.msgbox = {}
            self.msglist = []

    def get_param(self, key: str) -> Optional[str]:
        # Pattern: key='value' or key="value" or key=value
        pattern = re.compile(rf"{re.escape(key)}=(?:'([^']*)'|\"([^\"]*)\"|([^\s&]+))")
        match = pattern.search(self.action_params)
        if match:
            # Return the first non-None group among the matched ones
            return next(group for group in match.groups() if group is not None)
        return None

    def get_fileset(self) -> List[str]:
        return self.filenames

    def get_msgbox(self) -> Union[str, bytes, None]:
        """
        Restore original message from msgbox and return it.

        - If type is "ascii", return as string (str)
        - If type is "binary", base64 decode and return as bytes
        - Return None for invalid structure or failures
        """
        if not self.msgbox:
            return None

        try:
            msg_type = self.msgbox.get("type")
            data = self.msgbox.get("data")

            if msg_type == "ascii":
                return data

            elif msg_type == "binary":
                return base64.b64decode(data.encode('ascii'))

            else:
                # Note: self.logger is not available in this context, so we skip logging
                return None

        except Exception as e:
            # Note: self.logger is not available in this context, so we skip logging
            return None

    def set_param(self, param: Dict[str, Union[str, int]], devel: bool = False) -> None:
        if devel:
            self.action_params = '&'.join(f'{k}={v}' for k, v in param.items())

    def set_fileset(self, filename: str = "", devel: bool = False) -> None:
        if not filename.strip():
            self.filenames = []
            return

        if not devel:
            self.filenames.append(filename)
        else:
            self.filenames = filename.split(',')

    def set_msgbox(self, data: str = "") -> None:
        self.msglist.append(data)