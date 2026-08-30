"""Painel de progresso do laboratorio, em uma tela de terminal.

Uso::

    python verifica.py

Cada exercicio e executado de verdade em um framebuffer pequeno. O que
roda aparece como feito; o que ainda levanta ``NotImplementedError``
aparece como pendente; e o que quebra aparece com a excecao, para que um
erro de digitacao nao se disfarce de exercicio nao comecado.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from motor.exercicios import (  # noqa: E402  (precisa do sys.path acima)
    COM_ERRO,
    PENDENTE,
    PRONTO,
    panorama,
)

MARCAS = {PRONTO: "[x]", PENDENTE: "[ ]", COM_ERRO: "[!]"}
LARGURA = 64


def principal() -> int:
    """Imprime o panorama e devolve o codigo de saida do processo."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    linhas = panorama()
    feitos = sum(1 for _, situacao, _ in linhas if situacao == PRONTO)
    quebrados = [item for item in linhas if item[1] == COM_ERRO]

    print()
    print("  BANCADA RASTER".ljust(LARGURA) + f"{feitos} / {len(linhas)}")
    print("  " + "-" * (LARGURA - 2))

    familia = ""
    for exercicio, situacao, detalhe in linhas:
        if exercicio.familia != familia:
            familia = exercicio.familia
            print(f"\n  {familia.upper()}")
        marca = MARCAS[situacao]
        nome = f"{exercicio.numero:>2}  {exercicio.funcao}"
        nota = "" if situacao == PRONTO else f"  {detalhe}"
        print(f"  {marca} {nome.ljust(30)}{nota}")

    print()
    pendentes = [e for e, s, _ in linhas if s == PENDENTE]
    if quebrados:
        exercicio, _, detalhe = quebrados[0]
        print(f"  corrija primeiro  {exercicio.caminho}  "
              f"{exercicio.funcao}()")
        print(f"                    {detalhe}")
    elif pendentes:
        print(f"  próximo           {pendentes[0].caminho}  "
              f"{pendentes[0].funcao}()")
    else:
        print("  tudo pronto. rode: python bancada.py")
    print()
    return 1 if quebrados else 0


if __name__ == "__main__":
    raise SystemExit(principal())
