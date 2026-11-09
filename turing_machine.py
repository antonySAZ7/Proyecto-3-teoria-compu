"""
Simulador de Máquinas de Turing
Teoría de la Computación - Universidad del Valle de Guatemala

Este módulo contiene la clase principal TuringMachine que permite
simular una Máquina de Turing de una sola cinta.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class Transition:
    """Regla determinista para una celda de la cinta."""

    state: str
    read: str
    write: str
    move: str
    next_state: str


class SimulationResult:
    """Resultado de la simulación de una cadena en la MT."""

    def __init__(
        self,
        input_string: str,
        accepted: bool,
        steps: list[str],
        final_tape: str,
        halted_reason: str = "",
        *,
        limit_reached: bool = False,
        applied_transitions: Sequence[Transition] = (),
    ) -> None:
        self.input_string = input_string
        self.accepted = accepted
        self.steps = steps  # Lista de descripciones instantáneas (IDs)
        self.final_tape = final_tape
        self.halted_reason = halted_reason
        self.limit_reached = limit_reached
        self.applied_transitions = applied_transitions

    def __str__(self) -> str:
        return "\n".join((self.trace_header(), *self.trace_steps(), self.trace_outcome()))

    def trace_header(self) -> str:
        separator = "=" * 60
        display_input = self.input_string if self.input_string else "ε (vacía)"
        return "\n".join((
            separator,
            f'  Cadena de entrada: "{display_input}"',
            separator,
            "  Simulación paso a paso (Descripciones Instantáneas):",
            "  En cada paso, el estado aparece justo antes del símbolo bajo el cabezal.",
            "  B representa una celda en blanco.",
            "",
        ))

    def trace_steps(self) -> Iterator[str]:
        for number, description in enumerate(self.steps):
            step = f"    Paso {number}: {description}"
            if 0 < number <= len(self.applied_transitions):
                rule = self.applied_transitions[number - 1]
                direction = "derecha" if rule.move == "R" else "izquierda"
                yield (
                    f"      En {rule.state} lee {rule.read!r}, escribe {rule.write!r}, "
                    f"mueve el cabezal a la {direction} ({rule.move}) y pasa a {rule.next_state}.\n"
                    f"{step}"
                )
            else:
                yield step

    def trace_outcome(self) -> str:
        separator = "=" * 60
        if self.limit_reached:
            verdict = "SIN VEREDICTO (LÍMITE DE PASOS)"
        else:
            verdict = "✅ ACEPTADA" if self.accepted else "❌ RECHAZADA"
        lines = [
            "",
            f"  Resultado: {verdict}",
            f"  Cinta final: {self.final_tape}",
        ]
        if self.halted_reason:
            lines.append(f"  Razón: {self.halted_reason}")

        lines.append(separator)
        return "\n".join(lines)


class TuringMachine:
    """
    Simulador de Máquina de Turing de una sola cinta.

    Atributos:
        states: Lista de estados de la MT
        input_alphabet: Alfabeto de entrada
        tape_alphabet: Alfabeto de la cinta (incluye al de entrada)
        initial_state: Estado inicial
        accept_states: Lista de estados de aceptación
        transitions: Lista de funciones de transición
        BLANK: Símbolo blanco de la cinta ('B')
    """

    BLANK = "B"

    def __init__(
        self,
        states: Sequence[str | int],
        input_alphabet: Sequence[str | int],
        tape_alphabet: Sequence[str | int],
        initial_state: str | int,
        accept_states: Sequence[str | int],
        transitions: Sequence[Mapping[str, object]],
    ) -> None:
        self.states = [str(state) for state in states]
        self.input_alphabet = [str(symbol) for symbol in input_alphabet]
        self.tape_alphabet = [str(symbol) for symbol in tape_alphabet]
        self.initial_state = str(initial_state)
        self.accept_states = [str(state) for state in accept_states]
        self.transitions = transitions
        self._input_symbols = frozenset(self.input_alphabet)
        self._accepting_states = frozenset(self.accept_states)

        self._validate()
        self._transition_table = self._index_transitions()

    def _validate(self) -> None:
        """Valida la configuración de la MT."""
        if self.initial_state not in self.states:
            raise ValueError(
                f"El estado inicial '{self.initial_state}' "
                f"no está en la lista de estados."
            )

        for state in self.accept_states:
            if state not in self.states:
                raise ValueError(
                    f"El estado de aceptación '{state}' "
                    f"no está en la lista de estados."
                )

        if self.BLANK not in self.tape_alphabet or self.BLANK in self._input_symbols:
            raise ValueError(
                f"El blanco '{self.BLANK}' debe pertenecer solo al alfabeto de la cinta."
            )

        for symbol in self.tape_alphabet:
            if len(symbol) != 1:
                raise ValueError(f"Cada símbolo de cinta debe ser un solo carácter: {symbol!r}.")

        for symbol in self.input_alphabet:
            if symbol not in self.tape_alphabet:
                raise ValueError(
                    f"El símbolo de entrada '{symbol}' "
                    f"no está en el alfabeto de la cinta."
                )

    def _transition_symbol(self, value: object, field: str) -> str:
        if isinstance(value, list):
            if len(value) != 1:
                raise ValueError(f"'{field}' debe indicar un símbolo para una sola celda.")
            value = value[0]
        if type(value) not in (str, int) or str(value) not in self.tape_alphabet:
            raise ValueError(f"'{field}' contiene un símbolo ajeno al alfabeto de cinta: {value!r}.")
        return str(value)

    def _index_transitions(self) -> dict[tuple[str, str], Transition]:
        table: dict[tuple[str, str], Transition] = {}
        for number, rule in enumerate(self.transitions, 1):
            try:
                if type(rule["state"]) not in (str, int) or type(rule["next"]) not in (str, int):
                    raise ValueError("'state' y 'next' deben identificar estados.")
                state, next_state = str(rule["state"]), str(rule["next"])
                if state not in self.states or next_state not in self.states:
                    raise ValueError(f"La regla usa un estado sin declarar: {state!r} → {next_state!r}.")
                read = self._transition_symbol(rule["read"], "read")
                write = self._transition_symbol(rule["write"], "write")
                move = str(rule["move"]).upper()
                if move not in ("L", "R"):
                    raise ValueError("'move' debe ser L o R.")
                key = (state, read)
                if key in table:
                    raise ValueError(f"δ({state}, {read}) ya tiene una regla.")
                table[key] = Transition(state, read, write, move, next_state)
            except KeyError as error:
                raise ValueError(f"Transición {number}: falta el campo {error.args[0]!r}.") from error
            except ValueError as error:
                raise ValueError(f"Transición {number}: {error}") from error
        return table

    @property
    def transition_rules(self) -> tuple[Transition, ...]:
        return tuple(self._transition_table.values())

    def _get_instantaneous_description(self, tape: list[str], head: int, state: str) -> str:
        """
        Genera la descripción instantánea (ID) de la configuración actual.

        Formato: símbolos_izq estado símbolo_actual símbolos_der
        Ejemplo: a b q2 c d

        La ID muestra el contenido de la cinta con el estado insertado
        justo antes del símbolo que el cabezal está leyendo.
        """
        # Determinar los límites visibles de la cinta (recortar blancos innecesarios)
        left_bound = 0
        right_bound = len(tape) - 1

        # Encontrar el primer símbolo no-blanco o la posición del cabezal
        while left_bound < head and tape[left_bound] == self.BLANK:
            left_bound += 1

        # Encontrar el último símbolo no-blanco o la posición del cabezal
        while right_bound > head and tape[right_bound] == self.BLANK:
            right_bound -= 1

        return " ".join([*tape[left_bound:head], state, *tape[head:right_bound + 1]])

    def _get_final_tape(self, tape: list[str]) -> str:
        """Retorna el contenido de la cinta sin los blancos iniciales y finales."""
        # Encontrar límites no-blancos
        left = 0
        while left < len(tape) and tape[left] == self.BLANK:
            left += 1

        right = len(tape) - 1
        while right >= left and tape[right] == self.BLANK:
            right -= 1

        if left > right:
            return self.BLANK  # Cinta vacía

        return " ".join(tape[left:right + 1])

    def simulate(self, input_string: str, max_steps: int = 10000) -> SimulationResult:
        """
        Simula la MT con la cadena de entrada proporcionada.

        Args:
            input_string: Cadena de entrada a procesar
            max_steps: Número máximo de pasos (protección contra loops infinitos)

        Returns:
            SimulationResult con el resultado de la simulación
        """
        if max_steps < 0:
            raise ValueError("El límite de pasos debe ser mayor o igual a cero.")
        tape = list(input_string) or [self.BLANK]
        head = 0
        current_state = self.initial_state
        steps = [self._get_instantaneous_description(tape, head, current_state)]
        invalid_symbols = sorted(set(input_string) - self._input_symbols)
        if invalid_symbols:
            symbols = ", ".join(map(repr, invalid_symbols))
            return SimulationResult(
                input_string, False, steps, self._get_final_tape(tape),
                f"Símbolos ajenos al alfabeto de entrada: {symbols}.",
            )

        applied_transitions: list[Transition] = []
        limit_reached = False
        while current_state not in self._accepting_states:
            current_symbol = tape[head]
            transition = self._transition_table.get((current_state, current_symbol))
            if transition is None:
                reason = (
                    f"No hay una transición para δ({current_state}, {current_symbol}). "
                    f"La máquina se bloqueó en {current_state}, que no es un estado de aceptación."
                )
                break
            if len(applied_transitions) >= max_steps:
                limit_reached = True
                reason = (
                    f"Se alcanzó el límite de {max_steps} pasos en {current_state} "
                    "y aún hay una transición disponible."
                )
                break

            tape[head] = transition.write
            if transition.move == "R":
                head += 1
                # Extender la cinta a la derecha si es necesario
                if head >= len(tape):
                    tape.append(self.BLANK)
            else:
                head -= 1
                # Extender la cinta a la izquierda si es necesario
                if head < 0:
                    tape.insert(0, self.BLANK)
                    head = 0

            current_state = transition.next_state
            applied_transitions.append(transition)
            steps.append(self._get_instantaneous_description(tape, head, current_state))
        else:
            reason = f"Se alcanzó {current_state}, un estado de aceptación."

        return SimulationResult(
            input_string=input_string,
            accepted=current_state in self._accepting_states,
            steps=steps,
            final_tape=self._get_final_tape(tape),
            halted_reason=reason,
            limit_reached=limit_reached,
            applied_transitions=applied_transitions,
        )
