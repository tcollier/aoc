import json
import os
import traceback

from datetime import datetime

from lib.languages import language_config, all_languages
from lib.shell import (
    ShellException,
    TerminationException,
    is_process_running,
    shell_out,
)
from lib.solver_event import SolverEvent


class LanguageSolver(object):
    def __init__(self, parent_pid, conn, language, year, day, filename):
        self.parent_pid = parent_pid
        self.conn = conn
        self.language = language
        self.year = year
        self.day = day
        self.filename = filename

    def __call__(self, expected, outfile):
        config = language_config(self.language)
        commands = config.commands(self.filename)
        if commands.compiler:
            self._build(commands.compiler)
        actual = self._solve(commands.exec)
        if not expected:
            self._handle_output(actual, outfile)
        elif actual != expected:
            self._handle_invalid_output(expected, actual)
        else:
            self._dispatch(SolverEvent.SOLVE_SUCCEEDED)
            if config.timing:
                self._handle_timing(commands.time)
            else:
                self._dispatch(SolverEvent.TIMING_SKIPPED)

    def _dispatch(self, event, args={}):
        args["language"] = self.language
        args["year"] = self.year
        args["day"] = self.day
        self.conn.send(event)
        self.conn.send(args)

    def _shell_out(self, cmd):
        def should_terminate():
            if not is_process_running(self.parent_pid):
                return True
            if not self.conn.poll(0):
                return False
            cmd = self.conn.recv()
            _args = self.conn.recv()
            return cmd == SolverEvent.TERMINATE

        unwrapped = cmd() if callable(cmd) else cmd
        return shell_out(unwrapped, should_terminate)

    def _build(self, compiler_cmds):
        self._dispatch(SolverEvent.BUILD_STARTED)
        try:
            for cmd in compiler_cmds:
                self._shell_out(cmd)
            self._dispatch(SolverEvent.BUILD_FINISHED)
        except ShellException as e:
            # Include stdout since node writes error messages to stdout
            self._dispatch(
                SolverEvent.BUILD_FAILED, {"stdout": e.stdout, "stderr": e.stderr}
            )
            raise e
        except Exception as e:
            self._dispatch(SolverEvent.BUILD_FAILED)
            raise e

    def _solve(self, cmd):
        self._dispatch(SolverEvent.SOLVE_STARTED)
        try:
            actual = self._shell_out(cmd)
            self._dispatch(SolverEvent.SOLVE_FINISHED)
            return actual
        except ShellException as e:
            self._dispatch(SolverEvent.SOLVE_FAILED, {"stderr": e.stderr})
            raise e
        except Exception as e:
            self._dispatch(SolverEvent.SOLVE_FAILED)
            raise e

    def _handle_output(self, actual, outfile):
        self._dispatch(SolverEvent.SOLVE_ATTEMPTED, {"actual": actual})
        if outfile:
            open(outfile, "w").write(actual)
            self._dispatch(SolverEvent.OUTPUT_SAVED, {"file": outfile})

    def _handle_timing(self, cmd):
        self._dispatch(SolverEvent.TIMING_STARTED)
        try:
            start_time = datetime.now()
            timing_info = json.loads(self._shell_out(cmd))
            duration = datetime.now() - start_time
            self._dispatch(
                SolverEvent.TIMING_FINISHED, {"info": timing_info, "duration": duration}
            )
        except ShellException as e:
            self._dispatch(SolverEvent.TIMING_FAILED, {"stderr": e.stderr})
            raise e
        except Exception as e:
            self._dispatch(SolverEvent.TIMING_FAILED)
            raise e

    def _handle_invalid_output(self, expected, actual):
        self._dispatch(
            SolverEvent.SOLVE_INCORRECT, {"expected": expected, "actual": actual}
        )


class Solver(object):
    def __init__(self, conn, year, day, save=False):
        if not os.path.isdir(year):
            raise ValueError(f"No source code exists for year {year}")
        padded_day = day.zfill(2)
        if not os.path.isdir(os.path.join(year, padded_day)):
            raise ValueError(f"No source code exists for day {day} in {year}")
        self.base_dir = os.path.join(year, padded_day)
        self.conn = conn
        self.year = year
        self.day = day
        self.save = save
        self.outfile = os.path.join(year, padded_day, "output.txt")
        self.expected = None
        if os.path.isfile(self.outfile):
            self.expected = "".join(open(self.outfile, "r").readlines())

    @classmethod
    def has_solution(cls, year, day):
        return os.path.isfile(os.path.join(year, day.zfill(2), "output.txt"))

    def __call__(self, parent_pid, languages, save=False):
        """
        :param parent_pid: Process ID of the parent that spawned the solver. Keep
        tabs on it so we can exit if it mysteriously vanishes, e.g. with a SIGKILL
        """
        found = False
        for language, filename in self._find_files(languages):
            found = True
            try:
                solver = LanguageSolver(
                    parent_pid, self.conn, language, self.year, self.day, filename
                )
                solver(self.expected, self.outfile if self.save else None)
            except ShellException:
                continue
            except KeyboardInterrupt as e:
                raise e
            except TerminationException:
                break
            except:
                print()
                traceback.print_exc()
                continue
        if not found and languages:
            for language in languages:
                self._dispatch(SolverEvent.MISSING_SRC, {"language": language})

    def _dispatch(self, event, args={}):
        args["year"] = self.year
        args["day"] = self.day
        self.conn.send(event)
        self.conn.send(args)

    def _find_files(self, languages):
        if not languages:
            languages = all_languages()
        for language in languages:
            ext = language_config(language).extension
            filename = os.path.join(self.base_dir, f"main.{ext}")
            if os.path.isfile(filename):
                yield language, filename
