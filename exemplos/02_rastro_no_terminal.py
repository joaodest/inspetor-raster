"""Roda um algoritmo sob o rastreador e imprime o perfil no terminal.

Uso::

    python exemplos/02_rastro_no_terminal.py
    python exemplos/02_rastro_no_terminal.py reta_bresenham 2 2 40 14

E a mesma instrumentacao do inspetor, sem navegador: serve para colar o
resultado em um relatorio ou para depurar por cima do ombro de alguem.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from motor import (  # noqa: E402  (precisa do sys.path acima)
    PRETO,
    Framebuffer,
    analisa,
    primitivas,
    rastreia,
)
from motor.tracador import cronometra, formata_valor  # noqa: E402

LARGURA = 60
ALTURA = 24


def desenha_no_terminal(quadro: Framebuffer) -> str:
    """Converte o framebuffer em arte de terminal."""
    linhas = []
    for y in range(quadro.altura):
        celulas = ["#" if quadro.le(x, y) != quadro.le(0, 0) or
                   quadro.le(x, y) == PRETO else "."
                   for x in range(quadro.largura)]
        linhas.append("  " + "".join(celulas))
    return "\n".join(linhas)


def principal(argumentos: list[str]) -> int:
    """Rastreia a reta pedida e imprime tudo."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    nome = argumentos[0] if argumentos else "reta_dda"
    coordenadas = ([int(valor) for valor in argumentos[1:5]]
                   if len(argumentos) >= 5 else [3, 20, 56, 3])

    funcao = getattr(primitivas, nome, None)
    if funcao is None:
        print(f"nao existe primitivas.{nome}()")
        return 2

    quadro = Framebuffer(LARGURA, ALTURA)
    rastro = rastreia(funcao, *coordenadas, PRETO, 1, quadro, rotulo=nome)

    if rastro.pendente:
        print(f"{nome}() ainda nao foi implementada.")
        print("rode python verifica.py para ver o roteiro.")
        return 1
    if rastro.falhou:
        print(f"{nome}() quebrou: {type(rastro.erro).__name__}: "
              f"{rastro.erro}")
        return 1

    rastro.duracao_limpa = cronometra(
        funcao, *coordenadas, PRETO, 1, Framebuffer(LARGURA, ALTURA))
    perfil = analisa(rastro, referencia=tuple(coordenadas))

    print(f"\n  {nome}{tuple(coordenadas)}\n")
    print(desenha_no_terminal(quadro))
    print("\n  PERFIL ANALITICO")
    for medida in perfil.medidas():
        print(f"  {medida.rotulo.ljust(16)}{medida.valor.rjust(18)}"
              f"   {medida.detalhe}")

    meio = rastro.passos[len(rastro.passos) // 2]
    print(f"\n  ESTADO NO PASSO {meio.indice + 1} (linha {meio.linha})")
    print(f"  {'pixel'.ljust(16)}{f'({meio.x}, {meio.y})'.rjust(18)}")
    for chave, valor in meio.variaveis.items():
        print(f"  {chave.ljust(16)}{formata_valor(valor).rjust(18)}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(principal(sys.argv[1:]))
