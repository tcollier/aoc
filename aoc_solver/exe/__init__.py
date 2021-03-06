"""
usage: solver [-h] [-l LANGUAGE [LANGUAGE ...]] [--save] year [day]

Run Advent of Code solution for a given year/day in the chosen language

positional arguments:
  year                  competition year
  day                   competition day

optional arguments:
  -h, --help            show this help message and exit
  -l LANGUAGE [LANGUAGE ...], --language LANGUAGE [LANGUAGE ...]
                        programming language of the solution to run (available
                        languages: c, golang, haskell, java, kotlin, lisp,
                        python, ruby, rust, scala, typescript)
  --save                save the programs output to output.txt
"""

import os
import sys


class ExitCode:
    INVALID_ARGS = 2
    SIGNAL_BASE = 128
    SIGINT = SIGNAL_BASE + 2
    UNKNOWN_ERROR = 255

    @classmethod
    def for_signal(cls, signal: int) -> int:
        return cls.SIGNAL_BASE + signal


import argparse
import glob
import signal
import time

from datetime import datetime
from multiprocessing import Pipe, Process

AOC_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SOLUTIONS_PATH = os.environ.get("AOC_SOLUTIONS_PATH", ".")
sys.path.append(AOC_ROOT)

from aoc_solver.context_manager import ContextManager
from aoc_solver.display_event_loop import DisplayEventLoop
from aoc_solver.lang.registry import LanguageRegistry
from aoc_solver.solver_engine import SolverEngine
from aoc_solver.terminal.display import Display


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run Advent of Code solution for a given year/day in the chosen language"
        )
    )

    parser.add_argument("year", help=f"competition year")
    parser.add_argument("day", help=f"competition day", nargs="?")

    supported_languages = [l for l in LanguageRegistry.all()]
    language_helper = f"available languages: {', '.join(supported_languages)}"
    parser.add_argument(
        "-l",
        "--language",
        nargs="+",
        help=f"programming language of the solution to run ({language_helper})",
    )
    parser.add_argument(
        "--save", help=f"save the programs output to output.txt", action="store_true"
    )

    def argument_error(args):
        """
        There are certain combinations of arguments we want to disallow, but argparse
        doesn't provide easy ways to do this. So this function adds additional
        argument validations.

        :param args: parsed arguments from argparse
        """
        if args.language:
            unknown = [l for l in args.language if not LanguageRegistry.has(l)]
            if unknown:
                unknown_str = ", ".join(unknown)
                all_str = ", ".join(supported_languages)
                return f"Unrecognized language(s): {unknown_str} (available: {all_str})"
        if args.save:
            if not args.day:
                return "Must use `--save` with a specific day"
            elif SolverEngine.has_solution(args.year, args.day):
                return (
                    "Cannot save results when output already saved, "
                    "please delete existing file"
                )

    def sig_handler(signal: int, _frame):
        ContextManager.shutdown(signal=signal)
        sys.exit(ExitCode.for_signal(signal))

    signal.signal(signal.SIGQUIT, sig_handler)

    args = parser.parse_args()
    error_message = argument_error(args)
    if error_message:
        print(error_message)
        sys.exit(ExitCode.INVALID_ARGS)

    def days_to_solve(args):
        """
        :yield year, day: Yields each year/day combination that the arguments
        dictate need to be solved.
        """
        if args.day:
            yield int(args.year), int(args.day)
        else:
            days = glob.glob(
                f"{os.path.join(SOLUTIONS_PATH, str(args.year))}/[0-9][0-9]"
            )
            if len(days) > 0:
                days.sort()
                for day in days:
                    yield int(args.year), int(day.split("/")[-1])
            else:
                raise ValueError(f"No solutions found for {args.year}")

    ###
    # The solver engine and display logic run in two separate process and
    # communicate with each other through a pipe. The engine emits events
    # through the pipe (e.g. timing failed) and the display process receives
    # the events and updates accordingly. This file manages the pipe
    # connections and processes.
    ###

    try:
        # Create the pipe connections used by the two process to communicate
        # with each other and add them to the context manager for easy clean
        # up when shutting down.
        display_conn, solver_conn = Pipe(True)
        ContextManager.add_conn(display_conn)
        ContextManager.add_conn(solver_conn)

        # Spin up the display process.
        display = DisplayEventLoop(Display(), display_conn)
        display_proc = Process(target=display, name="AoC-display", args=(os.getpid(),))
        ContextManager.add_proc(display_proc)

        if args.language:
            languages = [LanguageRegistry.canonical(l) for l in args.language]
        else:
            languages = LanguageRegistry.all()
        for year, day in days_to_solve(args):
            # Spin up the solver for the given year/day
            solver = SolverEngine(solver_conn, SOLUTIONS_PATH, year, day, args.save)
            solver_proc = Process(
                target=solver, args=(os.getpid(), languages), name="AoC-solver",
            )
            ContextManager.add_proc(solver_proc)
            while solver_proc.is_alive():
                # If the display process dies for whatever reason (SIGKILL?), then
                # we should just shutdown.
                if not display_proc.is_alive():
                    ContextManager.shutdown()
                time.sleep(0.01)
        ContextManager.shutdown()
    except ValueError as e:
        ContextManager.shutdown(error=e)
        sys.exit(ExitCode.INVALID_ARGS)
    except KeyboardInterrupt as e:
        ContextManager.shutdown()
        sys.exit(ExitCode.SIGINT)
    except Exception as e:
        import traceback

        traceback.print_exc()
        ContextManager.shutdown(error=e)
        sys.exit(ExitCode.UNKNOWN_ERROR)


if __name__ == "__main__":
    main()
