"""Algoritmos de preenchimento de regiões.

Todos escrevem por meio de ``plota`` e leem por meio de ``le_pixel``,
então o inspetor consegue animar o avanço do preenchimento pixel a
pixel, na mesma ordem em que o seu algoritmo decidiu visitar.

Cuidado recorrente: preenchimento recursivo estoura a pilha do Python
em regiões grandes (o limite padrão é cerca de mil chamadas). Use uma
pilha explícita (``lista.append`` / ``lista.pop``).
"""

from __future__ import annotations

from collections.abc import Sequence

from .cores import PRETO, Cor
from .framebuffer import Framebuffer
from .tela import le_pixel, plota, tela  # noqa: F401  (usados nos exercícios)

Ponto = tuple[float, float]

VIZINHOS_4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
VIZINHOS_8 = VIZINHOS_4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def vizinhanca(conectividade: int = 4) -> tuple[tuple[int, int], ...]:
    """Devolve os deslocamentos da vizinhança pedida.

    Args:
        conectividade: ``4`` para vizinhança cruz, ``8`` para incluir
            as diagonais.

    Raises:
        ValueError: Se a conectividade não for 4 nem 8.
    """
    if conectividade == 4:
        return VIZINHOS_4
    if conectividade == 8:
        return VIZINHOS_8
    raise ValueError("conectividade deve ser 4 ou 8")


def flood_fill(x: int, y: int, cor_nova: Cor = PRETO,
               conectividade: int = 4,
               alvo: Framebuffer | None = None) -> int:
    """EXERCÍCIO 7: preenchimento por inundação a partir de uma semente.

    Roteiro:
        1. Leia a cor da semente com ``le_pixel(x, y)``. Se ela já for
           ``cor_nova``, ou estiver fora da tela, devolva 0.
        2. Empilhe a semente. Enquanto a pilha não esvaziar: desempilhe
           um ponto, confira se a cor dele ainda é a cor original,
           plote ``cor_nova`` e empilhe os vizinhos.
        3. Use ``vizinhanca(conectividade)`` para obter os
           deslocamentos.

    Args:
        x: Coluna da semente.
        y: Linha da semente.
        cor_nova: Cor que preenche a região.
        conectividade: 4 ou 8 vizinhos.
        alvo: Framebuffer alternativo.

    Returns:
        Quantidade de pixels preenchidos.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 7: implemente flood_fill()")


def preenche_contorno(x: int, y: int, cor_preenchimento: Cor,
                      cor_contorno: Cor, conectividade: int = 4,
                      alvo: Framebuffer | None = None) -> int:
    """EXERCÍCIO 8: boundary fill: preenche até encontrar o contorno.

    Diferença para o ``flood_fill``: aqui o critério de parada não é a
    cor original da semente, e sim encontrar ``cor_contorno``. Serve
    para pintar dentro de uma figura já desenhada sobre um fundo
    qualquer.

    Roteiro:
        1. Empilhe a semente.
        2. Desempilhe; ignore se estiver fora, se a cor for
           ``cor_contorno`` ou se já for ``cor_preenchimento``.
        3. Plote e empilhe os vizinhos.

    Returns:
        Quantidade de pixels preenchidos.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 8: implemente preenche_contorno()")


def preenche_poligono(pontos: Sequence[Ponto], cor: Cor = PRETO,
                      alvo: Framebuffer | None = None) -> int:
    """EXERCÍCIO 9: preenchimento de polígono por varredura (scanline).

    Roteiro:
        1. Descubra a faixa de linhas ``y`` ocupada pelo polígono.
        2. Para cada ``y``, percorra as arestas e guarde a coluna de
           cada cruzamento. Conte a aresta apenas quando
           ``min(ya, yb) <= y < max(ya, yb)``, para não contar o
           vértice duas vezes.
        3. Ordene os cruzamentos e preencha os pares (0-1, 2-3, ...),
           que são os trechos internos pela regra par-ímpar.
        4. Plote cada pixel do trecho com ``plota``.

    Args:
        pontos: Vértices do polígono, em qualquer sentido.
        cor: Cor do preenchimento.
        alvo: Framebuffer alternativo.

    Returns:
        Quantidade de pixels preenchidos.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 9: implemente preenche_poligono()")


def area_da_cor(cor: Cor, alvo: Framebuffer | None = None) -> int:
    """Conta quantos pixels da tela estão exatamente nesta cor.

    Útil para conferir o resultado de um preenchimento sem depender do
    valor devolvido pelo algoritmo.
    """
    quadro = tela(alvo)
    procurado = bytes(cor)
    dados = quadro.pixels
    return sum(1 for inicio in range(0, len(dados), 3)
               if dados[inicio:inicio + 3] == procurado)
