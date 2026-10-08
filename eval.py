"""Pipeline de evaluación para un clasificador de tickets con un modelo local de Ollama.

Cinco etapas: cargar el split, ejecutar y guardar el run, normalizar,
puntuar y comparar con un run anterior. Solo usa la biblioteca estándar.
"""

import argparse
import hashlib
import json
import sys
import unicodedata
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
CATEGORIAS = ["facturación", "bug", "acceso", "petición"]
INVALIDO = "inválido"
DIFICULTADES = ["fácil", "ambiguo", "trampa"]


def sha_corto(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:8]


# 1. Cargar el split

def cargar_split(nombre):
    ruta = Path(f"{nombre}.jsonl")
    texto = ruta.read_text(encoding="utf-8")
    casos = [json.loads(linea) for linea in texto.splitlines() if linea.strip()]
    return casos, sha_corto(texto)


# 2. Ejecutar el sistema bajo prueba y guardar el run

def preguntar_a_ollama(modelo, prompt, ticket, temperatura, seed):
    peticion = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": ticket},
        ],
        "stream": False,
        "options": {"temperature": temperatura, "seed": seed},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(peticion).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as respuesta:
        return json.load(respuesta)["message"]["content"]


def ejecutar(args):
    casos, split_sha = cargar_split(args.split)
    prompt_ruta = Path(args.prompt)
    prompt = prompt_ruta.read_text(encoding="utf-8")
    config = {
        "modelo": args.modelo,
        "temperatura": args.temperatura,
        "seed": args.seed,
        "prompt": prompt_ruta.name,
        "prompt_sha": sha_corto(prompt),
        "split": args.split,
        "split_sha": split_sha,
        "fecha": datetime.now().isoformat(timespec="seconds"),
    }
    resultados = []
    for i, caso in enumerate(casos, 1):
        crudo = preguntar_a_ollama(args.modelo, prompt, caso["input"], args.temperatura, args.seed)
        resultados.append({
            "id": caso["id"],
            "expected": caso["expected"],
            "dificultad": caso["dificultad"],
            "respuesta": crudo,
        })
        print(f"[{i}/{len(casos)}] {caso['id']}", file=sys.stderr)

    salida = Path(args.salida or f"runs/{args.split}-{prompt_ruta.stem}.json")
    salida.parent.mkdir(parents=True, exist_ok=True)
    run = {"config": config, "resultados": resultados}
    salida.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Run guardado en {salida}\n", file=sys.stderr)
    informe(run, args.comparar)


# 3. Normalizar la respuesta al conjunto cerrado

def sin_tildes(texto):
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def normalizar(respuesta):
    limpia = sin_tildes(respuesta.strip().strip(".\"'`*").lower())
    for categoria in CATEGORIAS:
        if limpia == sin_tildes(categoria):
            return categoria
    return INVALIDO


# 4. Puntuar

def puntuar(run):
    filas = [(r["expected"], normalizar(r["respuesta"]), r["dificultad"]) for r in run["resultados"]]
    total = len(filas)
    aciertos = sum(1 for esperado, predicho, _ in filas if esperado == predicho)
    mayoritaria, n_mayoritaria = Counter(e for e, _, _ in filas).most_common(1)[0]

    por_clase = {}
    for c in CATEGORIAS:
        tp = sum(1 for e, p, _ in filas if e == c and p == c)
        predichos = sum(1 for _, p, _ in filas if p == c)
        reales = sum(1 for e, _, _ in filas if e == c)
        por_clase[c] = (tp / predichos if predichos else None, tp / reales if reales else None)

    matriz = {e: Counter(p for ee, p, _ in filas if ee == e) for e in CATEGORIAS}

    por_dificultad = {}
    for d in DIFICULTADES:
        del_tipo = [(e, p) for e, p, dd in filas if dd == d]
        if del_tipo:
            por_dificultad[d] = (sum(1 for e, p in del_tipo if e == p), len(del_tipo))

    return {
        "total": total,
        "aciertos": aciertos,
        "invalidos": sum(1 for _, p, _ in filas if p == INVALIDO),
        "baseline": (mayoritaria, n_mayoritaria),
        "por_clase": por_clase,
        "matriz": matriz,
        "por_dificultad": por_dificultad,
    }


