"""
Silnik genetyczny dla programów SRAPL.

Implementuje mutacje na poziomie AST:
- Constant Jitter - zmiana wartości liczbowych o ±0.5
- Register Mutation - zmiana indeksu X[n] o ±2
- Node Swap - zamiana sąsiednich instrukcji w bloku
- Add Function Call - dodanie wywołania f_n(X[k], ...)
- Add Assignment - dodanie przypisania X[k] = expr
- Add Control Flow - dodanie REDO/RESTART
- Wrap With IF - opakowanie linii warunkiem IF(expr)
- Operator Mutation - zmiana operatora matematycznego
- Node Swell - rozbudowanie węzła E do (E op E')
- Delete Statement - usunięcie instrukcji lub wyrażenia
"""

import random
import logging
import copy
from pathlib import Path

from antlr4 import InputStream, CommonTokenStream
from antlr4.tree.Tree import TerminalNodeImpl

import sys
sys.path.insert(0, str(Path(__file__).parent / 'sraplBase'))
from sraplBase.SRAPLLexer import SRAPLLexer
from sraplBase.SRAPLParser import SRAPLParser
from sraplBase.SRAPLVisitor import SRAPLVisitor

logger = logging.getLogger('Genetics')

# Dostępne operatory matematyczne
MATH_OPERATORS = ['+', '-', '*', '/']

# Dostępne funkcje robotów (f_0 do f_8)
AVAILABLE_FUNCTIONS = list(range(9))


