class Interpreter:
    """
    Wykonuje program automatu.
    Pamięć to tablica floatów o stałym rozmiarze.
    """

    def __init__(self, program_ast, memory_size=32):
        self.program = program_ast
        self.memory = [0.0] * memory_size
        self.instruction_pointer = 0
        self.max_instructions_per_step = 100  # Zabezpieczenie przed pętlą nieskończoną

    def run_step(self, robot):
        """
        Uruchamia program na jeden krok symulacji.
        Zwraca ID funkcji (f_n) i argumenty do wykonania na końcu kroku.
        """
        instructions_executed = 0

        # Uproszczona pętla wykonawcza (w praktyce chodzenie po drzewie AST)
        while instructions_executed < self.max_instructions_per_step:
            node = self.get_current_node()

            if node.type == 'ASSIGNMENT':
                self.execute_assignment(node)

            elif node.type == 'IF':
                # if(wyrażenie){blok}
                if self.evaluate_expression(node.condition) > 0:
                    self.enter_block(node.true_block)
                else:
                    self.skip_block()

            elif node.type == 'REDO':
                # Skok do początku obecnego bloku
                self.jump_to_block_start()
                continue  # Nie zwiększamy licznika instrukcji drastycznie, ale trzeba uważać

            elif node.type == 'FUNCTION_CALL':
                # f_n(args) kończy działanie programu w tym kroku
                func_id = node.func_id
                args = [self.evaluate_expression(arg) for arg in node.args]
                return func_id, args

            instructions_executed += 1
            self.advance_pointer()

        return 0, []  # Default IDLE jeśli program nic nie wybrał

    def evaluate_expression(self, expr_node):
        # Oblicza (X[1]+(3/X[8]))
        pass