"""Test execution primitives used by the regression runner."""

from __future__ import annotations

import os
import time
import shlex
import asyncio
from enum import auto, IntEnum, StrEnum
from typing import cast, override
from pathlib import Path
from dataclasses import dataclass
from asyncio.subprocess import Process, PIPE

import psutil
from dynaconf.utils.boxing import DynaBox

from socx.io import logger
from socx.config import settings
from socx.patterns import Visitor
from socx.patterns import UIDMixin


class TestResult(StrEnum):
    """
    Represents the result of a test that had finished and exited normally.

    Members
    -------
    NA: StrEnum
        Test has not yet finished running and therefore result is
        non-applicable.

    Passed: StrEnum
        Test had finished and terminated normally with no errors and a 0 exit
        code.

    Failed: StrEnum
        Test had finished either normally or abnormally with a non-zero exit
        code.
    """

    NA = "n/a"
    Passed = "passed"
    Failed = "failed"


class TestStatus(IntEnum):
    """
    TestStatus representation of a test process as an `IntEnum`.

    Members
    -------
    Idle: IntEnum
        Idle, waiting to be scheduled for execution.

    Pending: IntEnum
        Test is scheduled for execution in an active session.

    Running: IntEnum
        Test is currently running.

    Stopped: IntEnum
        Test has been stopped intentionally.

    Finished: IntEnum
        Test had finished running normally with an exit code 0.

    Terminated: IntEnum
        Test was intentionally terminated by a signal.
    """

    Idle = 0
    Pending = auto()
    Stopped = auto()
    Running = auto()
    Finished = auto()
    Terminated = auto()


@dataclass(init=False)
class TestCommand(UIDMixin):
    """Represent a test invocation parsed from a command-line string."""

    line: str
    name: str
    escaped: str
    arguments: tuple[str, ...]

    def __init__(self, line: str | TestCommand) -> None:
        if isinstance(line, TestCommand):
            self = line
            return

        self.line = line
        self.arguments = tuple(arg.strip() for arg in self.line.split())
        self.name = self.arguments[0] if self.arguments else ""
        self.escaped = shlex.quote(self.line)

    def extract_argv(self, arg: str) -> str | None:
        """Return the value that follows the requested CLI argument."""
        for i, attr in enumerate(self.arguments):
            if attr.startswith("--") or attr.startswith("-"):
                if attr == arg and i + 1 < len(self.arguments):
                    return self.arguments[i + 1]
                if attr.removeprefix("-") == arg and i + 1 < len(
                    self.arguments
                ):
                    return self.arguments[i + 1]
                if attr.removeprefix("--") == arg and i + 1 < len(
                    self.arguments
                ):
                    return self.arguments[i + 1]
        return None

    def __getattr__(self, attr: str) -> str:
        """Provide attribute-style access to parsed command arguments."""
        rv = self.extract_argv(attr)
        if rv is not None:
            return rv
        else:
            err = f"No such argument: {attr}"
            raise AttributeError(err)

    def __hash__(self) -> int:
        return hash(tuple(set(self.arguments)))


@dataclass(init=False)
class TestABC:
    """Define basic properties common across all test types."""

    _pid: int
    _name: str
    _result: TestResult
    _status: TestStatus
    _command: TestCommand
    _process: Process | None = None
    _started_time: float | None = None
    _finished_time: float | None = None

    def accept(self, v: Visitor[TestABC]) -> None:
        """Accept a visit from a `Visitor`."""
        ...

    async def start(self) -> None:
        """Start the execution of an idle test."""
        ...

    def wait(self, timeout: float | None = None) -> None:
        """Wait for a test to terminate if it is running."""
        ...

    def kill(self) -> None:
        """Interrupt the execution of a running test with a SIGKILL signal."""
        ...

    def suspend(self) -> None:
        """Suspend the execution of a running test."""
        ...

    def resume(self) -> None:
        """Resume the execution of a paused test."""
        ...

    def interrupt(self) -> None:
        """Interrupt the execution of a running test with a SIGINT signal."""
        ...

    def terminate(self) -> None:
        """Interrupt the execution of a running test with a SIGTERM signal."""
        ...


