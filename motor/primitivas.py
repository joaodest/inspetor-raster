"""Primitivas de rasterização: retas, curvas e contornos.

Toda primitiva segue o mesmo contrato:

* recebe coordenadas em espaço de tela (origem no canto superior
  esquerdo, ``y`` crescendo para baixo);
* escreve exclusivamente por meio da função auxiliar ``plota``, que é o
  ponto observado pelo rastreador do inspetor;
* devolve a quantidade de pixels efetivamente acesos;
* aceita ``alvo=`` para desenhar fora da tela ativa.

``poligono`` já vem pronta e mostra o estilo esperado: nenhuma conta de
rasterização própria, apenas composição de primitivas mais simples. As
funções marcadas com ``NotImplementedError`` são os exercícios.
"""

from __future__ import annotations

from collections.abc import Sequence

from .cores import PRETO, Cor
from .framebuffer import Framebuffer
from .tela import plota, tela

Ponto = tuple[float, float]


def ponto(x: int, y: int, cor: Cor = PRETO, espessura: int = 1,
          alvo: Framebuffer | None = None) -> int:
    """Desenha um único ponto (envolve ``plota`` por simetria de API)."""
    return plota(x, y, cor, espessura, alvo)


def reta_dda(x0: float, y0: float, x1: float, y1: float,
             cor: Cor = PRETO, espessura: int = 1,
             alvo: Framebuffer | None = None) -> int:
    """EXERCÍCIO 1: reta pelo DDA (analisador diferencial digital).

    Roteiro:
        1. Arredonde as extremidades e calcule ``dx = x1 - x0`` e
           ``dy = y1 - y0``.
        2. ``passos = max(abs(dx), abs(dy))``. Se for zero, plote o
           ponto único e retorne.
        3. Os incrementos são ``dx / passos`` e ``dy / passos``: o eixo
           dominante anda 1 pixel por iteração, o outro anda a fração.
        4. Percorra ``passos + 1`` iterações plotando
           ``(round(x), round(y))`` e somando os incrementos.
        5. Acumule o retorno de cada ``plota`` e devolva o total.

    O que o inspetor vai mostrar: as variáveis ``x`` e ``y`` são float,
    então o painel classifica a aritmética como ponto flutuante, e o
    arredondamento costuma repetir pixels em retas quase horizontais.

    Args:
        x0: Coluna do ponto inicial.
        y0: Linha do ponto inicial.
        x1: Coluna do ponto final.
        y1: Linha do ponto final.
        cor: Cor do traço.
        espessura: Diâmetro do traço em pixels.
        alvo: Framebuffer alternativo.

    Returns:
        Quantidade de pixels acesos.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 1: implemente reta_dda()")


def reta_bresenham(x0: float, y0: float, x1: float, y1: float,
                   cor: Cor = PRETO, espessura: int = 1,
                   alvo: Framebuffer | None = None) -> int:
    """EXERCÍCIO 2: reta pelo ponto médio (Bresenham), só com inteiros.

    Roteiro:
        1. Arredonde as extremidades. Calcule ``dx = abs(x1 - x0)`` e
           ``dy = -abs(y1 - y0)``.
        2. Defina os sentidos ``sx`` e ``sy`` como ``+1`` ou ``-1``.
        3. Inicie o erro acumulado com ``erro = dx + dy``.
        4. Em laço infinito: plote ``(x, y)``; se chegou em
           ``(x1, y1)`` pare; calcule ``erro_dobro = 2 * erro``; se
           ``erro_dobro >= dy`` faça ``erro += dy`` e ``x += sx``; se
           ``erro_dobro <= dx`` faça ``erro += dx`` e ``y += sy``.
        5. Acumule o retorno de cada ``plota`` e devolva o total.

    O que o inspetor vai mostrar: nenhuma variável float, nenhum pixel
    repetido e nenhuma lacuna. Compare passo a passo com o DDA na
    entrada "DDA × Bresenham" do catálogo.

    Args:
        x0: Coluna do ponto inicial.
        y0: Linha do ponto inicial.
        x1: Coluna do ponto final.
        y1: Linha do ponto final.
        cor: Cor do traço.
        espessura: Diâmetro do traço em pixels.
        alvo: Framebuffer alternativo.

    Returns:
        Quantidade de pixels acesos.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 2: implemente reta_bresenham()")


def reta(x0: float, y0: float, x1: float, y1: float, cor: Cor = PRETO,
         espessura: int = 1, alvo: Framebuffer | None = None) -> int:
    """Traça um segmento com o melhor algoritmo disponível.

    Prefere ``reta_bresenham``; recai em ``reta_dda`` enquanto o
    exercício 2 não estiver pronto. As primitivas compostas
    (``poligono``, ``retangulo``, contornos de recorte) passam por aqui,
    então elas ganham vida assim que um dos dois algoritmos existir.
    """
    try:
        return reta_bresenham(x0, y0, x1, y1, cor, espessura, alvo)
    except NotImplementedError:
        return reta_dda(x0, y0, x1, y1, cor, espessura, alvo)


