import sys
from antlr4 import *
from SRAPLLexer import SRAPLLexer
from SRAPLParser import SRAPLParser
from SRAPLVisitor import SRAPLVisitor
from config import FunctionID

# Wyjątki sterujące przepływem (nie są błędami, lecz sygnałami)
class RedoSignal(Exception):
    pass

class RestartSignal(Exception):
    pass

class ProgramFinished(Exception):
    pass

class SRAPLExecutionVisitor(SRAPLVisitor):
    def __init__(self, automaton):
        self.automaton = automaton
        self.memory = automaton.memory # Referencja do pamięci automatu

    def visitProgrammSection(self, ctx: SRAPLParser.ProgrammSectionContext):
        # Główna pętla programu (Restart Loop)
        while True:
            try:
                # Odwiedź główny blok instrukcji
                if ctx.blockContent():
                    yield from self.visit(ctx.blockContent())
                
                # Jeśli program dojdzie do końca, kończymy (zostanie zrestartowany przez Interpretera)
                break 
            except RestartSignal:
                # Obsługa RESTART - pętla while True zacznie od nowa
                continue

    def visitBlockContent(self, ctx: SRAPLParser.BlockContentContext):
        # Odwiedzanie listy instrukcji w bloku
        for statement in ctx.statement():
            yield from self.visit(statement)

    def visitBlock(self, ctx: SRAPLParser.BlockContext):
        # Obsługa bloku i instrukcji REDO
        while True:
            try:
                if ctx.blockContent():
                    yield from self.visit(ctx.blockContent())
                break # Blok wykonany poprawnie, wychodzimy z while
            except RedoSignal:
                # Złapano REDO wewnątrz tego bloku -> pętla while zaczyna od nowa
                continue

    def visitAssignment(self, ctx: SRAPLParser.AssignmentContext):
        # X[i] = expr
        mem_idx = int(ctx.memoryRef().INT().getText())
        value = self.visit(ctx.expression())
        
        # Zabezpieczenie zakresu pamięci
        if 0 <= mem_idx < len(self.memory):
            self.memory[mem_idx] = float(value)
        return None

    def visitFunctionCall(self, ctx: SRAPLParser.FunctionCallContext):
        # Parsowanie ID funkcji: f_n -> n
        func_text = ctx.FUNC_ID().getText() # "f_1"
        func_id_val = int(func_text.split('_')[1])
        
        # Ewaluacja argumentów
        args = []
        if ctx.argList():
            for expr in ctx.argList().expression():
                args.append(float(self.visit(expr)))
        
        # YIELD - Zatrzymujemy wykonanie i zwracamy akcję do Symulatora
        # Konwertujemy int na Enum, jeśli istnieje w configu, lub zostawiamy int
        try:
            enum_id = FunctionID(func_id_val)
        except ValueError:
            enum_id = func_id_val # Fallback dla nieznanych ID

        yield (enum_id, args)

    def visitIfStatement(self, ctx: SRAPLParser.IfStatementContext):
        condition = self.visit(ctx.expression())
        if condition > 0:
            yield from self.visit(ctx.block())

    def visitRedoStatement(self, ctx: SRAPLParser.RedoStatementContext):
        raise RedoSignal()

    def visitRestartStatement(self, ctx: SRAPLParser.RestartStatementContext):
        raise RestartSignal()

    # --- Ewaluacja Wyrażeń ---

    def visitAtomExpr(self, ctx: SRAPLParser.AtomExprContext):
        # Liczba
        return float(ctx.value().getText())

    def visitVariableExpr(self, ctx: SRAPLParser.VariableExprContext):
        # Zmienna X[i]
        idx = int(ctx.memoryRef().INT().getText())
        if 0 <= idx < len(self.memory):
            return self.memory[idx]
        return 0.0

    def visitParensExpr(self, ctx: SRAPLParser.ParensExprContext):
        return self.visit(ctx.expression())

    def visitPowerExpr(self, ctx: SRAPLParser.PowerExprContext):
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        try:
            return math.pow(left, right)
        except OverflowError:
            return float('inf')

    def visitMulDivExpr(self, ctx: SRAPLParser.MulDivExprContext):
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText()
        if op == '*':
            return left * right
        else:
            return left / right if right != 0 else 0.0

    def visitAddSubExpr(self, ctx: SRAPLParser.AddSubExprContext):
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText()
        if op == '+':
            return left + right
        else:
            return left - right

    # --- Pomocnicze do Visitora (domyślne zachowanie) ---
    def defaultResult(self):
        return None
        
import math

class Interpreter:
    """
    Wykonuje program automatu używając ANTLR4.
    """

    def __init__(self, program_code):
        self.program_code = program_code
        self.generator = None
        
        # Wstępne parsowanie, aby sprawdzić błędy składni (opcjonalne, ale dobre dla debugu)
        self.tree = self._parse(program_code)

    def _parse(self, code):
        input_stream = InputStream(code)
        lexer = SRAPLLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SRAPLParser(stream)
        # file -> partsSection programmSection
        return parser.file() 

    @staticmethod
    def parse_parts_specs(program_code):
        """
        Statyczna metoda parsująca sekcję $PARTS, aby zbudować robota
        przed uruchomieniem interpretera.
        Zwraca: listę floatów (skale części).
        """
        input_stream = InputStream(program_code)
        lexer = SRAPLLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SRAPLParser(stream)
        
        # Parsujemy tylko sekcję parts
        tree = parser.partsSection()
        
        # Prosty visitor lokalny do wyciągnięcia liczb
        scales = []
        if tree.floatList():
            for val in tree.floatList().value():
                scales.append(float(val.getText()))
        return scales

    def run_step(self, robot):
        """
        Uruchamia program na jeden krok symulacji.
        Zwraca ID funkcji (f_n) i argumenty.
        """
        if self.generator is None:
            # Pierwsze uruchomienie - tworzymy generator
            visitor = SRAPLExecutionVisitor(robot)
            # Zaczynamy od sekcji programu (partsSection pomijamy przy egzekucji)
            program_ctx = self.tree.programmSection()
            self.generator = visitor.visitProgrammSection(program_ctx)

        try:
            # Wznów wykonanie do następnego yield (wywołania funkcji f_n)
            func_id, args = next(self.generator)
            return func_id, args
        
        except StopIteration:
            # Program się skończył (doszedł do końca kodu bez pętli)
            # Wg specyfikacji: "loop" - zaczynamy od nowa w tym samym kroku?
            # Czy w następnym? Przyjmijmy, że resetujemy generator i próbujemy jeszcze raz.
            self.generator = None
            
            # Rekurencyjne wywołanie (ostrożnie, żeby nie zapętlić w nieskończoność 
            # jeśli program jest pusty)
            # Dla bezpieczeństwa zwracamy IDLE, a restart nastąpi w kolejnym kroku
            return FunctionID.IDLE, []
            
        except Exception as e:
            print(f"Runtime Error in automaton {robot}: {e}")
            return FunctionID.IDLE, []