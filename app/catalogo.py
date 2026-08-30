"""Catalogo de demonstracoes da bancada.

Cada entrada amarra um exercicio do motor a uma cena concreta: o que
desenhar, com quais argumentos, e o que os dois pontos arrastaveis da
prancheta significam naquele contexto. Um mesmo par de pontos vira
extremos de reta, centro e raio, semente de preenchimento ou angulo de
rotacao, dependendo do algoritmo escolhido.

As funcoes sao resolvidas pelo nome a cada execucao, nunca guardadas em
variavel: e isso que faz a recarga a quente valer: salvar o arquivo e
ver o desenho mudar, sem reiniciar a bancada.
"""

from __future__ import annotations

import importlib
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from motor import Cor, Framebuffer
from motor.cores import CINZA_CLARO, PRETO
from motor.recorte import Janela

PRONTO = "pronto"
PENDENTE = "pendente"
COM_ERRO = "erro"

Ponto = tuple[int, int]


@dataclass(frozen=True)
class Cena:
    """Tudo o que uma demonstracao precisa saber para se desenhar."""

    tela: Framebuffer
    p0: Ponto
    p1: Ponto
    cor: Cor = PRETO
    espessura: int = 1

    @property
    def deslocamento(self) -> tuple[int, int]:
        """Vetor ``p1 - p0``."""
        return self.p1[0] - self.p0[0], self.p1[1] - self.p0[1]

    @property
    def distancia(self) -> float:
        """Comprimento do vetor ``p1 - p0``."""
        return math.hypot(*self.deslocamento)

    @property
    def angulo(self) -> float:
        """Angulo de ``p1`` em torno de ``p0``, em graus."""
        dx, dy = self.deslocamento
        return math.degrees(math.atan2(dy, dx))

    @property
    def centro(self) -> tuple[float, float]:
        """Ponto medio entre ``p0`` e ``p1``."""
        return ((self.p0[0] + self.p1[0]) / 2, (self.p0[1] + self.p1[1]) / 2)

    @property
    def caixa(self) -> tuple[int, int, int, int]:
        """Retangulo ``(x, y, largura, altura)`` definido pelos pontos."""
        x = min(self.p0[0], self.p1[0])
        y = min(self.p0[1], self.p1[1])
        dx, dy = self.deslocamento
        return x, y, abs(dx) + 1, abs(dy) + 1

    def janela_de_recorte(self) -> Janela:
        """Janela fixa, com margem de um quarto da tela."""
        margem_x = self.tela.largura // 4
        margem_y = self.tela.altura // 4
        return Janela(margem_x, margem_y,
                      self.tela.largura - margem_x - 1,
                      self.tela.altura - margem_y - 1)

    def poligono_padrao(self, lados: int = 5) -> list[Ponto]:
        """Poligono regular inscrito na caixa dos dois pontos."""
        x, y, largura, altura = self.caixa
        raio_x = max(2.0, largura / 2)
        raio_y = max(2.0, altura / 2)
        centro_x, centro_y = x + raio_x, y + raio_y
        return [
            (round(centro_x + raio_x * math.cos(
                math.tau * indice / lados - math.pi / 2)),
             round(centro_y + raio_y * math.sin(
                 math.tau * indice / lados - math.pi / 2)))
            for indice in range(lados)
        ]


@dataclass(frozen=True)
class Algoritmo:
    """Uma entrada do catalogo."""

    chave: str
    familia: str
    nome: str
    resumo: str
    pontos: str
    alvo: tuple[str, str]
    executa: Callable[[Cena], Any] | None = None
    prepara: Callable[[Cena], None] | None = None
    continuo: bool = True
    usa_referencia: bool = False
    comparacao: tuple[str, str] = field(default=())  # type: ignore[assignment]

    @property
    def eh_comparacao(self) -> bool:
        """Informa se a entrada confronta dois algoritmos."""
        return bool(self.comparacao)

    def funcao(self) -> Callable[..., Any]:
        """Resolve a funcao alvo no modulo ja recarregado."""
        modulo, nome = self.alvo
        return getattr(importlib.import_module(modulo), nome)


