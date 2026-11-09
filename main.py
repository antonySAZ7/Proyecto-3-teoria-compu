"""
Punto de entrada del Simulador de Máquinas de Turing.

Uso:
    python main.py
    python main.py mt_reconocedora.yaml
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

import yaml

from turing_machine import SimulationResult, TuringMachine

# Configurar stdout para evitar problemas de codificación en consolas Windows (cp1252)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def _scalar_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or any(type(item) not in (str, int) for item in value):
        raise ValueError(f"'{field}' debe ser una lista de cadenas o enteros.")
    return [str(item) for item in value]


def _compile_register_rules(
    states: list[str],
    tape_alphabet: list[str],
    initial_state: str,
    accept_states: list[str],
    transitions: list[dict[str, object]],
) -> tuple[list[str], str, list[str], list[dict[str, object]]]:
    """Convierte la notación del enunciado a estados de la forma [q, memoria]."""
    declared_states = set(states)
    final_states = set(accept_states)
    if initial_state not in declared_states or not final_states <= declared_states:
        raise ValueError("Los estados inicial y finales deben estar declarados en 'states'.")

    blank = TuringMachine.BLANK
    composite_states = {f"[{state},{blank}]": state for state in states}
    alphabet = set(tape_alphabet)
    compiled: list[dict[str, object]] = []

    for number, rule in enumerate(transitions, 1):
        read = _scalar_list(rule.get("read"), f"read de la transición {number}")
        write = _scalar_list(rule.get("write"), f"write de la transición {number}")
        if len(read) != 2 or len(write) != 2:
            raise ValueError(
                f"Transición {number}: la notación con memoria exige dos símbolos "
                "tanto en 'read' como en 'write' en todas las reglas."
            )
        if not alphabet.issuperset(read + write):
            raise ValueError(f"Transición {number}: los símbolos deben estar en el alfabeto de cinta.")

        state, next_state = rule.get("state"), rule.get("next")
        if type(state) not in (str, int) or type(next_state) not in (str, int):
            raise ValueError(f"Transición {number}: 'state' y 'next' deben identificar estados.")
        state_name, next_name = str(state), str(next_state)
        if state_name not in declared_states or next_name not in declared_states:
            raise ValueError(f"Transición {number}: la regla usa un estado sin declarar.")

        # δ([q, memoria], leído) = ([q', memoria nueva], escrito, dirección).
        tape_read, memory = read
        next_memory, tape_write = write
        source = f"[{state_name},{memory}]"
        target = f"[{next_name},{next_memory}]"
        composite_states[source] = state_name
        composite_states[target] = next_name
        compiled.append(
            {"state": source, "read": tape_read, "write": tape_write,
             "move": rule.get("move"), "next": target}
        )

    return (
        list(composite_states),
        f"[{initial_state},{blank}]",
        [name for name, state in composite_states.items() if state in final_states],
        compiled,
    )


def parse_yaml(filepath: str) -> tuple[TuringMachine, list[str]]:
    """Lee el YAML y construye la máquina antes de presentar sus reglas."""
    with open(filepath, "r", encoding="utf-8") as source:
        data: object = yaml.safe_load(source)

    if not isinstance(data, dict) or not isinstance(data.get("mt"), dict):
        raise ValueError("El YAML debe contener una sección 'mt' con la configuración.")

    mt_config = data["mt"]
    for field in (
        "states", "input_alphabet", "tape_alphabet",
        "initial_state", "accept_states", "transitions",
    ):
        if field not in mt_config:
            raise ValueError(f"Falta el campo requerido '{field}' en 'mt'.")

    initial_value = mt_config["initial_state"]
    if type(initial_value) not in (str, int):
        raise ValueError("'initial_state' debe identificar un estado.")
    initial_state = str(initial_value)
    transitions = mt_config["transitions"]
    if not isinstance(transitions, list) or not all(isinstance(rule, dict) for rule in transitions):
        raise ValueError("'transitions' debe ser una lista de reglas.")

    if "inputs" in data and "inputs" in mt_config:
        raise ValueError("Declara 'inputs' una sola vez, en la raíz del YAML o dentro de 'mt'.")
    inputs = _scalar_list(data.get("inputs", mt_config.get("inputs", [])), "inputs")
    states = _scalar_list(mt_config["states"], "states")
    tape_alphabet = _scalar_list(mt_config["tape_alphabet"], "tape_alphabet")
    accept_states = _scalar_list(mt_config["accept_states"], "accept_states")

    if any(
        isinstance(value, list) and len(value) == 2
        for rule in transitions
        for value in (rule.get("read"), rule.get("write"))
    ):
        states, initial_state, accept_states, transitions = _compile_register_rules(
            states, tape_alphabet, initial_state, accept_states, transitions
        )

    machine = TuringMachine(
        states=states,
        input_alphabet=_scalar_list(mt_config["input_alphabet"], "input_alphabet"),
        tape_alphabet=tape_alphabet,
        initial_state=initial_state,
        accept_states=accept_states,
        transitions=transitions,
    )
    return machine, inputs


def print_header(machine: TuringMachine) -> None:
    """Imprime la información de la MT configurada."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + "  SIMULADOR DE MÁQUINAS DE TURING".center(58) + "║")
    print("║" + "  Teoría de la Computación - UVG".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("  Configuración de la MT:")
    rules = machine.transition_rules
    print(f"    Estados:           {machine.states}")
    print(f"    Alfabeto entrada:  {machine.input_alphabet}")
    print(f"    Alfabeto cinta:    {machine.tape_alphabet}")
    print(f"    Estado inicial:    {machine.initial_state}")
    print(f"    Estados aceptación:{machine.accept_states}")
    print(f"    Transiciones:      {len(rules)} definidas")
    print()

    # Mostrar las funciones de transición
    print("  Funciones de transición:")
    for rule in rules:
        print(f"    δ({rule.state}, {rule.read}) = ({rule.next_state}, {rule.write}, {rule.move})")

    print()
    print("-" * 60)


def print_results(machine: TuringMachine, inputs: Sequence[str], max_steps: int) -> None:
    """Simula todas las entradas y muestra sus trazas y el resumen."""
    accepted_count = 0
    rejected_count = 0
    limited_count = 0

    for input_str in inputs:
        result = machine.simulate(input_str, max_steps=max_steps)
        print(result)

        if result.accepted:
            accepted_count += 1
        elif result.limit_reached:
            limited_count += 1
        else:
            rejected_count += 1

    # Resumen final
    print()
    print("─" * 60)
    print("  RESUMEN DE RESULTADOS")
    print("─" * 60)
    print(f"    Total de cadenas:  {len(inputs)}")
    print(f"    Aceptadas:         {accepted_count}")
    print(f"    Rechazadas:        {rejected_count}")
    print(f"    Sin veredicto:     {limited_count}")
    print("─" * 60)
    print()


@contextmanager
def _trace_key_reader() -> Iterator[Callable[[], str]]:
    """Lee teclas al instante en una terminal y líneas si se redirige stdin."""
    if not sys.stdin.isatty():
        yield input
        return

    if os.name == "nt":
        import msvcrt

        def read_windows_key() -> str:
            key = msvcrt.getwch()
            if key in ("\x00", "\xe0"):
                msvcrt.getwch()
                return "\x00"
            return key

        yield read_windows_key
        return

    import termios
    import tty

    descriptor = sys.stdin.fileno()
    original_settings = termios.tcgetattr(descriptor)

    def read_terminal_key() -> str:
        data = os.read(descriptor, 1)
        if not data:
            raise EOFError
        return chr(data[0])

    try:
        tty.setcbreak(descriptor, termios.TCSANOW)
        yield read_terminal_key
    finally:
        termios.tcsetattr(descriptor, termios.TCSANOW, original_settings)


def _trace_choice(read_key: Callable[[], str]) -> str:
    while True:
        print("  Siguiente paso [Espacio/Enter/T/V]: ", end="", flush=True)
        key = read_key()
        print()
        if key in ("\x04", "\x1a"):
            raise EOFError
        if key in ("", " ", "\r", "\n"):
            return ""
        if key.lower() in ("t", "v"):
            return key.lower()
        print("  Opción inválida. Usa Espacio, Enter, T o V.")


def _review_case(result: SimulationResult) -> None:
    """Muestra un caso con la opción de avanzar una transición a la vez."""
    if not result.applied_transitions:
        print(result)
        return

    print(result.trace_header())
    print("  Espacio o Enter avanza un paso, T muestra el resto y V vuelve a los casos.")
    steps = result.trace_steps()
    print(next(steps))
    with _trace_key_reader() as read_key:
        for step in steps:
            choice = _trace_choice(read_key)
            if choice == "v":
                return
            print(step)
            if choice == "t":
                for remaining_step in steps:
                    print(remaining_step)
                break
    print(result.trace_outcome())


def _machine_menu(
    title: str, machine: TuringMachine, inputs: list[str], max_steps: int
) -> None:
    cases = {str(number): word for number, word in enumerate(inputs, 1)}
    while True:
        print(f"\n{title}")
        if not cases:
            print("  El archivo no trae casos predefinidos.")
        for number, word in cases.items():
            print(f"  {number}. Simular {word!r}" if word else f"  {number}. Simular ε (vacía)")
        if cases:
            print("  T. Ejecutar todos los casos")
        print("  P. Probar una cadena propia")
        print("  R. Consultar estados y reglas")
        print("  0. Volver al menú principal")
        choice = input("Elige una opción: ").strip().lower()

        if choice == "0":
            return
        if choice == "t" and cases:
            print_results(machine, inputs, max_steps)
        elif choice == "r":
            print_header(machine)
        elif choice == "p":
            alphabet = ", ".join(map(repr, machine.input_alphabet)) or "vacío"
            word = input(f"Alfabeto de entrada ({alphabet}). Escribe la cadena (Enter para ε): ")
            _review_case(machine.simulate(word, max_steps=max_steps))
        elif choice in cases:
            _review_case(machine.simulate(cases[choice], max_steps=max_steps))
        else:
            print("Opción inválida. Elige una de las opciones del menú.")


def _run_menu(max_steps: int) -> None:
    directory = Path(__file__).resolve().parent
    examples = {
        "1": ("Reconocedora de aⁿbⁿcⁿ (n ≥ 1)", directory / "mt_reconocedora.yaml"),
        "2": ("Alteradora que invierte cadenas", directory / "mt_alteradora.yaml"),
    }
    while True:
        print("\nSIMULADOR DE MÁQUINAS DE TURING")
        for number, (title, _) in examples.items():
            print(f"  {number}. {title}")
        print("  3. Abrir otro archivo YAML")
        print("  0. Salir")
        choice = input("Elige una opción: ").strip()

        if choice == "0":
            return
        if choice in examples:
            title, path = examples[choice]
        elif choice == "3":
            filename = input("Ruta del archivo YAML (Enter para volver): ").strip()
            if not filename:
                continue
            path = Path(filename)
            title = path.name
        else:
            print("Opción inválida. Elige una de las opciones del menú.")
            continue

        try:
            machine, inputs = parse_yaml(str(path))
        except (OSError, ValueError, yaml.YAMLError) as error:
            print(f"Error en la configuración de la MT: {error}", file=sys.stderr)
            continue
        _machine_menu(title, machine, inputs, max_steps)


def main() -> int:
    """Abre el menú o ejecuta directamente el YAML indicado."""
    parser = argparse.ArgumentParser(description="Simulador de Máquinas de Turing")
    parser.add_argument(
        "archivo",
        nargs="?",
        help="Ruta a un archivo YAML. Sin ruta se abre el menú interactivo.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10000,
        help="Número máximo de pasos por simulación (por defecto, 10000)",
    )

    args = parser.parse_args()
    if args.max_steps < 0:
        parser.error("--max-steps debe ser mayor o igual a cero.")

    if args.archivo is None:
        try:
            _run_menu(args.max_steps)
        except EOFError:
            print()
        except KeyboardInterrupt:
            print()
            return 130
        return 0

    try:
        machine, inputs = parse_yaml(args.archivo)
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"Error en la configuración de la MT: {error}", file=sys.stderr)
        return 1

    print_header(machine)
    if not inputs:
        print("Advertencia: No se encontraron cadenas de entrada en el archivo.")
    print_results(machine, inputs, args.max_steps)
    return 0


if __name__ == "__main__":
    sys.exit(main())
