import asyncio
import os
import time
from typing import Optional, Callable, Awaitable
from pyolive.config import Config
from .athena_client import AthenaClient, AthenaMessage, AthenaException, DEFAULT_EXCHANGE


class Adapter:
    EXCHANGE_ACTION = "action"
    EXCHANGE_CONTROL = "control"
    EXCHANGE_METRIC = "metric"
    EXCHANGE_LOGS = "logs"

    def __init__(self, logger, channel_type: str = "Adapter"):
        self.logger = logger
        self.channel_type = channel_type
        self.client: Optional[AthenaClient] = None
        self.queue_type: Optional[str] = None
        self.agent_config: Optional[Config] = None  # athena-agent.yaml
        self.mq_config: Optional[Config] = None
        self.broker_url: Optional[str] = None
        self.broker_username: Optional[str] = None
        self.broker_password: Optional[str] = None
        # Named Queue 이름 저장 (재연결 시 같은 큐로 재등록)
        self._current_queue: Optional[str] = None

    def _load_config(self):
        """
        Load configuration once and cache values from both config files
        """
        if self.agent_config is None:
            # Load athena-agent.yaml for broker configuration
            self.agent_config = Config('athena-agent.yaml')

            # Athena Broker는 큐 타입 개념이 없음 (단순 큐만 사용)
            self.queue_type = None

            # Build Broker URL (NNG 형식)
            hosts = self.agent_config.get_value('broker/hosts')
            port = self.agent_config.get_value('broker/port', 2736)  # Athena Broker 기본 포트

            if not hosts:
                raise RuntimeError("Broker hosts not found in configuration")

            host = hosts[0]
            self.broker_url = f"tcp://{host}:{port}"

            # 인증 정보 저장 (현재는 사용하지 않지만 나중을 위해 저장)
            self.broker_username = self.agent_config.get_value('broker/username', 'guest')
            self.broker_password = self.agent_config.get_value('broker/password', 'guest')

        if self.mq_config is None:
            # Load athena-mq.yaml for queue mapping configuration
            self.mq_config = Config('athena-mq.yaml')

    async def open(self) -> bool:
        try:
            # Load configuration once
            self._load_config()

            # Create Athena Broker client
            # client_id 포맷: python_client_{pid}_{timestamp} (문서 권장)
            client_id = f"python_client_{os.getpid()}_{int(time.time())}"
            self.logger.info(f"{self.channel_type}: Connecting to Broker at {self.broker_url}")
            self.client = AthenaClient(self.broker_url, client_id=client_id)
            await self.client.connect()

            self.logger.info(f"{self.channel_type}: Connected")
            return True
        except AthenaException as e:
            # AthenaException은 이미 상세한 메시지를 포함하고 있음
            self.logger.error(f"{self.channel_type}: {e}")
            return False
        except Exception as e:
            # pynng 예외 등 다른 예외 처리
            error_type = type(e).__name__
            self.logger.error(
                f"{self.channel_type}: Connection failed to Athena Broker at {self.broker_url}.\n"
                f"Error type: {error_type}\n"
                f"Error message: {e}\n"
                f"\nPlease check:\n"
                f"  1. Athena Broker server is running\n"
                f"  2. Configuration file: {self.agent_config.path if self.agent_config else 'athena-agent.yaml'}\n"
                f"  3. Broker URL is correct: {self.broker_url}\n"
                f"  4. Network connectivity to {self.broker_url}"
            )
            return False

    async def close(self):
        try:
            if self.client:
                await self.client.close()
            self.logger.info(f"{self.channel_type}: Connection closed")
        except Exception as e:
            self.logger.warning(f"{self.channel_type}: Close failed: {e}")

    async def publish(self, exchange: str, routing_key: str, message: str):
        try:
            # Athena Broker 프로토콜 v2: exchange와 routing_key를 분리하여 전송
            await self.client.publish_str(routing_key, message, exchange=exchange)
        except Exception as e:
            self.logger.error(f"{self.channel_type}: Publish failed to {exchange}:{routing_key} - {e}")
            raise  # 예외를 다시 발생시켜서 producer가 에러를 감지할 수 있도록 함

    async def start_consume(self, namespace: str, callback: Callable[[AthenaMessage], Awaitable[None]],
                           routing_key: Optional[str] = None, exchange: Optional[str] = None,
                           running_flag: Optional[asyncio.Event] = None):
        """
        큐에서 메시지 소비 시작 (폴링 방식)

        process.c 패턴:
        - Named Queue는 서버에 미리 존재 (queue_declare 불필요)
        - msm_consumer(adpid, queue->name)만 호출
        - 재연결 시: msm_reopen() + msm_consumer(queue->name)

        Args:
            namespace: 네임스페이스
            callback: 메시지 수신 시 호출할 콜백
            routing_key: 라우팅 키 (None이면 namespace 사용)
            exchange: Exchange 이름 (None이면 EXCHANGE_ACTION 사용)
            running_flag: 실행 상태를 제어하는 Event (None이면 무한 루프)
        """
        try:
            # Named Queue 이름 조회 (설정 파일에서)
            queue_name = await self.get_queue_name(namespace)
            self._current_queue = queue_name  # 재연결 시 사용

            # process.c:72 - msm_consumer(adpid, queue->name)
            # Named Queue는 서버에 이미 존재하므로 queue_declare/bind 불필요
            from .athena_client import MSM_TIMEOUT

            while running_flag is None or running_flag.is_set():
                try:
                    # 연결 상태 확인 및 재연결 (process.c:95-99 re_connect 레이블)
                    if not self.client or not self.client.is_connected():
                        self.logger.warning(f"{self.channel_type}: Connection lost, attempting to reconnect...")
                        if not await self._reopen():
                            await asyncio.sleep(5)  # 재연결 실패 시 대기
                            continue

                    # MSM_TIMEOUT 사용 (서버와 동일)
                    message = await self.client.consume(queue_name, timeout_ms=None)

                    if message:
                        # 메시지 처리 중 heartbeat 시 자동 touch (ACK 타임아웃 연장)
                        self.client.set_current_delivery_tag(message.delivery_tag)
                        try:
                            await callback(message)
                        finally:
                            self.client.clear_current_delivery_tag()

                except asyncio.CancelledError:
                    break
                except AthenaException as e:
                    error_msg = str(e)
                    # 연결 관련 에러 감지 (process.c:80 - rv < 0 goto re_connect)
                    if "connect" in error_msg.lower() or "closed" in error_msg.lower():
                        self.logger.warning(f"{self.channel_type}: Connection error, will reconnect: {e}")
                        if not await self._reopen():
                            await asyncio.sleep(5)
                    else:
                        self.logger.error(f"{self.channel_type}: Consume error - {e}")
                        await asyncio.sleep(1)
                except Exception as e:
                    self.logger.error(f"{self.channel_type}: Consume error - {e}")
                    await asyncio.sleep(1)

                # running_flag가 clear되면 종료
                if running_flag is not None and not running_flag.is_set():
                    break

        except asyncio.CancelledError:
            self.logger.info(f"{self.channel_type}: Consume cancelled")
        except Exception as e:
            self.logger.error(f"{self.channel_type}: Consume failed - {e}")
            raise

    async def _reopen(self) -> bool:
        """
        재연결 (process.c:97 msm_reopen 패턴)
        기존 연결 정리 후 새로 연결
        """
        try:
            # 기존 클라이언트 정리
            if self.client:
                try:
                    await self.client.close()
                except Exception as e:
                    self.logger.debug(f"{self.channel_type}: Error closing old client: {e}")

            # 새로 연결
            success = await self.open()
            if success:
                self.logger.info(f"{self.channel_type}: Reconnected successfully, queue: {self._current_queue}")
            return success

        except Exception as e:
            self.logger.error(f"{self.channel_type}: Reconnect failed - {e}")
            return False

    async def ack(self, message: AthenaMessage):
        try:
            await self.client.ack(message.delivery_tag)
        except Exception as e:
            self.logger.warning(f"{self.channel_type}: Ack failed - {e}")

    async def nack(self, message: AthenaMessage, requeue: bool = True):
        try:
            await self.client.nack(message.delivery_tag, requeue=requeue)
        except Exception as e:
            self.logger.warning(f"{self.channel_type}: Nack failed - {e}")

    async def reject(self, message: AthenaMessage, requeue: bool = False):
        """
        Reject message (NACK with requeue=False)
        """
        try:
            await self.client.nack(message.delivery_tag, requeue=requeue)
        except Exception as e:
            self.logger.warning(f"{self.channel_type}: Reject failed - {e}")

    def _get_queue_type(self) -> str:
        """
        Get queue type from cached configuration
        """
        if self.queue_type is None:
            self._load_config()
        return self.queue_type

    async def _get_queue_type(self) -> str:
        """
        Get queue type from cached configuration (async version for compatibility)
        """
        return self._get_queue_type()

    async def _ensure_client_open(self):
        """
        Ensure the client is connected and ready for use
        """
        if not self.client or not self.client.is_connected():
            self.logger.info(f"{self.channel_type}: Client disconnected, reconnecting...")
            success = await self.open()
            if not success:
                raise RuntimeError("Failed to reconnect client")


    def get_broker_config(self) -> dict:
        """
        Get broker configuration from athena-agent.yaml
        """
        if self.agent_config is None:
            self._load_config()

        return {
            'vendor': 'Athena',
            'hosts': self.agent_config.get_value('broker/hosts', []),
            'port': self.agent_config.get_value('broker/port', 2736),
            'username': self.broker_username,
            'password': self.broker_password,
            'broker_url': self.broker_url
        }

    def get_queue_mapping(self, subsystem: str) -> list:
        """
        Get queue mapping configuration from athena-mq.yaml
        """
        if self.mq_config is None:
            self._load_config()

        return self.mq_config.get_value(subsystem, [])

    def get_queue_config(self) -> dict:
        """
        Get queue configuration for Athena Broker
        Athena Broker는 단순 큐만 사용하며, 큐 타입 개념이 없음
        """
        return {
            'prefetch_count': 1,
            'confirm_delivery': True,
            'retry_attempts': 2,
            'retry_delay': 1.0
        }

    async def get_queue_name(self, namespace: str) -> str:
        subsystem, module = namespace.split('.')[:2]

        # Use cached config or load if not available
        if self.mq_config is None:
            self._load_config()

        entries = self.mq_config.get_value(subsystem)
        for entry in entries:
            if module == entry.split(':')[1]:
                return 'ovq.' + subsystem + '-' + entry.split(':')[0]
        raise RuntimeError(f"Queue name not found for namespace {namespace}")

    def get_queue_binding(self, queue_name: str) -> tuple[str, str]:
        """
        큐 이름으로 바인딩 정보(routing_key, exchange)를 가져옵니다.

        Args:
            queue_name: 큐 이름 (예: "ovq.dps-m.pywork")

        Returns:
            (routing_key, exchange) 튜플
        """
        # Use cached config or load if not available
        if self.mq_config is None:
            self._load_config()

        # 큐 이름에서 subsystem 추출 (예: "ovq.dps-m.pywork" -> "dps")
        # 큐 이름 형식: "ovq.{subsystem}-{module}"
        if queue_name.startswith('ovq.'):
            queue_part = queue_name[4:]  # "ovq." 제거
            if '-' in queue_part:
                subsystem = queue_part.split('-')[0]

                # subsystem의 모든 엔트리를 확인하여 큐 이름과 일치하는 것 찾기
                entries = self.mq_config.get_value(subsystem, [])
                for entry in entries:
                    # entry 형식: "module:module_name" 또는 dict
                    if isinstance(entry, dict):
                        # dict 형식: {"queue": "ovq.dps-m.pywork", "routing_key": "...", "exchange": "..."}
                        if entry.get('queue') == queue_name:
                            routing_key = entry.get('routing_key')
                            exchange = entry.get('exchange', self.EXCHANGE_ACTION)
                            if routing_key:
                                return routing_key, exchange
                    elif isinstance(entry, str):
                        # 기존 형식: "module:module_name"
                        parts = entry.split(':')
                        if len(parts) >= 2:
                            module = parts[0]
                            expected_queue = 'ovq.' + subsystem + '-' + module
                            if expected_queue == queue_name:
                                # 기본값 반환 (설정 파일에 바인딩 정보가 없는 경우)
                                break

        # 기본값 반환 (설정 파일에서 찾지 못한 경우)
        # namespace를 routing_key로 사용하고, exchange는 "action" 사용
        return None, None
