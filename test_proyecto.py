"""Pruebas del simulador, las dos máquinas y la interfaz de consola."""

from __future__ import annotations

import itertools
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from main import parse_yaml
from turing_machine import TuringMachine


ROOT = Path(__file__).resolve().parent
ENUNCIADO_YAML = """\
mt:
  states: [q0, q1, q2, qf]
  input_alphabet: [a, b]
  tape_alphabet: [a, b, B, X, Y]
  initial_state: q0
  accept_states: [qf]
  transitions:
    - state: q0
      read: [a, B]
      write: [a, B]
      move: R
      next: q1
    - state: q0
      read: [b, B]
      write: [b, B]
      move: R
      next: q1
  inputs:
    - "aabb"
    - "ab"
    - "aaabbb"
"""


def run_cli(*arguments: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(ROOT / "main.py"), *arguments],
        cwd=ROOT,
        input=input_text,
        capture_output=True,
        encoding="utf-8",
        timeout=10,
    )


class DemoTests(unittest.TestCase):
    def test_recognizer_against_language_definition(self) -> None:
        machine, _ = parse_yaml(str(ROOT / "mt_reconocedora.yaml"))
        for length in range(10):
            for symbols in itertools.product("abc", repeat=length):
                word = "".join(symbols)
                expected = (
                    re.fullmatch(r"a+b+c+", word) is not None
                    and word.count("a") == word.count("b") == word.count("c")
                )
                result = machine.simulate(word)
                self.assertFalse(result.limit_reached, word)
                self.assertEqual(result.accepted, expected, word)

    def test_reversal_against_reference_output(self) -> None:
        machine, _ = parse_yaml(str(ROOT / "mt_alteradora.yaml"))
        for length in range(13):
            for symbols in itertools.product("ab", repeat=length):
                word = "".join(symbols)
                result = machine.simulate(word)
                self.assertTrue(result.accepted, word)
                self.assertEqual(result.final_tape, " ".join(reversed(word)) or "B", word)

    def test_official_demo_cases_print_traces_and_verdicts(self) -> None:
        cases = {
            "mt_reconocedora.yaml": (
                ("aabbcc", "ACEPTADA", "X X Y Y Z Z"),
                ("aaabbbccc", "ACEPTADA", "X X X Y Y Y Z Z Z"),
                ("aabbc", "RECHAZADA", "X X Y Y Z"),
                ("aabbccc", "RECHAZADA", "X X Y Y Z Z c"),
            ),
            "mt_alteradora.yaml": (
                ("aabbb", "ACEPTADA", "b b b a a"),
                ("aabba", "ACEPTADA", "a b b a a"),
                ("aaabb", "ACEPTADA", "b b a a a"),
                ("ababba", "ACEPTADA", "a b b a b a"),
            ),
        }
        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                run = run_cli(filename)
                self.assertEqual(run.returncode, 0, run.stderr)
                sections = run.stdout.split("Cadena de entrada: ")[1:]
                self.assertEqual(len(sections), len(expected))
                self.assertIn("Sin veredicto:     0", run.stdout)
                for section, (word, verdict, tape) in zip(sections, expected):
                    self.assertTrue(section.startswith(f'"{word}"\n'))
                    self.assertIn(f" {verdict}\n", section)
                    self.assertIn(f"Cinta final: {tape}\n", section)
                    steps = re.findall(r"^\s*Paso (\d+):", section, re.MULTILINE)
                    self.assertGreater(len(steps), 1)
                    self.assertEqual(steps, [str(step) for step in range(len(steps))])
                    self.assertEqual(section.count("mueve el cabezal"), len(steps) - 1)


