# Universidad del Valle de Guatemala

**Facultad de Ingeniería**

**Teoría de la Computación**

## Proyecto 3: Simulador de máquinas de Turing

Juan Francisco Orozco Mijangos (24647), Antony David Melquisedec Saz Saz (24710)

## Descripción del proyecto

Implementamos en Python un simulador de máquinas de Turing de una sola cinta. Lo hicimos para ver cómo las reglas de una máquina cambian la cinta y cómo esos cambios llevan a aceptar o rechazar una cadena.

Incluimos dos máquinas. La reconocedora verifica que una cadena tenga bloques consecutivos de `a`, `b` y `c` con la misma cantidad de símbolos en cada bloque. La alteradora invierte una cadena de `a` y `b` intercambiando los extremos en la misma cinta. Guardamos los estados, las reglas y los casos de prueba en archivos YAML para poder cambiar la configuración sin modificar el simulador.

Desde el menú podemos elegir un caso o escribir nuestra propia cadena. Al avanzar con Espacio, vemos qué leyó la máquina, qué escribió, cómo movió el cabezal y a qué estado pasó. Al final podemos revisar la cinta y el motivo por el que se detuvo.

[Video del proyecto](https://www.youtube.com/watch?v=_ftb73exxbQ&t=10s)

---

## 1. Instalación

- **Python 3.8+**
- `PyYAML` para leer los archivos YAML.

Instalación de dependencias en macOS o Linux desde la raíz del repositorio.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

---

## 2. Estructura del Proyecto

```text
├── turing_machine.py     # Núcleo del simulador: validaciones, cinta dinámica y cálculo de IDs
├── main.py               # Punto de entrada CLI con parsing YAML y formateo de resultados
├── mt_reconocedora.yaml  # Configuración y casos de la MT reconocedora: {a^n b^n c^n | n >= 1}
├── mt_alteradora.yaml    # Configuración y casos de la MT alteradora: Inversión de cadenas (reversa)
├── test_proyecto.py      # Pruebas de las máquinas, del simulador y de la consola
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Documentación e instrucciones
```

---

## 3. Instrucciones de Ejecución

Abre el menú interactivo desde la raíz del repositorio.

```bash
python -B main.py
```

En el menú principal, elige **1** para la reconocedora, **2** para la alteradora o **3** para abrir otro archivo YAML. Dentro de cada máquina puedes elegir un caso por número, ejecutar todos con **T**, introducir una cadena propia con **P** o consultar los estados y reglas con **R**. Usa **0** para volver al menú principal o salir.

Al elegir un caso individual en una terminal, pulsa **Espacio** para ver la siguiente transición sin pulsar Enter. También puedes avanzar con **Enter**, mostrar el resto con **T** o volver a los casos con **V**. La traza empieza en el paso 0, antes de aplicar transiciones. Luego muestra el símbolo que se leyó, el que se escribió, hacia dónde se movió el cabezal y el estado al que pasó. Al final muestra la cinta, el veredicto y el motivo de la parada antes de volver al menú de casos.

También puedes ejecutar todas las entradas de un archivo directamente.

```bash
python -B main.py <ruta_archivo_yaml>
```

### Ejecución directa de las máquinas incluidas

```bash
python -B main.py mt_reconocedora.yaml
python -B main.py mt_alteradora.yaml
```

La opción `--max-steps <N>` ajusta el límite de transiciones, que es de `10000` por defecto. Si la máquina aún puede continuar al llegar al límite, el programa informa **sin veredicto**.

```bash
python -B main.py mt_reconocedora.yaml --max-steps 5000
```

---

## 4. Especificación del Archivo YAML

YAML es un formato de texto que usa la indentación para agrupar datos. Aquí los archivos `.yaml` definen los estados, los alfabetos, las reglas y las entradas de prueba. Python lee esos archivos para simular la máquina. El formato representa una MT determinista de una cinta $M = (Q, \Sigma, \Gamma, \delta, q_0, B, F)$.

Cada regla lee y escribe un símbolo en la celda bajo el cabezal. En el formato de las dos máquinas incluidas, `read` y `write` aceptan un escalar como `a` o una lista de un elemento como `[a]`. El blanco `B` debe declararse en el alfabeto de cinta y se reserva para la simulación. Declara `inputs` en la raíz del YAML o dentro de `mt`. Escribe las entradas entre comillas para conservar símbolos como los ceros iniciales y usa `""` para representar la cadena vacía.

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

El YAML del enunciado usa pares con la convención de su fórmula $\delta([q_0,B],a)=([q_1,a],B,R)$. En `read: [a, B]`, el primer valor se lee de la cinta y el segundo es la memoria del estado. En `write: [a, B]`, el primer valor es la memoria nueva y el segundo se escribe en la cinta. La memoria inicial es `B`. El lector convierte esta notación en estados compuestos, como `[q0,B]`, antes de simular. La máquina sigue operando sobre una cinta. Si se usan pares, todas las reglas de ese archivo deben usar el mismo formato.

---

## 5. Máquinas de Turing Incluidas

### 5.1 MT Reconocedora (`mt_reconocedora.yaml`)
- **Lenguaje:** $L = \{a^n b^n c^n \mid n \ge 1\}$
- **Dificultad.** El lenguaje es sensible al contexto y queda fuera de los lenguajes libres de contexto que reconoce un autómata de pila.
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
- **Objetivo.** Calcular la reversa $w^R$ de una cadena sobre $\{a, b\}^*$ en las mismas celdas que ocupaba la entrada.
- **Intercambio.** Marca el extremo izquierdo pendiente con `P` y recuerda su valor en el estado. Recorre el segmento pendiente hasta su extremo derecho, deposita allí el valor recordado y vuelve a `P` con el valor que desplazó. Cada extremo queda marcado como `X` si su valor final es `a` o como `Y` si es `b`.
- **Invariante.** Después de cada intercambio, las marcas de ambos extremos ya contienen los símbolos de la reversa en sus posiciones definitivas. Solo queda pendiente el segmento entre ellos. Si la longitud es impar, se conserva el símbolo central. Al terminar, un último recorrido convierte las marcas en los símbolos de salida.
- **Coste.** La máquina realiza $O(n^2)$ transiciones y usa las $n$ celdas de la entrada y los blancos adyacentes. La reversa de una cadena de 5 símbolos toma 30 transiciones.
- **Cadenas de prueba (longitud $\ge$ 5).** `aabbb → bbbaa`, `aabba → abbaa`, `aaabb → bbaaa` y `ababba → abbaba`.

---

## 6. Arquitectura del Simulador

El diseño está compuesto por dos módulos desacoplados:

1. **`TuringMachine` (`turing_machine.py`):**
   - **Cinta infinita dinámica:** Representada mediante una lista en memoria (`list`), la cual se expande dinámicamente con el símbolo blanco `B` al moverse más allá del índice 0 (hacia la izquierda con `insert(0, 'B')`) o al sobrepasar la longitud actual (hacia la derecha con `append('B')`).
   - **Descripciones Instantáneas (IDs):** En cada paso $i$, genera la representación canónica:
     $$\alpha \, q_k \, X \, \beta$$
     donde $\alpha$ son los símbolos a la izquierda del cabezal, $q_k$ es el estado actual, $X$ es el símbolo bajo lectura, y $\beta$ es el resto de la cinta a la derecha. Los blancos triviales a los extremos son recortados para legibilidad.
   - **Transiciones.** Las reglas se indexan por el par (estado, símbolo leído), lo que permite consultar la transición en tiempo constante promedio en cada paso.
   - **Parada.** La máquina acepta al alcanzar un estado final, incluso en la última transición permitida, y rechaza si se bloquea fuera de un estado final. El límite de pasos deja una ejecución pendiente cuando aún hay una transición disponible.

2. **`main.py`:**
   - Lee el YAML con `yaml.safe_load`, comprueba sus campos y construye la máquina antes de mostrar sus reglas. Presenta la traza, el veredicto y la cinta final de cada entrada.

## 7. Pruebas automatizadas

Desde la raíz del repositorio, después de instalar las dependencias, ejecuta este comando.

```bash
python -B -m unittest -v
```

Las pruebas verifican los ocho casos incluidos en los YAML, la navegación por el menú, el avance con Espacio, los límites de pasos, los símbolos fuera del alfabeto y el formato YAML del enunciado. También comparan todas las cadenas de longitud 0 a 9 del alfabeto de la reconocedora y de 0 a 12 del alfabeto de la alteradora con los resultados esperados.

