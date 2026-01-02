import sys
from .io import VarphiIO, DebugView
from .model import State, TuringMachine


def main(k: int, initial_state: State, debug: bool) -> None:
    io = VarphiIO.from_stdin()
    tm = TuringMachine(k, io.tapes, initial_state)
    time_complexity = 1

    # Define a separator line
    SEPARATOR = "—" * 60

    while tm.peek():
        if debug:
            # Print a visual delimiter and the current step number
            print(f"\n{SEPARATOR}", file=sys.stderr)
            print(f"STEP {time_complexity} [State: {tm.state.name}]", file=sys.stderr)
            print(f"{SEPARATOR}", file=sys.stderr)

            # Print the machine state
            print(DebugView(tm), file=sys.stderr)

            # Distinct prompt for user action
            try:
                input("\n>> Press ENTER to step forward...")
            except (KeyboardInterrupt, EOFError):
                print("\nInterrupted.", file=sys.stderr)
                return

        tm.step()
        time_complexity += 1

    if sys.stdout.isatty():
        print(f"\n{SEPARATOR}", file=sys.stderr)
        print(f"HALTED at state '{tm.state.name}'", file=sys.stderr)
        print(f"Time complexity: {time_complexity} steps", file=sys.stderr)
        print(
            f"Space complexity: {sum(head.space_complexity() for head in tm.heads)} cells visited",
            file=sys.stderr,
        )

    VarphiIO(tm.tapes).print()