class SRAPLCodeGenerator(SRAPLVisitor):
    """
    Visitor konwertujący AST z powrotem do kodu SRAPL.

    Obsługuje atrybuty mutacji dodane przez GeneticsEngine:
    - _mutated_value: zmieniona wartość liczbowa
    - _mutated_index: zmieniony indeks pamięci
    - _swap_indices: para indeksów instrukcji do zamiany
    - _added_statements: lista instrukcji do dodania
    - _deleted_indices: zbiór indeksów instrukcji do usunięcia
    - _wrap_with_if: indeks instrukcji do opakowania IF-em
    - _mutated_operator: zmieniony operator matematyczny
    - _swelled_expression: wyrażenie rozbudowane do (E op E')
    """

    def visitFile(self, ctx: SRAPLParser.FileContext) -> str:
        """Generuje cały plik SRAPL."""
        parts = self.visit(ctx.partsSection())
        program = self.visit(ctx.programmSection())
        return f"{parts}\n{program}"

    def visitPartsSection(self, ctx: SRAPLParser.PartsSectionContext) -> str:
        """Generuje sekcję $PARTS."""
        values = self.visit(ctx.floatList())
        return f"$PARTS:\n{values};"

    def visitFloatList(self, ctx: SRAPLParser.FloatListContext) -> str:
        """Generuje listę wartości float."""
        values = []
        for val_ctx in ctx.value():
            values.append(self.visit(val_ctx))
        return ", ".join(values)

    def visitValue(self, ctx: SRAPLParser.ValueContext) -> str:
        """Generuje wartość liczbową (z możliwą mutacją)."""
        if hasattr(ctx, '_mutated_value'):
            # Użyj zmutowanej wartości
            return f"{ctx._mutated_value:.1f}"
        return ctx.getText()

    def visitProgrammSection(self, ctx: SRAPLParser.ProgrammSectionContext) -> str:
        """Generuje sekcję $PROGRAMM."""
        content = ""
        if ctx.blockContent():
            content = self.visit(ctx.blockContent())
        return f"$PROGRAMM\n{content}"

    def visitBlockContent(self, ctx: SRAPLParser.BlockContentContext) -> str:
        """Generuje zawartość bloku (lista instrukcji)."""
        statements = list(ctx.statement())

        # Obsługa zamiany instrukcji
        if hasattr(ctx, '_swap_indices'):
            i, j = ctx._swap_indices
            if 0 <= i < len(statements) and 0 <= j < len(statements):
                statements[i], statements[j] = statements[j], statements[i]

        lines = []
        deleted_indices = getattr(ctx, '_deleted_indices', set())
        wrap_with_if = getattr(ctx, '_wrap_with_if', None)

        for idx, stmt in enumerate(statements):
            # Pomiń usunięte instrukcje
            if idx in deleted_indices:
                continue

            line = self.visit(stmt)
            if line:
                # Opakuj w IF jeśli wymagane
                if wrap_with_if is not None and idx == wrap_with_if['index']:
                    condition = wrap_with_if['condition']
                    line = f"IF ({condition}) {{\n    {line}\n}}"
                lines.append(line)

        # Dodaj nowe instrukcje
        if hasattr(ctx, '_added_statements'):
            for stmt in ctx._added_statements:
                lines.append(stmt)

        return "\n".join(lines)

    def visitStatement(self, ctx) -> str:
        """Deleguje do konkretnego typu instrukcji."""
        return self.visitChildren(ctx)

    def visitBlock(self, ctx: SRAPLParser.BlockContext) -> str:
        """Generuje blok kodu { ... }."""
        content = ""
        if ctx.blockContent():
            content = self.visit(ctx.blockContent())
        # Dodaj wcięcie do zawartości bloku
        indented = "\n".join("    " + line for line in content.split("\n") if line.strip())
        return "{\n" + indented + "\n}"

    def visitAssignment(self, ctx: SRAPLParser.AssignmentContext) -> str:
        """Generuje przypisanie X[i] = expr;"""
        mem_ref = self.visit(ctx.memoryRef())
        expr = self.visit(ctx.expression())
        return f"{mem_ref} = {expr};"

    def visitFunctionCall(self, ctx: SRAPLParser.FunctionCallContext) -> str:
        """Generuje wywołanie funkcji f_n(args);"""
        func_id = ctx.FUNC_ID().getText()
        args = ""
        if ctx.argList():
            args = self.visit(ctx.argList())
        return f"{func_id}({args});"

    def visitArgList(self, ctx: SRAPLParser.ArgListContext) -> str:
        """Generuje listę argumentów."""
        args = []
        for expr in ctx.expression():
            args.append(self.visit(expr))
        return ", ".join(args)

    def visitIfStatement(self, ctx: SRAPLParser.IfStatementContext) -> str:
        """Generuje instrukcję IF(expr) { block }."""
        condition = self.visit(ctx.expression())
        block = self.visit(ctx.block())
        return f"IF ({condition}) {block}"

    def visitRedoStatement(self, ctx: SRAPLParser.RedoStatementContext) -> str:
        """Generuje REDO;"""
        return "REDO;"

    def visitRestartStatement(self, ctx: SRAPLParser.RestartStatementContext) -> str:
        """Generuje RESTART;"""
        return "RESTART;"

    def visitMemoryRef(self, ctx: SRAPLParser.MemoryRefContext) -> str:
        """Generuje odwołanie do pamięci X[i] (z możliwą mutacją indeksu)."""
        if hasattr(ctx, '_mutated_index'):
            return f"X[{ctx._mutated_index}]"
        # Obsługa zarówno INT jak i FLOAT (konwertuj float na int)
        if ctx.INT():
            idx = ctx.INT().getText()
        elif ctx.FLOAT():
            idx = str(int(round(float(ctx.FLOAT().getText()))))
        else:
            idx = "0"
        return f"X[{idx}]"

    # --- Wyrażenia ---

    def visitParensExpr(self, ctx: SRAPLParser.ParensExprContext) -> str:
        """Generuje wyrażenie w nawiasach (expr)."""
        inner = self.visit(ctx.expression())
        return f"({inner})"

    def visitPowerExpr(self, ctx: SRAPLParser.PowerExprContext) -> str:
        """Generuje potęgowanie a ** b."""
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        return f"{left} ** {right}"

    def visitMulDivExpr(self, ctx: SRAPLParser.MulDivExprContext) -> str:
        """Generuje mnożenie/dzielenie a * b lub a / b."""
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        # Użyj zmutowanego operatora jeśli istnieje
        if hasattr(ctx, '_mutated_operator'):
            op = ctx._mutated_operator
        else:
            op = ctx.getChild(1).getText()
        return f"{left} {op} {right}"

    def visitAddSubExpr(self, ctx: SRAPLParser.AddSubExprContext) -> str:
        """Generuje dodawanie/odejmowanie a + b lub a - b."""
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        # Użyj zmutowanego operatora jeśli istnieje
        if hasattr(ctx, '_mutated_operator'):
            op = ctx._mutated_operator
        else:
            op = ctx.getChild(1).getText()
        return f"{left} {op} {right}"

    def visitVariableExpr(self, ctx: SRAPLParser.VariableExprContext) -> str:
        """Generuje zmienną X[i]."""
        base = self.visit(ctx.memoryRef())
        # Obsługa "spuchniętego" wyrażenia
        if hasattr(ctx, '_swelled_expression'):
            return f"({base} {ctx._swelled_expression})"
        return base

    def visitAtomExpr(self, ctx: SRAPLParser.AtomExprContext) -> str:
        """Generuje atom (wartość liczbową)."""
        base = self.visit(ctx.value())
        # Obsługa "spuchniętego" wyrażenia
        if hasattr(ctx, '_swelled_expression'):
            return f"({base} {ctx._swelled_expression})"
        return base

    def defaultResult(self):
        return ""

    def aggregateResult(self, aggregate, nextResult):
        if nextResult:
            return nextResult
        return aggregate


