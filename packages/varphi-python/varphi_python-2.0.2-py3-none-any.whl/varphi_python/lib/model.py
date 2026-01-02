from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Iterable, Set
import random
from collections import defaultdict

from varphi_devkit import BLANK, LEFT, RIGHT


@dataclass(frozen=True)
class Instruction:
    """
    Runtime representation of the 'action' part of a transition.
    The compiler's VarphiTransition is split: 'read' goes to Rule, 'action' goes here.
    """

    next_state: State
    write_symbols: tuple[str, ...]
    shift_directions: tuple[str, ...]
    line_number: int


@dataclass
class Rule:
    """A single transition rule compiled into a State."""

    pattern: tuple[str, ...]
    instruction: Instruction
    total_vars: int
    unique_vars: int


class State:
    name: str
    rules: list[Rule]

    def __init__(self, name: str) -> None:
        self.name = name
        self.rules = []

    def add_instruction(
        self, read_symbols: tuple[str, ...], instruction: Instruction
    ) -> None:
        total_vars = sum(1 for s in read_symbols if s.startswith("$"))
        unique_vars = len(set(s for s in read_symbols if s.startswith("$")))

        self.rules.append(
            Rule(
                pattern=read_symbols,
                instruction=instruction,
                total_vars=total_vars,
                unique_vars=unique_vars,
            )
        )

    def get_instruction(
        self, tape_readings: tuple[str, ...]
    ) -> Optional[Tuple[Instruction, Dict[str, str]]]:
        candidates = []

        for rule in self.rules:
            bindings = self._check_match(rule.pattern, tape_readings)

            if bindings is not None:
                # Append (Rule, Bindings, SpecificityScore)
                candidates.append((rule, bindings, (rule.total_vars, rule.unique_vars)))

        if not candidates:
            return None

        # Find the lowest (best) score
        # More variables give a higher (worse score)
        # Unique variables are used to break ties; the less unique variables, the better, since the rule is more specific in that case; e.g., ($1, $2) is less specific than ($1, $1)
        best_score = min(c[2] for c in candidates)

        # Filter for only the best candidates
        best_candidates = [c for c in candidates if c[2] == best_score]

        # Nondeterministically select a candidate
        chosen = random.choice(best_candidates)
        return chosen[0].instruction, chosen[1]

    def _check_match(
        self, pattern: tuple[str, ...], readings: tuple[str, ...]
    ) -> Optional[Dict[str, str]]:
        """Checks match. Relies on compiler guarantees for length consistency."""
        bindings = {}

        for p_sym, r_sym in zip(pattern, readings):
            if p_sym.startswith("$"):
                if p_sym not in bindings:
                    bindings[p_sym] = r_sym
                elif bindings[p_sym] != r_sym:
                    # Variable constraint violation (e.g. $1 must be 'a', found 'b')
                    return None
            elif p_sym != r_sym:
                # Literal mismatch
                return None

        return bindings

    def __repr__(self) -> str:
        return f"State({self.name})"


class Tape:
    _tape: defaultdict[int, str]
    _min_idx: Optional[int]
    _max_idx: Optional[int]

    def __init__(self, initial_values: Iterable[str]) -> None:
        self._tape = defaultdict(lambda: BLANK)
        self._min_idx = None
        self._max_idx = None

        for i, char in enumerate(initial_values):
            self[i] = char

    def __getitem__(self, index: int) -> str:
        self._update_bounds(index)
        return self._tape[index]

    def __setitem__(self, index: int, value: str) -> None:
        self._update_bounds(index)
        self._tape[index] = value

    def _update_bounds(self, index: int) -> None:
        if self._min_idx is None or self._max_idx is None:
            self._min_idx = index
            self._max_idx = index
        else:
            self._max_idx = max(self._max_idx, index)
            self._min_idx = min(self._min_idx, index)

    def to_string(self) -> str:
        if self._min_idx is None or self._max_idx is None:
            return ""
        return "".join(self._tape[i] for i in range(self._min_idx, self._max_idx + 1))

    @property
    def is_empty(self) -> bool:
        return self._min_idx is None


class Head:
    tape: Tape
    index: int
    user_input_cell_range: Optional[tuple[int, int]]
    new_accessed_cells: Set[int]

    def __init__(self, tape: Tape) -> None:
        self.tape = tape
        self.index = 0
        self.new_accessed_cells = set()

        if tape.is_empty:
            self.user_input_cell_range = None
        else:
            self.user_input_cell_range = (tape._min_idx, tape._max_idx)

    def move(self, direction: str) -> None:
        if direction == LEFT:
            self.index -= 1
        elif direction == RIGHT:
            self.index += 1

    def read(self) -> str:
        self._check_access()
        return self.tape[self.index]

    def write(self, value: str) -> None:
        self._check_access()
        self.tape[self.index] = value

    def _check_access(self):
        if self.user_input_cell_range is None:
            self.new_accessed_cells.add(self.index)
        else:
            start, end = self.user_input_cell_range
            if self.index < start or self.index > end:
                self.new_accessed_cells.add(self.index)

    def space_complexity(self) -> int:
        return len(self.new_accessed_cells)


class TuringMachine:
    tapes: tuple[Tape, ...]
    heads: tuple[Head, ...]
    state: State
    _next_instruction: Optional[Instruction]
    _current_bindings: dict[str, str]

    def __init__(self, k: int, tapes: tuple[Tape, ...], initial_state: State) -> None:
        self.tapes = tapes
        # Pad tapes to k if necessary
        while len(self.tapes) < k:
            self.tapes += (Tape([]),)

        self.heads = tuple(Head(t) for t in self.tapes[:k])
        self.state = initial_state
        self._next_instruction = None
        self._current_bindings = {}

    def peek(self) -> bool:
        """
        Determines the next move without executing it.
        Returns False if the machine halts (no valid transition).
        """
        reads = tuple(h.read() for h in self.heads)
        result = self.state.get_instruction(reads)

        if result is None:
            self._next_instruction = None
            self._current_bindings = {}
            return False

        self._next_instruction, self._current_bindings = result
        return True

    def step(self) -> None:
        """Executes the move determined by peek()."""
        instr = self._next_instruction
        bindings = self._current_bindings

        if instr is None:
            return

        self.state = instr.next_state

        for i, head in enumerate(self.heads):
            sym = instr.write_symbols[i]
            val_to_write = sym
            if sym.startswith("$"):
                val_to_write = bindings[sym]
            head.write(val_to_write)
            head.move(instr.shift_directions[i])
