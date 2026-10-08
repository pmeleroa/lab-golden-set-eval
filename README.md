# lab-golden-set-eval

Ejemplo mínimo de **golden set** y **pipeline de evaluación** para un sistema basado en un LLM: un clasificador de tickets de soporte que corre en local con [Ollama](https://ollama.com).

Acompaña al post [Golden sets: cómo saber si tu IA ha mejorado o solo lo parece](https://pablomeleroalonso.me/blog/golden-sets-y-pipelines-de-evaluacion/).

> Los tickets son **ficticios** y están construidos para ilustrar el método. Las cifras de `runs/` salen de ejecutar el pipeline de verdad, pero no miden la calidad de ningún modelo: el set es pequeño y está diseñado para enseñar.

## Qué hay aquí

| Fichero | Qué es |
|---|---|
| `guia-etiquetado.md` | El criterio de etiquetado. Se escribió antes que los casos. |
| `dev.jsonl` | 25 casos para iterar: aquí se miran los fallos. |
| `test.jsonl` | 15 casos que no se miran: se ejecutan una sola vez, al final. |
| `prompts/` | Las versiones del prompt de sistema que se han evaluado. |
| `eval.py` | El pipeline: cargar, ejecutar, normalizar, puntuar y comparar. |
| `runs/` | Los runs guardados: respuestas crudas y configuración de cada ejecución. |

## Requisitos

- Python 3 (solo biblioteca estándar).
- Ollama en marcha en `localhost:11434` y el modelo descargado:

```bash
ollama pull qwen2.5:7b
```

Los comandos son para una terminal Linux, y son idénticos en macOS. En Windows, usa [WSL2](https://learn.microsoft.com/es-es/windows/wsl/install).

## Uso

Ejecutar un prompt sobre `dev` y guardar el run:

```bash
python3 eval.py run --split dev --prompt prompts/v1.txt
```

Ejecutar otra versión y compararla caso a caso con la anterior:

```bash
python3 eval.py run --split dev --prompt prompts/v2.txt --comparar runs/dev-v1.json
```

Volver a puntuar un run guardado sin llamar al modelo:

```bash
python3 eval.py report runs/dev-v2.json
```

Cuando hayas terminado de iterar, ejecutar el prompt final **una sola vez** sobre `test`:

```bash
python3 eval.py run --split test --prompt prompts/v2.txt
```

Opciones de `run`: `--modelo` (por defecto `qwen2.5:7b`), `--temperatura` (por defecto `0`), `--seed` (por defecto `42`) y `--salida` (por defecto `runs/<split>-<prompt>.json`).

## Licencia

[MIT](LICENSE).
