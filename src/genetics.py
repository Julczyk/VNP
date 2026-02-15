"""
Silnik genetyczny dla programów SRAPL.

Implementuje mutacje na poziomie AST:
- Constant Jitter - zmiana wartości liczbowych o ±0.5
- Register Mutation - zmiana indeksu X[n] o ±2
- Node Swap - zamiana sąsiednich instrukcji w bloku
"""

import random
import logging
from pathlib import Path

from antlr4 import InputStream, CommonTokenStream
from antlr4.tree.Tree import TerminalNodeImpl

import sys
sys.path.insert(0, str(Path(__file__).parent / 'sraplBase'))
from sraplBase.SRAPLLexer import SRAPLLexer
from sraplBase.SRAPLParser import SRAPLParser
from sraplBase.SRAPLVisitor import SRAPLVisitor

logger = logging.getLogger('Genetics')


class SRAPLCodeGenerator(SRAPLVisitor):
    """
    Visitor konwertujący AST z powrotem do kodu SRAPL.

    Obsługuje atrybuty mutacji dodane przez GeneticsEngine:
    - _mutated_value: zmieniona wartość liczbowa
    - _mutated_index: zmieniony indeks pamięci
    - _swap_indices: para indeksów instrukcji do zamiany
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
        for stmt in statements:
            line = self.visit(stmt)
            if line:
                lines.append(line)
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
        idx = ctx.INT().getText()
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
        op = ctx.getChild(1).getText()
        return f"{left} {op} {right}"

    def visitAddSubExpr(self, ctx: SRAPLParser.AddSubExprContext) -> str:
        """Generuje dodawanie/odejmowanie a + b lub a - b."""
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText()
        return f"{left} {op} {right}"

    def visitVariableExpr(self, ctx: SRAPLParser.VariableExprContext) -> str:
        """Generuje zmienną X[i]."""
        return self.visit(ctx.memoryRef())

    def visitAtomExpr(self, ctx: SRAPLParser.AtomExprContext) -> str:
        """Generuje atom (wartość liczbową)."""
        return self.visit(ctx.value())

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

        # Mutacja wartości liczbowych
        if isinstance(ctx, SRAPLParser.ValueContext):
            if random.random() < self.mutation_rate:
                self._mutate_constant(ctx)

        # Mutacja indeksów pamięci
        elif isinstance(ctx, SRAPLParser.MemoryRefContext):
            if random.random() < self.mutation_rate:
                self._mutate_memory_index(ctx)

        # Zamiana sąsiednich instrukcji w bloku
        elif isinstance(ctx, SRAPLParser.BlockContentContext):
            if random.random() < self.mutation_rate:
                self._swap_adjacent_statements(ctx)

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
            current_index = int(mem_ref_ctx.INT().getText())
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
