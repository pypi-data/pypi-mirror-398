import asyncio
import os
import signal
import socket
import json
from typing import Any, Optional
from pyolive.channel.athena_client import AthenaMessage

from .config import Config
from .log import AgentLog, AppLog
from .job_context import JobContext
from .status import AppStatus
from .heartbeat import Heartbeat
from .job_executor import JobExecutor
from .resource_watcher import start_resource_watcher
from pyolive.channel import ConsumerChannel, ProducerChannel


class Athena:
    def __init__(self, namespace: str, alias: str):
        self.namespace = namespace
        self.alias = alias
        self.worker_name = "ovd-node"
        self.hostname = socket.gethostname()
        self._log = AgentLog(self.alias)
        self.agent_logger = self._log.get_logger()

        self.tasks: dict[str, Any] = {}
        self.hot_reload = self._load_reload_option()
        self.default_poolsize = self._load_pool_size()
        self.semaphores: dict[str, asyncio.Semaphore] = {}

        self.consumer: Optional[ConsumerChannel] = None
        self.publisher: Optional[ProducerChannel] = None
        self.heartbeat: Optional[Heartbeat] = None  # 타입 힌트 수정
        self._running = True

    def _load_reload_option(self) -> bool:
        config = Config('athena-agent.yaml')
        return config.get_value('pywork/reload-on-change', False)

    def _load_pool_size(self) -> int:
        config = Config('athena-app.yaml')
        return config.get_value('pool-size', 1)

    def add_resource(self, resource, app_name: str):
        if app_name in self.tasks:
            self.agent_logger.warning("App '%s' is already registered. Overwriting.", app_name)
        self.tasks[app_name] = resource

    def _maybe_update_poolsize(self, app_name: str, pool_value: str):
        try:
            new_pool = int(pool_value)
            if new_pool <= 0:
                return

            # 현재 값이 존재하면 가져오고 없으면 기본값 사용
            current_semaphore = self.semaphores.get(app_name)
            current_value = current_semaphore._value if current_semaphore else self.default_poolsize

            if new_pool > current_value:
                self.semaphores[app_name] = asyncio.Semaphore(new_pool)
                self.agent_logger.debug("Updated pool size for '%s': %d -> %d", app_name, current_value, new_pool)
            else:
                self.agent_logger.debug("Ignored pool size update for '%s' (current: %d >= new: %d)", app_name, current_value, new_pool)

        except Exception as e:
            self.agent_logger.warning("Invalid pool size for app '%s': %s", app_name, e)

    def _get_semaphore(self, app_name: str) -> asyncio.Semaphore:
        return self.semaphores.get(app_name, asyncio.Semaphore(self.default_poolsize))

    async def _callback_subscribe(self, message: AthenaMessage):
        try:
            body = message.body
            payload = json.loads(body.decode())
            
            # routing_key를 topic으로 매핑 (JobContext가 topic을 기대함)
            if 'topic' not in payload and message.routing_key:
                payload['topic'] = message.routing_key
            
            self.agent_logger.debug("received message: %s", payload)

            ctx = JobContext(payload)
            app_name = ctx.action_app
            regkey = ctx.regkey

            pool_param = ctx.get_param('pool')
            if pool_param:
                self._maybe_update_poolsize(app_name, pool_param)

            sem = self._get_semaphore(app_name)

            if sem.locked():
                self.agent_logger.warning("Pool exhausted for app '%s'. Nacking message.", app_name)
                await self.consumer.nack(message, requeue=True)
                return

            async with sem:
                log_key = f"{regkey.split('@')[0]}+{app_name}"
                app_logger = AppLog(log_key).get_logger()

                resource = self.tasks.get(app_name)
                if resource is None:
                    self.agent_logger.warning("No matching task for app: %s", app_name)
                    await self.consumer.nack(message, requeue=False)
                    return

                executor = JobExecutor(
                    resource=resource,
                    channel=self.publisher,
                    agent_logger=self.agent_logger,
                    app_logger=app_logger,
                    context=ctx
                )

                await executor.run()
                await self.consumer.ack(message)

        except Exception as e:
            self.agent_logger.exception("Subscribe callback error: %s", e)
            await self.consumer.nack(message, requeue=True)

    def _create_pid_file(self):
        athena_home = Config.ATHENA_HOME or '.'
        path = os.path.join(athena_home, 'var/run')
        os.makedirs(path, exist_ok=True)
        name = f"{self.worker_name}+{self.namespace}@{self.hostname}.pid"
        pid_file_path = os.path.join(path, name)
        
        with open(pid_file_path, "w") as f:
            f.write(str(os.getpid()))

    def _remove_pid_file(self):
        athena_home = Config.ATHENA_HOME or '.'
        path = os.path.join(athena_home, 'var/run')
        name = f"{self.worker_name}+{self.namespace}@{self.hostname}.pid"
        full_path = os.path.join(path, name)
        
        if os.path.exists(full_path):
            os.remove(full_path)

    async def run(self):
        self.agent_logger.info("== Start Athena Agent ==")
        self._create_pid_file()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._shutdown)

        try:
            self.publisher = ProducerChannel(self.agent_logger, self.namespace, self.alias)
            self.consumer = ConsumerChannel(self.agent_logger, self.namespace, self._callback_subscribe)
            self.heartbeat = Heartbeat(self.agent_logger, self.publisher, self.namespace, self.alias)

            await self.publisher.start()
            await self.consumer.start()
            await self.heartbeat.start()

            if self.hot_reload:
                task_dicts = [{"resource": r} for r in self.tasks.values()]
                start_resource_watcher(task_dicts, self.agent_logger)

            self.agent_logger.info("Agent started successfully")

            while self._running:
                await asyncio.sleep(1)

        except Exception as e:
            self.agent_logger.error("Error during agent startup: %s", e)
            raise
        finally:
            await self.stop()

    def _shutdown(self):
        self.agent_logger.info("Shutdown signal received")
        self._running = False

    async def stop(self):
        self.agent_logger.info("Stopping agent...")

        # 순차적으로 안전하게 종료
        if self.heartbeat:
            try:
                await self.heartbeat.stop()
            except Exception as e:
                self.agent_logger.warning("Error stopping heartbeat: %s", e)

        if self.consumer:
            try:
                await self.consumer.stop()
            except Exception as e:
                self.agent_logger.warning("Error stopping consumer: %s", e)

        if self.publisher:
            try:
                await self.publisher.stop()
            except Exception as e:
                self.agent_logger.warning("Error stopping publisher: %s", e)

        self._remove_pid_file()

        try:
            self._log.close()
        except Exception as e:
            self.agent_logger.warning("Error closing log: %s", e)

        self.agent_logger.info("Agent stopped successfully")