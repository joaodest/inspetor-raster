"""Motor grafico raster: framebuffer, primitivas e instrumentacao.

Uso tipico::

    from motor import cria_tela, plota, PRETO, salva

    cria_tela(320, 240)
    plota(10, 10, PRETO)
    salva(tela(), "saidas/teste.png")

Os modulos ``primitivas``, ``preenchimento``, ``transformacoes`` e
``recorte`` guardam os exercicios; ``tracador`` e ``analise`` sao a
instrumentacao usada pela bancada.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

from .analise import Comparacao, Medida, Perfil, analisa, compara
from .cores import (
    AMARELO,
    AZUL,
    BRANCO,
    CIANO,
    CINZA,
    CINZA_CLARO,
    CINZA_ESCURO,
    LARANJA,
    MAGENTA,
    MARROM,
    PALETA,
    PRETO,
    ROSA,
    ROXO,
    VERDE,
    VERMELHO,
    Cor,
    limita,
    mistura,
    sobrepoe,
)
from .framebuffer import Framebuffer
from .imagem import (
    carrega_ppm,
    para_base64_png,
    para_base64_ppm,
    para_png,
    para_ppm,
    salva,
    salva_png,
    salva_ppm,
)
from .tela import (
    altura,
    cria_tela,
    define_tela,
    dentro,
    dimensoes,
    ha_tela,
    largura,
    le_pixel,
    limpa,
    plota,
    plota_disco,
    plota_pontos,
    tela,
)
from .tracador import LimiteDePassos, Passo, Rastro, rastreia

MODULOS_DE_EXERCICIO = (
    "motor.primitivas",
    "motor.preenchimento",
    "motor.transformacoes",
    "motor.recorte",
)

__all__ = [
    "AMARELO", "AZUL", "BRANCO", "CIANO", "CINZA", "CINZA_CLARO",
    "CINZA_ESCURO", "LARANJA", "MAGENTA", "MARROM", "PALETA", "PRETO",
    "ROSA", "ROXO", "VERDE", "VERMELHO",
    "Comparacao", "Cor", "Framebuffer", "LimiteDePassos", "Medida",
    "Passo", "Perfil", "Rastro",
    "altura", "analisa", "carrega_ppm", "compara", "cria_tela",
    "define_tela", "dentro", "dimensoes", "ha_tela", "largura", "le_pixel",
    "limita", "limpa", "mistura", "para_base64_png", "para_base64_ppm",
    "para_png", "para_ppm",
    "plota", "plota_disco", "plota_pontos", "rastreia", "recarrega",
    "salva", "salva_png", "salva_ppm", "sobrepoe", "tela",
]


def recarrega() -> list[ModuleType]:
    """Recarrega os modulos de exercicio sem reiniciar o processo.

    So os modulos que contem exercicios sao recarregados; o nucleo
    (``tela``, ``framebuffer``, ``tracador``) permanece intacto, para
    que o rastreador e a tela ativa sobrevivam a recarga. E o que
    permite a bancada redesenhar assim que o arquivo e salvo.

    Returns:
        Os modulos efetivamente recarregados, na ordem de dependencia.
    """
    recarregados = []
    for nome in MODULOS_DE_EXERCICIO:
        modulo = sys.modules.get(nome)
        modulo = (importlib.reload(modulo) if modulo
                  else importlib.import_module(nome))
        recarregados.append(modulo)
    return recarregados
