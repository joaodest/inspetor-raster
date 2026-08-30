"""Desenha um cartao de teste com todas as primitivas e salva um PNG.

Uso::

    python exemplos/01_cartao_de_teste.py

O que ainda nao foi implementado simplesmente nao aparece no cartao, e
sai listado no fim. E o jeito mais rapido de ver o motor inteiro
funcionando fora da bancada.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from motor import (  # noqa: E402  (precisa do sys.path acima)
    AZUL,
    CINZA_CLARO,
    LARANJA,
    PRETO,
    ROXO,
    VERDE,
    VERMELHO,
    cria_tela,
    preenchimento,
    primitivas,
    salva,
    tela,
    transformacoes,
)

LARGURA = 320
ALTURA = 200


def tenta(rotulo: str, acao) -> str | None:
    """Executa um trecho do cartao e engole exercicios pendentes."""
    try:
        acao()
    except NotImplementedError:
        return rotulo
    return None


def desenha() -> list[str]:
    """Monta o cartao inteiro e devolve o que ficou faltando."""
    faltando = [
        tenta("reta", lambda: [
            primitivas.reta(10, 10 + n * 6, 150, 40 + n * 3, PRETO)
            for n in range(5)]),
        tenta("retangulo", lambda: primitivas.retangulo(
            170, 10, 60, 40, AZUL)),
        tenta("circunferencia", lambda: [
            primitivas.circunferencia(265, 30, raio, VERMELHO)
            for raio in (8, 16, 24)]),
        tenta("elipse", lambda: primitivas.elipse(60, 120, 45, 22, ROXO)),
        tenta("bezier", lambda: primitivas.bezier_cubica(
            (10, 190), (90, 120), (190, 250), (300, 170), LARANJA, 1, 60)),
        tenta("poligono", lambda: primitivas.poligono(
            [(175, 75), (230, 75), (247, 120), (202, 148), (158, 120)],
            CINZA_CLARO)),
        tenta("preenchimento", lambda: preenchimento.flood_fill(
            202, 110, VERDE)),
        tenta("transformacoes", lambda: _figura_transformada()),
    ]
    return [rotulo for rotulo in faltando if rotulo]


def _figura_transformada() -> None:
    """Repete um triangulo girado, para exercitar as matrizes."""
    triangulo = [(0, -18), (16, 12), (-16, 12)]
    for passo in range(6):
        matriz = transformacoes.compoe(
            transformacoes.translacao(275, 140),
            transformacoes.rotacao(passo * 60),
            transformacoes.escala(1 - passo * 0.1))
        vertices = transformacoes.arredonda(
            transformacoes.aplica_em(matriz, triangulo))
        primitivas.poligono(vertices, PRETO)


def principal() -> int:
    """Desenha, salva e relata."""
    cria_tela(LARGURA, ALTURA)
    faltando = desenha()
    destino = salva(tela(), RAIZ / "saidas" / "cartao_de_teste.png")

    print(f"cartao salvo em {destino.relative_to(RAIZ)}")
    if faltando:
        print("ficou faltando: " + ", ".join(faltando))
        print("rode python verifica.py para ver o que falta implementar")
    else:
        print("cartao completo: as 17 primitivas responderam")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
