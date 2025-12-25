import asyncio
import logging
from dataclasses import dataclass

import pytest
from django.db import models

from csu.worker.engine import AbstractConsumer
from csu.worker.engine import AbstractEngine
from csu.worker.job import Job


@dataclass
class SleepyJob(Job):
    time: float


class ResultType(models.IntegerChoices):
    PENDING = 6, "PENDING"
    SUCCESS = 7, "SUCCESS"
    ABSENT = 8, "ABSENT"
    ERROR = 9, "ERROR"


class Consumer(AbstractConsumer):
    result_type_enum = ResultType

    async def save_result(self, job: SleepyJob, /, **kwargs):
        logging.info("save_result: %r %r", job, kwargs)
        return kwargs

    async def perform_work(self, job: SleepyJob):
        try:
            logging.info("perform_work: %r sleeping %s seconds...", job, job.time)
            await asyncio.sleep(job.time)
            return {"time": job.time}
        except Exception as exc:
            logging.exception("perform_work: %r", exc)
            raise


class Engine(AbstractEngine):
    async def start(self):
        worker = Consumer(engine=self)
        worker.start()
        self.workers.append(worker)
        logging.info("engine started")


@pytest.mark.asyncio
async def test_cancel():
    engine = Engine()
    await engine.start()
    job1 = SleepyJob(0.2)
    engine.push_nowait(job1)
    job2 = SleepyJob(0)
    engine.push_nowait(job2)
    await asyncio.sleep(0.1)
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(job1.done, 0.1)
    result = await asyncio.wait_for(job2.done, 1)
    assert result == {"result_type": ResultType.SUCCESS, "result_details": None, "time": 0}
