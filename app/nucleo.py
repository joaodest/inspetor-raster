"""Execucao, memorizacao e reconstrucao de quadros.

A bancada e uma interface sem estado proprio: cada interacao recalcula
o resultado a partir dos parametros visiveis na tela (algoritmo, os dois
pontos, espessura). Para que isso nao custe caro, o ultimo punhado de
execucoes fica memorizado aqui.

E um cache de processo, nao de sessao: a bancada e uma ferramenta local
de uma pessoa so. Se um dia ela for servida para varios usuarios ao
mesmo tempo, este cache precisa virar estado por sessao.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import motor
from motor.analise import Comparacao, Perfil, analisa, compara
from motor.cores import BRANCO, PRETO, Cor
from motor.framebuffer import Framebuffer
from motor.tracador import Rastro, cronometra, rastreia

from . import tema
from .catalogo import CATALOGO, POR_CHAVE, Algoritmo, Cena, sonda
from .prancheta import ALTURA_DA_GRADE, LARGURA_DA_GRADE

TAMANHO_DO_CACHE = 6

Ponto = tuple[int, int]


@dataclass
class Resultado:
    """Tudo o que uma execucao produziu, pronto para a interface ler."""

    algoritmo: Algoritmo
    p0: Ponto
    p1: Ponto
    espessura: int
    base: bytes
    quadro: Framebuffer
    rastro: Rastro | None = None
    perfil: Perfil | None = None
    comparacao: Comparacao | None = None
    confrontados: tuple[Rastro, Rastro] | None = None

    @property
    def total(self) -> int:
        """Quantidade de passos percorriveis na trilha."""
        if self.comparacao is not None or self.rastro is None:
            return 0
        return len(self.rastro.passos)

    @property
    def pendente(self) -> bool:
        """Informa se o exercicio ainda nao foi implementado."""
        if self.confrontados is not None:
            return any(r.pendente for r in self.confrontados)
        return self.rastro is not None and self.rastro.pendente

    def passo(self, indice: int) -> object | None:
        """Passo de indice 1-based, ou ``None`` fora da faixa."""
        if self.rastro is None or not 1 <= indice <= len(self.rastro.passos):
            return None
        return self.rastro.passos[indice - 1]


_cache: OrderedDict[tuple, Resultado] = OrderedDict()


def limpa_cache() -> None:
    """Descarta os resultados memorizados; chamado apos recarregar."""
    _cache.clear()


def executa(chave: str, p0: Ponto, p1: Ponto, espessura: int) -> Resultado:
    """Roda o algoritmo escolhido e devolve o resultado memorizado."""
    assinatura = (chave, p0, p1, espessura)
    memorizado = _cache.get(assinatura)
    if memorizado is not None:
        _cache.move_to_end(assinatura)
        return memorizado

    algoritmo = POR_CHAVE[chave]
    resultado = (_confronta(algoritmo, p0, p1, espessura)
                 if algoritmo.eh_comparacao
                 else _executa_um(algoritmo, p0, p1, espessura))

    _cache[assinatura] = resultado
    while len(_cache) > TAMANHO_DO_CACHE:
        _cache.popitem(last=False)
    return resultado


def _tela_limpa() -> Framebuffer:
    """Framebuffer novo do tamanho da prancheta."""
    return Framebuffer(LARGURA_DA_GRADE, ALTURA_DA_GRADE, BRANCO)


def _executa_um(algoritmo: Algoritmo, p0: Ponto, p1: Ponto,
                espessura: int) -> Resultado:
    """Executa um algoritmo com rastreamento e cronometragem separadas."""
    quadro = _tela_limpa()
    cena = Cena(tela=quadro, p0=p0, p1=p1, cor=PRETO, espessura=espessura)
    _prepara(algoritmo, cena)
    base = quadro.instantaneo()

    rastro = rastreia(algoritmo.executa, cena, rotulo=algoritmo.nome)
    rastro.duracao_limpa = _cronometra(algoritmo, p0, p1, espessura)

    perfil = analisa(
        rastro,
        referencia=(*p0, *p1) if algoritmo.usa_referencia else None,
        espera_continuidade=algoritmo.continuo)
    return Resultado(algoritmo=algoritmo, p0=p0, p1=p1, espessura=espessura,
                     base=base, quadro=quadro, rastro=rastro, perfil=perfil)


def _cronometra(algoritmo: Algoritmo, p0: Ponto, p1: Ponto,
                espessura: int) -> float | None:
    """Mede a duracao do algoritmo sem a sobrecarga do rastreador."""
    if algoritmo.executa is None:
        return None
    quadro = _tela_limpa()
    cena = Cena(tela=quadro, p0=p0, p1=p1, cor=PRETO, espessura=espessura)
    if not _prepara(algoritmo, cena):
        return None
    return cronometra(algoritmo.executa, cena)


def _prepara(algoritmo: Algoritmo, cena: Cena) -> bool:
    """Desenha o cenario de apoio; devolve se ele pode ser montado."""
    if algoritmo.prepara is None:
        return True
    try:
        algoritmo.prepara(cena)
    except Exception:  # noqa: BLE001 - o cenario depende de exercicios
        return False
    return True


def _confronta(algoritmo: Algoritmo, p0: Ponto, p1: Ponto,
               espessura: int) -> Resultado:
    """Roda os dois algoritmos do confronto e pinta a divergencia."""
    primeiro, segundo = (POR_CHAVE[c] for c in algoritmo.comparacao)
    rastros = []
    for item in (primeiro, segundo):
        quadro = _tela_limpa()
        cena = Cena(tela=quadro, p0=p0, p1=p1, cor=PRETO,
                    espessura=espessura)
        rastros.append(rastreia(item.executa, cena, rotulo=item.nome))

    diferenca = compara(rastros[0], rastros[1], primeiro.nome, segundo.nome)
    quadro = _tela_limpa()
    for pixels, cor in ((diferenca.comuns, tema.TINTA),
                        (diferenca.apenas_a, tema.DIVERGENCIA_A),
                        (diferenca.apenas_b, tema.DIVERGENCIA_B)):
        tinta = Cor(*cor)
        for x, y in pixels:
            quadro.plota(x, y, tinta)

    return Resultado(algoritmo=algoritmo, p0=p0, p1=p1, espessura=espessura,
                     base=quadro.instantaneo(), quadro=quadro,
                     rastro=rastros[0], comparacao=diferenca,
                     confrontados=(rastros[0], rastros[1]))


def quadro_no_passo(resultado: Resultado, passo: int) -> Framebuffer:
    """Reconstroi o framebuffer com os primeiros ``passo`` passos.

    A reconstrucao e sempre feita do zero a partir do cenario de apoio.
    Custa alguns milissegundos mesmo em trilhas longas e evita a classe
    de bug em que o quadro exibido e o quadro real saem de sincronia.
    """
    if resultado.comparacao is not None or resultado.rastro is None:
        return resultado.quadro

    quadro = resultado.quadro
    quadro.restaura(resultado.base)
    for registro in resultado.rastro.passos[:passo]:
        if registro.escrito:
            quadro.plota(registro.x, registro.y, registro.cor)
    return quadro


def recarrega() -> str | None:
    """Recarrega os modulos de exercicio e limpa o cache.

    Returns:
        ``None`` se deu certo, ou a mensagem de erro do modulo do usuario.
    """
    try:
        motor.recarrega()
    except SyntaxError as erro:
        limpa_cache()
        arquivo = Path(erro.filename).name if erro.filename else "arquivo"
        return f"erro de sintaxe em {arquivo}, linha {erro.lineno}: {erro.msg}"
    except Exception as erro:  # noqa: BLE001 - o modulo e do usuario
        limpa_cache()
        return f"{type(erro).__name__}: {erro}"
    limpa_cache()
    return None


def estados_do_catalogo() -> dict[str, str]:
    """Sonda cada entrada do catalogo para saber o que ja roda.

    Returns:
        Mapa ``chave -> "pronto" | "pendente" | "erro"``.
    """
    rascunho = _tela_limpa()
    return {item.chave: sonda(item, rascunho) for item in CATALOGO}
