import glob
import os

from typing import Callable, Union


CompilerCommand = Union[str, Callable[[], str]]


class Commands:
    def __init__(self, exec: str):
        self.compiler = []
        self.exec = exec
        self.time = f"{exec} --time"

    def add_compiler_command(self, command: CompilerCommand):
        self.compiler.append(command)


def c_cmds(file: str) -> Commands:
    bin_file = file.replace(".", "_")
    cmds = Commands(os.path.join(".", bin_file))
    lib_files = glob.glob(os.path.join("lib", "c", "*.c"))
    cmds.add_compiler_command(f"gcc -O3 -o {bin_file} {file} {' '.join(lib_files)}")
    return cmds


def golang_cmds(file: str) -> Commands:
    bin_file = file.replace(".", "_")
    cmds = Commands(os.path.join(".", bin_file))
    cmds.add_compiler_command(f"go build -o {bin_file} {file}")
    return cmds


def java_cmds(file: str) -> Commands:
    lib_dir = os.path.join("lib", "java")
    lib_src = glob.glob(os.path.join(lib_dir, "**", "*.java"))
    base_dir = os.path.dirname(file)

    def jar_class_arguments(base_dir, class_files):
        args = []
        for file in class_files:
            args.append(f"-C {base_dir} {file[len(base_dir) + 1:]}")
        return args

    def purge_class_files():
        class_files = glob.glob(os.path.join(base_dir, "*.class"))
        if class_files:
            return f"rm {' '.join(class_files)}"
        else:
            return "echo"

    jar_file = file.replace(".java", ".jar")

    def build_jar():
        lib_files = glob.glob(os.path.join(lib_dir, "**", "*.class"))
        class_files = glob.glob(os.path.join(base_dir, "*.class"))
        if not class_files:
            raise Exception("No class files generated by javac")
        jar_classes = jar_class_arguments(base_dir, class_files) + jar_class_arguments(
            lib_dir, lib_files
        )
        return f"jar cfe {jar_file} Main {' '.join(jar_classes)}"

    cmds = Commands(f"java -jar {jar_file}")
    cmds.add_compiler_command(purge_class_files)
    cmds.add_compiler_command(
        f"javac -sourcepath {lib_dir} -d {lib_dir} {' '.join(lib_src)}"
    )
    cmds.add_compiler_command(
        f"javac -sourcepath {base_dir} -classpath {lib_dir} -d {base_dir} {file}"
    )
    cmds.add_compiler_command(build_jar)
    cmds.add_compiler_command(purge_class_files)
    return cmds


def lisp_cmds(file: str) -> Commands:
    return Commands(f"sbcl --script {file}")


def python_cmds(file: str) -> Commands:
    return Commands(f"python {file}")


def ruby_cmds(file: str) -> Commands:
    return Commands(f"ruby {file}")


def rust_cmds(file: str) -> Commands:
    lib_dir = os.path.join("lib", "rust")
    bin_file = file.replace(".", "_")
    cmds = Commands(os.path.join(".", bin_file))
    cmds.add_compiler_command(f"rustc -C opt-level=3 -o {bin_file} {file} -L {lib_dir}")
    return cmds


def scala_cmds(file: str) -> Commands:
    lib_dir = os.path.join("lib", "scala")
    lib_src = glob.glob(os.path.join(lib_dir, "**", "*.java"))
    base_dir = os.path.dirname(file)
    cmds = Commands(f"scala -classpath {base_dir}:{lib_dir} Main")
    cmds.add_compiler_command(f"scalac -optimize -d {lib_dir} {' '.join(lib_src)}")
    cmds.add_compiler_command(f"scalac  -d {base_dir} -classpath {lib_dir} {file}")
    return cmds


def typescript_cmds(file: str) -> Commands:
    js_file = os.path.join(".", file.replace(".ts", ""))
    entry_file = os.path.join(".", "lib", "javascript", "index.js")
    cmds = Commands(f"node {entry_file} {js_file}")
    cmds.add_compiler_command(f"yarn tsc {file}")
    return cmds


class LanguageConfig:
    def __init__(self, extension: str, commands: Commands, timing: bool = True):
        self.extension = extension
        self.commands = commands
        self.timing = timing


LANGUAGES = {
    "c": LanguageConfig("c", c_cmds),
    "golang": LanguageConfig("go", golang_cmds, timing=False),
    "java": LanguageConfig("java", java_cmds),
    "lisp": LanguageConfig("lisp", lisp_cmds, timing=False),
    "python": LanguageConfig("py", python_cmds),
    "ruby": LanguageConfig("rb", ruby_cmds),
    "rust": LanguageConfig("rs", rust_cmds),
    "scala": LanguageConfig("scala", scala_cmds),
    "typescript": LanguageConfig("ts", typescript_cmds),
}


def language_config(language):
    if language in LANGUAGES:
        return LANGUAGES[language]
    else:
        raise Exception(f"Unknown language {language}")


def all_languages():
    return [l for l in LANGUAGES.keys()]