class GeneticsEngine:
    """
    Silnik genetyczny operujący na AST programów SRAPL.

    Typy mutacji:
    1. Constant Jitter - zmiana wartości liczbowych o ±CONSTANT_JITTER_RANGE
    2. Register Mutation - zmiana indeksu X[n] o ±REGISTER_MUTATION_RANGE
    3. Node Swap - zamiana sąsiednich instrukcji w bloku
    4. Add Function Call - dodanie wywołania f_n(X[k], ...)
    5. Add Assignment - dodanie przypisania X[k] = expr
    6. Add Control Flow - dodanie REDO/RESTART
    7. Wrap With IF - opakowanie linii warunkiem IF(expr)
    8. Operator Mutation - zmiana operatora matematycznego
    9. Node Swell - rozbudowanie węzła E do (E op E')
    10. Delete Statement - usunięcie instrukcji
    """

    CONSTANT_JITTER_RANGE = 0.5
    REGISTER_MUTATION_RANGE = 2
    MEMORY_INDEX_MAX = 63
    MAX_MUTATION_RETRIES = 5

    def __init__(self, mutation_rate: float = 0.1):
        """
        Inicjalizuje silnik genetyczny.

        Args:
            mutation_rate: Prawdopodobieństwo mutacji dla każdego węzła (0.0-1.0)
        """
        self.mutation_rate = mutation_rate
        self._in_parts_section = False  # Flaga dla pominięcia mutacji w $PARTS

    def _parse(self, program_code: str) -> SRAPLParser.FileContext:
        """Parsuje kod SRAPL i zwraca drzewo AST."""
        input_stream = InputStream(program_code)
        lexer = SRAPLLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SRAPLParser(stream)
        return parser.file_()

    def mutate_program(self, program_code: str) -> str:
        """
        Główna metoda: mutuj program i zwróć poprawny kod SRAPL.

        Próbuje wielokrotnie (MAX_MUTATION_RETRIES razy) zastosować mutacje.
        Jeśli wszystkie próby zawiodą, zwraca oryginalny kod.

        Args:
            program_code: Kod źródłowy SRAPL do zmutowania

        Returns:
            Zmutowany kod SRAPL (lub oryginał jeśli mutacja się nie powiodła)
        """
        for attempt in range(self.MAX_MUTATION_RETRIES):
            try:
                # Parsuj kod
                tree = self._parse(program_code)

                # Aplikuj mutacje do AST
                self._mutate_ast(tree)

                # Wygeneruj kod z powrotem
                generator = SRAPLCodeGenerator()
                new_code = generator.visit(tree)

                # Walidacja: spróbuj sparsować wygenerowany kod
                self._parse(new_code)

                logger.debug(f"Mutation successful on attempt {attempt + 1}")
                return new_code

            except Exception as e:
                logger.debug(f"Mutation attempt {attempt + 1} failed: {e}")
                continue

        logger.warning("All mutation attempts failed, returning original code")
        return program_code

    def _mutate_ast(self, ctx):
        """
        Rekurencyjnie aplikuj mutacje do węzłów AST.

        Przechodzi przez drzewo i z prawdopodobieństwem mutation_rate
        aplikuje odpowiednie mutacje do różnych typów węzłów.
        """
        if ctx is None:
            return

        # Śledź czy jesteśmy w sekcji $PARTS (nie mutujemy tej sekcji)
        if isinstance(ctx, SRAPLParser.PartsSectionContext):
            self._in_parts_section = True

        if isinstance(ctx, SRAPLParser.ProgrammSectionContext):
            self._in_parts_section = False

        # Mutacja wartości liczbowych (tylko poza $PARTS)
        if isinstance(ctx, SRAPLParser.ValueContext) and not self._in_parts_section:
            if random.random() < self.mutation_rate:
                self._mutate_constant(ctx)

        # Mutacja indeksów pamięci (tylko poza $PARTS)
        elif isinstance(ctx, SRAPLParser.MemoryRefContext) and not self._in_parts_section:
            if random.random() < self.mutation_rate:
                self._mutate_memory_index(ctx)

        # Mutacje na poziomie bloku (tylko poza $PARTS)
        elif isinstance(ctx, SRAPLParser.BlockContentContext) and not self._in_parts_section:
            # Zamiana sąsiednich instrukcji
            if random.random() < self.mutation_rate:
                self._swap_adjacent_statements(ctx)
            # Dodanie nowej instrukcji
            if random.random() < self.mutation_rate:
                self._add_statement(ctx)
            # Usunięcie instrukcji
            if random.random() < self.mutation_rate:
                self._delete_statement(ctx)
            # Opakowanie instrukcji w IF
            if random.random() < self.mutation_rate:
                self._wrap_with_if(ctx)

        # Mutacja operatorów (tylko poza $PARTS)
        elif isinstance(ctx, (SRAPLParser.MulDivExprContext, SRAPLParser.AddSubExprContext)) and not self._in_parts_section:
            if random.random() < self.mutation_rate:
                self._mutate_operator(ctx)

        # Mutacja "spuchnięcia" węzła (tylko poza $PARTS)
        elif isinstance(ctx, (SRAPLParser.VariableExprContext, SRAPLParser.AtomExprContext)) and not self._in_parts_section:
            if random.random() < self.mutation_rate:
                self._swell_node(ctx)

        # Rekurencja do dzieci
        if hasattr(ctx, 'children') and ctx.children:
            for child in ctx.children:
                if not isinstance(child, TerminalNodeImpl):
                    self._mutate_ast(child)

    def _mutate_constant(self, value_ctx: SRAPLParser.ValueContext):
        """
        Mutacja stałych: dodaje szum ±CONSTANT_JITTER_RANGE.

        Args:
            value_ctx: Kontekst węzła wartości liczbowej
        """
        try:
            current_value = float(value_ctx.getText())
            jitter = random.uniform(-self.CONSTANT_JITTER_RANGE, self.CONSTANT_JITTER_RANGE)
            new_value = current_value + jitter

            # Nie pozwól na wartości ujemne dla skal części (pierwszy floatList)
            # ale pozwól na ujemne wartości w wyrażeniach programu
            value_ctx._mutated_value = new_value

            logger.debug(f"Constant mutation: {current_value} -> {new_value}")
        except ValueError:
            pass

    def _mutate_memory_index(self, mem_ref_ctx: SRAPLParser.MemoryRefContext):
        """
        Mutacja indeksu rejestru: X[n] → X[n ± REGISTER_MUTATION_RANGE].

        Args:
            mem_ref_ctx: Kontekst węzła odwołania do pamięci
        """
        try:
            # Obsługa zarówno INT jak i FLOAT
            if mem_ref_ctx.INT():
                current_index = int(mem_ref_ctx.INT().getText())
            elif mem_ref_ctx.FLOAT():
                current_index = int(round(float(mem_ref_ctx.FLOAT().getText())))
            else:
                return

            delta = random.randint(-self.REGISTER_MUTATION_RANGE, self.REGISTER_MUTATION_RANGE)
            new_index = max(0, min(self.MEMORY_INDEX_MAX, current_index + delta))

            mem_ref_ctx._mutated_index = new_index

            logger.debug(f"Register mutation: X[{current_index}] -> X[{new_index}]")
        except ValueError:
            pass

    def _swap_adjacent_statements(self, block_ctx: SRAPLParser.BlockContentContext):
        """
        Zamiana sąsiednich instrukcji w bloku.

        Args:
            block_ctx: Kontekst węzła zawartości bloku
        """
        statements = block_ctx.statement()
        if len(statements) >= 2:
            idx = random.randint(0, len(statements) - 2)
            block_ctx._swap_indices = (idx, idx + 1)

            logger.debug(f"Statement swap: indices {idx} <-> {idx + 1}")

    def _generate_random_expression(self, depth: int = 0) -> str:
        """
        Generuje losowe wyrażenie SRAPL.

        Args:
            depth: Głębokość rekurencji (dla ograniczenia złożoności)

        Returns:
            String z wyrażeniem SRAPL
        """
        max_depth = 2

        if depth >= max_depth or random.random() < 0.6:
            # Wygeneruj atom (końcowy węzeł)
            if random.random() < 0.5:
                # Stała liczbowa
                value = round(random.uniform(0.0, 10.0), 1)
                return f"{value}"
            else:
                # Odwołanie do pamięci X[k]
                idx = random.randint(0, self.MEMORY_INDEX_MAX)
                return f"X[{idx}]"
        else:
            # Wygeneruj wyrażenie binarne
            left = self._generate_random_expression(depth + 1)
            right = self._generate_random_expression(depth + 1)
            op = random.choice(MATH_OPERATORS)
            return f"({left} {op} {right})"

    def _generate_random_function_call(self) -> str:
        """
        Generuje losowe wywołanie funkcji robota.

        Returns:
            String z wywołaniem funkcji f_n(args);
        """
        func_id = random.choice(AVAILABLE_FUNCTIONS)
        num_args = random.randint(0, 3)
        args = []
        for _ in range(num_args):
            if random.random() < 0.5:
                # Użyj odwołania do pamięci
                idx = random.randint(0, self.MEMORY_INDEX_MAX)
                args.append(f"X[{idx}]")
            else:
                # Użyj stałej liczbowej
                value = round(random.uniform(0.0, 5.0), 1)
                args.append(f"{value}")

        args_str = ", ".join(args)
        return f"f_{func_id}({args_str});"

    def _generate_random_assignment(self) -> str:
        """
        Generuje losowe przypisanie do pamięci.

        Returns:
            String z przypisaniem X[k] = expr;
        """
        idx = random.randint(0, self.MEMORY_INDEX_MAX)
        expr = self._generate_random_expression()
        return f"X[{idx}] = {expr};"

    def _add_statement(self, block_ctx: SRAPLParser.BlockContentContext):
        """
        Dodaje nową instrukcję do bloku.

        Args:
            block_ctx: Kontekst węzła zawartości bloku
        """
        if not hasattr(block_ctx, '_added_statements'):
            block_ctx._added_statements = []

        # Losowy typ instrukcji
        stmt_type = random.choice(['function', 'assignment', 'redo', 'restart'])

        if stmt_type == 'function':
            stmt = self._generate_random_function_call()
        elif stmt_type == 'assignment':
            stmt = self._generate_random_assignment()
        elif stmt_type == 'redo':
            stmt = "REDO;"
        else:  # restart
            stmt = "RESTART;"

        block_ctx._added_statements.append(stmt)
        logger.debug(f"Added statement: {stmt}")

    def _delete_statement(self, block_ctx: SRAPLParser.BlockContentContext):
        """
        Usuwa instrukcję z bloku.

        Args:
            block_ctx: Kontekst węzła zawartości bloku
        """
        statements = block_ctx.statement()
        if len(statements) > 1:  # Nie usuwaj ostatniej instrukcji
            if not hasattr(block_ctx, '_deleted_indices'):
                block_ctx._deleted_indices = set()

            idx = random.randint(0, len(statements) - 1)
            block_ctx._deleted_indices.add(idx)
            logger.debug(f"Deleted statement at index: {idx}")

    def _wrap_with_if(self, block_ctx: SRAPLParser.BlockContentContext):
        """
        Opakowuje instrukcję w bloku warunkiem IF.

        Args:
            block_ctx: Kontekst węzła zawartości bloku
        """
        statements = block_ctx.statement()
        if len(statements) > 0:
            idx = random.randint(0, len(statements) - 1)
            condition = self._generate_random_expression()
            block_ctx._wrap_with_if = {'index': idx, 'condition': condition}
            logger.debug(f"Wrapped statement {idx} with IF ({condition})")

    def _mutate_operator(self, expr_ctx):
        """
        Zmienia operator matematyczny na losowy inny.

        Args:
            expr_ctx: Kontekst węzła wyrażenia (MulDivExpr lub AddSubExpr)
        """
        current_op = expr_ctx.getChild(1).getText()
        # Wybierz inny operator
        other_ops = [op for op in MATH_OPERATORS if op != current_op]
        new_op = random.choice(other_ops)
        expr_ctx._mutated_operator = new_op
        logger.debug(f"Operator mutation: {current_op} -> {new_op}")

    def _swell_node(self, node_ctx):
        """
        Rozbudowuje węzeł E do (E op E'), gdzie E' to losowy węzeł końcowy.

        Args:
            node_ctx: Kontekst węzła (VariableExpr lub AtomExpr)
        """
        op = random.choice(MATH_OPERATORS)

        # Wygeneruj losowy węzeł końcowy
        if random.random() < 0.5:
            # Stała liczbowa
            value = round(random.uniform(0.0, 10.0), 1)
            new_node = f"{value}"
        else:
            # Odwołanie do pamięci
            idx = random.randint(0, self.MEMORY_INDEX_MAX)
            new_node = f"X[{idx}]"

        node_ctx._swelled_expression = f"{op} {new_node}"
        logger.debug(f"Node swell: E -> (E {op} {new_node})")


class Mutator:
    """
    Klasa pomocnicza dla kompatybilności wstecznej.
    """

    @staticmethod
    def mutate_genome(parts_genome: list, mutation_rate: float = 0.1) -> list:
        """
        Modyfikuje listę części (zmienia skalę).

        Args:
            parts_genome: Lista krotek (PartClass, scale)
            mutation_rate: Prawdopodobieństwo mutacji każdej części

        Returns:
            Zmutowana lista genomu
        """
        mutated = []
        for part_cls, scale in parts_genome:
            if random.random() < mutation_rate:
                # Zmiana skali o ±10%
                mutation_factor = random.uniform(0.9, 1.1)
                new_scale = max(0.1, scale * mutation_factor)
                mutated.append((part_cls, new_scale))
            else:
                mutated.append((part_cls, scale))
        return mutated

    @staticmethod
    def mutate_program(program_code: str, mutation_rate: float = 0.1) -> str:
        """
        Mutuje program SRAPL.

        Args:
            program_code: Kod źródłowy SRAPL
            mutation_rate: Prawdopodobieństwo mutacji

        Returns:
            Zmutowany kod programu
        """
        engine = GeneticsEngine(mutation_rate=mutation_rate)
        return engine.mutate_program(program_code)
