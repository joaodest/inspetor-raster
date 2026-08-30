"""Entrada e saida de imagem, sem dependencias externas.

Sao suportados dois formatos: PPM binario (P6), trivial de escrever e
de ler, e PNG, escrito aqui com ``zlib`` da biblioteca padrao. Nenhum
dos dois depende de Pillow: o motor continua sem dependencia externa
mesmo entregando arquivo de imagem.
"""

from __future__ import annotations

import base64
import struct
import zlib
from pathlib import Path

from .cores import Cor
from .framebuffer import Framebuffer

ASSINATURA_PNG = b"\x89PNG\r\n\x1a\n"


def para_ppm(quadro: Framebuffer) -> bytes:
    """Serializa o framebuffer como PPM binario (P6)."""
    cabecalho = f"P6\n{quadro.largura} {quadro.altura}\n255\n"
    return cabecalho.encode("ascii") + bytes(quadro.pixels)


def para_base64_ppm(quadro: Framebuffer) -> str:
    """PPM em base64; util para transportar a imagem como texto."""
    return base64.b64encode(para_ppm(quadro)).decode("ascii")


def para_base64_png(quadro: Framebuffer, nivel: int = 1) -> str:
    """PNG em base64, para embutir a imagem como texto.

    O nivel de compressao padrao e baixo de proposito: quem recodifica
    a imagem a cada quadro de animacao prefere velocidade a tamanho de
    arquivo.
    """
    return base64.b64encode(para_png(quadro, nivel)).decode("ascii")


def salva_ppm(quadro: Framebuffer, caminho: str | Path) -> Path:
    """Grava o framebuffer em disco no formato PPM."""
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(para_ppm(quadro))
    return destino


def carrega_ppm(caminho: str | Path) -> Framebuffer:
    """Le um PPM binario (P6) de disco.

    Raises:
        ValueError: Se o arquivo nao for um P6 valido.
    """
    dados = Path(caminho).read_bytes()
    if not dados.startswith(b"P6"):
        raise ValueError("apenas PPM binario (P6) e suportado")

    campos: list[bytes] = []
    posicao = 2
    while len(campos) < 3:
        while posicao < len(dados) and dados[posicao:posicao + 1].isspace():
            posicao += 1
        if dados[posicao:posicao + 1] == b"#":
            while posicao < len(dados) and dados[posicao] != 0x0A:
                posicao += 1
            continue
        inicio = posicao
        while (posicao < len(dados)
               and not dados[posicao:posicao + 1].isspace()):
            posicao += 1
        campos.append(dados[inicio:posicao])

    largura, altura, maximo = (int(campo) for campo in campos)
    if maximo != 255:
        raise ValueError("apenas PPM de 8 bits por canal e suportado")

    corpo = dados[posicao + 1:]
    quadro = Framebuffer(largura, altura)
    esperado = largura * altura * 3
    if len(corpo) < esperado:
        raise ValueError("PPM truncado")
    quadro.pixels[:] = corpo[:esperado]
    return quadro


def _pedaco(tipo: bytes, dados: bytes) -> bytes:
    """Monta um chunk PNG com tamanho, tipo, dados e CRC."""
    crc = zlib.crc32(tipo + dados) & 0xFFFFFFFF
    return (struct.pack(">I", len(dados)) + tipo + dados
            + struct.pack(">I", crc))


def para_png(quadro: Framebuffer, nivel: int = 9) -> bytes:
    """Codifica o framebuffer como PNG RGB de 8 bits, sem filtros.

    Args:
        quadro: Framebuffer a codificar.
        nivel: Nivel de compressao do zlib, de 0 a 9.
    """
    linhas = bytearray()
    passo = quadro.largura * 3
    for inicio in range(0, len(quadro.pixels), passo):
        linhas.append(0)
        linhas += quadro.pixels[inicio:inicio + passo]

    cabecalho = struct.pack(">IIBBBBB", quadro.largura, quadro.altura,
                            8, 2, 0, 0, 0)
    return b"".join((
        ASSINATURA_PNG,
        _pedaco(b"IHDR", cabecalho),
        _pedaco(b"IDAT", zlib.compress(bytes(linhas), nivel)),
        _pedaco(b"IEND", b""),
    ))


def salva_png(quadro: Framebuffer, caminho: str | Path) -> Path:
    """Grava o framebuffer em disco no formato PNG."""
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(para_png(quadro))
    return destino


def salva(quadro: Framebuffer, caminho: str | Path) -> Path:
    """Grava escolhendo o formato pela extensao do arquivo.

    Raises:
        ValueError: Se a extensao nao for ``.png``, ``.ppm`` ou vazia.
    """
    destino = Path(caminho)
    extensao = destino.suffix.lower()
    if extensao in ("", ".png"):
        return salva_png(quadro, destino.with_suffix(".png"))
    if extensao == ".ppm":
        return salva_ppm(quadro, destino)
    raise ValueError(f"extensao nao suportada: {extensao}")


def histograma(quadro: Framebuffer) -> dict[Cor, int]:
    """Conta quantos pixels existem de cada cor presente na tela."""
    contagem: dict[Cor, int] = {}
    dados = quadro.pixels
    for inicio in range(0, len(dados), 3):
        cor = Cor(dados[inicio], dados[inicio + 1], dados[inicio + 2])
        contagem[cor] = contagem.get(cor, 0) + 1
    return contagem