def pct(valor):
    return "  -  " if valor is None else f"{valor:5.0%}"


def informe(run, comparar_con=None):
    c = run["config"]
    m = puntuar(run)
    total = m["total"]
    clase, n = m["baseline"]
    print(f"Modelo: {c['modelo']} | prompt: {c['prompt']} ({c['prompt_sha']}) | split: {c['split']} ({c['split_sha']})")
    print(f"Accuracy:           {m['aciertos']}/{total} = {m['aciertos'] / total:.0%}")
    print(f"Baseline ('{clase}' siempre): {n}/{total} = {n / total:.0%}")
    print(f"Respuestas inválidas: {m['invalidos']}")

    print("\nPor clase        precisión  recall")
    for categoria, (precision, recall) in m["por_clase"].items():
        print(f"  {categoria:<14} {pct(precision):>9}  {pct(recall):>6}")

    columnas = CATEGORIAS + [INVALIDO]
    print("\nMatriz de confusión (filas: esperado, columnas: predicho)")
    print(" " * 14 + "".join(f"{col:>13}" for col in columnas))
    for esperado in CATEGORIAS:
        print(f"  {esperado:<12}" + "".join(f"{m['matriz'][esperado][col]:>13}" for col in columnas))

    print("\nPor dificultad")
    for dificultad, (ok, n_dif) in m["por_dificultad"].items():
        print(f"  {dificultad:<8} {ok}/{n_dif}")

    if comparar_con:
        comparar(json.loads(Path(comparar_con).read_text(encoding="utf-8")), run)


# 5. Comparar con el run anterior, caso a caso

def comparar(anterior, actual):
    if anterior["config"]["split_sha"] != actual["config"]["split_sha"]:
        sys.exit("No se pueden comparar: los runs usan versiones distintas del split.")
    antes = {r["id"]: normalizar(r["respuesta"]) == r["expected"] for r in anterior["resultados"]}
    arreglados, regresiones = [], []
    for r in actual["resultados"]:
        ahora = normalizar(r["respuesta"]) == r["expected"]
        if ahora and not antes[r["id"]]:
            arreglados.append(r["id"])
        elif antes[r["id"]] and not ahora:
            regresiones.append(r["id"])
    print(f"\nFrente a {anterior['config']['prompt']} ({anterior['config']['prompt_sha']})")
    print(f"  Arreglados ({len(arreglados)}):  {', '.join(arreglados) or '-'}")
    print(f"  Regresiones ({len(regresiones)}): {', '.join(regresiones) or '-'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="comando", required=True)

    p_run = sub.add_parser("run", help="ejecuta el modelo sobre un split y guarda el run")
    p_run.add_argument("--split", choices=["dev", "test"], required=True)
    p_run.add_argument("--prompt", required=True, help="fichero con el prompt de sistema")
    p_run.add_argument("--modelo", default="qwen2.5:7b")
    p_run.add_argument("--temperatura", type=float, default=0.0)
    p_run.add_argument("--seed", type=int, default=42)
    p_run.add_argument("--salida", help="ruta del run (por defecto runs/<split>-<prompt>.json)")
    p_run.add_argument("--comparar", help="run anterior con el que comparar")

    p_inf = sub.add_parser("report", help="vuelve a puntuar un run guardado, sin llamar al modelo")
    p_inf.add_argument("run")
    p_inf.add_argument("--comparar", help="run anterior con el que comparar")

    args = parser.parse_args()
    if args.comando == "run":
        ejecutar(args)
    else:
        informe(json.loads(Path(args.run).read_text(encoding="utf-8")), args.comparar)


if __name__ == "__main__":
    main()
