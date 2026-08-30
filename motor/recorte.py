"""Recorte (clipping) de segmentos e poligonos contra uma janela.

Recorte e o que separa o espaco do mundo do espaco de tela: antes de
rasterizar, descarta-se tudo que esta fora da janela de visualizacao.
O ``plota`` ja descarta pixel a pixel, mas isso é desperdício; o
recorte resolve o problema no nivel da geometria.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from .cores import PRETO, Cor
from .framebuffer import Framebuffer

Ponto = tuple[float, float]
Segmento = tuple[float, float, float, float]

DENTRO = 0b0000
ESQUERDA = 0b0001
DIREITA = 0b0010
ABAIXO = 0b0100
ACIMA = 0b1000

NOMES_DAS_REGIOES = (
    (ESQUERDA, "esquerda"),
    (DIREITA, "direita"),
    (ABAIXO, "abaixo"),
    (ACIMA, "acima"),
)


class Janela(NamedTuple):
    """Retângulo de recorte, com limites inclusivos."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def largura(self) -> float:
        """Largura da janela."""
        return self.x_max - self.x_min

    @property
    def altura(self) -> float:
        """Altura da janela."""
        return self.y_max - self.y_min

    def contem(self, x: float, y: float) -> bool:
        """Informa se o ponto está dentro da janela."""
        return (self.x_min <= x <= self.x_max
                and self.y_min <= y <= self.y_max)

    @property
    def vertices(self) -> tuple[Ponto, Ponto, Ponto, Ponto]:
        """Os quatro cantos, em sentido horário a partir do superior."""
        return ((self.x_min, self.y_min), (self.x_max, self.y_min),
                (self.x_max, self.y_max), (self.x_min, self.y_max))


def descreve_regiao(codigo: int) -> str:
    """Traduz um código de região para texto legível."""
    if codigo == DENTRO:
        return "dentro"
    return "+".join(nome for bit, nome in NOMES_DAS_REGIOES if codigo & bit)


def desenha_janela(janela: Janela, cor: Cor = PRETO, espessura: int = 1,
                   alvo: Framebuffer | None = None) -> int:
    """Traça o contorno da janela de recorte na tela."""
    from .primitivas import poligono

    return poligono(janela.vertices, cor, espessura, True, alvo)


def codigo_regiao(x: float, y: float, janela: Janela) -> int:
    """EXERCÍCIO 15: código de região de Cohen-Sutherland.

    Roteiro:
        Comece com ``codigo = DENTRO`` e acumule com ``|=``:
        ``ESQUERDA`` se ``x < janela.x_min``, ``DIREITA`` se
        ``x > janela.x_max``, ``ABAIXO`` se ``y < janela.y_min``,
        ``ACIMA`` se ``y > janela.y_max``.

    Returns:
        Inteiro de 4 bits identificando a região do ponto.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 15: implemente codigo_regiao()")


def recorta_linha(x0: float, y0: float, x1: float, y1: float,
                  janela: Janela) -> Segmento | None:
    """EXERCÍCIO 16: recorte de segmento por Cohen-Sutherland.

    Roteiro:
        1. Calcule os códigos das duas extremidades.
        2. Aceite de imediato se ``codigo_0 | codigo_1 == DENTRO``.
        3. Rejeite de imediato se ``codigo_0 & codigo_1 != 0`` (as duas
           pontas estão do mesmo lado de fora).
        4. Caso contrário, escolha a ponta de código não nulo, calcule
           a intersecção com a borda correspondente pela equação
           paramétrica da reta, substitua a ponta e repita.

    Returns:
        O segmento recortado ``(x0, y0, x1, y1)``, ou ``None`` quando o
        segmento está inteiramente fora da janela.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 16: implemente recorta_linha()")


def recorta_poligono(pontos: Sequence[Ponto],
                     janela: Janela) -> list[Ponto]:
    """EXERCÍCIO 17: recorte de polígono por Sutherland-Hodgman.

    Roteiro:
        1. Percorra as quatro bordas da janela, uma por vez.
        2. Para cada borda, varra as arestas do polígono atual: se o
           segundo vértice está dentro, emita a intersecção (quando o
           primeiro estava fora) e o próprio vértice; se só o primeiro
           estava dentro, emita apenas a intersecção.
        3. A saída de uma borda vira a entrada da próxima.

    Returns:
        Lista de vértices do polígono recortado (vazia se nada sobrou).

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 17: implemente recorta_poligono()")
