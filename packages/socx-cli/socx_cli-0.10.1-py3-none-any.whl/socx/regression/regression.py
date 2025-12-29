"""Asynchronous regression runner that orchestrates test execution."""

from __future__ import annotations

import time
import logging
import asyncio as aio
from typing import Any, TypeVar
from typing import override
from threading import RLock
from dataclasses import dataclass, field
from collections import deque
from collections.abc import Iterator
from collections.abc import Iterable
from collections.abc import AsyncIterator

from rich.progress import Progress
from rich.progress import TextColumn
from rich.progress import BarColumn
from rich.progress import TaskProgressColumn
from rich.progress import TimeRemainingColumn
from rich.progress import SpinnerColumn
from rich.progress import TimeElapsedColumn
from rich.progress import MofNCompleteColumn

from socx.config import settings
from socx.regression.test import Test
from socx.regression.test import TestBase
from socx.regression.test import TestStatus
from socx.regression.test import TestResult


logger = logging.getLogger(__name__)


__all__ = ("Regression",)

TestType = TypeVar("TestType", bound=Test)


@dataclass(init=False)
class Regression(TestBase):
    """Manage and execute a collection of tests with concurrency control."""

    _tests: deque[Test] = field(default_factory=deque)

    def __init__(
        self, name: str, tests: Iterable[TestType], *args: Any, **kwargs: Any
    ) -> None:
        TestBase.__init__(self, name, *args, **kwargs)
        tests = set(tests)
        self.done: aio.Queue = aio.Queue()
        self.pending: aio.Queue = aio.Queue(self.run_limit)
        self.messages: aio.Queue = aio.Queue()
        self._lock = RLock()
        self._tests = deque(tests)
        self._runner_tid = None
        self._scheduler_tid = None
        self._regression_tid = None
        self._progress: Progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TaskProgressColumn(),
            BarColumn(),
            "[green]Completed:",
            MofNCompleteColumn(),
            "[yellow]Elapsed:",
            TimeElapsedColumn(),
            "[cyan]Remaining:",
            TimeRemainingColumn(),
            speed_estimate_period=15,
            transient=False,
            expand=True,
        )

    def __len__(self) -> int:
        """Return the number of tests scheduled within the regression."""
        return len(self._tests)

    def __iter__(self) -> Iterator[Test]:
        """Iterate over tests defined in a regression."""
        return iter(self._tests)

    async def __aiter__(self) -> AsyncIterator[Test]:
        """Allow asynchronous iteration over the regression tests."""
        for test in self._tests:
            yield test

    def __contains__(self, test: Test) -> bool:
        """Return ``True`` if ``test`` is tracked by this regression."""
        return test is not None and test in self._tests

    @classmethod
    def from_lines(
        cls, name: str, lines: Iterable[str], test_cls: type | None = None
    ) -> Regression:
        """Construct a regression from serialized command lines."""
        test_cls = test_cls or Test
        tests = [test_cls(line) for line in lines]
        return Regression(name, tests)

    @property
    def tests(self) -> deque[Test]:
        """An iterable of all tests defined in the regression."""
        with self._lock:
            return self._tests

    @property
    def progress(self):
        """Expose the ``Progress`` instance tracking regression status."""
        with self._lock:
            return self._progress

    @property
    def run_limit(self) -> int:
        """Return the maximum number of tests that may run concurrently."""
        return settings.regression.max_runs_in_parallel

    @override
    async def start(self) -> None:
        """Start the regression."""
        logger.info("regression starting...")
        self._status = TestStatus.Pending

        try:
            self._status = TestStatus.Running
            logger.info("regression starting...")
            self._started_time = time.perf_counter()
            async with aio.TaskGroup() as tg:
                if len(self):
                    tg.create_task(self._animate_progress())
                    tg.create_task(self._schedule_tests())
                    tg.create_task(self._run_tests())
                logger.info("regression started.")
        finally:
            self._finished_time = time.perf_counter()
            self._result = (
                TestResult.Passed
                if all(test.passed for test in self)
                else TestResult.Failed
            )
            self._status = (
                TestStatus.Finished
                if all(test.status == TestStatus.Finished for test in self)
                else TestStatus.Terminated
            )
            logger.info(f"regression {self._status.name.lower()}.")

    @override
    def suspend(self) -> None:
        """Suspend the execution of a running test."""
        for test in self.tests:
            test.suspend()
        if self._status == TestStatus.Running:
            self._status = TestStatus.Stopped

    @override
    def resume(self) -> None:
        """Resume the execution of a paused test."""
        for test in self.tests:
            test.resume()
        if self._status == TestStatus.Stopped:
            self._status = TestStatus.Running

    @override
    def interrupt(self) -> None:
        """Interrupt the execution of a running test with a SIGINT signal."""
        for test in self.tests:
            test.interrupt()

    @override
    def terminate(self) -> None:
        """Interrupt the execution of a running test with a SIGTERM signal."""
        for test in self.tests:
            test.terminate()

    @override
    def kill(self) -> None:
        """Interrupt the execution of a running test with a SIGKILL signal."""
        for test in self.tests:
            test.kill()

    async def _schedule_tests(self) -> None:
        """Spawn scheduler tasks responsible for queueing each test."""
        try:
            await self.messages.put("Scheduling tests...")
            async with aio.TaskGroup() as tg:
                async for test in self:  # removed async cause it was 2 fast
                    tg.create_task(self._scheduler(test))
        finally:
            await self.messages.put("All tests scheduled.")

    async def _scheduler(self, test) -> None:
        """Queue an individual test for execution."""
        await self.messages.put(f"Scheduler({test.name}): scheduling test...")
        await self.pending.put(test)
        await self.messages.put(f"Scheduler({test.name}): test scheduled.")
        self._scheduler_advance()

    async def _run_tests(self) -> None:
        """Run the configured number of worker tasks that execute tests."""
        try:
            async with aio.TaskGroup() as tg:
                for _ in range(self.run_limit):
                    tg.create_task(self._runner())
        finally:
            await self.messages.put("All tests finished.")

    async def _runner(self) -> None:
        """Consume tests from the queue and execute them sequentially."""
        while not self.progress.finished:
            if self.pending.empty():
                await aio.sleep(0)
                continue

            try:
                test: Test = await self.pending.get()
                await self.messages.put(f"Runner({test.name}): running...")
                self._runner_advance()
                await test.start()
                await self.messages.put(
                    f"Runner({test.name}): test {test.result}."
                )
                self._regression_advance()
                await self.done.put(test)
            finally:
                self.pending.task_done()

    async def _animate_progress(self) -> None:
        """Update progress tasks and flush log messages while running."""
        with self.progress:
            self._scheduler_start()
            self._runner_start()
            self._regression_start()
            await self._process_messages()

    async def _process_messages(self) -> None:
        """Drain the message queue and mirror events to the progress log."""
        while not self.progress.finished:
            while not self.messages.empty():
                try:
                    msg = await self.messages.get()
                    self.progress.log(msg)
                finally:
                    self.messages.task_done()
            await aio.sleep(0)

    def _scheduler_start(self) -> None:
        """Initialise the scheduler progress task if it is not active."""
        if self._scheduler_tid is None:
            self._scheduler_tid = self.progress.add_task(
                description="[red]Schedulers: pending...",
                total=len(self),
                start=False,
                visible=True,
            )

    def _scheduler_advance(self) -> None:
        """Advance the scheduler progress task based on queued tests."""
        if self._scheduler_tid is not None:
            task = self.progress.tasks[self._scheduler_tid]
            if not task.started:
                self.progress.start_task(self._scheduler_tid)
                self.progress.update(
                    self._scheduler_tid,
                    total=len(self),
                    refresh=True,
                    description="[yellow]Schedulers: working...",
                )

            if task.completed + 1 < len(self):
                self.progress.update(
                    advance=1,
                    refresh=True,
                    task_id=task.id,
                )
            else:
                self.progress.update(
                    advance=1,
                    refresh=True,
                    task_id=task.id,
                    description="[light_green]Schedulers: done.",
                )

    def _runner_start(self) -> None:
        """Initialise the runner progress task if it is not active."""
        if self._runner_tid is None:
            self._runner_tid = self.progress.add_task(
                description="[red]Runners: pending...",
                total=len(self),
                start=False,
                visible=True,
            )

    def _runner_advance(self) -> None:
        """Advance the runner progress task for each completed test."""
        if self._runner_tid is not None:
            task = self.progress.tasks[self._runner_tid]
            if not task.started:
                self.progress.start_task(self._runner_tid)
                self.progress.update(
                    refresh=True,
                    visible=True,
                    task_id=self._runner_tid,
                    description="[yellow]Runners: working...",
                )

            if task.completed + 1 < len(self):
                self.progress.update(
                    advance=1,
                    refresh=True,
                    task_id=self._runner_tid,
                )
            else:
                self.progress.update(
                    advance=1,
                    refresh=True,
                    task_id=self._runner_tid,
                    description="[light_green]Runners: done.",
                )

    def _regression_start(self) -> None:
        """Initialise the overall regression progress task."""
        if self._regression_tid is None:
            self._regression_tid = self.progress.add_task(
                total=len(self),
                start=True,
                visible=True,
                description="[yellow]Regression: in progress...",
            )

    def _regression_advance(self) -> None:
        """Advance the overall regression progress task once work begins."""
        if self._regression_tid is not None:
            task = self.progress.tasks[self._regression_tid]
            if task.completed + 1 < len(self):
                self.progress.update(
                    advance=1,
                    refresh=True,
                    task_id=task.id,
                )
            else:
                self.progress.update(
                    total=len(self),
                    refresh=True,
                    task_id=task.id,
                    completed=len(self),
                    description="[light_green]Regression: done.",
                )