class MenuTests(unittest.TestCase):
    def test_selects_and_reviews_an_individual_case(self) -> None:
        run = run_cli(input_text="1\n3\n\nT\nR\n0\n0\n")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.count("Cadena de entrada:"), 1)
        self.assertIn('Cadena de entrada: "aabbc"', run.stdout)
        self.assertIn("Paso 0: q0 a a b b c", run.stdout)
        self.assertIn(
            "En q0 lee 'a', escribe 'X', mueve el cabezal a la derecha (R) y pasa a q1.",
            run.stdout,
        )
        self.assertIn("Paso 1: X q1 a b b c", run.stdout)
        self.assertEqual(run.stdout.count("Siguiente paso [Espacio/Enter/T/V]"), 2)
        self.assertIn("Razón: No hay una transición para δ(q2, B).", run.stdout)
        self.assertIn("Funciones de transición:", run.stdout)

    def test_can_leave_a_trace_and_enter_a_custom_word(self) -> None:
        run = run_cli(input_text="9\n2\n1\nV\nP\nabb\nT\n0\n0\n")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Opción inválida.", run.stdout)
        cancelled, custom = run.stdout.split('Cadena de entrada: "abb"', 1)
        self.assertIn('Cadena de entrada: "aabbb"', cancelled)
        self.assertNotIn("Cinta final:", cancelled)
        self.assertIn("Cinta final: b b a", custom)
        self.assertIn("Razón: Se alcanzó qf, un estado de aceptación.", custom)

    def test_can_recover_from_bad_path_and_run_another_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "otra máquina.yaml"
            path.write_text(ENUNCIADO_YAML, encoding="utf-8")
            missing = path.with_name("ausente.yaml")
            run = run_cli(input_text=f"3\n{missing}\n3\n{path}\nT\n0\n0\n")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Error en la configuración", run.stderr)
        self.assertIn("otra máquina.yaml", run.stdout)
        self.assertIn("Total de cadenas:  3", run.stdout)
        self.assertIn("Rechazadas:        3", run.stdout)

    def test_end_of_input_closes_the_menu(self) -> None:
        run = run_cli(input_text="")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("0. Salir", run.stdout)

    @unittest.skipUnless(os.name == "posix", "Requiere una pseudoterminal POSIX.")
    def test_space_advances_each_step_without_enter_in_a_terminal(self) -> None:
        import pty
        import select
        import termios
        import time

        master, slave = pty.openpty()
        output = bytearray()

        def expect(fragment: str) -> None:
            target = fragment.encode("utf-8")
            deadline = time.monotonic() + 3
            while target not in output:
                remaining = max(0.0, deadline - time.monotonic())
                ready, _, _ = select.select([master], [], [], remaining)
                if not ready:
                    self.fail(f"No apareció {fragment!r}: {output.decode('utf-8', 'replace')}")
                chunk = os.read(master, 4096)
                if not chunk:
                    self.fail(f"La terminal se cerró antes de mostrar {fragment!r}.")
                output.extend(chunk)
            del output[: output.index(target) + len(target)]

        try:
            initial_settings = termios.tcgetattr(slave)
            with subprocess.Popen(
                [sys.executable, "-B", str(ROOT / "main.py")],
                cwd=ROOT,
                stdin=slave,
                stdout=slave,
                stderr=slave,
            ) as process:
                try:
                    expect("Elige una opción: ")
                    os.write(master, b"1\n")
                    expect("Elige una opción: ")
                    os.write(master, b"3\n")
                    expect("Paso 0:")
                    for number in range(1, 14):
                        expect("Siguiente paso [Espacio/Enter/T/V]: ")
                        os.write(master, b" ")
                        expect(f"Paso {number}:")
                    expect("Resultado: ❌ RECHAZADA")
                    expect("Razón: No hay una transición para δ(q2, B).")
                    expect("Elige una opción: ")
                    line_input_flags = termios.ICANON | termios.ECHO
                    self.assertEqual(
                        termios.tcgetattr(slave)[3] & line_input_flags,
                        initial_settings[3] & line_input_flags,
                    )
                    os.write(master, b"0\n")
                    expect("Elige una opción: ")
                    os.write(master, b"0\n")
                    self.assertEqual(process.wait(timeout=3), 0)
                finally:
                    if process.poll() is None:
                        process.kill()
        finally:
            os.close(slave)
            os.close(master)


