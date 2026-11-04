"""
Simulador de Máquinas de Turing
Teoría de la Computación - Universidad del Valle de Guatemala

Este módulo contiene la clase principal TuringMachine que permite
simular una Máquina de Turing de una sola cinta.
"""


class SimulationResult:
    """Resultado de la simulación de una cadena en la MT."""

    def __init__(self, input_string, accepted, steps, final_tape, halted_reason=""):
        self.input_string = input_string
        self.accepted = accepted
        self.steps = steps  # Lista de descripciones instantáneas (IDs)
        self.final_tape = final_tape
        self.halted_reason = halted_reason

    def __str__(self):
        separator = "=" * 60
        result_icon = "✅ ACEPTADA" if self.accepted else "❌ RECHAZADA"
        display_input = self.input_string if self.input_string else "ε (vacía)"

        lines = [
            separator,
            f'  Cadena de entrada: "{display_input}"',
            separator,
            "  Simulación paso a paso (Descripciones Instantáneas):",
            "",
        ]

        for i, step in enumerate(self.steps):
            lines.append(f"    Paso {i}: {step}")

        lines.append("")
        lines.append(f"  Resultado: {result_icon}")
        lines.append(f"  Cinta final: {self.final_tape}")

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
        blank_symbol: Símbolo blanco de la cinta (por defecto 'B')
    """

    BLANK = "B"

    def __init__(self, states, input_alphabet, tape_alphabet,
                 initial_state, accept_states, transitions):
        self.states = states
        self.input_alphabet = input_alphabet
        self.tape_alphabet = tape_alphabet
        self.initial_state = initial_state
        self.accept_states = accept_states
        self.transitions = transitions

        # Validaciones básicas
        self._validate()

    def _validate(self):
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

        for symbol in self.input_alphabet:
            if symbol not in self.tape_alphabet:
                raise ValueError(
                    f"El símbolo de entrada '{symbol}' "
                    f"no está en el alfabeto de la cinta."
                )

    def _find_transition(self, current_state, current_symbol):
        """
        Busca una transición que coincida con el estado actual
        y el símbolo leído de la cinta.

        Retorna la transición encontrada o None si no hay transición válida.
        """
        for t in self.transitions:
            t_state = str(t["state"])
            # El campo 'read' puede ser una lista o un valor simple
            t_read = t["read"]
            if isinstance(t_read, list):
                t_read_symbol = str(t_read[0])
            else:
                t_read_symbol = str(t_read)

            if t_state == current_state and t_read_symbol == current_symbol:
                return t

        return None

    def _get_instantaneous_description(self, tape, head, state):
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
        while left_bound < head and str(tape[left_bound]) == self.BLANK:
            left_bound += 1

        # Encontrar el último símbolo no-blanco o la posición del cabezal
        while right_bound > head and str(tape[right_bound]) == self.BLANK:
            right_bound -= 1

        # Construir la descripción instantánea
        parts = []

        # Símbolos a la izquierda del cabezal
        for i in range(left_bound, head):
            parts.append(str(tape[i]))

        # Estado actual (insertado antes del símbolo bajo el cabezal)
        parts.append(state)

        # Símbolo bajo el cabezal y símbolos a la derecha
        for i in range(head, right_bound + 1):
            parts.append(str(tape[i]))

        return " ".join(parts)

    def _get_final_tape(self, tape):
        """Retorna el contenido de la cinta sin los blancos iniciales y finales."""
        # Convertir todo a string
        tape_str = [str(s) for s in tape]

        # Encontrar límites no-blancos
        left = 0
        while left < len(tape_str) and tape_str[left] == self.BLANK:
            left += 1

        right = len(tape_str) - 1
        while right >= left and tape_str[right] == self.BLANK:
            right -= 1

        if left > right:
            return self.BLANK  # Cinta vacía

        return " ".join(tape_str[left:right + 1])

    def simulate(self, input_string, max_steps=10000):
        """
        Simula la MT con la cadena de entrada proporcionada.

        Args:
            input_string: Cadena de entrada a procesar
            max_steps: Número máximo de pasos (protección contra loops infinitos)

        Returns:
            SimulationResult con el resultado de la simulación
        """
        # Inicializar la cinta
        if input_string:
            tape = [str(c) for c in input_string]
        else:
            tape = [self.BLANK]

        head = 0
        current_state = str(self.initial_state)
        steps = []

        # Registrar la configuración inicial (ID)
        initial_id = self._get_instantaneous_description(tape, head, current_state)
        steps.append(initial_id)

        for step_num in range(max_steps):
            # Leer el símbolo actual bajo el cabezal
            current_symbol = str(tape[head])

            # Verificar si estamos en un estado de aceptación
            if current_state in [str(s) for s in self.accept_states]:
                return SimulationResult(
                    input_string=input_string,
                    accepted=True,
                    steps=steps,
                    final_tape=self._get_final_tape(tape),
                    halted_reason="Se alcanzó un estado de aceptación."
                )

            # Buscar transición aplicable
            transition = self._find_transition(current_state, current_symbol)

            if transition is None:
                # No hay transición: la MT se detiene
                return SimulationResult(
                    input_string=input_string,
                    accepted=False,
                    steps=steps,
                    final_tape=self._get_final_tape(tape),
                    halted_reason=(
                        f"No se encontró transición para "
                        f"δ({current_state}, {current_symbol})."
                    )
                )

            # Aplicar la transición
            # Obtener el símbolo a escribir
            t_write = transition["write"]
            if isinstance(t_write, list):
                write_symbol = str(t_write[0])
            else:
                write_symbol = str(t_write)

            # Escribir en la cinta
            tape[head] = write_symbol

            # Obtener la dirección de movimiento
            move = str(transition["move"]).upper()

            # Obtener el nuevo estado
            new_state = str(transition["next"])

            # Mover el cabezal
            if move == "R":
                head += 1
                # Extender la cinta a la derecha si es necesario
                if head >= len(tape):
                    tape.append(self.BLANK)
            elif move == "L":
                head -= 1
                # Extender la cinta a la izquierda si es necesario
                if head < 0:
                    tape.insert(0, self.BLANK)
                    head = 0

            # Actualizar el estado
            current_state = new_state

            # Registrar la nueva descripción instantánea
            current_id = self._get_instantaneous_description(
                tape, head, current_state
            )
            steps.append(current_id)

        # Se alcanzó el límite de pasos
        return SimulationResult(
            input_string=input_string,
            accepted=False,
            steps=steps,
            final_tape=self._get_final_tape(tape),
            halted_reason=(
                f"Se alcanzó el límite de {max_steps} pasos. "
                f"Posible loop infinito."
            )
        )
