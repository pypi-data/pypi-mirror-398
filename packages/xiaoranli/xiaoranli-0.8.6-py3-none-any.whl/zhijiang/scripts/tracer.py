import linecache
import os
import sys
import inspect
import threading


class _Ignore:
    def __init__(self, include_dirs=(), exclude_name=(), exclude_dirs=(), include_name=()):
        self.include_dirs = set(include_dirs)
        self.exclude_name = set(exclude_name)

        self.exclude_dirs = set(exclude_dirs)
        self.include_name = set(include_name)

    def __call__(self, filename):
        dirs = set(os.path.dirname(filename).split(os.sep))
        file_name = os.path.basename(filename)
        if self.include_dirs:
            if (self.include_dirs & dirs) and (file_name not in self.exclude_name):
                return False
            return True

        if self.exclude_dirs:
            if (self.exclude_dirs & dirs) and (file_name not in self.include_name):
                return True

        return False


class PyTracer:
    def __init__(self, include_dirs=(), exclude_name=(), exclude_dirs=(), include_name=(), call_stack_depth=None, only_func_name=True):
        """
        if file dirs in include_dirs, and file name is not in exclude_name, then trace it;
        if file dirs not in exclude_dirs or file name in include_name, then trace it;

        call_stack_depth: only output call stack then the specified value

        call tracer.start() to start tracing, it will output function call and line content
        call tracer.end() to end tracing

        dir can't contain / or \\
        file name needs contain the suffix
        """
        self.ignore = _Ignore(include_dirs=include_dirs, exclude_name=exclude_name,
                              exclude_dirs=exclude_dirs, include_name=include_name)
        self.call_stack_depth = call_stack_depth
        self.tab = " "
        self.only_func_name = only_func_name

    def globaltrace(self, frame, why, arg):
        if why == "call":
            code = frame.f_code
            filename = frame.f_globals.get("__file__", None)
            if filename and not self.ignore(filename):
                self.cur_call_stack_depth += 1
                try:
                    lineno = inspect.getsourcelines(code)[1]
                except:
                    lineno = 1
                if (
                    self.call_stack_depth is None
                    or self.cur_call_stack_depth <= self.call_stack_depth
                ):
                    print(
                        f"{self.tab*self.cur_call_stack_depth}fn: {code.co_name}, {filename}:{lineno}"
                    )
                return self.localtrace

            return None

    def localtrace(self, frame, why, arg):
        if why == "line":
            if self.only_func_name:
                return
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno

            line_content = linecache.getline(filename, lineno)
            if (
                self.call_stack_depth is None
                or self.cur_call_stack_depth <= self.call_stack_depth
            ):
                print(f"{filename}:{lineno}: {line_content}", end="")

        if why == "return":
            assert self.cur_call_stack_depth > 0, "call stack depth is negative"
            self.cur_call_stack_depth -= 1

        return self.localtrace

    def start(self):
        self.cur_call_stack_depth = 1
        threading.settrace(self.globaltrace)
        sys.settrace(self.globaltrace)

    def stop(self):
        sys.settrace(None)
        threading.settrace(None)