class TestBase(TestABC):
    """Provide common process-management behaviour for regression tests."""

    def __init__(self, command: str | TestCommand, *args, **kwargs) -> None:
        cmd = TestCommand(command) if isinstance(command, str) else command
        self._pid = os.getpid()
        self._name = cmd.name
        self._status = TestStatus.Idle
        self._result = TestResult.NA
        self._command = cmd
        self._process = None
        self._returncode = 0
        self._started_time = None
        self._finished_time = None

    @override
    def accept(self, v: Visitor[TestABC]) -> None:
        """Accept a visit from a `Visitor`."""
        v.visit(self)

    @property
    def pid(self) -> int:
        """Return the process identifier for the test's subprocess."""
        return self._process.pid if self._process is not None else os.getpid()

    @property
    def name(self) -> str:
        """Return the test's human readable name."""
        return self._name

    @property
    def command(self) -> TestCommand:
        """Test execution command representation as an object."""
        return self._command

    @property
    def status(self) -> TestStatus:
        """Return the current lifecycle status of the test."""
        return self._status

    @property
    def result(self) -> TestResult:
        """Return the result enum once a test has completed."""
        return self._result

    @property
    def started_time(self) -> str:
        """Return the formatted timestamp captured when the test started."""
        return time.ctime(self._started_time)

    @property
    def finished_time(self) -> str:
        """Return the formatted timestamp captured when the test finished."""
        return time.ctime(self._finished_time)


