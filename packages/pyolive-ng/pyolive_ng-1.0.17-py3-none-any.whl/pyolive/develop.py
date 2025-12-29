import os
import logging
from .log import AppLog
from .job_context import JobContext
from pyolive.channel import ProducerChannel


async def develop_mode(infile: str, params: dict):
    logger = AppLog("pywork", devel=True).get_logger()
    channel = ProducerChannel(logger=logger, namespace="dps.psm", alias="pywork", devel=True)
    await channel.start()  # Start the channel loop
    context = JobContext(devel=True)

    logger.info("Developer mode started ...")
    context.set_fileset(infile, devel=True)
    context.set_param(params, devel=True)
    context.regkey = 'test@1'

    return logger, channel, context