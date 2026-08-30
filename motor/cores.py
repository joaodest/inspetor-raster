"""Modelo de cor RGB de 8 bits e paleta padrao do motor.

Convencao adotada em todo o motor: uma cor e uma tripla imutavel
``(r, g, b)`` cujos componentes sao inteiros no intervalo [0, 255].
"""

from __future__ import annotations

from typing import NamedTuple

COMPONENTE_MINIMO = 0
COMPONENTE_MAXIMO = 255


def limita(valor: float,
           minimo: int = COMPONENTE_MINIMO,
           maximo: int = COMPONENTE_MAXIMO) -> int:
    """Restringe ``valor`` ao intervalo fechado ``[minimo, maximo]``.

    Args:
        valor: Numero a ser restringido (aceita float).
        minimo: Limite inferior do intervalo.
        maximo: Limite superior do intervalo.

    Returns:
        O inteiro mais proximo de ``valor`` dentro do intervalo.
    """
    return int(max(minimo, min(maximo, round(valor))))


class Cor(NamedTuple):
    """Cor RGB com um byte por canal.

    Por ser uma tupla nomeada, uma ``Cor`` e imutavel, comparavel por
    valor e pode ser desempacotada como ``r, g, b = cor``.
    """

    r: int
    g: int
    b: int

    @classmethod
    def segura(cls, r: float, g: float, b: float) -> Cor:
        """Cria uma cor limitando cada componente a [0, 255]."""
        return cls(limita(r), limita(g), limita(b))

    @classmethod
    def de_hex(cls, texto: str) -> Cor:
        """Converte ``"#RRGGBB"`` (ou ``"#RGB"``) em uma ``Cor``.

        Raises:
            ValueError: Se o texto nao for um hexadecimal valido.
        """
        digitos = texto.strip().lstrip("#")
        if len(digitos) == 3:
            digitos = "".join(d * 2 for d in digitos)
        if len(digitos) != 6:
            raise ValueError(f"cor hexadecimal invalida: {texto!r}")
        try:
            valor = int(digitos, 16)
        except ValueError as erro:
            raise ValueError(f"cor hexadecimal invalida: {texto!r}") from erro
        return cls((valor >> 16) & 0xFF, (valor >> 8) & 0xFF, valor & 0xFF)

    def para_hex(self) -> str:
        """Devolve a cor no formato ``"#rrggbb"`` usado em CSS."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def invertida(self) -> Cor:
        """Devolve o negativo da cor."""
        return Cor(COMPONENTE_MAXIMO - self.r,
                   COMPONENTE_MAXIMO - self.g,
                   COMPONENTE_MAXIMO - self.b)

    def luminancia(self) -> float:
        """Luminancia percebida (Rec. 601), util para tons de cinza."""
        return 0.299 * self.r + 0.587 * self.g + 0.114 * self.b

    def em_cinza(self) -> Cor:
        """Devolve a versao acromatica da cor."""
        tom = limita(self.luminancia())
        return Cor(tom, tom, tom)


def mistura(origem: Cor, destino: Cor, fator: float) -> Cor:
    """Interpola linearmente entre duas cores.

    Args:
        origem: Cor devolvida quando ``fator`` vale 0.
        destino: Cor devolvida quando ``fator`` vale 1.
        fator: Peso da interpolacao, restrito a [0, 1].

    Returns:
        A cor resultante da mistura.
    """
    peso = max(0.0, min(1.0, fator))
    return Cor.segura(
        origem.r + (destino.r - origem.r) * peso,
        origem.g + (destino.g - origem.g) * peso,
        origem.b + (destino.b - origem.b) * peso,
    )


def sobrepoe(fundo: Cor, frente: Cor, alfa: float) -> Cor:
    """Compoe ``frente`` sobre ``fundo`` com opacidade ``alfa``."""
    return mistura(fundo, frente, alfa)


PRETO = Cor(0, 0, 0)
BRANCO = Cor(255, 255, 255)
VERMELHO = Cor(220, 38, 38)
VERDE = Cor(22, 163, 74)
AZUL = Cor(37, 99, 235)
AMARELO = Cor(250, 204, 21)
CIANO = Cor(6, 182, 212)
MAGENTA = Cor(192, 38, 211)
LARANJA = Cor(234, 88, 12)
ROSA = Cor(236, 72, 153)
ROXO = Cor(124, 58, 237)
MARROM = Cor(120, 72, 40)
CINZA = Cor(128, 128, 128)
CINZA_CLARO = Cor(203, 213, 225)
CINZA_ESCURO = Cor(51, 65, 85)

PALETA: tuple[tuple[str, Cor], ...] = (
    ("preto", PRETO),
    ("branco", BRANCO),
    ("vermelho", VERMELHO),
    ("laranja", LARANJA),
    ("amarelo", AMARELO),
    ("verde", VERDE),
    ("ciano", CIANO),
    ("azul", AZUL),
    ("roxo", ROXO),
    ("magenta", MAGENTA),
    ("rosa", ROSA),
    ("marrom", MARROM),
    ("cinza claro", CINZA_CLARO),
    ("cinza", CINZA),
    ("cinza escuro", CINZA_ESCURO),
)
