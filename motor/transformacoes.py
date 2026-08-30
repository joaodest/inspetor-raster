"""Transformações geométricas 2D em coordenadas homogêneas.

Uma transformação é uma matriz 3x3 representada como tupla de três
linhas. Pontos são pares ``(x, y)`` promovidos a ``(x, y, 1)`` na hora
de aplicar. A composição ``compoe(a, b)`` produz "aplique b, depois a",
igual à notação matemática ``A . B``.

A infraestrutura (``identidade``, ``multiplica``, ``compoe``,
``aplica``) já está pronta; as matrizes elementares são os exercícios.
"""

from __future__ import annotations

import math  # noqa: F401  (usado no exercício de rotação)
from collections.abc import Iterable, Sequence

Matriz = tuple[tuple[float, float, float],
               tuple[float, float, float],
               tuple[float, float, float]]
Ponto = tuple[float, float]


def identidade() -> Matriz:
    """Matriz que não altera nada."""
    return ((1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0))


def multiplica(a: Matriz, b: Matriz) -> Matriz:
    """Produto matricial ``a . b``."""
    return tuple(
        tuple(sum(a[linha][k] * b[k][coluna] for k in range(3))
              for coluna in range(3))
        for linha in range(3)
    )  # type: ignore[return-value]


def compoe(*matrizes: Matriz) -> Matriz:
    """Compõe várias matrizes da direita para a esquerda.

    ``compoe(t, r, e)`` aplica primeiro ``e``, depois ``r``, depois
    ``t``: a mesma ordem de leitura da álgebra linear.
    """
    resultado = identidade()
    for matriz in matrizes:
        resultado = multiplica(resultado, matriz)
    return resultado


def aplica(matriz: Matriz, ponto: Ponto) -> Ponto:
    """Transforma um ponto, dividindo pela coordenada homogênea."""
    x, y = ponto
    nx = matriz[0][0] * x + matriz[0][1] * y + matriz[0][2]
    ny = matriz[1][0] * x + matriz[1][1] * y + matriz[1][2]
    peso = matriz[2][0] * x + matriz[2][1] * y + matriz[2][2]
    if peso not in (0.0, 1.0):
        return nx / peso, ny / peso
    return nx, ny


def aplica_em(matriz: Matriz, pontos: Iterable[Ponto]) -> list[Ponto]:
    """Transforma uma sequência de pontos."""
    return [aplica(matriz, ponto) for ponto in pontos]


def arredonda(pontos: Iterable[Ponto]) -> list[tuple[int, int]]:
    """Leva pontos contínuos para a grade inteira da tela."""
    return [(int(round(x)), int(round(y))) for x, y in pontos]


def centroide(pontos: Sequence[Ponto]) -> Ponto:
    """Média aritmética dos pontos; útil como pivô de rotação."""
    if not pontos:
        raise ValueError("sequência de pontos vazia")
    total_x = sum(x for x, _ in pontos)
    total_y = sum(y for _, y in pontos)
    return total_x / len(pontos), total_y / len(pontos)


def em_torno_de(matriz: Matriz, pivo_x: float, pivo_y: float) -> Matriz:
    """Aplica ``matriz`` em torno de um pivô em vez da origem.

    Equivale a ``T(pivô) . matriz . T(-pivô)``. Depende do exercício
    ``translacao``.
    """
    return compoe(translacao(pivo_x, pivo_y),
                  matriz,
                  translacao(-pivo_x, -pivo_y))


def translacao(deslocamento_x: float, deslocamento_y: float) -> Matriz:
    """EXERCÍCIO 10: matriz de translação.

    Roteiro:
        A translação é a identidade com o deslocamento na terceira
        coluna: ``[[1, 0, tx], [0, 1, ty], [0, 0, 1]]``. É justamente
        por causa dela que se usa coordenada homogênea: sem a terceira
        linha, translação não caberia em uma matriz 2x2.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 10: implemente translacao()")


def escala(fator_x: float, fator_y: float | None = None) -> Matriz:
    """EXERCÍCIO 11: matriz de escala em torno da origem.

    Roteiro:
        Coloque ``fator_x`` e ``fator_y`` na diagonal. Quando
        ``fator_y`` vier ``None``, use escala uniforme. Lembre que a
        escala pura afasta a figura da origem: para escalar no lugar,
        combine com ``em_torno_de``.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 11: implemente escala()")


def rotacao(graus: float) -> Matriz:
    """EXERCÍCIO 12: matriz de rotação em torno da origem.

    Roteiro:
        Converta para radianos com ``math.radians``. A matriz é
        ``[[cos, -sen, 0], [sen, cos, 0], [0, 0, 1]]``. Como o eixo
        ``y`` da tela aponta para baixo, o giro aparece no sentido
        horário na prancheta: isso é esperado, não é bug.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 12: implemente rotacao()")


def cisalhamento(fator_x: float = 0.0, fator_y: float = 0.0) -> Matriz:
    """EXERCÍCIO 13: matriz de cisalhamento (shear).

    Roteiro:
        ``fator_x`` empurra ``x`` proporcionalmente a ``y`` e vice
        versa: ``[[1, fx, 0], [fy, 1, 0], [0, 0, 1]]``.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 13: implemente cisalhamento()")


def reflexao(eixo: str = "x") -> Matriz:
    """EXERCÍCIO 14: matriz de reflexão.

    Roteiro:
        ``"x"`` espelha em torno do eixo x (inverte o sinal de ``y``),
        ``"y"`` espelha em torno do eixo y e ``"origem"`` inverte os
        dois. Levante ``ValueError`` para qualquer outro valor.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 14: implemente reflexao()")


__all__ = [
    "Matriz", "Ponto", "identidade", "multiplica", "compoe", "aplica",
    "aplica_em", "arredonda", "centroide", "em_torno_de", "translacao",
    "escala", "rotacao", "cisalhamento", "reflexao",
]