def _reta_dda(cena: Cena) -> Any:
    funcao = importlib.import_module("motor.primitivas").reta_dda
    return funcao(*cena.p0, *cena.p1, cena.cor, cena.espessura, cena.tela)


def _reta_bresenham(cena: Cena) -> Any:
    funcao = importlib.import_module("motor.primitivas").reta_bresenham
    return funcao(*cena.p0, *cena.p1, cena.cor, cena.espessura, cena.tela)


def _retangulo(cena: Cena) -> Any:
    x, y, largura, altura = cena.caixa
    funcao = importlib.import_module("motor.primitivas").retangulo
    return funcao(x, y, largura, altura, cena.cor, cena.espessura, cena.tela)


def _circunferencia(cena: Cena) -> Any:
    funcao = importlib.import_module("motor.primitivas").circunferencia
    return funcao(*cena.p0, round(cena.distancia), cena.cor, cena.espessura,
                  cena.tela)


def _elipse(cena: Cena) -> Any:
    centro_x, centro_y = cena.centro
    dx, dy = cena.deslocamento
    funcao = importlib.import_module("motor.primitivas").elipse
    return funcao(round(centro_x), round(centro_y), max(1, abs(dx) // 2),
                  max(1, abs(dy) // 2), cena.cor, cena.espessura, cena.tela)


def _poligono(cena: Cena) -> Any:
    funcao = importlib.import_module("motor.primitivas").poligono
    return funcao(cena.poligono_padrao(5), cena.cor, cena.espessura, True,
                  cena.tela)


def _bezier(cena: Cena) -> Any:
    controle_a = (cena.p1[0], cena.p0[1])
    controle_b = (cena.p0[0], cena.p1[1])
    funcao = importlib.import_module("motor.primitivas").bezier_cubica
    return funcao(cena.p0, controle_a, controle_b, cena.p1, cena.cor,
                  cena.espessura, 48, cena.tela)


def _cena_com_contorno(cena: Cena) -> None:
    """Desenha o poligono que serve de recipiente aos preenchimentos."""
    poligono = importlib.import_module("motor.primitivas").poligono
    vertices = _contorno_fixo(cena)
    poligono(vertices, PRETO, 1, True, cena.tela)


def _contorno_fixo(cena: Cena) -> list[Ponto]:
    """Poligono centrado na tela, independente dos pontos arrastaveis."""
    largura, altura = cena.tela.dimensoes
    raio_x = largura * 0.36
    raio_y = altura * 0.36
    centro_x, centro_y = largura / 2, altura / 2
    return [
        (round(centro_x + raio_x * math.cos(math.tau * i / 7 - math.pi / 2)),
         round(centro_y + raio_y * math.sin(math.tau * i / 7 - math.pi / 2)))
        for i in range(7)
    ]


def _flood_fill(cena: Cena) -> Any:
    funcao = importlib.import_module("motor.preenchimento").flood_fill
    return funcao(*cena.p1, cena.cor, 4, cena.tela)


def _preenche_contorno(cena: Cena) -> Any:
    funcao = importlib.import_module("motor.preenchimento").preenche_contorno
    return funcao(*cena.p1, cena.cor, PRETO, 4, cena.tela)


def _preenche_poligono(cena: Cena) -> Any:
    funcao = importlib.import_module("motor.preenchimento").preenche_poligono
    return funcao(cena.poligono_padrao(5), cena.cor, cena.tela)


def _cena_do_recorte(cena: Cena) -> None:
    """Desenha a janela de recorte e o segmento inteiro, em cinza."""
    primitivas = importlib.import_module("motor.primitivas")
    recorte = importlib.import_module("motor.recorte")
    recorte.desenha_janela(cena.janela_de_recorte(), CINZA_CLARO, 1, cena.tela)
    primitivas.reta(*cena.p0, *cena.p1, CINZA_CLARO, 1, cena.tela)


def _recorta_linha(cena: Cena) -> Any:
    recorte = importlib.import_module("motor.recorte")
    primitivas = importlib.import_module("motor.primitivas")
    sobrou = recorte.recorta_linha(*cena.p0, *cena.p1,
                                   cena.janela_de_recorte())
    if sobrou is None:
        return 0
    return primitivas.reta(*sobrou, cena.cor, cena.espessura, cena.tela)


def _cena_do_poligono_original(cena: Cena) -> None:
    """Desenha o poligono de partida das transformacoes, em cinza."""
    primitivas = importlib.import_module("motor.primitivas")
    primitivas.poligono(_contorno_fixo(cena), CINZA_CLARO, 1, True, cena.tela)


def _transforma(cena: Cena) -> Any:
    transformacoes = importlib.import_module("motor.transformacoes")
    primitivas = importlib.import_module("motor.primitivas")
    largura, altura = cena.tela.dimensoes
    fator = max(0.25, min(2.0, cena.distancia / (min(largura, altura) * 0.3)))
    matriz = transformacoes.em_torno_de(
        transformacoes.compoe(transformacoes.rotacao(cena.angulo),
                              transformacoes.escala(fator)),
        largura / 2, altura / 2)
    vertices = transformacoes.arredonda(
        transformacoes.aplica_em(matriz, _contorno_fixo(cena)))
    return primitivas.poligono(vertices, cena.cor, cena.espessura, True,
                               cena.tela)


CATALOGO: tuple[Algoritmo, ...] = (
    Algoritmo(
        chave="dda",
        familia="Retas",
        nome="DDA",
        resumo="Passo unitário no eixo dominante e incremento fracionário "
               "no outro. Simples, mas carrega ponto flutuante até o fim.",
        pontos="os dois pontos são os extremos do segmento",
        alvo=("motor.primitivas", "reta_dda"),
        executa=_reta_dda,
        usa_referencia=True,
    ),
    Algoritmo(
        chave="bresenham",
        familia="Retas",
        nome="Bresenham",
        resumo="Decide o próximo pixel por um erro acumulado inteiro. "
               "Sem divisão, sem float, sem pixel repetido.",
        pontos="os dois pontos são os extremos do segmento",
        alvo=("motor.primitivas", "reta_bresenham"),
        executa=_reta_bresenham,
        usa_referencia=True,
    ),
    Algoritmo(
        chave="dda_x_bresenham",
        familia="Retas",
        nome="DDA × Bresenham",
        resumo="Roda os dois sobre o mesmo segmento e pinta a divergência: "
               "onde só um dos dois acendeu um pixel.",
        pontos="os dois pontos são os extremos do segmento",
        alvo=("motor.primitivas", "reta_dda"),
        comparacao=("dda", "bresenham"),
        usa_referencia=True,
    ),
    Algoritmo(
        chave="retangulo",
        familia="Contornos",
        nome="Retângulo",
        resumo="Composição pura: quatro vértices entregues ao polígono, "
               "que por sua vez chama a sua reta.",
        pontos="os dois pontos são cantos opostos",
        alvo=("motor.primitivas", "retangulo"),
        executa=_retangulo,
    ),
    Algoritmo(
        chave="circunferencia",
        familia="Contornos",
        nome="Circunferência",
        resumo="Ponto médio em um octante e oito reflexões por passo. "
               "Repare no salto entre pixels consecutivos da trilha.",
        pontos="p0 é o centro, p1 define o raio",
        alvo=("motor.primitivas", "circunferencia"),
        executa=_circunferencia,
        continuo=False,
    ),
    Algoritmo(
        chave="elipse",
        familia="Contornos",
        nome="Elipse",
        resumo="Ponto médio em duas regiões: troca de eixo dominante "
               "quando a tangente passa de -1.",
        pontos="os pontos são cantos da caixa que envolve a elipse",
        alvo=("motor.primitivas", "elipse"),
        executa=_elipse,
        continuo=False,
    ),
    Algoritmo(
        chave="poligono",
        familia="Contornos",
        nome="Polígono",
        resumo="Já implementado. Serve de teste da sua reta: cada aresta "
               "é uma chamada nova, com inclinação diferente.",
        pontos="os pontos definem a caixa do pentágono",
        alvo=("motor.primitivas", "poligono"),
        executa=_poligono,
    ),
    Algoritmo(
        chave="bezier",
        familia="Curvas",
        nome="Bézier cúbica",
        resumo="Amostragem paramétrica ligada por segmentos. Poucas "
               "amostras deixam a curva facetada, muitas repetem pixel.",
        pontos="os pontos são as âncoras; os controles saem deles",
        alvo=("motor.primitivas", "bezier_cubica"),
        executa=_bezier,
    ),
    Algoritmo(
        chave="flood_fill",
        familia="Preenchimento",
        nome="Flood fill",
        resumo="Inundação a partir de uma semente, trocando a cor "
               "original. A ordem da trilha revela a estrutura da pilha.",
        pontos="p1 é a semente; clique para movê-la",
        alvo=("motor.preenchimento", "flood_fill"),
        executa=_flood_fill,
        prepara=_cena_com_contorno,
        continuo=False,
    ),
    Algoritmo(
        chave="preenche_contorno",
        familia="Preenchimento",
        nome="Boundary fill",
        resumo="Mesma inundação, critério de parada diferente: para no "
               "contorno, não na troca de cor.",
        pontos="p1 é a semente; clique para movê-la",
        alvo=("motor.preenchimento", "preenche_contorno"),
        executa=_preenche_contorno,
        prepara=_cena_com_contorno,
        continuo=False,
    ),
    Algoritmo(
        chave="preenche_poligono",
        familia="Preenchimento",
        nome="Varredura (scanline)",
        resumo="Linha a linha, cruzamentos ordenados e pares preenchidos. "
               "A trilha desce a tela em ordem, sem pilha nenhuma.",
        pontos="os pontos definem a caixa do pentágono",
        alvo=("motor.preenchimento", "preenche_poligono"),
        executa=_preenche_poligono,
        continuo=False,
    ),
    Algoritmo(
        chave="recorte",
        familia="Composições",
        nome="Recorte de segmento",
        resumo="Cohen-Sutherland corta o segmento na janela e só o trecho "
               "que sobrou vai para a rasterização.",
        pontos="os dois pontos são os extremos do segmento",
        alvo=("motor.recorte", "recorta_linha"),
        executa=_recorta_linha,
        prepara=_cena_do_recorte,
    ),
    Algoritmo(
        chave="transformacoes",
        familia="Composições",
        nome="Rotação e escala",
        resumo="Matrizes homogêneas aplicadas aos vértices antes da "
               "rasterização. O cinza é a figura original.",
        pontos="p1 gira em torno de p0: ângulo e distância viram a matriz",
        alvo=("motor.transformacoes", "rotacao"),
        executa=_transforma,
        prepara=_cena_do_poligono_original,
    ),
)

POR_CHAVE = {algoritmo.chave: algoritmo for algoritmo in CATALOGO}


def itens_da_lista() -> list[tuple[str, str, str]]:
    """Triplas ``(chave, familia, nome)`` para montar a lista lateral."""
    return [(a.chave, a.familia, a.nome) for a in CATALOGO]


def sonda(algoritmo: Algoritmo, tela: Framebuffer) -> str:
    """Descobre se o exercicio de uma entrada ja foi resolvido.

    A entrada e executada de verdade sobre um framebuffer de rascunho,
    sem rastreamento. E a unica forma honesta de responder: ler o
    codigo-fonte diria apenas o que esta escrito, nao o que roda.

    Returns:
        ``PRONTO``, ``PENDENTE`` ou ``COM_ERRO``.
    """
    cena = Cena(tela=tela,
                p0=(tela.largura // 4, tela.altura // 2),
                p1=(tela.largura * 3 // 4, tela.altura // 3))
    alvos = ([POR_CHAVE[chave] for chave in algoritmo.comparacao]
             if algoritmo.eh_comparacao else [algoritmo])
    for item in alvos:
        if item.executa is None:
            continue
        tela.limpa()
        try:
            if item.prepara is not None:
                item.prepara(cena)
            item.executa(cena)
        except NotImplementedError:
            return PENDENTE
        except Exception:  # noqa: BLE001 - a sonda nunca derruba a bancada
            return COM_ERRO
    return PRONTO
