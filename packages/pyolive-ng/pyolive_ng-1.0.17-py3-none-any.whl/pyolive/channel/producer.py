import asyncio
import json
import socket
import os
import time
import base64
from enum import Enum
from typing import Any, Optional, Dict
from pyolive.status import JobStatus
from pyolive.job_context import JobContext
from .adapter import Adapter


class ProducerChannel:
    def __init__(self, logger: Any, namespace: str, alias: str, devel: bool = False):
        self.logger = logger
        self.namespace = namespace
        self.alias = alias
        self.hostname = socket.gethostname()
        self.adapter = Adapter(logger, "ProducerChannel")
        self.queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.devel = devel
        self.queue_config: Optional[dict] = None

    async def start(self):
        if self.devel:
            self.running = True
            # devel 모드에서는 백그라운드 태스크 없이 직접 처리
            return

        if not await self.adapter.open():
            self.logger.error("ProducerChannel: Failed to open adapter")
            return

        # Get queue configuration from adapter
        self.queue_config = self.adapter.get_queue_config()

        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        self.logger.info("ProducerChannel: Started")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # devel 모드에서는 adapter가 열리지 않았으므로 close하지 않음
        if not self.devel:
            await self.adapter.close()
        self.logger.info("ProducerChannel: Stopped")

    async def _run_loop(self):
        while self.running:
            try:
                item = await self.queue.get()
                await self._publish_with_retry(
                    item["exchange"],
                    item["routing_key"],
                    item["body"],
                    item.get("priority", 0)  # Athena Broker는 priority 미지원, 기본값 0
                )
            except Exception as e:
                self.logger.error("ProducerChannel: Publish failed - %s", e)
            await asyncio.sleep(0.001)

    async def _publish_with_retry(self, exchange: str, routing_key: str, message: str, priority: int = 0):
        """
        Publish message with retry logic based on queue type
        """
        retry_count = 0
        max_retries = self.queue_config['retry_attempts']

        while retry_count <= max_retries:
            try:
                await self._publish_enhanced(exchange, routing_key, message, priority)
                return  # Success

            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    self.logger.error(
                        f"ProducerChannel: Failed to publish after {max_retries} attempts - {e}"
                    )
                    raise

                self.logger.warning(
                    f"ProducerChannel: Publish attempt {retry_count} failed, retrying - {e}"
                )
                await asyncio.sleep(self.queue_config['retry_delay'] * retry_count)

    async def _publish_enhanced(self, exchange: str, routing_key: str, message: str, priority: int = 0):
        """
        Enhanced publish method with queue type specific features
        """
        try:
            # devel 모드에서는 adapter를 열지 않으므로 실제 publish는 스킵
            if self.devel:
                self.logger.debug(f"ProducerChannel (devel): Would publish to {exchange}:{routing_key}")
                return
            
            # Athena Broker v2 프로토콜은 PUBLISH 패킷에 flags/priority 필드가 없음
            # 따라서 priority는 무시됨 (또는 다른 방식으로 지원될 경우 구현 필요)
            
            # Publish via adapter
            await self.adapter.publish(exchange, routing_key, message)

        except Exception as e:
            self.logger.error(f"ProducerChannel: Enhanced publish failed to {exchange}:{routing_key} - {e}")
            raise

    async def publish_heartbeat(self, agent_name: str):
        data = {
            'metric_type': 4,
            'metric_status': 0,
            'metric_name': self.alias,
            'namespace': self.namespace,
            'process': agent_name,
            'psn': 0,
            'hostname': self.hostname,
            'timestamp': time.time()
        }
        rk = f'sys.{self.namespace}.heartbeat.agent'
        await self._enqueue(Adapter.EXCHANGE_METRIC, rk, json.dumps(data), priority=1)  # Higher priority

    async def publish_job(self, ctx: JobContext, priority: int = 0):
        if not ctx.msglist:
            ctx.msgbox = {"type": "ascii", "size": 0, "data": ""}
            await self._nextjob(ctx, self._build_data(ctx), priority)
            return

        for msg in ctx.msglist.copy():
            if isinstance(msg, bytes):
                # Binary message -> base64 encoding
                encoded = base64.b64encode(msg).decode('ascii')
                ctx.msgbox = {
                    "type": "binary",
                    "size": len(msg),
                    "data": encoded
                }
            elif isinstance(msg, str):
                msg_bytes = msg.encode('utf-8')
                ctx.msgbox = {
                    "type": "ascii",
                    "size": len(msg_bytes),
                    "data": msg
                }
            else:
                # Fallback: force convert to string
                msg_str = str(msg)
                msg_bytes = msg_str.encode('utf-8')
                ctx.msgbox = {
                    "type": "ascii",
                    "size": len(msg_bytes),
                    "data": msg_str
                }

            await self._nextjob(ctx, self._build_data(ctx), priority)

    def _build_data(self, ctx: JobContext) -> Dict[str, Any]:
        return {
            'regkey': ctx.regkey,
            'topic': ctx.topic,
            'action_id': ctx.action_id,
            'action_ns': ctx.action_ns,
            'action_app': ctx.action_app,
            'action_params': ctx.action_params,
            'job_id': ctx.job_id,
            'job_hostname': ctx.job_hostname,
            'job_seq': ctx.job_seq,
            'timestamp': ctx.timestamp,
            'filenames': ctx.filenames,
            'msgbox': ctx.msgbox,
        }

    async def _nextjob(self, ctx: JobContext, data: Dict[str, Any], priority: int = 0):
        """
        서버 코드(agent_job.c)와 동일한 형식으로 routing key 생성
        형식: job.des.msm.{kind}.{domain}
        - namespace: 항상 "des.msm" (SUBSYSTEM_DES, MODULE_MSM)
        - kind: timestamp == 0이면 "fast", 아니면 "now"
        - domain: ctx.topic에서 추출 (job.{subsystem}.{module}.{kind}.{domain} 형식에서 마지막 부분)
        """
        # ctx.topic에서 domain 추출
        # 형식: job.{subsystem}.{module}.{kind}.{domain}
        # 예: job.dps.psm.now.sysm -> domain = "sysm"
        topic_parts = ctx.topic.split('.')
        if len(topic_parts) >= 5:
            # job.{subsystem}.{module}.{kind}.{domain} 형식
            domain = topic_parts[-1]  # 마지막 부분이 domain
        else:
            # 형식이 맞지 않으면 전체 topic을 domain으로 사용 (fallback)
            domain = ctx.topic
        
        # kind 결정 (timestamp에 따라)
        kind = 'fast' if ctx.timestamp == 0 else 'now'
        
        # routing key 생성: job.des.msm.{kind}.{domain}
        key = f'job.des.msm.{kind}.{domain}'
        await self._enqueue(Adapter.EXCHANGE_ACTION, key, json.dumps(data), priority)

    async def publish_notify(self, ctx: JobContext, text: str = '', status: Enum = JobStatus.RUNNING, elapsed: int = 0):
        job_status_value = status.value if isinstance(status, Enum) else int(status)
        data = {
            'job_id': ctx.job_id,
            'job_status': job_status_value,
            'job_elapsed': elapsed,
            'reg_subject': ctx.regkey.split('@')[0],
            'reg_version': ctx.regkey.split('@')[1],
            'reg_topic': ctx.topic,
            'action_id': ctx.action_id,
            'action_app': ctx.action_app,
            'action_ns': ctx.action_ns,
            'hostname': self.hostname,
            'timestamp': int(time.time()),
            'filesize': 0,
            'filenames': ctx.filenames,
            'err_code': 0,
            'err_mesg': text
        }

        for f in ctx.filenames:
            try:
                data['filesize'] += os.stat(f).st_size
            except Exception as e:
                self.logger.debug("ProducerChannel: Failed to stat file %s - %s", f, e)

        # Logs have lower priority than jobs
        await self._enqueue(Adapter.EXCHANGE_LOGS, f'log.{ctx.action_ns}', json.dumps(data), priority=0)

    async def _enqueue(self, exchange: str, routing_key: str, body: str, priority: int = 0):
        await self.queue.put({
            "exchange": exchange,
            "routing_key": routing_key,
            "body": body,
            "priority": priority
        })

    async def get_queue_size(self) -> int:
        """
        Get current internal queue size
        """
        return self.queue.qsize()

    async def flush_queue(self, timeout: float = 30.0):
        """
        Wait for internal queue to be processed
        """
        if self.devel:
            # devel 모드에서는 큐에 있는 메시지를 직접 처리
            while not self.queue.empty():
                try:
                    item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                    await self._publish_enhanced(
                        item["exchange"],
                        item["routing_key"],
                        item["body"],
                        item.get("priority", 0)
                    )
                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    self.logger.error(f"ProducerChannel: Failed to process queued message - {e}")
            return
        
        start_time = time.time()
        while not self.queue.empty() and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)

        if not self.queue.empty():
            self.logger.warning(f"ProducerChannel: Queue flush timeout, {self.queue.qsize()} messages remaining")

    def _load_quorum_config(self) -> dict:
        """
        Deprecated: Configuration is now loaded from adapter
        """
        return {}