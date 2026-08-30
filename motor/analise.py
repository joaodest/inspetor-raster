"""Perfil analitico de um rastro de execucao.

Enquanto o ``tracador`` captura o que aconteceu, este modulo interpreta.
As medidas foram escolhidas para responder as perguntas que aparecem ao
comparar dois algoritmos de rasterizacao:

* o traco tem buraco? (continuidade)
* algum pixel foi escrito duas vezes? (trabalho repetido)
* a conta e inteira ou usa ponto flutuante? (custo por passo)
* o resultado fica quantos pixels longe da reta exata? (fidelidade)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .tracador import Passo, Rastro

TOM_NEUTRO = "neutro"
TOM_BOM = "bom"
TOM_ALERTA = "alerta"
TOM_RUIM = "ruim"

MEIA_DIAGONAL = math.sqrt(2.0) / 2.0

Segmento = tuple[float, float, float, float]


@dataclass(frozen=True)
class Medida:
    """Uma linha do painel analitico."""

    rotulo: str
    valor: str
    detalhe: str = ""
    tom: str = TOM_NEUTRO


@dataclass(frozen=True)
class Perfil:
    """Leitura completa de um rastro."""

    passos: int
    pixels: int
    repetidos: int
    descartados: int
    duracao_ms: float
    aritmetica: str
    duracao_limpa: bool
    variaveis: tuple[str, ...]
    maior_salto: int
    espera_continuidade: bool
    desvio_maximo: float | None
    desvio_medio: float | None
    caixa: tuple[int, int, int, int] | None

    @property
    def continuo(self) -> bool:
        """Informa se o traco nao deixou lacunas entre passos."""
        return self.maior_salto <= 1

    def medidas(self) -> list[Medida]:
        """Monta as linhas exibidas no painel, na ordem de leitura."""
        linhas = [
            Medida("passos", f"{self.passos}",
                   "chamadas a plota()"),
            Medida("pixels", f"{self.pixels}",
                   "posições distintas acesas"),
            Medida("duração", _formata_duracao(self.duracao_ms),
                   "execução limpa, sem o rastreador"
                   if self.duracao_limpa
                   else "inclui a sobrecarga do rastreador"),
            Medida("aritmética", self.aritmetica,
                   "tipos das variáveis observadas",
                   TOM_BOM if self.aritmetica == "inteira" else TOM_NEUTRO),
        ]

        if self.espera_continuidade:
            linhas.append(Medida(
                "continuidade",
                ("sem lacunas" if self.continuo
                 else f"salto de {self.maior_salto} px"),
                "distância entre passos consecutivos",
                TOM_BOM if self.continuo else TOM_RUIM,
            ))
        elif self.maior_salto > 1:
            linhas.append(Medida(
                "maior salto", f"{self.maior_salto} px",
                "esperado em algoritmos com simetria"))

        linhas.append(Medida(
            "repetidos", f"{self.repetidos}",
            "pixels escritos mais de uma vez",
            TOM_BOM if self.repetidos == 0 else TOM_ALERTA))

        if self.descartados:
            linhas.append(Medida(
                "fora da tela", f"{self.descartados}",
                "descartados pelo recorte do plota()", TOM_ALERTA))

        if self.desvio_maximo is not None:
            linhas.append(Medida(
                "desvio máximo", f"{self.desvio_maximo:.3f} px",
                "distância do pixel mais distante até a reta exata",
                TOM_BOM if self.desvio_maximo <= MEIA_DIAGONAL else TOM_RUIM))
            linhas.append(Medida(
                "desvio médio", f"{self.desvio_medio:.3f} px",
                "média das distâncias até a reta exata"))

        return linhas


@dataclass(frozen=True)
class Comparacao:
    """Diferenca entre os pixels produzidos por dois algoritmos."""

    rotulo_a: str
    rotulo_b: str
    comuns: frozenset[tuple[int, int]]
    apenas_a: frozenset[tuple[int, int]]
    apenas_b: frozenset[tuple[int, int]]

    @property
    def concordancia(self) -> float:
        """Fracao de pixels em que os dois algoritmos concordam."""
        total = len(self.comuns) + len(self.apenas_a) + len(self.apenas_b)
        return len(self.comuns) / total if total else 1.0

    @property
    def identicos(self) -> bool:
        """Informa se os dois algoritmos produziram o mesmo traco."""
        return not self.apenas_a and not self.apenas_b

    def medidas(self) -> list[Medida]:
        """Linhas do painel para o modo de comparacao."""
        return [
            Medida("concordância", f"{self.concordancia * 100:.1f}%",
                   "pixels iguais nos dois traços",
                   TOM_BOM if self.identicos else TOM_ALERTA),
            Medida("em comum", f"{len(self.comuns)}", "acesos pelos dois"),
            Medida(f"só {self.rotulo_a}", f"{len(self.apenas_a)}",
                   "pixels exclusivos"),
            Medida(f"só {self.rotulo_b}", f"{len(self.apenas_b)}",
                   "pixels exclusivos"),
        ]


def analisa(rastro: Rastro, referencia: Segmento | None = None,
            espera_continuidade: bool = True) -> Perfil:
    """Le um rastro e devolve o perfil analitico correspondente.

    Args:
        rastro: Execucao capturada pelo ``tracador``.
        referencia: Segmento exato ``(x0, y0, x1, y1)`` usado para medir
            a fidelidade; ``None`` desliga as medidas de desvio.
        espera_continuidade: ``True`` para algoritmos que percorrem um
            caminho continuo (retas, curvas); ``False`` para os que
            saltam por simetria (circunferencia, elipse).

    Returns:
        O perfil pronto para exibicao.
    """
    escritos = rastro.escritos
    posicoes = [passo.posicao for passo in escritos]
    unicos = set(posicoes)

    desvio_maximo: float | None = None
    desvio_medio: float | None = None
    if referencia is not None and posicoes:
        desvios = [_distancia_ate_a_reta(x, y, *referencia)
                   for x, y in posicoes]
        desvio_maximo = max(desvios)
        desvio_medio = sum(desvios) / len(desvios)

    return Perfil(
        passos=len(rastro.passos),
        pixels=len(unicos),
        repetidos=len(posicoes) - len(unicos),
        descartados=len(rastro.passos) - len(escritos),
        duracao_ms=(rastro.duracao_limpa if rastro.duracao_limpa is not None
                    else rastro.duracao) * 1000.0,
        aritmetica=_classifica_aritmetica(rastro.passos),
        duracao_limpa=rastro.duracao_limpa is not None,
        variaveis=_variaveis_observadas(rastro.passos),
        maior_salto=_maior_salto(posicoes),
        espera_continuidade=espera_continuidade,
        desvio_maximo=desvio_maximo,
        desvio_medio=desvio_medio,
        caixa=_caixa(posicoes),
    )


def compara(rastro_a: Rastro, rastro_b: Rastro,
            rotulo_a: str, rotulo_b: str) -> Comparacao:
    """Confronta os pixels produzidos por duas execucoes."""
    pixels_a = {passo.posicao for passo in rastro_a.escritos}
    pixels_b = {passo.posicao for passo in rastro_b.escritos}
    return Comparacao(
        rotulo_a=rotulo_a,
        rotulo_b=rotulo_b,
        comuns=frozenset(pixels_a & pixels_b),
        apenas_a=frozenset(pixels_a - pixels_b),
        apenas_b=frozenset(pixels_b - pixels_a),
    )


def _classifica_aritmetica(passos: list[Passo]) -> str:
    """Descobre se o algoritmo trabalhou com inteiros ou com floats."""
    viu_variavel = False
    for passo in passos:
        for nome, valor in passo.variaveis.items():
            if nome == "cor":
                continue
            viu_variavel = True
            if isinstance(valor, float):
                return "ponto flutuante"
            if isinstance(valor, tuple) and any(
                    isinstance(item, float) for item in valor):
                return "ponto flutuante"
    return "inteira" if viu_variavel else "-"


def _variaveis_observadas(passos: list[Passo]) -> tuple[str, ...]:
    """Nomes das variaveis capturadas, na ordem em que apareceram."""
    nomes: dict[str, None] = {}
    for passo in passos:
        for nome in passo.variaveis:
            nomes.setdefault(nome, None)
    return tuple(nomes)


def _maior_salto(posicoes: list[tuple[int, int]]) -> int:
    """Maior distancia de Chebyshev entre dois passos consecutivos."""
    maior = 0
    for (xa, ya), (xb, yb) in zip(posicoes, posicoes[1:], strict=False):
        maior = max(maior, abs(xb - xa), abs(yb - ya))
    return maior


def _caixa(posicoes: list[tuple[int, int]]
           ) -> tuple[int, int, int, int] | None:
    """Retangulo envolvente dos pixels acesos."""
    if not posicoes:
        return None
    xs = [x for x, _ in posicoes]
    ys = [y for _, y in posicoes]
    return min(xs), min(ys), max(xs), max(ys)


def _distancia_ate_a_reta(px: float, py: float, x0: float, y0: float,
                          x1: float, y1: float) -> float:
    """Distancia perpendicular de um ponto ate a reta que passa por dois."""
    dx = x1 - x0
    dy = y1 - y0
    comprimento = math.hypot(dx, dy)
    if comprimento == 0.0:
        return math.hypot(px - x0, py - y0)
    return abs(dy * px - dx * py + x1 * y0 - y1 * x0) / comprimento


def _formata_duracao(milissegundos: float) -> str:
    """Formata a duracao na unidade mais legivel."""
    if milissegundos < 1.0:
        return f"{milissegundos * 1000:.0f} us"
    if milissegundos < 1000.0:
        return f"{milissegundos:.2f} ms"
    return f"{milissegundos / 1000:.2f} s"
