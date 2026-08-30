"""Tela ativa e funcoes auxiliares de desenho.

Este modulo mantem um framebuffer "corrente" para que o codigo do
usuario possa simplesmente chamar ``plota(x, y, cor)`` sem carregar o
buffer por toda parte. Todas as primitivas do motor aceitam tambem o
argumento opcional ``alvo=`` para trabalhar sobre outro buffer.
"""

from __future__ import annotations

from collections.abc import Iterable

from . import tracador
from .cores import BRANCO, PRETO, Cor
from .framebuffer import Framebuffer

_tela_ativa: Framebuffer | None = None


def cria_tela(largura_: int, altura_: int,
              cor_fundo: Cor = BRANCO) -> Framebuffer:
    """Cria um framebuffer e o define como tela ativa."""
    return define_tela(Framebuffer(largura_, altura_, cor_fundo))


def define_tela(framebuffer: Framebuffer) -> Framebuffer:
    """Torna ``framebuffer`` a tela ativa e o devolve."""
    global _tela_ativa
    _tela_ativa = framebuffer
    return framebuffer


def tela(alvo: Framebuffer | None = None) -> Framebuffer:
    """Resolve o framebuffer a ser usado por uma operacao.

    Args:
        alvo: Buffer explicito; quando ``None``, usa a tela ativa.

    Raises:
        RuntimeError: Se nao houver tela ativa nem alvo explicito.
    """
    if alvo is not None:
        return alvo
    if _tela_ativa is None:
        raise RuntimeError(
            "nenhuma tela ativa: chame cria_tela(largura, altura) antes")
    return _tela_ativa


def ha_tela() -> bool:
    """Informa se ja existe uma tela ativa."""
    return _tela_ativa is not None


def plota(x: int, y: int, cor: Cor = PRETO, espessura: int = 1,
          alvo: Framebuffer | None = None) -> int:
    """Acende o pixel ``(x, y)`` na tela ativa.

    E a funcao auxiliar basica do motor. Coordenadas fora da tela sao
    descartadas (recorte implicito), de modo que nenhuma primitiva
    precisa validar limites.

    E tambem o ponto observado pelo rastreador: com um rastro aberto,
    cada chamada vira um passo do inspetor, junto com a linha do seu
    codigo e as variaveis locais daquele instante.

    Args:
        x: Coluna do pixel.
        y: Linha do pixel.
        cor: Cor RGB a ser escrita.
        espessura: Diametro do traco; ``1`` escreve um unico ponto.
        alvo: Framebuffer alternativo (padrao: tela ativa).

    Returns:
        Quantidade de pixels efetivamente escritos.
    """
    quadro = tela(alvo)
    if espessura <= 1:
        escritos = 1 if quadro.plota(x, y, cor) else 0
    else:
        escritos = plota_disco(x, y, espessura / 2.0, cor, quadro)

    rastro = tracador.ativo()
    if rastro is not None:
        rastro.registra(x, y, cor, escritos > 0)
    return escritos


def plota_disco(x: int, y: int, raio: float, cor: Cor = PRETO,
                alvo: Framebuffer | None = None) -> int:
    """Acende um disco cheio de centro ``(x, y)``; util para pinceis."""
    quadro = tela(alvo)
    centro_x, centro_y = int(x), int(y)
    limite = max(0, int(raio))
    raio_quadrado = raio * raio
    escritos = 0
    for passo_y in range(-limite, limite + 1):
        for passo_x in range(-limite, limite + 1):
            if (passo_x * passo_x + passo_y * passo_y <= raio_quadrado
                    and quadro.plota(centro_x + passo_x,
                                     centro_y + passo_y, cor)):
                escritos += 1
    return escritos


def plota_pontos(pontos: Iterable[tuple[int, int]], cor: Cor = PRETO,
                 espessura: int = 1,
                 alvo: Framebuffer | None = None) -> int:
    """Aplica ``plota`` a uma sequencia de coordenadas."""
    quadro = tela(alvo)
    return sum(plota(x, y, cor, espessura, quadro) for x, y in pontos)


def le_pixel(x: int, y: int, alvo: Framebuffer | None = None) -> Cor | None:
    """Devolve a cor de ``(x, y)`` ou ``None`` se estiver fora da tela."""
    return tela(alvo).le(x, y)


def limpa(cor: Cor = BRANCO, alvo: Framebuffer | None = None) -> None:
    """Preenche a tela inteira com uma cor solida."""
    tela(alvo).limpa(cor)


def dentro(x: int, y: int, alvo: Framebuffer | None = None) -> bool:
    """Informa se ``(x, y)`` esta dentro da tela."""
    return tela(alvo).dentro(int(x), int(y))


def largura(alvo: Framebuffer | None = None) -> int:
    """Largura da tela em pixels."""
    return tela(alvo).largura


def altura(alvo: Framebuffer | None = None) -> int:
    """Altura da tela em pixels."""
    return tela(alvo).altura


def dimensoes(alvo: Framebuffer | None = None) -> tuple[int, int]:
    """Par ``(largura, altura)`` da tela."""
    return tela(alvo).dimensoes
