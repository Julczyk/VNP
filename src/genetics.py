import random

class Mutator:
    @staticmethod
    def mutate_genome(parts_genome):
        """
        Modyfikuje listę części (dodaje, usuwa, zmienia skalę).
        """
        if random.random() < 0.1:
            # Zmiana skali losowej części
            idx = random.randrange(len(parts_genome))
            part_cls, scale = parts_genome[idx]
            new_scale = scale * random.uniform(0.9, 1.1)
            parts_genome[idx] = (part_cls, new_scale)
        return parts_genome

    @staticmethod
    def mutate_program(program_ast):
        """
        Modyfikuje drzewo programu (zmienia stałe, operatory, lub podmienia poddrzewa).
        Najlepiej, żeby każdy obiekt AST miał metodę `mutate()` do losowej mutacji siebie samego.
        """
        # To jest trudne, wymaga operacji na AST
        pass