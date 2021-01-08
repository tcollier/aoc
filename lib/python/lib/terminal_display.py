from queue import PriorityQueue

from lib.languages import all_languages
from lib.shell import is_process_running
from lib.solver_event import SolverEvent
from lib.ui import CURSOR_RETURN, Align, Box, Color, Spinner, Table, Text


class Priority(object):
    MEDIUM = 1
    HIGH = 0


class PrioritizedItem(object):
    def __init__(self, output, msg_num, priority):
        self.output = output
        self.msg_num = msg_num
        self.priority = priority

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.msg_num < other.msg_num
        else:
            return self.priority < other.priority


def _duration(duration):
    """
    Convert the duration from microseconds to the unit that will allow the
    number to be between 1 <= n < 1,000 and apply the unit (e.g. "ms") and
    any colorization.

    :param duration: time in microseconds
    """
    if duration < 1:
        value = duration * 1000
        unit = "ns"
        color = Color.GREEN
    elif duration < 1000:
        value = duration
        unit = "μs"
        color = None
    elif duration < 1000000:
        value = duration / 1000
        unit = "ms"
        color = Color.YELLOW
    else:
        value = duration / 1000000
        unit = "s"
        color = Color.RED
    formatted_value = "{:.2f}".format(value)
    box_width = len(f"NNN.NN {unit}")
    return str(Box(Text(f"{formatted_value} {unit}", color), box_width, Align.RIGHT))


def _language(language):
    """
    Right pad the language name with spaces so that all languages will take up
    the same width.
    """
    max = 0
    for l in all_languages():
        if len(l) > max:
            max = len(l)
    return language.ljust(max, " ")


def _status(label, color, args):
    """
    Generic formatter for the solver's status of running the language/day
    """
    language = args["language"]
    year = args["year"]
    day = args["day"]
    day_language = f"{year}/{day.rjust(2, '0')} {_language(language)}"
    return Text(f"{label.ljust(4, ' ')} [{day_language}]", color)


def _success(args):
    return _status("PASS", Color.GREEN, args)


def _failure(args):
    return _status("FAIL", Color.RED, args)


def _diff(expected, actual):
    exp_parts = expected.split("\n")
    act_parts = actual.split("\n")
    table = [[""], ["Expected"], ["Actual"]]
    if len(act_parts) < 1:
        table[0].append("Part 1")
        table[1].append(exp_parts[0])
        table[2].append("")
    elif exp_parts[0] != act_parts[0]:
        table[0].append("Part 1")
        table[1].append(exp_parts[0])
        table[2].append(act_parts[0])
    if len(act_parts) < 2:
        table[0].append("Part 2")
        table[1].append(exp_parts[1])
        table[2].append("")
    elif exp_parts[1] != act_parts[1]:
        table[0].append("Part 2")
        table[1].append(exp_parts[1])
        table[2].append(act_parts[1])
    return Table(table, {1: Color.CYAN, 2: Color.YELLOW})


def _timing(timing_info, duration):
    duration_us = duration.seconds * 1000000 + duration.microseconds
    overhead = (
        duration_us
        - timing_info["part1"]["duration"]
        - timing_info["part2"]["duration"]
    )
    part1_avg_time = (
        timing_info["part1"]["duration"] / timing_info["part1"]["iterations"]
    )
    part2_avg_time = (
        timing_info["part2"]["duration"] / timing_info["part2"]["iterations"]
    )
    part2_spacer = " " if part1_avg_time >= 1000000 else ""
    overhead_spacer = " " if part2_avg_time >= 1000000 else ""
    end_spacer = " " if overhead >= 1000000 else ""
    contents = ", ".join(
        [
            f"part1: {_duration(part1_avg_time)}",
            f"{part2_spacer}part2: {_duration(part2_avg_time)}",
            f"{overhead_spacer}overhead: {_duration(overhead)}{end_spacer}",
        ]
    )
    return f"({contents})"


