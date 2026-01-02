from typing import List, Set, Optional
from varphi_devkit import VarphiCompiler, VarphiTransition, VarphiSyntaxError

# UPDATED TEMPLATE: Imports from the new 'varphi_python.lib' location
TEMPLATE = """\
from varphi_python.lib import State, Instruction, main

# --- State Definitions ---
{state_definitions}

# --- Instruction Definitions ---
{instruction_definitions}

# --- Runtime Setup ---
initial_state = {initial_state}
k = {num_tapes}
debug_mode = {debug_mode}

if __name__ == "__main__":
    main(k, initial_state, debug_mode)
"""


class VarphiToPythonCompiler(VarphiCompiler):
    _initial_state: Optional[str]
    _seen_states: Set[str]
    _instructions_code: List[str]
    _number_of_tapes: Optional[int]
    debug_mode: bool

    def __init__(self):
        super().__init__()  # Good practice to call super
        self._initial_state = None
        self._seen_states = set()
        self._instructions_code = []
        self._number_of_tapes = None
        self.debug_mode = False

    def toggle_debug(self):
        self.debug_mode = not self.debug_mode

    def handle_transition(self, t: VarphiTransition):
        if self._number_of_tapes is None:
            self._number_of_tapes = len(t.read_symbols)
        elif len(t.read_symbols) != self._number_of_tapes:
            raise VarphiSyntaxError("Tape count mismatch.", t.line_number, 0)

        self._seen_states.add(t.current_state)
        self._seen_states.add(t.next_state)
        if self._initial_state is None:
            self._initial_state = t.current_state

        # Quote symbols for Python output
        read_str = "(" + ", ".join(f"'{s}'" for s in t.read_symbols)
        read_str += ",)" if len(t.read_symbols) == 1 else ")"

        write_str = "(" + ", ".join(f"'{s}'" for s in t.write_symbols)
        write_str += ",)" if len(t.write_symbols) == 1 else ")"

        code = (
            f"{t.current_state}.add_instruction(\n"
            f"    read_symbols={read_str},\n"
            f"    instruction=Instruction(\n"
            f"    next_state={t.next_state},\n"
            f"    write_symbols={write_str},\n"
            f"    shift_directions={t.shift_directions},\n"
            f"    line_number={t.line_number}\n"
            f"))\n"
        )
        self._instructions_code.append(code)

    def generate_compiled_program(self) -> str:
        state_defs = "\n".join(
            f"{name} = State('{name}')" for name in self._seen_states
        )
        instr_defs = "\n".join(self._instructions_code)

        return TEMPLATE.format(
            state_definitions=state_defs,
            instruction_definitions=instr_defs,
            initial_state=self._initial_state,
            num_tapes=self._number_of_tapes,
            debug_mode=self.debug_mode,
        )
