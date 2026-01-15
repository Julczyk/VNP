class Interpreter:
    """
    Interpreter v1.0
    Program = lista akcji [(func_id, args), ...]
    Wykonywane cyklicznie.
    """

    def __init__(self, program):
        self.program = program
        self.ip = 0  # instruction pointer

    def run_step(self, robot):
        if not self.program:
            return 0, []

        func_id, args = self.program[self.ip]

        # cykliczne wykonanie programu
        self.ip = (self.ip + 1) % len(self.program)

        return func_id, args
