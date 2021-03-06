import os

from aoc_solver import SOLUTIONS_ROOT
from aoc_solver.lang.registry import LanguageSettings, register_language


@register_language(name="typescript", extension="ts")
class TypescriptSettings(LanguageSettings):
    ENTRY_FILE = os.path.join(SOLUTIONS_ROOT, "..", "aoc_executor.js", "index.js")

    def __init__(self, file):
        self._js_file = file.replace(".ts", "")
        super(TypescriptSettings, self).__init__(file)

    def compile(self):
        yield f"yarn tsc {self.file}"

    def solve(self):
        return f"node {self.ENTRY_FILE} {self._js_file}"
