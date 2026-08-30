"""Operacoes de imagem que percorrem o framebuffer inteiro.

Diferente das primitivas, estas funcoes ja vem implementadas: elas nao
sao exercicio de rasterizacao, sao as operacoes de edicao que o Paint
oferece. Todas trabalham diretamente sobre o vetor ``pixels``, por isso
sao rapidas e nao aparecem no rastreador do inspetor.
"""

from __future__ import annotations

from .cores import COMPONENTE_MAXIMO, Cor, limita
from .framebuffer import CANAIS, Framebuffer
from .tela import tela


def inverte_cores(alvo: Framebuffer | None = None) -> None:
    """Troca cada componente pelo seu complemento."""
    quadro = tela(alvo)
    quadro.pixels[:] = bytes(COMPONENTE_MAXIMO - v for v in quadro.pixels)


def converte_para_cinza(alvo: Framebuffer | None = None) -> None:
    """Achata a imagem para tons de cinza pela luminancia Rec. 601."""
    quadro = tela(alvo)
    dados = quadro.pixels
    for inicio in range(0, len(dados), CANAIS):
        tom = limita(0.299 * dados[inicio]
                     + 0.587 * dados[inicio + 1]
                     + 0.114 * dados[inicio + 2])
        dados[inicio] = dados[inicio + 1] = dados[inicio + 2] = tom


def espelha_horizontal(alvo: Framebuffer | None = None) -> None:
    """Espelha a imagem da esquerda para a direita."""
    quadro = tela(alvo)
    passo = quadro.largura * CANAIS
    dados = quadro.pixels
    for inicio in range(0, len(dados), passo):
        linha = dados[inicio:inicio + passo]
        invertida = bytearray(passo)
        for coluna in range(quadro.largura):
            origem = coluna * CANAIS
            destino = (quadro.largura - 1 - coluna) * CANAIS
            invertida[destino:destino + CANAIS] = linha[origem:origem + CANAIS]
        dados[inicio:inicio + passo] = invertida


def espelha_vertical(alvo: Framebuffer | None = None) -> None:
    """Espelha a imagem de cima para baixo."""
    quadro = tela(alvo)
    passo = quadro.largura * CANAIS
    dados = quadro.pixels
    linhas = [bytes(dados[inicio:inicio + passo])
              for inicio in range(0, len(dados), passo)]
    dados[:] = b"".join(reversed(linhas))


def substitui_cor(procurada: Cor, nova: Cor,
                  alvo: Framebuffer | None = None) -> int:
    """Troca toda ocorrencia exata de uma cor por outra.

    Returns:
        Quantidade de pixels alterados.
    """
    quadro = tela(alvo)
    origem = bytes(procurada)
    destino = bytes(nova)
    dados = quadro.pixels
    trocados = 0
    for inicio in range(0, len(dados), CANAIS):
        if dados[inicio:inicio + CANAIS] == origem:
            dados[inicio:inicio + CANAIS] = destino
            trocados += 1
    return trocados


def mescla(fundo: Framebuffer, frente: Framebuffer,
           opacidade: float = 0.5) -> Framebuffer:
    """Combina dois framebuffers do mesmo tamanho em um novo.

    Raises:
        ValueError: Se os buffers tiverem dimensoes diferentes.
    """
    if fundo.dimensoes != frente.dimensoes:
        raise ValueError("os framebuffers precisam ter o mesmo tamanho")
    peso = max(0.0, min(1.0, opacidade))
    resultado = fundo.copia()
    resultado.pixels[:] = bytes(
        limita(a + (b - a) * peso)
        for a, b in zip(fundo.pixels, frente.pixels, strict=True)
    )
    return resultado
