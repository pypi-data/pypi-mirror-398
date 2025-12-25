"""
Optionally database-backed job system designed to run inside an asyncio event loop.

The engine manages consumers and producers around a queue. All are reported as workers with states for introspection purposes.

Producers take pending jobs from a model. Usually there's just one producer (no need to have more than one coroutine query the database),

Consumers process said jobs. Usually there's many consumers, depending on how much concurrency you want.

Typical batch processing workload::

  DB             Producer (one)                      Engine         Consumers (one or more)
  Task      ---> get_first_and_mark_scheduled
                 Job(**task.job_kwargs)        --->  push(job)
                                                     pull()    ---> perform_work(job) -> result
  Task      <------------------------------------------------------ save_result(job, **result)

The database is completely optional.
"""

from logging import getLogger

logger = getLogger("worker")
