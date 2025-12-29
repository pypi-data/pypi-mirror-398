import asyncio
from typing import Any, Callable, Awaitable, Optional
from .adapter import Adapter, AthenaMessage


class ConsumerChannel:
    def __init__(self, logger: Any, namespace: str, callback: Callable[[AthenaMessage], Awaitable[None]]):
        self.logger = logger
        self.namespace = namespace
        self.callback = callback
        self.adapter = Adapter(logger, "ConsumerChannel")
        self._task: Optional[asyncio.Task] = None
        self.running = False
        self._running_event = asyncio.Event()
        self.queue_config: Optional[dict] = None

    async def start(self):
        if not await self.adapter.open():
            self.logger.error("ConsumerChannel: Failed to open adapter")
            return

        # Get queue configuration from adapter
        self.queue_config = self.adapter.get_queue_config()

        self.running = True
        self._running_event.set()

        # Set up queue specific configuration
        await self._setup_queue()

        self._task = asyncio.create_task(
            self.adapter.start_consume(self.namespace, self._enhanced_callback, running_flag=self._running_event)
        )
        self.logger.info(f"ConsumerChannel: Started consuming on queue {self.namespace}")

    async def _setup_queue(self):
        """
        Setup queue with proper configuration based on queue type
        """
        # Athena Broker는 prefetch를 consume 메시지에서 설정
        pass

    async def _enhanced_callback(self, message: AthenaMessage):
        """
        Enhanced callback with queue type specific handling
        """
        try:
            # Call original callback
            await self.callback(message)

        except Exception as e:
            self.logger.error(f"ConsumerChannel: Enhanced callback failed - {e}")
            # Let the original callback handle the error
            raise

    async def stop(self):
        self.running = False
        self._running_event.clear()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.adapter.close()
        self.logger.info("ConsumerChannel: Stopped")

    async def ack(self, message: AthenaMessage):
        await self.adapter.ack(message)

    async def nack(self, message: AthenaMessage, requeue: bool = True):
        await self.adapter.nack(message, requeue=requeue)

    async def reject(self, message: AthenaMessage, requeue: bool = False):
        """
        Reject message
        """
        await self.adapter.reject(message, requeue=requeue)

    async def get_queue_status(self) -> dict:
        """
        Get current queue status and metrics
        """
        try:
            queue_name = await self.adapter.get_queue_name(self.namespace)
            return {
                "name": queue_name,
                "type": "athena",
                "status": "active" if self.running else "stopped"
            }
        except Exception as e:
            self.logger.warning(f"ConsumerChannel: Failed to get queue status - {e}")
            return {}

    def _load_quorum_config(self) -> dict:
        """
        Deprecated: Configuration is now loaded from adapter
        """
        return {}