import traceback
from contextlib import redirect_stdout
from io import StringIO
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection


def worker(parent_pipe: Connection, pipe: Connection):
    parent_pipe.close()

    globals = {}
    locals = {}

    while True:
        try:
            todo = pipe.recv()
        except EOFError:
            break

        todo = compile(source=todo, filename="sphinxrun_code.py", mode="exec")

        try:
            with redirect_stdout(StringIO()) as buffer:
                exec(todo, globals, locals)
        except Exception as e:
            ok = False
            out = "\n".join(traceback.format_exception(e))
        else:
            ok = True
            out = buffer.getvalue()

        pipe.send((ok, out))


class Runner:
    def __init__(self):
        self.pipe, child_pipe = Pipe()
        self.proc = Process(target=worker, args=[self.pipe, child_pipe])
        self.proc.start()
        child_pipe.close()

    def __del__(self):
        self.stop()

    def stop(self):
        if self.proc.is_alive():
            self.proc.terminate()

        self.proc.join()

    def submit(self, code):
        self.pipe.send(code)
        _, out = self.pipe.recv()

        return out