def poligono(pontos: Sequence[Ponto], cor: Cor = PRETO,
             espessura: int = 1, fechado: bool = True,
             alvo: Framebuffer | None = None) -> int:
    """Liga uma sequência de vértices com segmentos de reta.

    Args:
        pontos: Vértices na ordem em que devem ser ligados.
        cor: Cor do contorno.
        espessura: Diâmetro do traço.
        fechado: Quando ``True``, liga o último vértice ao primeiro.
        alvo: Framebuffer alternativo.

    Returns:
        Quantidade de pixels acesos.
    """
    quadro = tela(alvo)
    vertices = [(float(x), float(y)) for x, y in pontos]
    if not vertices:
        return 0
    if len(vertices) == 1:
        x, y = vertices[0]
        return plota(round(x), round(y), cor, espessura, quadro)

    caminho = vertices + [vertices[0]] if fechado else vertices
    acesos = 0
    for (xa, ya), (xb, yb) in zip(caminho, caminho[1:], strict=False):
        acesos += reta(xa, ya, xb, yb, cor, espessura, quadro)
    return acesos


def retangulo(x: float, y: float, largura: float, altura: float,
              cor: Cor = PRETO, espessura: int = 1,
              alvo: Framebuffer | None = None) -> int:
    """EXERCÍCIO 3: contorno de retângulo a partir do canto superior.

    Roteiro:
        1. Calcule o canto oposto ``(x + largura - 1, y + altura - 1)``.
        2. Monte a lista dos quatro vértices em sentido horário.
        3. Delegue o traço a ``poligono(..., fechado=True)``.

    Args:
        x: Coluna do canto superior esquerdo.
        y: Linha do canto superior esquerdo.
        largura: Largura em pixels.
        altura: Altura em pixels.
        cor: Cor do contorno.
        espessura: Diâmetro do traço.
        alvo: Framebuffer alternativo.

    Returns:
        Quantidade de pixels acesos.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 3: implemente retangulo()")


def circunferencia(centro_x: float, centro_y: float, raio: float,
                   cor: Cor = PRETO, espessura: int = 1,
                   alvo: Framebuffer | None = None) -> int:
    """EXERCÍCIO 4: circunferência pelo algoritmo do ponto médio.

    Roteiro:
        1. Rasterize apenas um octante, enquanto ``x <= y``.
        2. Comece com ``x = 0``, ``y = raio`` e ``decisao = 1 - raio``.
        3. A cada passo plote os oito pontos simétricos
           ``(±x, ±y)`` e ``(±y, ±x)`` somados ao centro.
        4. Se ``decisao < 0`` use ``decisao += 2 * x + 3``; caso
           contrário ``decisao += 2 * (x - y) + 5`` e ``y -= 1``.
        5. Incremente ``x`` e repita.

    Returns:
        Quantidade de pixels acesos.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 4: implemente circunferencia()")


def elipse(centro_x: float, centro_y: float, raio_x: float, raio_y: float,
           cor: Cor = PRETO, espessura: int = 1,
           alvo: Framebuffer | None = None) -> int:
    """EXERCÍCIO 5: elipse pelo ponto médio, em duas regiões.

    Roteiro:
        1. Região 1: enquanto a tangente for maior que -1, avance em
           ``x`` e decida sobre ``y`` pelo erro acumulado.
        2. Região 2: a partir dali, avance em ``y`` e decida sobre ``x``.
        3. Em ambas, plote os quatro pontos simétricos ``(±x, ±y)``
           somados ao centro.

    Returns:
        Quantidade de pixels acesos.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 5: implemente elipse()")


def bezier_cubica(p0: Ponto, p1: Ponto, p2: Ponto, p3: Ponto,
                  cor: Cor = PRETO, espessura: int = 1,
                  passos: int = 60,
                  alvo: Framebuffer | None = None) -> int:
    """EXERCÍCIO 6: curva de Bézier cúbica por amostragem.

    Roteiro:
        1. Para ``t`` de 0 a 1 em ``passos`` amostras, avalie
           ``B(t) = (1-t)^3 p0 + 3(1-t)^2 t p1
           + 3(1-t) t^2 p2 + t^3 p3``.
        2. Ligue cada amostra à anterior com ``reta``, para a curva não
           sair pontilhada quando ``passos`` for pequeno.

    Returns:
        Quantidade de pixels acesos.

    Raises:
        NotImplementedError: Enquanto o exercício não for resolvido.
    """
    raise NotImplementedError("EXERCÍCIO 6: implemente bezier_cubica()")
