# Proyecto 3: Simulador de Máquinas de Turing
**Teoría de la Computación**  
*Universidad del Valle de Guatemala*

Este proyecto consiste en un simulador formal de **Máquinas de Turing (MT)** de una sola cinta capaz de interpretar configuraciones estructuradas en archivos YAML, procesar cadenas de prueba paso a paso generando **Descripciones Instantáneas (IDs)** completas, e indicar si la cadena es aceptada o rechazada junto a su configuración final en la cinta.

---

## 1. Requisitos y Dependencias

- **Python 3.8+**
- `PyYAML` para la lectura y parsing de los archivos YAML.

Instalación de dependencias:
```bash
pip install -r requirements.txt
```

---

## 2. Estructura del Proyecto

```text
├── turing_machine.py     # Núcleo del simulador: validaciones, cinta dinámica y cálculo de IDs
├── main.py               # Punto de entrada CLI con parsing YAML y formateo de resultados
├── mt_reconocedora.yaml  # Configuración y casos de la MT reconocedora: {a^n b^n c^n | n >= 1}
├── mt_alteradora.yaml    # Configuración y casos de la MT alteradora: Inversión de cadenas (reversa)
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Documentación e instrucciones
```

---

## 3. Instrucciones de Ejecución

Para ejecutar cualquier Máquina de Turing configurada:

```bash
python main.py <ruta_archivo_yaml>
```

### Ejemplos directos:

1. **Ejecutar la MT Reconocedora:**
   ```bash
   python main.py mt_reconocedora.yaml
   ```

2. **Ejecutar la MT Alteradora:**
   ```bash
   python main.py mt_alteradora.yaml
   ```

3. **Opciones adicionales:**
   - `--max-steps <N>`: Permite ajustar el límite máximo de pasos para evitar bucles infinitos (por defecto `10000`).
     ```bash
     python main.py mt_reconocedora.yaml --max-steps 5000
     ```

---

## 4. Especificación del Archivo YAML

El formato sigue las especificaciones estándar de la definición formal de una MT $M = (Q, \Sigma, \Gamma, \delta, q_0, B, F)$:

```yaml
mt:
  states: [q0, q1, q2, qf]           # Conjunto de estados Q
  input_alphabet: [a, b]             # Alfabeto de entrada Σ
  tape_alphabet: [a, b, X, Y, B]     # Alfabeto de la cinta Γ (debe contener a Σ y al blanco 'B')
  initial_state: q0                  # Estado inicial q0 ∈ Q
  accept_states: [qf]                # Conjunto de estados de aceptación F ⊆ Q
  transitions:                       # Función de transición δ: Q x Γ -> Q x Γ x {L, R}
    - state: q0
      read: [a]
      write: [X]
      move: R
      next: q1
inputs:                              # Lista de cadenas a simular
  - "ab"
  - "aabb"
```

---

## 5. Máquinas de Turing Incluidas

### 5.1 MT Reconocedora (`mt_reconocedora.yaml`)
- **Lenguaje:** $L = \{a^n b^n c^n \mid n \ge 1\}$
- **Dificultad:** Alta (Lenguaje sensible al contexto / no libre de contexto). Demuestra el poder computacional de una MT frente a Autómatas de Pila o Finitos.
- **Lógica:**
  1. Marca la primera 'a' no procesada con `X`.
  2. Avanza hacia la derecha buscando y emparejando la primera 'b' con `Y`.
  3. Continúa hacia la derecha buscando y emparejando la primera 'c' con `Z`.
  4. Regresa hacia la izquierda hasta el último `X` y repite.
  5. Una vez agotadas las 'a', entra en una fase de verificación (`q4`) asegurando que no queden 'b' ni 'c' sobrantes antes de alcanzar el blanco `B`.
- **Cadenas de prueba (longitud $\ge$ 5):**
  - `"aabbcc"` $\rightarrow$ **ACEPTADA** ($n = 2$, longitud 6)
  - `"aaabbbccc"` $\rightarrow$ **ACEPTADA** ($n = 3$, longitud 9)
  - `"aabbc"` $\rightarrow$ **RECHAZADA** (desbalance de 'c', longitud 5)
  - `"aabbccc"` $\rightarrow$ **RECHAZADA** (desbalance de 'c', longitud 7)

---

### 5.2 MT Alteradora (`mt_alteradora.yaml`)
- **Objetivo:** Invertir una cadena sobre $\{a, b\}^*$ (calcular $w^R$).
- **Dificultad:** Alta. En una sola cinta, requiere desplazamiento dinámico y marcadores delimitadores.
- **Lógica:**
  1. **Fase 1 (Marcador):** Escanea hasta el final de la cadena de entrada y coloca un delimitador `H`.
  2. **Fase 2 (Reversa):** Toma de forma iterativa el carácter sin procesar más a la derecha del bloque original, lo reemplaza por `X`, y lo traslada a la derecha de `H` (apilándolo al final), construyendo paso a paso la cadena en reversa.
  3. **Fase 3 (Limpieza):** Una vez procesados todos los símbolos, recorre la cinta borrando las marcas auxiliares `X` y el separador `H`, dejando en la cinta únicamente la cadena invertida.
- **Cadenas de prueba (longitud $\ge$ 5):**
  - `"aabbb"` $\rightarrow$ Resultado: `"bbbaa"` (Longitud 5)
  - `"ababa"` $\rightarrow$ Resultado: `"ababa"` (Palíndromo, longitud 5)
  - `"aabba"` $\rightarrow$ Resultado: `"abbaa"` (Longitud 5)
  - `"baaab"` $\rightarrow$ Resultado: `"baaab"` (Palíndromo, longitud 5)

---

## 6. Arquitectura del Simulador

El diseño está compuesto por dos módulos desacoplados:

1. **`TuringMachine` (`turing_machine.py`):**
   - **Cinta infinita dinámica:** Representada mediante una lista en memoria (`list`), la cual se expande dinámicamente con el símbolo blanco `B` al moverse más allá del índice 0 (hacia la izquierda con `insert(0, 'B')`) o al sobrepasar la longitud actual (hacia la derecha con `append('B')`).
   - **Descripciones Instantáneas (IDs):** En cada paso $i$, genera la representación canónica:
     $$\alpha \, q_k \, X \, \beta$$
     donde $\alpha$ son los símbolos a la izquierda del cabezal, $q_k$ es el estado actual, $X$ es el símbolo bajo lectura, y $\beta$ es el resto de la cinta a la derecha. Los blancos triviales a los extremos son recortados para legibilidad.
   - **Manejo de parada:** Si en un estado $q$ leyendo $s$ no existe regla en $\delta$, o si se alcanza un estado en $F$, la simulación se detiene inmediatamente indicando si fue por aceptación o detención por bloqueo.

2. **`main.py`:**
   - Realiza la lectura robusta con `yaml.safe_load`, valida los tipos y presencia de las 7 tuplas de la MT, configura la salida en consola para soporte UTF-8 (emojis y caracteres griegos $\delta$) y tabula las ejecuciones con un resumen final.

