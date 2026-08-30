"""Rastreador de execucao: transforma um algoritmo em uma trilha legivel.

Enquanto um rastro esta aberto, cada chamada a ``tela.plota`` registra
um ``Passo`` contendo o pixel escrito, a linha exata do codigo-fonte
que pediu a escrita e uma fotografia das variaveis locais daquele
momento. E disso que o inspetor vive: nao ha nada a instrumentar no seu
algoritmo, basta ele usar ``plota``.

Duas travas protegem a interface de um laco infinito no algoritmo em
desenvolvimento: ``limite_de_passos`` e ``limite_de_tempo``. Quando uma
delas estoura, a execucao e interrompida com ``LimiteDePassos`` e o
rastro fica marcado como interrompido, com tudo o que ja foi desenhado
preservado para inspecao.
"""

from __future__ import annotations

import inspect
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .cores import Cor

LIMITE_DE_PASSOS = 40_000
LIMITE_DE_TEMPO = 4.0

_TIPOS_EXIBIVEIS = (Cor, bool, int, float, str)
_NOMES_IGNORADOS = frozenset({"alvo", "quadro", "self", "cls"})


class LimiteDePassos(RuntimeError):
    """Levantada quando um rastro excede as travas de seguranca."""


@dataclass(frozen=True)
class Fonte:
    """Codigo-fonte da funcao responsavel por um trecho do rastro."""

    funcao: str
    arquivo: str
    primeira_linha: int
    linhas: tuple[str, ...]

    def indice_da_linha(self, numero: int) -> int | None:
        """Converte um numero de linha do arquivo em indice local."""
        indice = numero - self.primeira_linha
        if 0 <= indice < len(self.linhas):
            return indice
        return None


@dataclass(frozen=True)
class Passo:
    """Uma unica chamada a ``plota`` capturada pelo rastreador."""

    indice: int
    x: int
    y: int
    cor: Cor
    escrito: bool
    funcao: str
    linha: int
    variaveis: Mapping[str, Any]

    @property
    def posicao(self) -> tuple[int, int]:
        """Par ``(x, y)`` do pixel visitado."""
        return self.x, self.y


@dataclass
class Rastro:
    """Resultado completo de uma execucao observada."""

    rotulo: str
    passos: list[Passo] = field(default_factory=list)
    fontes: dict[str, Fonte] = field(default_factory=dict)
    duracao: float = 0.0
    duracao_limpa: float | None = None
    retorno: Any = None
    erro: BaseException | None = None
    interrompido: bool = False
    limite_de_passos: int = LIMITE_DE_PASSOS
    limite_de_tempo: float = LIMITE_DE_TEMPO
    _inicio: float = 0.0

    @property
    def pendente(self) -> bool:
        """Informa se o algoritmo ainda e um exercicio nao resolvido."""
        return isinstance(self.erro, NotImplementedError)

    @property
    def falhou(self) -> bool:
        """Informa se a execucao terminou em erro de verdade."""
        return self.erro is not None and not self.pendente

    @property
    def escritos(self) -> list[Passo]:
        """Somente os passos que realmente acenderam um pixel."""
        return [passo for passo in self.passos if passo.escrito]

    def fonte_do_passo(self, passo: Passo) -> Fonte | None:
        """Codigo-fonte da funcao que executou um passo."""
        return self.fontes.get(passo.funcao)

    def registra(self, x: int, y: int, cor: Cor, escrito: bool) -> None:
        """Captura um passo; chamada exclusivamente por ``tela.plota``."""
        if len(self.passos) >= self.limite_de_passos:
            raise LimiteDePassos(
                f"o algoritmo passou de {self.limite_de_passos} chamadas a "
                "plota() sem terminar")
        if time.perf_counter() - self._inicio > self.limite_de_tempo:
            raise LimiteDePassos(
                f"o algoritmo passou de {self.limite_de_tempo:.0f}s de "
                "execucao sem terminar")

        try:
            frame = sys._getframe(2)
        except ValueError:  # pragma: no cover - profundidade insuficiente
            return

        fonte = self._fonte_do_frame(frame)
        self.passos.append(Passo(
            indice=len(self.passos),
            x=int(x),
            y=int(y),
            cor=cor,
            escrito=escrito,
            funcao=fonte.funcao,
            linha=frame.f_lineno,
            variaveis=_fotografa(frame.f_locals),
        ))

    def _fonte_do_frame(self, frame: Any) -> Fonte:
        """Recupera (e memoriza) o codigo-fonte da funcao em execucao."""
        codigo = frame.f_code
        nome = codigo.co_qualname
        fonte = self.fontes.get(nome)
        if fonte is None:
            fonte = _le_fonte(codigo, nome)
            self.fontes[nome] = fonte
        return fonte


_rastro_ativo: Rastro | None = None


def ativo() -> Rastro | None:
    """Devolve o rastro em captura, ou ``None`` fora de uma execucao."""
    return _rastro_ativo


