import os
import time
import traceback
import inspect
from typing import Any
from .status import AppStatus, JobStatus
from .job_context import JobContext


class JobExecutor:
    def __init__(self, resource: Any, channel: Any, agent_logger: Any, app_logger: Any, context: JobContext):
        self.resource = resource
        self.channel = channel
        self.agent_logger = agent_logger
        self.app_logger = app_logger
        self.context = context

    async def run(self):
        try:
            app = self._create_instance()

            # joblog start message
            tm_st = int(time.time())
            await self.channel.publish_notify(self.context, 'job start', JobStatus.STARTED)
            self.agent_logger.info("start %s [%s] (%s:%s)",
                                self.context.action_app, self.context.job_id,
                                self.context.regkey, self.context.action_id)
            self.app_logger.info("main: jobid[%s]", self.context.job_id)

            files = self.context.get_fileset()
            for _f in files:
                try:
                    _sz = os.path.getsize(_f)
                except FileNotFoundError:
                    _sz = -1
                self.app_logger.info("main: in-file (%s, %d)", _f, _sz)

            # 실행
            status = await self._execute(app)

            if status == AppStatus.OK:
                tm_ed = int(time.time())

                files = self.context.get_fileset()
                for _f in files:
                    try:
                        _sz = os.path.getsize(_f)
                    except FileNotFoundError:
                        _sz = -1
                    self.app_logger.info("main: out-file (%s, %d)", _f, _sz)

                self.agent_logger.info("end   %s [%s] (%s:%s)",
                                    self.context.action_app, self.context.job_id,
                                    self.context.regkey, self.context.action_id)
                self.app_logger.info("main: status is success")
                await self.channel.publish_job(self.context)
                await self.channel.publish_notify(self.context, 'job end, success', JobStatus.ENDED, tm_ed-tm_st)
            elif status == AppStatus.FIN:
                self.agent_logger.warn("fin   %s [%s] (%s:%s)",
                                    self.context.action_app, self.context.job_id,
                                    self.context.regkey, self.context.action_id)
                self.app_logger.warn("main: status is finish")
                await self.channel.publish_notify(self.context, 'job end, finish', JobStatus.FAILED)
            else:
                self.agent_logger.error("end   %s [%s] (%s:%s)",
                                    self.context.action_app, self.context.job_id,
                                    self.context.regkey, self.context.action_id)
                self.app_logger.error("main: status is failure")
                await self.channel.publish_notify(self.context, 'job end, failed', JobStatus.FAILED)
        except Exception as e:
            self.agent_logger.error("job_executor: exception: %s", e)
            self.agent_logger.debug(traceback.format_exc())
            await self.channel.publish_notify(self.context, str(e), JobStatus.FAILED)

    def _create_instance(self):
        if isinstance(self.resource, type):
            self.app_logger.debug("Instantiating resource class: %s", self.resource.__name__)
            return self.resource(
                logger=self.app_logger,
                channel=self.channel,
                context=self.context
            )
        self.app_logger.debug("Using existing resource instance: %s", self.resource)
        return self.resource

    async def _execute(self, app: Any):
        if hasattr(app, "app_main"):
            method = app.app_main
            self.app_logger.debug("Found app_main: %s", method)

            if callable(method):
                if inspect.iscoroutinefunction(method):
                    self.app_logger.debug("app_main is coroutine, awaiting...")
                    return await method()
                else:
                    self.app_logger.debug("app_main is normal function, calling...")
                    return method()
            else:
                self.app_logger.error("app_main is not callable")
        else:
            self.app_logger.error("job_executor: no attribute 'app_main' in app")

        return AppStatus.ERROR
