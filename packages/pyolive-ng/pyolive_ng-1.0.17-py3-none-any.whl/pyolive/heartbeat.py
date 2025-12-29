import asyncio
from asyncio import CancelledError

class Heartbeat:
    def __init__(self, logger, channel, namespace: str, agent_name: str, interval: int = 3):
        self.logger = logger
        self.channel = channel
        self.namespace = namespace
        self.agent_name = agent_name
        self.interval = interval
        self._task: asyncio.Task | None = None
        self._running = False

    async def _loop(self):
        try:
            while self._running:
                await self.channel.publish_heartbeat(self.agent_name)
                await asyncio.sleep(self.interval)
        except CancelledError:
            pass  # Graceful shutdown

    async def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())
        self.logger.info(f"Heartbeat: Started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except CancelledError:
                pass
        self.logger.info("Heartbeat: Stopped")
