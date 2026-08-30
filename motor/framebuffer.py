"""Buffer de quadro (framebuffer): a memoria de video do motor.

Sistema de coordenadas
----------------------
A origem ``(0, 0)`` fica no canto superior esquerdo, ``x`` cresce para
a direita e ``y`` cresce para baixo, como em qualquer dispositivo
raster. O pixel ``(x, y)`` ocupa os tres bytes a partir do deslocamento
``(y * largura + x) * 3`` do vetor ``pixels``.
"""

from __future__ import annotations

from .cores import BRANCO, Cor

CANAIS = 3


class Framebuffer:
    """Matriz de pixels RGB sobre a qual todo o desenho acontece."""

    __slots__ = ("largura", "altura", "pixels")

    def __init__(self, largura: int, altura: int,
                 cor_fundo: Cor = BRANCO) -> None:
        """Cria um buffer de ``largura`` x ``altura`` pixels.

        Raises:
            ValueError: Se alguma dimensao nao for positiva.
        """
        if largura <= 0 or altura <= 0:
            raise ValueError("largura e altura devem ser positivas")
        self.largura = int(largura)
        self.altura = int(altura)
        self.pixels = bytearray(self.largura * self.altura * CANAIS)
        self.limpa(cor_fundo)

    @property
    def dimensoes(self) -> tuple[int, int]:
        """Par ``(largura, altura)`` em pixels."""
        return self.largura, self.altura

    def dentro(self, x: int, y: int) -> bool:
        """Informa se ``(x, y)`` cai dentro dos limites do buffer."""
        return 0 <= x < self.largura and 0 <= y < self.altura

    def indice(self, x: int, y: int) -> int:
        """Deslocamento em bytes do pixel ``(x, y)`` em ``pixels``."""
        return (y * self.largura + x) * CANAIS

    def le(self, x: int, y: int) -> Cor | None:
        """Devolve a cor de ``(x, y)`` ou ``None`` se estiver fora."""
        x, y = int(x), int(y)
        if not self.dentro(x, y):
            return None
        base = self.indice(x, y)
        return Cor(self.pixels[base], self.pixels[base + 1],
                   self.pixels[base + 2])

    def plota(self, x: int, y: int, cor: Cor) -> bool:
        """Acende um unico pixel; ignora coordenadas fora do buffer.

        Esta e a unica operacao de escrita elementar do motor: todas as
        primitivas devem terminar em chamadas a ela.

        Returns:
            ``True`` se o pixel foi escrito, ``False`` se descartado.
        """
        x, y = int(x), int(y)
        if not self.dentro(x, y):
            return False
        base = (y * self.largura + x) * CANAIS
        self.pixels[base] = cor[0]
        self.pixels[base + 1] = cor[1]
        self.pixels[base + 2] = cor[2]
        return True

    def limpa(self, cor: Cor = BRANCO) -> None:
        """Pinta o buffer inteiro com uma unica cor."""
        self.pixels[:] = bytes(cor) * (self.largura * self.altura)

    def instantaneo(self) -> bytes:
        """Congela o conteudo atual para posterior ``restaura``."""
        return bytes(self.pixels)

    def restaura(self, instantaneo: bytes) -> None:
        """Devolve o buffer ao estado capturado por ``instantaneo``.

        Raises:
            ValueError: Se o instantaneo tiver tamanho inesperado.
        """
        if len(instantaneo) != len(self.pixels):
            raise ValueError("instantaneo incompativel com o framebuffer")
        self.pixels[:] = instantaneo

    def copia(self) -> Framebuffer:
        """Cria um novo framebuffer com o mesmo conteudo."""
        clone = Framebuffer(self.largura, self.altura)
        clone.pixels[:] = self.pixels
        return clone

    def __repr__(self) -> str:
        """Representacao curta, com as dimensoes do buffer."""
        return f"Framebuffer({self.largura}x{self.altura})"