def rastreia(funcao: Callable[..., Any], *args: Any,
             rotulo: str | None = None,
             limite_de_passos: int = LIMITE_DE_PASSOS,
             limite_de_tempo: float = LIMITE_DE_TEMPO,
             **kwargs: Any) -> Rastro:
    """Executa ``funcao`` capturando cada pixel que ela desenha.

    Excecoes levantadas pelo algoritmo nao escapam: elas ficam em
    ``rastro.erro``, para o inspetor poder mostrar o erro ao lado do que
    ja tinha sido desenhado ate ali.

    Args:
        funcao: Algoritmo a observar.
        *args: Argumentos posicionais repassados a ``funcao``.
        rotulo: Nome exibido no inspetor (padrao: nome da funcao).
        limite_de_passos: Trava de seguranca contra laco infinito.
        limite_de_tempo: Trava de seguranca em segundos.
        **kwargs: Argumentos nomeados repassados a ``funcao``.

    Returns:
        O rastro completo da execucao.
    """
    global _rastro_ativo

    rastro = Rastro(
        rotulo=rotulo or getattr(funcao, "__name__", "algoritmo"),
        limite_de_passos=limite_de_passos,
        limite_de_tempo=limite_de_tempo,
    )
    anterior = _rastro_ativo
    _rastro_ativo = rastro
    rastro._inicio = time.perf_counter()
    try:
        rastro.retorno = funcao(*args, **kwargs)
    except LimiteDePassos as erro:
        rastro.erro = erro
        rastro.interrompido = True
    except Exception as erro:  # noqa: BLE001 - o erro e o resultado aqui
        rastro.erro = erro
    finally:
        rastro.duracao = time.perf_counter() - rastro._inicio
        _rastro_ativo = anterior
    return rastro


def cronometra(funcao: Callable[..., Any], *args: Any,
               repeticoes: int = 3, **kwargs: Any) -> float | None:
    """Mede a duracao da funcao com o rastreador desligado.

    O rastreamento cobra caro por passo (uma fotografia das variaveis a
    cada pixel), entao o tempo do rastro nao serve como medida do
    algoritmo. Esta funcao roda de novo, limpa, e devolve o menor tempo
    entre as repeticoes: o menos contaminado por ruido do sistema.

    Args:
        funcao: Algoritmo a medir.
        *args: Argumentos posicionais; aponte-os para um framebuffer de
            rascunho, porque o desenho vai acontecer de novo.
        repeticoes: Quantidade de execucoes cronometradas.
        **kwargs: Argumentos nomeados.

    Returns:
        A menor duracao em segundos, ou ``None`` se a funcao falhar.
    """
    melhor: float | None = None
    for _ in range(max(1, repeticoes)):
        inicio = time.perf_counter()
        try:
            funcao(*args, **kwargs)
        except Exception:  # noqa: BLE001 - medir nunca deve derrubar a UI
            return None
        decorrido = time.perf_counter() - inicio
        melhor = decorrido if melhor is None else min(melhor, decorrido)
    return melhor


def _le_fonte(codigo: Any, nome: str) -> Fonte:
    """Le o codigo-fonte de um objeto de codigo, tolerando falhas."""
    try:
        linhas, primeira = inspect.getsourcelines(codigo)
    except (OSError, TypeError):  # pragma: no cover - fonte indisponivel
        return Fonte(nome, "<desconhecido>", 0, ())
    return Fonte(
        funcao=nome,
        arquivo=codigo.co_filename,
        primeira_linha=primeira or 1,
        linhas=tuple(linha.rstrip("\n") for linha in linhas),
    )


def _fotografa(locais: Mapping[str, Any]) -> dict[str, Any]:
    """Copia as variaveis locais que fazem sentido exibir no inspetor."""
    fotografia: dict[str, Any] = {}
    for nome, valor in locais.items():
        if nome.startswith("_") or nome in _NOMES_IGNORADOS:
            continue
        # Cor vem antes do ramo generico de tupla: por ser uma tupla
        # nomeada, ela cairia la e perderia a formatacao em hexadecimal.
        if isinstance(valor, _TIPOS_EXIBIVEIS):
            fotografia[nome] = valor
        elif (isinstance(valor, tuple | list) and len(valor) <= 4
                and all(isinstance(item, int | float) for item in valor)):
            fotografia[nome] = tuple(valor)
    return fotografia


def formata_valor(valor: Any) -> str:
    """Formata um valor de variavel para a tabela de estado."""
    if isinstance(valor, Cor):
        return valor.para_hex()
    if isinstance(valor, bool):
        return "sim" if valor else "nao"
    if isinstance(valor, float):
        if valor != valor or valor in (float("inf"), float("-inf")):
            return str(valor)
        if valor == int(valor) and abs(valor) < 1e15:
            return f"{valor:.1f}"
        texto = f"{valor:.4f}".rstrip("0")
        return texto + "0" if texto.endswith(".") else texto
    if isinstance(valor, tuple):
        return "(" + ", ".join(formata_valor(item) for item in valor) + ")"
    if isinstance(valor, str):
        return valor if len(valor) <= 24 else valor[:21] + "..."
    return str(valor)