class TerminalDisplay(object):
    def __init__(self):
        self._busy = False
        self._was_busy = False
        self._spinner = Spinner()
        self._queue = PriorityQueue()
        self._msg_num = 0

    def handle(self, message):
        event = message["event"]
        handler = (
            self.HANDLERS[event] if event in self.HANDLERS else self._invalid_command
        )
        for output in handler(self, message):
            self._enqueue(output)

    def tick(self):
        if not self._was_busy and self._busy:
            self._enqueue(self._spinner.start())
            self._was_busy = True
        if self._busy:
            self._enqueue(self._spinner.tick())
        elif self._was_busy:
            self._enqueue(self._spinner.stop(), Priority.HIGH)
            self._was_busy = False
        while not self._queue.empty():
            item = self._queue.get(False)
            print(item.output, end="", flush=self._queue.empty())

    def _enqueue(self, output, priority=Priority.MEDIUM):
        self._queue.put(PrioritizedItem(output, self._msg_num, priority), False)
        self._msg_num += 1

    def _invalid_command(self, cmd, args):
        yield Text(f"Invalid command {cmd} with arguments {args}", Color.RED)
        yield "\n"

    def _missing_src(self, args):
        yield f"{_failure(args)} (no source code found)\n"
        yield "\n"

    def _build_started(self, args):
        self._busy = True
        yield _status("COMP", Color.GREY, args)

    def _build_finished(self, args):
        self._busy = False
        yield CURSOR_RETURN

    def _build_failed(self, args):
        self._busy = False
        yield CURSOR_RETURN
        yield _failure(args)
        yield "\n"
        if "stdout" in args:
            yield args["stdout"]
        if "stderr" in args:
            yield args["stderr"]

    def _solve_started(self, args):
        yield _status("EXEC", Color.CYAN, args)
        self._busy = True

    def _solve_finished(self, args):
        self._busy = False
        yield CURSOR_RETURN

    def _solve_failed(self, args):
        self._busy = False
        yield CURSOR_RETURN
        yield _failure(args)
        yield "\n"
        if "stderr" in args:
            yield args["stderr"]

    def _solve_attempted(self, args):
        yield _status("TRY", Color.YELLOW, args)
        yield "\n"
        yield args["actual"].rstrip()
        yield "\n"

    def _solve_succeeded(self, args):
        yield _success(args)

    def _solve_incorrect(self, args):
        yield _failure(args)
        yield "\n"
        yield _diff(args["expected"], args["actual"])
        yield "\n"

    def _output_saved(self, args):
        yield f"Saved result to {args['file']}"
        yield "\n"

    def _timing_started(self, args):
        yield " "
        yield Text("timing", Color.GREY)
        self._busy = True

    def _timing_skipped(self, args):
        yield "\n"

    def _timing_finished(self, args):
        self._busy = False
        timing_info = _timing(args["info"], args["duration"])
        yield CURSOR_RETURN
        yield f"{_success(args)} {timing_info}"
        yield "\n"

    def _timing_failed(self, args):
        self._busy = False
        yield CURSOR_RETURN
        yield _failure(args)
        yield "\n"
        if "stderr" in args:
            yield args["stderr"]

    HANDLERS = {
        SolverEvent.MISSING_SRC: _missing_src,
        SolverEvent.BUILD_STARTED: _build_started,
        SolverEvent.BUILD_FINISHED: _build_finished,
        SolverEvent.BUILD_FAILED: _build_failed,
        SolverEvent.SOLVE_STARTED: _solve_started,
        SolverEvent.SOLVE_FINISHED: _solve_finished,
        SolverEvent.SOLVE_SUCCEEDED: _solve_succeeded,
        SolverEvent.SOLVE_FAILED: _solve_failed,
        SolverEvent.SOLVE_ATTEMPTED: _solve_attempted,
        SolverEvent.SOLVE_INCORRECT: _solve_incorrect,
        SolverEvent.OUTPUT_SAVED: _output_saved,
        SolverEvent.TIMING_STARTED: _timing_started,
        SolverEvent.TIMING_SKIPPED: _timing_skipped,
        SolverEvent.TIMING_FINISHED: _timing_finished,
        SolverEvent.TIMING_FAILED: _timing_failed,
    }