@dataclass(init=False)
class Test(UIDMixin, TestBase):
    """Holds information about a test."""

    _seed: int = 0
    _flow: str | None = None
    _build: str | None = None
    _stdout: str | None = None
    _stderr: str | None = None

    @override
    def __init__(self, command: str | TestCommand, *args, **kwargs) -> None:
        TestBase.__init__(self, command, *args, **kwargs)
        UIDMixin.__init__(self)

        try:
            name = self.command.test
        except AttributeError:
            self._missing_test_name_err(command)
            raise

        if "/" in name:
            name = name.partition("/")[-1]

        self._name = name
        self._seed = 0
        self._flow = None
        self._build = None

    @property
    def cfg(self) -> DynaBox:
        return cast(DynaBox, settings.regression)

    @property
    def flow(self) -> str:
        """Return the execution flow name extracted from the command."""
        try:
            rv = self.command.flow
        except AttributeError:
            raise
        else:
            return rv

    @property
    def build(self) -> str:
        """Return the randomisation build identifier, if provided."""
        try:
            return str(self.command.build)
        except AttributeError:
            return ""

    @property
    def seed(self) -> int:
        """Return the randomisation seed for the test."""
        try:
            rv = int(self.command.seed)
        except AttributeError:
            rv = 0
        return rv

    @property
    def idle(self) -> bool:
        """True if test has no active process and has not yet started."""
        return self.process is None and self.status is TestStatus.Idle

    @property
    def pending(self):
        """Return ``True`` if the test is queued but not yet running."""
        return self.status == TestStatus.Pending

    @property
    def started(self) -> bool:
        """Return ``True`` once ``start`` has spawned the subprocess."""
        return self.status > TestStatus.Pending

    @property
    def suspended(self) -> bool:
        """Return ``True`` if the subprocess is currently stopped."""
        return self.status == TestStatus.Stopped

    @property
    def running(self) -> bool:
        """True if test is currently running in a dedicated process."""
        return self.process is not None and self.status is TestStatus.Running

    @property
    def finished(self) -> bool:
        """Return ``True`` if the test completed and recorded a result."""
        return self.status == TestStatus.Finished

    @property
    def terminated(self) -> bool:
        """Return ``True`` if the test ended due to termination signals."""
        return self.status == TestStatus.Terminated

    @property
    def passed(self) -> bool:
        """Return ``True`` if the test finished successfully."""
        return self.finished and self.result is TestResult.Passed

    @property
    def failed(self) -> bool:
        """Return ``True`` if the test finished with a failure result."""
        return (
            self.terminated or self.finished
        ) and self.result == TestResult.Failed

    @property
    def stdin(self) -> str | None:
        """Return ``None``; subclasses may override to expose stdin."""
        return None  # not currently needed, can be overridden by subclass

    @property
    def stdout(self) -> str | None:
        """Return captured standard output once the test has finished."""
        return self._stdout

    @property
    def stderr(self) -> str | None:
        """Return captured standard error once the test has finished."""
        return self._stderr

    @property
    def process(self) -> psutil.Process | None:
        """Return a ``psutil.Process`` wrapper for the test's subprocess."""
        if self.pid == -1 or self._process is None:
            return None
        else:
            return psutil.Process(self.pid)

    @property
    def returncode(self) -> int | None:
        """The return code from the test process or None if running or idle."""
        return self._returncode

    @property
    def runtime_cfg(self) -> DynaBox:
        """Return the runtime settings section for this test."""
        return cast(DynaBox, self.cfg.run)

    @property
    def runtime_path(self) -> Path:
        """Return the resolved runtime directory for this test instance."""
        path = cast(str | Path, self.runtime_cfg.get("logs.path"))

        if isinstance(path, str):
            path = Path(path)

        return (path / self.dirname).resolve()

    @property
    def runtime_logs(self):
        """Return the path where the simulator writes log files."""
        log_dir = cast(str | Path, self.runtime_cfg.get("logs.directory"))
        return self.runtime_path / log_dir

    @property
    def dirname(self):
        """Return the directory name derived from the test identifier."""
        return Path(self.command.test).with_suffix("")

    @override
    async def start(self) -> None:
        """Start a test in a subprocess."""
        if self.started:
            msg = "Cannot start a test when it is already running."
            exc = OSError(msg)
            logger.exception(msg, exc_info=exc, stack_info=True)
            raise exc

        if self.idle:
            self._status = TestStatus.Pending

        self._status = TestStatus.Running
        self._process = await asyncio.create_subprocess_shell(
            cmd=self.command.line, stdin=None, stdout=PIPE, stderr=PIPE
        )
        self._started_time = time.time()
        while self._process.returncode is None:
            await asyncio.sleep(0)
        self._returncode = await self._process.wait()
        self._finished_time = time.time()
        stdout, stderr = await self._process.communicate()
        self._stdout = stdout.decode()
        self._stderr = stderr.decode()
        self._status = TestStatus.Finished
        self._result = self._parse_result()

    @override
    def suspend(self) -> None:
        """Send a SIGSTOP signal to suspend the test's running process."""
        if self.running and self.process:
            self.process.suspend()
            self._status = TestStatus.Stopped

    @override
    def resume(self) -> None:
        """Resume the process if it is paused (sends a SIGCONT signal)."""
        if self.suspended and self.process:
            self.process.resume()
            self._status = TestStatus.Running

    @override
    def wait(self, timeout: float | None = None) -> None:
        """Wait for a test to terminate if it is running."""
        if self.running and self.process:
            self.process.wait()

    @override
    def terminate(self) -> None:
        """Terminate the process with SIGTERM."""
        if self.running and self.process:
            self.process.terminate()
            self._status = TestStatus.Terminated

    @override
    def kill(self) -> None:
        """Kill the process with SIGKILL as a last resort."""
        if self.running and self.process:
            self.process.kill()
            self._status = TestStatus.Terminated

    def _parse_result(self) -> TestResult:
        """Map the subprocess return code to a ``TestResult`` enum."""
        return (
            TestResult.Failed
            if self.returncode != 0 or self.status != TestStatus.Finished
            else TestResult.Passed
        )

    def __hash__(self) -> int:
        return hash(self.command)

    @classmethod
    def _missing_test_name_err(cls, cmd) -> ValueError:
        err = f"No test was specified in the run command: {cmd}"
        exc = ValueError(err)
        logger.exception(err, exc_info=exc)
        raise exc
