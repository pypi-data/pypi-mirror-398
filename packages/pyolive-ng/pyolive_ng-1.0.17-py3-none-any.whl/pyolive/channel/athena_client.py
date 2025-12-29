"""
Athena Broker 클라이언트 (async 버전)
MSM 프로토콜을 사용하여 Athena Broker와 통신
"""
import struct
import time
import uuid
import asyncio
import logging
import threading
from typing import Optional, Tuple
from pynng import Req0, Push0, Timeout
from pynng.exceptions import ConnectionRefused

# 모듈 로거
_logger = logging.getLogger(__name__)

# Opcodes (msm_protocol.h: msm_opcode_t)
MSG_OP_CONNECT = 0x01          # 클라이언트 연결
MSG_OP_CONNACK = 0x02          # 연결 승인 응답
MSG_OP_PUBLISH = 0x03          # 메시지 발행
MSG_OP_PUBACK = 0x04           # 발행 승인
MSG_OP_SUBSCRIBE = 0x05        # 토픽 구독
MSG_OP_SUBACK = 0x06           # 구독 승인
MSG_OP_UNSUBSCRIBE = 0x07      # 구독 해제
MSG_OP_UNSUBACK = 0x08         # 구독 해제 승인
MSG_OP_PUSH = 0x09             # 서버 → 컨슈머 푸시
MSG_OP_ACK = 0x0A              # 메시지 승인
MSG_OP_HEARTBEAT = 0x0B        # Heartbeat/Ping (keepalive)
MSG_OP_DISCONNECT = 0x0C       # 연결 종료
MSG_OP_TOUCH = 0x0D            # ACK 타임아웃 연장
MSG_OP_QUEUE_DECLARE = 0x10    # 큐 생성
MSG_OP_QUEUE_DECLARE_OK = 0x11 # 큐 생성 성공
MSG_OP_QUEUE_BIND = 0x12       # 큐를 라우팅 키에 바인드
MSG_OP_QUEUE_BIND_OK = 0x13    # 큐 바인드 성공
MSG_OP_QUEUE_UNBIND = 0x14     # 큐 언바인드
MSG_OP_QUEUE_UNBIND_OK = 0x15  # 큐 언바인드 성공
MSG_OP_QUEUE_DELETE = 0x16     # 큐 삭제
MSG_OP_QUEUE_DELETE_OK = 0x17  # 큐 삭제 성공
MSG_OP_QUEUE_PURGE = 0x18      # 큐 메시지 정리
MSG_OP_QUEUE_PURGE_OK = 0x19   # 큐 정리 성공
MSG_OP_CONSUME = 0x1A          # 큐에서 메시지 요청
MSG_OP_DELIVER = 0x1B          # 브로커 → 컨슈머 배달
MSG_OP_NACK = 0x1C             # 부정적 승인 (거부/재큐)
MSG_OP_CONSUME_EMPTY = 0x1D    # 라운드로빈: 현재 컨슈머 차례 아님
MSG_OP_CONSUME_START = 0x20    # 스트리밍 소비 시작
MSG_OP_CONSUME_START_OK = 0x21 # 스트리밍 소비 시작 성공
MSG_OP_CONSUME_STOP = 0x22     # 스트리밍 소비 중지
MSG_OP_CONSUME_STOP_OK = 0x23  # 스트리밍 소비 중지 성공
MSG_OP_ERROR = 0xFF            # 에러 응답

# Response codes
MSM_RESP_SUCCESS = 0x00
MSM_RESP_TIMEOUT = 0x0A  # Timeout

# Protocol version
MSM_PROTOCOL_VERSION = 0x01  # Protocol version 1

# Timeout constants (from include/mod/msm_defs.h)
MSM_TIMEOUT = 5  # 아답터 수신대기 시간(초)
MSM_POLL_INTERVAL_MS = 500  # 브로커 폴링 간격 (밀리초) - 500ms로 설정하여 부하 감소
MSM_HEARTBEAT_INTERVAL = 30  # 하트비트 전송 간격 (초) - 브로커 타임아웃(60초)의 절반

# Default exchange (msm_protocol.h: MSM_EXCHANGE_DEFAULT)
DEFAULT_EXCHANGE = "generic"


class AthenaException(Exception):
    """Athena 클라이언트 예외"""
    pass


class AthenaMessage:
    """수신된 메시지"""
    def __init__(self, delivery_tag: int, queue_name: str, exchange: str,
                 routing_key: str, message_id: int, payload: bytes):
        self.delivery_tag = delivery_tag
        self.queue_name = queue_name
        self.exchange = exchange
        self.routing_key = routing_key
        self.message_id = message_id
        self.payload = payload
        self._body = None

    def get_payload_str(self, encoding='utf-8') -> str:
        """페이로드를 문자열로 반환"""
        return self.payload.decode(encoding)

    @property
    def body(self) -> bytes:
        """페이로드"""
        return self.payload

    def __repr__(self):
        return (f"AthenaMessage(tag={self.delivery_tag}, queue={self.queue_name}, "
                f"exchange={self.exchange}, routing_key={self.routing_key}, id={self.message_id})")


