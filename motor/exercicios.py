"""Registro dos exercicios do laboratorio.

Uma unica lista descreve os 17 exercicios do motor. O verificador de
linha de comando e a suite de testes leem daqui, entao nao existe uma
segunda copia da lista para sair de sincronia.

O estado de cada exercicio e apurado executando a funcao de verdade,
nunca lendo o codigo-fonte: so a execucao distingue "escrito" de
"funcionando".
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .cores import PRETO
from .framebuffer import Framebuffer
from .recorte import Janela

PRONTO = "pronto"
PENDENTE = "pendente"
COM_ERRO = "erro"

LARGURA_DE_PROVA = 40
ALTURA_DE_PROVA = 28


@dataclass(frozen=True)
class Exercicio:
    """Um exercicio do laboratorio e como prova-lo."""

    numero: int
    familia: str
    modulo: str
    funcao: str
    prova: Callable[[Framebuffer], Any]

    @property
    def caminho(self) -> str:
        """Caminho do arquivo, relativo a raiz do projeto."""
        return self.modulo.replace(".", "/") + ".py"

    @property
    def assinatura(self) -> str:
        """Como o exercicio aparece nas listagens."""
        return f"{self.modulo}.{self.funcao}()"

    def alvo(self) -> Callable[..., Any]:
        """Resolve a funcao no modulo, respeitando recargas a quente."""
        import importlib

        return getattr(importlib.import_module(self.modulo), self.funcao)


def _primitivas() -> Any:
    import importlib

    return importlib.import_module("motor.primitivas")


def _preenchimento() -> Any:
    import importlib

    return importlib.import_module("motor.preenchimento")


def _transformacoes() -> Any:
    import importlib

    return importlib.import_module("motor.transformacoes")


def _recorte() -> Any:
    import importlib

    return importlib.import_module("motor.recorte")


JANELA_DE_PROVA = Janela(8, 6, 30, 20)
QUADRADO_DE_PROVA = ((10, 8), (28, 8), (28, 18), (10, 18))

EXERCICIOS: tuple[Exercicio, ...] = (
    Exercicio(1, "Retas", "motor.primitivas", "reta_dda",
              lambda t: _primitivas().reta_dda(4, 3, 34, 22, PRETO, 1, t)),
    Exercicio(2, "Retas", "motor.primitivas", "reta_bresenham",
              lambda t: _primitivas().reta_bresenham(4, 3, 34, 22, PRETO, 1,
                                                     t)),
    Exercicio(3, "Contornos", "motor.primitivas", "retangulo",
              lambda t: _primitivas().retangulo(5, 4, 24, 16, PRETO, 1, t)),
    Exercicio(4, "Contornos", "motor.primitivas", "circunferencia",
              lambda t: _primitivas().circunferencia(20, 14, 9, PRETO, 1, t)),
    Exercicio(5, "Contornos", "motor.primitivas", "elipse",
              lambda t: _primitivas().elipse(20, 14, 14, 8, PRETO, 1, t)),
    Exercicio(6, "Curvas", "motor.primitivas", "bezier_cubica",
              lambda t: _primitivas().bezier_cubica(
                  (4, 22), (12, 2), (28, 26), (36, 5), PRETO, 1, 24, t)),
    Exercicio(7, "Preenchimento", "motor.preenchimento", "flood_fill",
              lambda t: _preenchimento().flood_fill(20, 14, PRETO, 4, t)),
    Exercicio(8, "Preenchimento", "motor.preenchimento", "preenche_contorno",
              lambda t: _com_moldura(t, lambda: _preenchimento(
              ).preenche_contorno(20, 14, PRETO, PRETO, 4, t))),
    Exercicio(9, "Preenchimento", "motor.preenchimento", "preenche_poligono",
              lambda t: _preenchimento().preenche_poligono(
                  QUADRADO_DE_PROVA, PRETO, t)),
    Exercicio(10, "Transformações", "motor.transformacoes", "translacao",
              lambda _t: _transformacoes().translacao(3, -2)),
    Exercicio(11, "Transformações", "motor.transformacoes", "escala",
              lambda _t: _transformacoes().escala(2, 0.5)),
    Exercicio(12, "Transformações", "motor.transformacoes", "rotacao",
              lambda _t: _transformacoes().rotacao(90)),
    Exercicio(13, "Transformações", "motor.transformacoes", "cisalhamento",
              lambda _t: _transformacoes().cisalhamento(0.5, 0)),
    Exercicio(14, "Transformações", "motor.transformacoes", "reflexao",
              lambda _t: _transformacoes().reflexao("x")),
    Exercicio(15, "Recorte", "motor.recorte", "codigo_regiao",
              lambda _t: _recorte().codigo_regiao(0, 0, JANELA_DE_PROVA)),
    Exercicio(16, "Recorte", "motor.recorte", "recorta_linha",
              lambda _t: _recorte().recorta_linha(0, 0, 39, 27,
                                                  JANELA_DE_PROVA)),
    Exercicio(17, "Recorte", "motor.recorte", "recorta_poligono",
              lambda _t: _recorte().recorta_poligono(QUADRADO_DE_PROVA,
                                                     JANELA_DE_PROVA)),
)

POR_FUNCAO = {exercicio.funcao: exercicio for exercicio in EXERCICIOS}


def _com_moldura(tela: Framebuffer, corpo: Callable[[], Any]) -> Any:
    """Desenha um contorno antes de provar um preenchimento por borda."""
    _primitivas().poligono(QUADRADO_DE_PROVA, PRETO, 1, True, tela)
    return corpo()


def tela_de_prova() -> Framebuffer:
    """Framebuffer pequeno usado pelas provas."""
    return Framebuffer(LARGURA_DE_PROVA, ALTURA_DE_PROVA)


def estado(exercicio: Exercicio) -> tuple[str, str]:
    """Executa a prova de um exercicio e classifica o resultado.

    Returns:
        Par ``(estado, detalhe)``, com estado em ``PRONTO``,
        ``PENDENTE`` ou ``COM_ERRO``.
    """
    tela = tela_de_prova()
    try:
        exercicio.prova(tela)
    except NotImplementedError:
        return PENDENTE, "ainda levanta NotImplementedError"
    except Exception as erro:  # noqa: BLE001 - o codigo provado e do usuario
        return COM_ERRO, f"{type(erro).__name__}: {erro}"
    return PRONTO, ""


def panorama() -> list[tuple[Exercicio, str, str]]:
    """Estado de todos os exercicios, na ordem do laboratorio."""
    return [(exercicio, *estado(exercicio)) for exercicio in EXERCICIOS]
