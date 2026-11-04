"""
Punto de entrada del Simulador de Máquinas de Turing.

Uso:
    python main.py <archivo_yaml>

Ejemplo:
    python main.py mt_reconocedora.yaml
"""

import argparse
import sys
import yaml
from turing_machine import TuringMachine

# Configurar stdout para evitar problemas de codificación en consolas Windows (cp1252)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def parse_yaml(filepath):
    """
    Lee y parsea el archivo YAML con la configuración de la MT.

    Retorna:
        Tupla (config_mt, inputs) donde config_mt es el dict de la MT
        e inputs es la lista de cadenas a simular.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{filepath}'.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error al parsear el archivo YAML: {e}")
        sys.exit(1)

    # Extraer la configuración de la MT
    if "mt" not in data:
        print("Error: El archivo YAML debe contener una clave 'mt'.")
        sys.exit(1)

    mt_config = data["mt"]

    # Validar campos requeridos
    required_fields = [
        "states", "input_alphabet", "tape_alphabet",
        "initial_state", "accept_states", "transitions"
    ]
    for field in required_fields:
        if field not in mt_config:
            print(f"Error: Falta el campo requerido '{field}' en la configuración.")
            sys.exit(1)

    # Extraer las cadenas de entrada
    inputs = data.get("inputs", [])
    if not inputs:
        print("Advertencia: No se encontraron cadenas de entrada en el archivo.")

    return mt_config, inputs


def print_header(mt_config):
    """Imprime la información de la MT configurada."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + "  SIMULADOR DE MÁQUINAS DE TURING".center(58) + "║")
    print("║" + "  Teoría de la Computación - UVG".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("  Configuración de la MT:")
    print(f"    Estados:           {mt_config['states']}")
    print(f"    Alfabeto entrada:  {mt_config['input_alphabet']}")
    print(f"    Alfabeto cinta:    {mt_config['tape_alphabet']}")
    print(f"    Estado inicial:    {mt_config['initial_state']}")
    print(f"    Estados aceptación:{mt_config['accept_states']}")
    print(f"    Transiciones:      {len(mt_config['transitions'])} definidas")
    print()

    # Mostrar las funciones de transición
    print("  Funciones de transición:")
    for t in mt_config["transitions"]:
        state = t["state"]
        read_sym = t["read"][0] if isinstance(t["read"], list) else t["read"]
        write_sym = t["write"][0] if isinstance(t["write"], list) else t["write"]
        move = t["move"]
        next_state = t["next"]
        print(f"    δ({state}, {read_sym}) = ({next_state}, {write_sym}, {move})")

    print()
    print("-" * 60)


def main():
    """Función principal del simulador."""
    # Configurar argumentos de línea de comando
    parser = argparse.ArgumentParser(
        description="Simulador de Máquinas de Turing"
    )
    parser.add_argument(
        "archivo",
        help="Ruta al archivo YAML con la configuración de la MT"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10000,
        help="Número máximo de pasos por simulación (default: 10000)"
    )

    args = parser.parse_args()

    # Parsear el archivo YAML
    mt_config, inputs = parse_yaml(args.archivo)

    # Mostrar información de la MT
    print_header(mt_config)

    # Crear la Máquina de Turing
    try:
        tm = TuringMachine(
            states=[str(s) for s in mt_config["states"]],
            input_alphabet=[str(s) for s in mt_config["input_alphabet"]],
            tape_alphabet=[str(s) for s in mt_config["tape_alphabet"]],
            initial_state=str(mt_config["initial_state"]),
            accept_states=[str(s) for s in mt_config["accept_states"]],
            transitions=mt_config["transitions"]
        )
    except ValueError as e:
        print(f"Error en la configuración de la MT: {e}")
        sys.exit(1)

    # Simular cada cadena de entrada
    accepted_count = 0
    rejected_count = 0

    for input_str in inputs:
        input_str = str(input_str)
        result = tm.simulate(input_str, max_steps=args.max_steps)
        print(result)

        if result.accepted:
            accepted_count += 1
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
    print("─" * 60)
    print()


if __name__ == "__main__":
    main()
