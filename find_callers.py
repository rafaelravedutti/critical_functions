import os
import sys
import subprocess
import re


class ListFCallers:
    def __init__(self, binary_file, F):
        self._binary_file = binary_file
        self._graph = None
        self._F = F
        self._stack_trace = []
        self._callers = set()
        self._visited = set()

    def __call__(self):
        self._build_calling_graph()
        for func in self._graph:
            self.visit(func)

    def _build_calling_graph(self):
        objdump_output = subprocess.check_output(['objdump', '-d', '-j', '.text', self._binary_file]).decode('utf-8')
        current_function = None
        self._graph = {}

        for line in objdump_output.split('\n'):
            match = re.match(r'^\w+ \<(\w+)\>:', line)

            if match:
                current_function = match.group(1)

                if current_function not in self._graph:
                    self._graph[current_function] = set()

            if current_function is not None and 'callq' in line:
                instruction = re.sub("\s\s+", " ", line[line.index('callq'):])
                segments = instruction.split(' ')

                if len(segments) == 3:
                    callee = re.sub("@plt", "", segments[2][1:-1])
                    self._graph[current_function].add(callee)

    def visit(self, func):
        if func in self._F or (func in self._visited and func in self._callers):
            for f in self._stack_trace:
                self._callers.add(f)

        elif func not in self._visited:
            if func in self._graph and func not in self._stack_trace:
                self._stack_trace.append(func)

                for callee in self._graph[func]:
                    self.visit(callee)

                self._stack_trace.pop()

            self._visited.add(func)

    def calling_graph(self):
        return self._graph

    def callers(self):
        return self._callers


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <binary_file>")
    sys.exit(-1)

binary_file = sys.argv[1]
F = {'allocate', 'reallocate'}

list_f_callers = ListFCallers(binary_file, F)
list_f_callers()

for k, v in list_f_callers.calling_graph().items():
    print(f"{k} -> {v}")

f_callers = list_f_callers.callers()
print(f"f-callers: {f_callers}")