class AthenaClient:
    """Athena Broker 클라이언트 (async 지원)"""

    def __init__(self, broker_url: str = "tcp://localhost:2736",
                 client_id: Optional[str] = None, timeout_ms: Optional[int] = None):
        """
        Args:
            broker_url: Broker URL (예: "tcp://localhost:2736")
            client_id: 클라이언트 ID (None이면 자동 생성)
            timeout_ms: 기본 타임아웃 (밀리초, None이면 MSM_TIMEOUT 사용)
        """
        self.broker_url = broker_url
        self.client_id = client_id or self._generate_client_id()
        self.timeout_ms = timeout_ms or (MSM_TIMEOUT * 1000)  # MSM_TIMEOUT 초를 밀리초로 변환
        self.socket: Optional[Req0] = None
        self.push_socket: Optional[Push0] = None  # PUSH 소켓 (publish 전용, 비동기)
        self.push_connected = False  # PUSH 소켓 연결 상태
        self.connected = False
        self._lock = threading.Lock()  # 소켓 동기화 (스레드 공유)
        self._push_lock = asyncio.Lock()  # PUSH 소켓 전용 lock
        # 하트비트/터치 관련 (별도 스레드에서 실행, 메인 소켓 공유)
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_stop_event = threading.Event()  # 스레드 중지 이벤트
        self._heartbeat_interval = MSM_HEARTBEAT_INTERVAL
        self._heartbeat_sequence = 0
        self._current_delivery_tag: Optional[int] = None  # 현재 처리 중인 메시지
        self._touch_lock = threading.Lock()  # delivery_tag 접근 동기화

    @staticmethod
    def _generate_client_id() -> str:
        """고유한 클라이언트 ID 생성"""
        timestamp = int(time.time() * 1000)
        unique_id = uuid.uuid4().hex[:8]
        return f"python_client_{timestamp}_{unique_id}"

    @staticmethod
    def _bytes_to_hex(data: bytes) -> str:
        """바이트 배열을 16진수 문자열로 변환 (디버깅용)"""
        return ' '.join(f'{b:02x}' for b in data)

    def _make_push_url(self, url: str) -> str:
        """
        Control URL에서 PUSH URL 생성 (port + 2)
        예: tcp://localhost:2736 -> tcp://localhost:2738
        """
        import re
        match = re.match(r'^(tcp://[^:]+):(\d+)$', url)
        if match:
            host_part = match.group(1)
            port = int(match.group(2))
            return f"{host_part}:{port + 2}"
        return url  # 파싱 실패 시 원본 반환

    async def connect(self, timeout_ms: Optional[int] = None):
        """Broker에 연결"""
        timeout = timeout_ms or self.timeout_ms
        self.socket = None
        self.push_socket = None

        try:
            # NNG REQ 소켓 생성 (Control 채널)
            self.socket = Req0(dial=self.broker_url, send_timeout=timeout, recv_timeout=timeout)

            # CONNECT 메시지 전송
            connect_msg = self._build_connect_message()
            await asyncio.to_thread(self.socket.send, connect_msg)

            # CONNACK 응답 수신
            # CONNACK은 고정 길이(2 bytes)이므로 이를 검증해야 함
            response = await asyncio.to_thread(self.socket.recv)

            if len(response) < 2 or response[0] != MSG_OP_CONNACK:
                raise AthenaException("Invalid CONNACK response")

            if response[1] != MSM_RESP_SUCCESS:
                raise AthenaException(f"Connection failed: response_code=0x{response[1]:02x}")

            # PUSH 소켓 생성 (Data 채널 - Publish 전용)
            # port + 2로 연결 (예: 2736 -> 2738)
            push_url = self._make_push_url(self.broker_url)
            try:
                self.push_socket = Push0(send_timeout=1000)  # PUSH는 짧은 timeout
                self.push_socket.dial(push_url, block=False)  # Non-blocking 연결
                self.push_connected = True
            except Exception:
                # PUSH 소켓 연결 실패 시 REQ/REP 폴백 모드로 동작
                if self.push_socket:
                    try:
                        self.push_socket.close()
                    except:
                        pass
                self.push_socket = None
                self.push_connected = False

            self.connected = True

            # 백그라운드 하트비트 시작 (브로커 연결 유지)
            await self.start_heartbeat()

        except Exception as e:
            self.connected = False
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            if self.push_socket:
                try:
                    self.push_socket.close()
                except:
                    pass
                self.push_socket = None

            # 에러 메시지 상세화
            error_msg = str(e)
            raise AthenaException(
                f"Failed to connect to Athena Broker at {self.broker_url}.\n"
                f"Error type: {type(e).__name__}\n"
                f"Error message: {error_msg}\n"
                f"\nPlease check:\n"
                f"  1. Athena Broker server is running and accessible\n"
                f"  2. Configuration file: $ATHENA_HOME/etc/athena-agent.yaml\n"
                f"  3. Broker URL: {self.broker_url}"
            )

    def _build_connect_message(self) -> bytes:
        """
        CONNECT 메시지 생성
        
        서버는 sizeof(msm_connect_msg_t) = 160 bytes를 기대합니다.
        총 크기: 161 bytes (opcode 1 + 구조체 160)
        """
        client_id_bytes = self.client_id.encode('utf-8')
        client_id_len = min(len(client_id_bytes), 127)  # 최대 128 bytes (null 포함)

        msg = struct.pack('>B', MSG_OP_CONNECT)              # opcode (1 byte)
        msg += struct.pack('>B', MSM_PROTOCOL_VERSION)       # protocol_version (1 byte, offset 0)
        msg += client_id_bytes[:client_id_len]                # client_id (128 bytes, offset 1)
        msg += b'\x00' * (128 - client_id_len)                # null padding
        msg += b'\x00' * 3                                    # padding (3 bytes, offset 129-131)
        msg += struct.pack('>I', 60)                         # keepalive (4 bytes, offset 132, 60s)
        msg += struct.pack('>H', 0)                          # flags (2 bytes, offset 136)
        msg += b'\x00' * 6                                    # padding (6 bytes, offset 138-143)
        msg += struct.pack('>Q', 0)                          # username pointer (8 bytes, offset 144)
        msg += struct.pack('>Q', 0)                          # password pointer (8 bytes, offset 152)

        return msg

    async def publish(self, topic: str, payload: bytes, exchange: Optional[str] = None):
        """
        메시지 발행

        PUSH 소켓이 사용 가능하면 비동기 fire & forget 방식으로 전송하고,
        그렇지 않으면 기존 REQ/REP 방식으로 폴백합니다.

        Args:
            topic: 토픽/라우팅 키
            payload: 메시지 내용 (bytes)
            exchange: Exchange 이름 (None이면 기본값 사용)
        """
        if not self.connected:
            raise AthenaException("Not connected to broker")

        effective_exchange = exchange or DEFAULT_EXCHANGE
        publish_msg = self._build_publish_message(effective_exchange, topic, payload)

        if self.push_connected and self.push_socket:
            # PUSH 소켓 사용 (비동기, 응답 대기 없음 - fire & forget)
            async with self._push_lock:
                try:
                    await asyncio.to_thread(self.push_socket.send, publish_msg)
                    return  # 성공 시 바로 리턴
                except Exception:
                    # PUSH 실패 시 연결 상태 해제하고 REQ/REP 폴백
                    self.push_connected = False

        # REQ/REP 폴백 (동기, PUBACK 응답 대기)
        await self._publish_via_req(publish_msg)

    async def _publish_via_req(self, publish_msg: bytes):
        """REQ/REP를 통한 publish (fallback)"""
        with self._lock:
            try:
                await asyncio.to_thread(self.socket.send, publish_msg)

                # PUBACK 수신 (타임아웃 설정)
                old_timeout = self.socket.recv_timeout
                try:
                    self.socket.recv_timeout = 5000  # 5초 타임아웃
                    response = await asyncio.to_thread(self.socket.recv)

                    if len(response) < 1:
                        raise AthenaException("Empty PUBACK response")

                    if response[0] != MSG_OP_PUBACK:
                        error_code = response[1] if len(response) >= 2 else 0xFF
                        raise AthenaException(f"Invalid PUBACK response: opcode=0x{response[0]:02x}, error=0x{error_code:02x}")
                except Timeout:
                    raise AthenaException("PUBACK timeout - broker did not respond")
                finally:
                    self.socket.recv_timeout = old_timeout

            except AthenaException:
                raise
            except Exception as e:
                raise AthenaException(f"Failed to publish via REQ/REP: {e}")

    async def publish_str(self, topic: str, message: str, encoding='utf-8', exchange: Optional[str] = None):
        """문자열 메시지 발행 (편의 메서드)"""
        await self.publish(topic, message.encode(encoding), exchange)

    def _build_publish_message(self, exchange: str, topic: str, payload: bytes) -> bytes:
        """
        PUBLISH 메시지 생성 (Protocol 3.3)

        Frame format:
        [opcode:1][client_id_len:1][client_id:N][exchange:string][routing_key:string][payload:bytes]
        """
        client_id_bytes = self.client_id.encode('utf-8')
        client_id_len = min(len(client_id_bytes), 127)  # 최대 127 bytes
        exchange_bytes = exchange.encode('utf-8')
        topic_bytes = topic.encode('utf-8')

        msg = struct.pack('>B', MSG_OP_PUBLISH)              # opcode (1 byte)
        msg += struct.pack('>B', client_id_len)              # client_id_len (1 byte)
        msg += client_id_bytes[:client_id_len]               # client_id (N bytes)
        msg += exchange_bytes                                # exchange
        msg += b'\x00'                                       # null terminator
        msg += topic_bytes                                   # topic (routing_key)
        msg += b'\x00'                                       # null terminator
        msg += payload                                       # payload

        return msg

    async def queue_declare(self, queue_name: Optional[str] = None, max_size: int = 10000,
                           ttl: int = 0, persistent: bool = False, exclusive: bool = False,
                           auto_delete: bool = False, prefix: str = "pywork") -> Tuple[str, int, int]:
        """
        큐 선언

        Args:
            queue_name: 큐 이름 (None이면 임시 큐 생성)
            max_size: 최대 메시지 개수
            ttl: 메시지 TTL (초, 0 = 무제한)
            persistent: 영속성 여부 (bit 0)
            exclusive: 독점 큐 여부 (bit 1)
            auto_delete: 자동 삭제 여부 (bit 2)
            prefix: 큐 접두사 (임시 큐 생성 시 사용, 기본값: "pywork")

        Returns:
            (queue_name, message_count, consumer_count) 튜플
        """
        if not self.connected:
            raise AthenaException("Not connected to broker")

        with self._lock:
            try:
                # flags 계산
                flags = 0
                if persistent: flags |= 0x01
                if exclusive: flags |= 0x02
                if auto_delete: flags |= 0x04

                # queue_name이 None이면 빈 문자열로 처리 (서버가 이름 생성)
                target_queue_name = queue_name or ""

                declare_msg = self._build_queue_declare_message(
                    target_queue_name, max_size, ttl, flags, prefix
                )
                await asyncio.to_thread(self.socket.send, declare_msg)

                # QUEUE_DECLARE_OK 수신
                # 구조: [opcode:1][queue_name:256][message_count:4][consumer_count:4]
                response = await asyncio.to_thread(self.socket.recv)

                if len(response) < 1 or response[0] != MSG_OP_QUEUE_DECLARE_OK:
                    raise AthenaException("Invalid QUEUE_DECLARE_OK response")
                
                if len(response) < 265:
                     raise AthenaException(f"QUEUE_DECLARE_OK response too short: {len(response)} bytes")

                # 응답 파싱
                offset = 1
                
                # queue_name (256 bytes)
                qname_bytes = response[offset:offset+256]
                null_index = qname_bytes.find(b'\x00')
                if null_index >= 0:
                    declared_queue_name = qname_bytes[:null_index].decode('utf-8')
                else:
                    declared_queue_name = qname_bytes.decode('utf-8')
                offset += 256
                
                # message_count (4 bytes)
                message_count = struct.unpack_from('>I', response, offset)[0]
                offset += 4
                
                # consumer_count (4 bytes)
                consumer_count = struct.unpack_from('>I', response, offset)[0]
                
                return declared_queue_name, message_count, consumer_count
            
            except Exception as e:
                raise AthenaException(f"Failed to declare queue: {e}")

    async def queue_bind(self, queue_name: str, exchange: str, routing_key: str):
        """
        큐 바인딩

        Args:
            queue_name: 큐 이름
            exchange: Exchange 이름
            routing_key: 라우팅 키
        """
        if not self.connected:
            raise AthenaException("Not connected to broker")

        with self._lock:
            try:
                bind_msg = self._build_queue_bind_message(queue_name, exchange, routing_key)
                await asyncio.to_thread(self.socket.send, bind_msg)

                # QUEUE_BIND_OK 수신 (0x13)
                # 구조: [opcode:1][result_code:1]
                response = await asyncio.to_thread(self.socket.recv)

                if len(response) < 2 or response[0] != MSG_OP_QUEUE_BIND_OK:
                    raise AthenaException(f"Invalid QUEUE_BIND_OK response: {self._bytes_to_hex(response)}")
                
                result_code = response[1]
                if result_code != MSM_RESP_SUCCESS:
                    raise AthenaException(f"Queue bind failed: result_code=0x{result_code:02x}")

            except Exception as e:
                raise AthenaException(f"Failed to bind queue: {e}")

    def _build_queue_bind_message(self, queue_name: str, exchange: str, routing_key: str) -> bytes:
        """
        QUEUE_BIND 메시지 생성
        구조 (protocol.h):
        typedef struct {
            char queue_name[256];
            char binding_key[256];  /* Topic pattern */
            char exchange[256];     /* Exchange name */
        } queue_bind_msg_t;
        
        총 크기: 768 bytes + Opcode(1) = 769 bytes
        """
        queue_bytes = queue_name.encode('utf-8')
        exchange_bytes = exchange.encode('utf-8')
        routing_key_bytes = routing_key.encode('utf-8')

        msg = struct.pack('>B', MSG_OP_QUEUE_BIND)           # opcode
        
        # 1. queue_name (256)
        q_len = min(len(queue_bytes), 255)
        msg += queue_bytes[:q_len]
        msg += b'\x00' * (256 - q_len)
        
        # 2. binding_key (routing_key) (256)
        r_len = min(len(routing_key_bytes), 255)
        msg += routing_key_bytes[:r_len]
        msg += b'\x00' * (256 - r_len)

        # 3. exchange (256)
        e_len = min(len(exchange_bytes), 255)
        msg += exchange_bytes[:e_len]
        msg += b'\x00' * (256 - e_len)
        
        return msg

    def _build_queue_declare_message(self, queue_name: str, max_size: int,
                                    ttl: int, flags: int, prefix: str) -> bytes:
        """
        QUEUE_DECLARE 메시지 생성
        
        구조체 정의 (include/mod/msm_protocol.h):
        typedef struct {
            char queue_name[256];
            uint8_t flags;
            // [패딩 3 bytes]
            uint32_t max_size;
            uint32_t ttl;
            char queue_prefix[64];
        } msm_queue_declare_msg_t;
        
        총 크기: 332 bytes + Opcode(1) = 333 bytes
        """
        queue_bytes = queue_name.encode('utf-8')
        queue_len = min(len(queue_bytes), 255)  # 최대 256 bytes (null 포함)
        
        prefix_bytes = prefix.encode('utf-8')
        prefix_len = min(len(prefix_bytes), 63) # 최대 64 bytes (null 포함)

        msg = struct.pack('>B', MSG_OP_QUEUE_DECLARE)        # opcode (1)
        msg += queue_bytes[:queue_len]                       # queue_name (256 bytes)
        msg += b'\x00' * (256 - queue_len)                    # null padding
        msg += struct.pack('>B', flags)                      # flags (1 byte)
        msg += b'\x00' * 3                                    # padding (3 bytes)
        msg += struct.pack('>I', max_size)                    # max_size (4 bytes, Big-Endian)
        msg += struct.pack('>I', ttl)                         # ttl (4 bytes, Big-Endian)
        msg += prefix_bytes[:prefix_len]                     # queue_prefix (64 bytes)
        msg += b'\x00' * (64 - prefix_len)                    # null padding

        return msg

    async def subscribe(self, topic_pattern: str, qos: int = 0) -> int:
        """
        토픽 구독

        Args:
            topic_pattern: 토픽 패턴 (와일드카드 지원: *, #)
            qos: QoS 레벨 (0, 1, 또는 2)

        Returns:
            구독 ID
        """
        if not self.connected:
            raise AthenaException("Not connected to broker")

        with self._lock:
            try:
                subscribe_msg = self._build_subscribe_message(topic_pattern, qos)
                await asyncio.to_thread(self.socket.send, subscribe_msg)

                # SUBACK 응답 수신
                response = await asyncio.to_thread(self.socket.recv)

                if len(response) < 10 or response[0] != MSG_OP_SUBACK:
                    raise AthenaException("Invalid SUBACK response")

                if response[1] != MSM_RESP_SUCCESS:
                    raise AthenaException(f"Subscribe failed: {response[1]}")

                # subscription_id 추출 (8 bytes, Big-Endian)
                subscription_id = struct.unpack_from('>Q', response, 2)[0]
                return subscription_id

            except Exception as e:
                raise AthenaException(f"Failed to subscribe: {e}")

    def _build_subscribe_message(self, topic_pattern: str, qos: int, queue_prefix: str = "") -> bytes:
        """
        SUBSCRIBE 메시지 생성

        구조체 정의 (protocol.h:101-107):
        typedef struct {
            uint32_t subscription_id;               // 4 bytes
            char topic_pattern[MAX_TOPIC_LENGTH];   // 256 bytes
            uint8_t qos;                            // 1 byte
            uint16_t flags;                         // 2 bytes
            char queue_prefix[64];                  // 64 bytes
        } subscribe_msg_t;

        구조체 크기: 327 bytes
        실제 전송 크기: opcode(1) + 구조체(327) = 328 bytes

        Note: Subscribe는 client_id 불필요 (서버가 세션의 client_id 사용)
        """
        pattern_bytes = topic_pattern.encode('utf-8')
        pattern_len = min(len(pattern_bytes), 255)  # 최대 256 bytes (null 포함)
        prefix_bytes = queue_prefix.encode('utf-8')
        prefix_len = min(len(prefix_bytes), 63)  # 최대 64 bytes (null 포함)

        msg = struct.pack('>B', MSG_OP_SUBSCRIBE)          # opcode
        msg += struct.pack('<I', 0)                        # subscription_id (4 bytes, LE)
        msg += pattern_bytes[:pattern_len]                 # topic_pattern (256 bytes)
        msg += b'\x00' * (256 - pattern_len)               # null padding
        msg += struct.pack('B', qos)                       # qos (1 byte)
        msg += struct.pack('<H', 0)                        # flags (2 bytes, LE)
        msg += prefix_bytes[:prefix_len]                   # queue_prefix (64 bytes)
        msg += b'\x00' * (64 - prefix_len)                 # null padding

        return msg

    async def consume(self, queue_name: str, timeout_ms: Optional[int] = None) -> Optional[AthenaMessage]:
        """
        큐에서 메시지 소비 (블로킹)
        서버 코드(msm_adapter.c)와 동일하게 MSM_TIMEOUT 사용

        Args:
            queue_name: 큐 이름
            timeout_ms: 타임아웃 (밀리초, None이면 MSM_TIMEOUT 사용)

        Returns:
            수신된 메시지 (타임아웃 시 None)
        """
        if not self.connected:
            raise AthenaException("Not connected to broker")

        # 전체 타임아웃: 기본값 MSM_TIMEOUT * 1000 (5초)
        total_timeout = timeout_ms or (MSM_TIMEOUT * 1000)
        # 폴링 간격: 100ms (lock을 짧게 잡아서 heartbeat 스레드가 끼어들 수 있게 함)
        poll_interval = MSM_POLL_INTERVAL_MS

        old_send_timeout = self.socket.send_timeout
        old_recv_timeout = self.socket.recv_timeout

        try:
            # 소켓 타임아웃을 폴링 간격에 맞게 설정
            self.socket.send_timeout = poll_interval + 500
            self.socket.recv_timeout = poll_interval + 500

            # 폴링 루프: 전체 타임아웃까지 짧은 간격으로 반복
            start_time = time.time()
            elapsed_ms = 0

            while elapsed_ms < total_timeout:
                remaining = total_timeout - elapsed_ms
                current_poll = min(poll_interval, remaining)

                with self._lock:
                    consume_msg = self._build_consume_message(queue_name, current_poll)
                    await asyncio.to_thread(self.socket.send, consume_msg)

                    try:
                        response = await asyncio.to_thread(self.socket.recv)
                    except Timeout:
                        # 이번 폴링은 타임아웃, 다음 폴링 시도
                        elapsed_ms = int((time.time() - start_time) * 1000)
                        continue

                    if len(response) < 1:
                        elapsed_ms = int((time.time() - start_time) * 1000)
                        continue

                    if response[0] == MSG_OP_DELIVER:
                        return self._parse_deliver_message(response)

                    # Round-Robin: not this consumer's turn - treat as no message
                    if response[0] == MSG_OP_CONSUME_EMPTY:
                        elapsed_ms = int((time.time() - start_time) * 1000)
                        continue

                    # 에러 응답 처리 (0xFF)
                    if response[0] == 0xFF and len(response) >= 2:
                        error_code = response[1]
                        if error_code == MSM_RESP_TIMEOUT:
                            # 타임아웃은 정상적인 "메시지 없음" 상태
                            elapsed_ms = int((time.time() - start_time) * 1000)
                            continue

                    elapsed_ms = int((time.time() - start_time) * 1000)

                # Lock 해제 후 잠시 대기 (이벤트 루프에 양보)
                await asyncio.sleep(0.001)
                elapsed_ms = int((time.time() - start_time) * 1000)

            return None

        except Timeout:
            return None
        except Exception as e:
            raise AthenaException(f"Failed to consume: {e}")
        finally:
            self.socket.send_timeout = old_send_timeout
            self.socket.recv_timeout = old_recv_timeout

    def _build_consume_message(self, queue_name: str, timeout_ms: int) -> bytes:
        """
        CONSUME 메시지 생성 (Protocol 3.3)

        구조체 정의 (msm_protocol.h:187-193):
        typedef struct {
            char queue_name[256];       // 256 bytes, offset 0
            char client_id[128];        // 128 bytes, offset 256 (NEW: session tracking)
            uint16_t prefetch_count;    // 2 bytes, offset 384
            uint8_t flags;              // 1 byte, offset 386
            // padding 1 byte           // offset 387 (uint32_t 정렬용)
            uint32_t timeout_ms;        // 4 bytes, offset 388
        } msm_consume_msg_t;

        구조체 크기: 392 bytes (패딩 포함)
        실제 전송 크기: opcode(1) + 구조체(392) = 393 bytes
        """
        queue_bytes = queue_name.encode('utf-8')
        queue_len = min(len(queue_bytes), 255)  # 최대 256 bytes (null 포함)
        client_id_bytes = self.client_id.encode('utf-8')
        client_id_len = min(len(client_id_bytes), 127)  # 최대 128 bytes (null 포함)

        msg = struct.pack('>B', MSG_OP_CONSUME)              # opcode
        msg += queue_bytes[:queue_len]                       # queue_name (256 bytes, offset 0)
        msg += b'\x00' * (256 - queue_len)                   # null padding
        msg += client_id_bytes[:client_id_len]               # client_id (128 bytes, offset 256)
        msg += b'\x00' * (128 - client_id_len)               # null padding
        msg += struct.pack('<H', 1)                          # prefetch_count (2 bytes, offset 384, LE)
        msg += struct.pack('B', 0)                           # flags (1 byte, offset 386)
        msg += b'\x00'                                       # padding (1 byte, offset 387)
        msg += struct.pack('<I', timeout_ms)                 # timeout_ms (4 bytes, offset 388, LE)

        return msg

    def _parse_deliver_message(self, data: bytes) -> AthenaMessage:
        """
        DELIVER 메시지 파싱
        고정 헤더 크기: 800 bytes

        주의: 서버(nng_transport.c)에서 memcpy를 사용하여 정수값을 저장하므로
        모든 정수 필드는 네이티브 바이트 오더(Little-Endian on x86/x64)로 읽어야 함
        """
        if len(data) < 800:
            raise AthenaException(f"DELIVER message too small: {len(data)} bytes")

        offset = 0

        # opcode (1 byte)
        opcode = data[offset]
        if opcode != MSG_OP_DELIVER:
            raise AthenaException(f"Invalid DELIVER opcode: 0x{opcode:02x}")
        offset += 1

        # delivery_tag (8 bytes, Little-Endian - 서버에서 memcpy 사용)
        delivery_tag = struct.unpack_from('<Q', data, offset)[0]
        offset += 8

        # queue_name (256 bytes, null-terminated)
        queue_name_bytes = data[offset:offset+256]
        null_index = queue_name_bytes.find(b'\x00')
        if null_index >= 0:
            queue_name = queue_name_bytes[:null_index].decode('utf-8')
        else:
            queue_name = queue_name_bytes.rstrip(b'\x00').decode('utf-8')
        offset += 256

        # exchange (256 bytes, null-terminated)
        exchange_bytes = data[offset:offset+256]
        null_index = exchange_bytes.find(b'\x00')
        if null_index >= 0:
            exchange = exchange_bytes[:null_index].decode('utf-8')
        else:
            exchange = exchange_bytes.rstrip(b'\x00').decode('utf-8')
        offset += 256

        # routing_key (256 bytes, null-terminated)
        routing_key_bytes = data[offset:offset+256]
        null_index = routing_key_bytes.find(b'\x00')
        if null_index >= 0:
            routing_key = routing_key_bytes[:null_index].decode('utf-8')
        else:
            routing_key = routing_key_bytes.rstrip(b'\x00').decode('utf-8')
        offset += 256

        # message_id (8 bytes, Little-Endian - 서버에서 memcpy 사용)
        message_id = struct.unpack_from('<Q', data, offset)[0]
        offset += 8

        # payload_len (4 bytes, Little-Endian - 서버에서 memcpy 사용)
        payload_len = struct.unpack_from('<I', data, offset)[0]
        offset += 4

        # flags (2 bytes, Little-Endian - 서버에서 memcpy 사용)
        offset += 2

        # timestamp (8 bytes, Little-Endian - 서버에서 memcpy 사용)
        offset += 8

        # redelivered (1 byte)
        offset += 1

        # payload
        if len(data) < 800 + payload_len:
            raise AthenaException(f"DELIVER message payload incomplete: "
                                 f"expected {800 + payload_len} bytes, got {len(data)}")

        payload = data[offset:offset+payload_len]

        return AthenaMessage(delivery_tag, queue_name, exchange, routing_key,
                            message_id, payload)

    async def ack(self, delivery_tag: int):
        """
        메시지 확인 응답 (ACK)

        구조체 정의 (msm_protocol.h:195-199):
        typedef struct {
            uint64_t message_id;    // 8 bytes (delivery_tag)
            uint8_t return_code;    // 1 byte
            char reason[128];       // 128 bytes
        } msm_ack_msg_t;            // 137 bytes + padding

        Args:
            delivery_tag: 전달 태그
        """
        if not self.connected:
            raise AthenaException("Not connected to broker")

        try:
            msg = struct.pack('>B', MSG_OP_ACK)          # opcode
            msg += struct.pack('<Q', delivery_tag)       # message_id/delivery_tag (8 bytes, LE)
            msg += struct.pack('B', MSM_RESP_SUCCESS)    # return_code (1 byte)
            msg += b'\x00' * 128                         # reason (128 bytes)
            msg += b'\x00' * 7                           # padding (7 bytes) -> 144 bytes struct

            with self._lock:
                await asyncio.to_thread(self.socket.send, msg)
            # ACK는 응답을 기다리지 않음

        except Exception as e:
            raise AthenaException(f"Failed to send ACK: {e}")

    async def nack(self, delivery_tag: int, requeue: bool = True, multiple: bool = False):
        """
        메시지 거부 (NACK)

        구조체 정의 (protocol.h:197-201):
        typedef struct {
            uint64_t delivery_tag;  // 8 bytes
            bool requeue;           // 1 byte
            bool multiple;          // 1 byte
        } nack_msg_t;               // 10 bytes + padding

        Args:
            delivery_tag: 전달 태그
            requeue: 재큐잉 여부
            multiple: 다중 NACK 여부
        """
        if not self.connected:
            raise AthenaException("Not connected to broker")

        try:
            msg = struct.pack('>B', MSG_OP_NACK)         # opcode
            msg += struct.pack('<Q', delivery_tag)       # delivery_tag (8 bytes, LE)
            msg += struct.pack('B', 1 if requeue else 0) # requeue (1 byte)
            msg += struct.pack('B', 1 if multiple else 0) # multiple (1 byte)
            msg += b'\x00' * 6                           # padding (6 bytes)

            with self._lock:
                await asyncio.to_thread(self.socket.send, msg)

                # NACK에 대한 응답(ACK) 대기 (서버 소스: MSG_OP_ACK 반환함)
                # Client: MSG_OP_NACK -> Server: MSG_OP_ACK
                response = await asyncio.to_thread(self.socket.recv)

        except Exception as e:
            raise AthenaException(f"Failed to send NACK: {e}")

    def _send_heartbeat_sync(self) -> bool:
        """
        하트비트 전송 (동기 버전 - heartbeat 스레드 전용)
        메인 소켓 공유 사용

        Returns:
            True: 성공, False: 실패
        """
        if not self.connected or not self.socket:
            return False

        try:
            # heartbeat_msg_t: [opcode:1][timestamp:8][sequence:4] = 13 bytes
            msg = struct.pack('>B', MSG_OP_HEARTBEAT)              # opcode (Big-Endian)
            msg += struct.pack('<Q', int(time.time()))             # timestamp (Little-Endian, 초)
            msg += struct.pack('<I', self._heartbeat_sequence)     # sequence (Little-Endian)
            self._heartbeat_sequence += 1

            with self._lock:
                self.socket.send(msg)
                response = self.socket.recv()

            # 응답 검증: [opcode:1][result:1]
            if len(response) >= 2 and response[0] == MSG_OP_HEARTBEAT and response[1] == MSM_RESP_SUCCESS:
                return True
            return False

        except Exception as e:
            _logger.warning("heartbeat error: %s", e)
            return False

    def _touch_sync(self, delivery_tag: int) -> bool:
        """
        ACK 타임아웃 연장 (동기 버전 - heartbeat 스레드 전용)
        메인 소켓 공유 사용

        프로토콜 스펙:
        요청: [opcode:1][delivery_tag:8, LE] = 9 bytes
        응답: [opcode:1][result:1]
              result: 0x00=성공, 0x01=실패(delivery_tag not found)

        Args:
            delivery_tag: 연장할 메시지의 delivery tag

        Returns:
            True: 성공, False: 실패
        """
        if not self.connected or not self.socket:
            return False

        try:
            # touch_msg: [opcode:1][delivery_tag:8, Little-Endian] = 9 bytes
            msg = struct.pack('<BQ', MSG_OP_TOUCH, delivery_tag)

            with self._lock:
                self.socket.send(msg)
                response = self.socket.recv()

            # 응답 검증: [opcode:1][result:1]
            if len(response) >= 2:
                opcode, result = response[0], response[1]
                if opcode == MSG_OP_TOUCH:
                    if result == MSM_RESP_SUCCESS:
                        return True
                    else:
                        # 0x01 = delivery_tag not found (이미 ACK됨 또는 만료됨)
                        _logger.debug("touch failed: delivery_tag=%s not found (result=0x%02x)", delivery_tag, result)
                        return False
            return False

        except Exception as e:
            _logger.warning("touch error: %s", e)
            return False

    def set_current_delivery_tag(self, delivery_tag: int):
        """현재 처리 중인 메시지의 delivery_tag 설정 (heartbeat 시 자동 touch)"""
        with self._touch_lock:
            self._current_delivery_tag = delivery_tag

    def clear_current_delivery_tag(self):
        """현재 처리 중인 메시지 해제"""
        with self._touch_lock:
            self._current_delivery_tag = None

    def _heartbeat_thread_loop(self):
        """
        백그라운드 하트비트/터치 스레드 (OS 스레드에서 실행)

        기능:
        - 세션 유지: 30초마다 heartbeat 전송
        - ACK 타임아웃 연장: 현재 처리 중인 메시지가 있으면 touch도 전송

        구현:
        - threading.Event().wait(interval) 사용으로 즉시 중지 가능
        - _touch_lock으로 delivery_tag 접근 동기화
        - 메인 소켓을 공유하여 동일한 세션에서 touch 전송
        """
        _logger.debug("heartbeat thread started (interval=%ds)", self._heartbeat_interval)

        try:
            # Event.wait()는 interval 동안 대기하다가, set()되면 즉시 리턴
            while not self._heartbeat_stop_event.wait(self._heartbeat_interval):
                if not self.connected:
                    break

                # heartbeat 전송 (세션 유지)
                self._send_heartbeat_sync()

                # 현재 처리 중인 메시지가 있으면 touch (ACK 타임아웃 연장)
                with self._touch_lock:
                    tag = self._current_delivery_tag

                if tag is not None:
                    result = self._touch_sync(tag)

                    # touch 실패 시 메시지가 이미 만료/requeue됨
                    if not result:
                        with self._touch_lock:
                            # 실패한 tag와 현재 tag가 같으면 클리어
                            if self._current_delivery_tag == tag:
                                self._current_delivery_tag = None

        except Exception as e:
            _logger.error("heartbeat thread error: %s", e)
        finally:
            _logger.debug("heartbeat thread stopped")

    async def start_heartbeat(self):
        """하트비트 스레드 시작"""
        if self._heartbeat_thread is None or not self._heartbeat_thread.is_alive():
            self._heartbeat_stop_event.clear()
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_thread_loop,
                daemon=True,
                name="heartbeat"
            )
            self._heartbeat_thread.start()

    async def stop_heartbeat(self):
        """하트비트 스레드 중지"""
        self._heartbeat_stop_event.set()  # 즉시 중지 신호

        with self._touch_lock:
            self._current_delivery_tag = None

        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2.0)
        self._heartbeat_thread = None

    async def close(self):
        """연결 종료"""
        # 하트비트 태스크 먼저 중지
        await self.stop_heartbeat()

        if self.push_socket:
            try:
                await asyncio.to_thread(self.push_socket.close)
            except:
                pass
            self.push_socket = None
            self.push_connected = False
        if self.socket:
            try:
                await asyncio.to_thread(self.socket.close)
            except:
                pass
            self.socket = None
        self.connected = False

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.connected

    async def __aenter__(self):
        """async with 문 지원"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 문 종료 시 자동 정리"""
        await self.close()