class SimulatorTests(unittest.TestCase):
    def test_final_step_distinguishes_acceptance_rejection_and_limit(self) -> None:
        machine, _ = parse_yaml(str(ROOT / "mt_reconocedora.yaml"))
        self.assertTrue(machine.simulate("aabbcc", max_steps=23).accepted)
        blocked = machine.simulate("aabbc", max_steps=13)
        self.assertFalse(blocked.accepted)
        self.assertFalse(blocked.limit_reached)
        run = run_cli("mt_reconocedora.yaml", "--max-steps", "23")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Aceptadas:         1", run.stdout)
        self.assertIn("Rechazadas:        2", run.stdout)
        self.assertIn("Sin veredicto:     1", run.stdout)

    def test_accepting_initial_state_with_zero_steps(self) -> None:
        machine = TuringMachine(["qf"], [], ["B"], "qf", ["qf"], [])
        self.assertTrue(machine.simulate("", max_steps=0).accepted)

    def test_internal_symbols_in_input_are_rejected_before_moving(self) -> None:
        machine, _ = parse_yaml(str(ROOT / "mt_reconocedora.yaml"))
        for word in ("Y", "abcBabc", "abcd"):
            with self.subTest(word=word):
                result = machine.simulate(word)
                self.assertFalse(result.accepted)
                self.assertEqual(len(result.steps), 1)
                self.assertIn("ajenos al alfabeto", result.halted_reason)


class YamlTests(unittest.TestCase):
    def write_config(self, directory: str, content: str) -> Path:
        path = Path(directory) / "machine.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_literal_pdf_example(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory, ENUNCIADO_YAML)
            run = run_cli(str(path))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("δ([q0,B], a) = ([q1,a], B, R)", run.stdout)
        self.assertIn("δ([q0,B], b) = ([q1,b], B, R)", run.stdout)
        self.assertIn("Paso 1: [q1,a] a b b", run.stdout)
        self.assertIn("Cinta final: a b b", run.stdout)
        self.assertIn("Rechazadas:        3", run.stdout)

    def test_register_is_carried_between_steps(self) -> None:
        rule = "    - {state: q1, read: [b, a], write: [Y, a], move: L, next: qf}\n"
        content = ENUNCIADO_YAML.replace("  inputs:", f"{rule}  inputs:")
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory, content)
            machine, _ = parse_yaml(str(path))
        accepted = machine.simulate("ab")
        self.assertTrue(accepted.accepted)
        self.assertEqual(accepted.final_tape, "a")
        self.assertEqual(accepted.steps[-1], "[qf,Y] B a")
        self.assertFalse(machine.simulate("bb").accepted)

    def test_bad_configurations_fail_with_clear_messages(self) -> None:
        cases = {
            "": "sección 'mt'",
            "mt: null": "sección 'mt'",
            ENUNCIADO_YAML + 'inputs: ["ab"]\n': "Declara 'inputs' una sola vez",
            ENUNCIADO_YAML.replace("read: [a, B]", "read: [a]"): "exige dos símbolos",
            ENUNCIADO_YAML.replace("write: [a, B]", "write: [Z, B]"): "alfabeto de cinta",
            ENUNCIADO_YAML.replace("read: [b, B]", "read: [a, B]"): "ya tiene una regla",
            ENUNCIADO_YAML.replace("move: R", "move: U"): "'move' debe ser L o R",
        }
        with tempfile.TemporaryDirectory() as directory:
            for content, message in cases.items():
                with self.subTest(message=message):
                    path = self.write_config(directory, content)
                    run = run_cli(str(path))
                    self.assertEqual(run.returncode, 1)
                    self.assertIn(message, run.stderr)
                    self.assertNotIn("Traceback", run.stderr)


if __name__ == "__main__":
    unittest.main()
