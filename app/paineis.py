"""Montagem do HTML dos paineis de leitura.

Tres blocos vivem no trilho direito e mudam a cada passo:

* **perfil analitico**: o que a execucao inteira produziu;
* **estado no passo**: as variaveis do seu codigo naquele instante,
  com destaque no que mudou desde o passo anterior;
* **codigo em execucao**: a sua funcao com a linha que plotou o pixel
  em foco, e quantas vezes cada linha plotou.

Quando o exercicio ainda nao foi feito, o perfil da lugar ao roteiro
lido da propria docstring da funcao: nada aqui e duplicado a mao.
"""

from __future__ import annotations

import re
from html import escape

from motor.analise import Medida
from motor.tracador import Passo, formata_valor

from . import tema
from .nucleo import Resultado

LINHAS_DE_CONTEXTO = 12


def cabecalho(resultado: Resultado) -> str:
    """Barra superior: marca, chamada corrente e selo de estado."""
    modulo, funcao = resultado.algoritmo.alvo
    texto, cor = _estado(resultado)
    return f"""
<div class="cabecalho">
  <span class="marca">Inspetor Raster</span>
  <span class="disciplina">computação gráfica</span>
  <span class="chamada">{escape(modulo)}.{escape(funcao)}()
    &nbsp;·&nbsp; p0 {resultado.p0} &nbsp;→&nbsp; p1 {resultado.p1}</span>
  <span class="selo" style="color:{cor}">{escape(texto)}</span>
</div>"""


def _estado(resultado: Resultado) -> tuple[str, str]:
    """Par (texto, cor) que resume o resultado da ultima execucao."""
    if resultado.comparacao is not None:
        if resultado.pendente:
            return "falta um dos dois", tema.SINAL
        if resultado.comparacao.identicos:
            return "traços idênticos", tema.OK
        return "traços divergem", tema.ALERTA
    rastro = resultado.rastro
    if rastro is None:
        return "sem dados", tema.TEXTO_FRACO
    if rastro.pendente:
        return "a fazer", tema.SINAL
    if rastro.interrompido:
        return "interrompido", tema.ERRO
    if rastro.falhou:
        return type(rastro.erro).__name__, tema.ERRO
    return "executado", tema.OK


def perfil(resultado: Resultado) -> str:
    """Bloco de medidas, roteiro do exercicio ou relato de erro."""
    partes = ['<p class="resumo">'
              + escape(resultado.algoritmo.resumo) + "</p>",
              '<p class="rotulo">perfil analítico</p>']

    rastro = resultado.rastro
    if resultado.pendente:
        partes.append(_roteiro(resultado))
    elif rastro is not None and rastro.falhou:
        partes.append(_erro(resultado))
    else:
        medidas = (resultado.comparacao.medidas()
                   if resultado.comparacao is not None
                   else resultado.perfil.medidas() if resultado.perfil
                   else [])
        partes.extend(_medida(m) for m in medidas)
        if rastro is not None and rastro.interrompido:
            partes.append(
                f'<p class="pista" style="color:{tema.ERRO}">'
                f"{escape(str(rastro.erro))}</p>")
    return "\n".join(partes)


def _medida(medida: Medida) -> str:
    """Uma linha rotulo/valor com a explicacao logo abaixo."""
    cor = tema.TONS.get(medida.tom, tema.TEXTO_MEDIO)
    detalhe = (f'<div class="detalhe">{escape(medida.detalhe)}</div>'
               if medida.detalhe else "")
    return (f'<div class="medida"><span class="nome">'
            f'{escape(medida.rotulo)}</span>'
            f'<span class="valor" style="color:{cor}">'
            f'{escape(medida.valor)}</span></div>{detalhe}')


def _roteiro(resultado: Resultado) -> str:
    """Roteiro do exercicio, extraido da docstring da funcao alvo."""
    modulo, funcao = resultado.algoritmo.alvo
    arquivo = modulo.replace(".", "/") + ".py"
    passos = _passos_da_docstring(resultado)
    itens = "".join(f"<li>{_com_codigo(p)}</li>" for p in passos)
    return (f'<p class="aviso"><strong>{escape(funcao)}()</strong> ainda '
            f'levanta NotImplementedError. Escreva o algoritmo em '
            f'<span class="arquivo">{escape(arquivo)}</span> e use '
            f'<em>recarregar módulos</em> para ver o resultado aqui.</p>'
            f'<ol class="roteiro">{itens}</ol>')


def _passos_da_docstring(resultado: Resultado) -> list[str]:
    """Le a secao ``Roteiro:`` da docstring do alvo."""
    try:
        documento = resultado.algoritmo.funcao().__doc__ or ""
    except Exception:  # noqa: BLE001 - o modulo pode estar quebrado
        return []
    linhas = documento.splitlines()
    try:
        inicio = next(i for i, linha in enumerate(linhas)
                      if linha.strip() == "Roteiro:")
    except StopIteration:
        return []

    passos: list[str] = []
    for linha in linhas[inicio + 1:]:
        texto = linha.strip()
        if not texto:
            continue
        if texto.endswith(":") and not texto[0].isdigit():
            break
        if texto[0].isdigit() or not passos:
            passos.append(re.sub(r"^\d+\.\s*", "", texto))
        else:
            passos[-1] += " " + texto
    return passos


def _com_codigo(texto: str) -> str:
    """Escapa o texto e converte ``assim`` da docstring em <code>."""
    return re.sub(r"``(.+?)``", r"<code>\g<1></code>", escape(texto))


def _erro(resultado: Resultado) -> str:
    """Relato da excecao levantada pelo algoritmo do usuario."""
    rastro = resultado.rastro
    erro = rastro.erro if rastro else None
    desenhados = len(rastro.passos) if rastro else 0
    return (f'<p class="aviso"><strong style="color:{tema.ERRO}">'
            f'{escape(type(erro).__name__)}</strong><br>'
            f'{escape(str(erro))}</p>'
            f'<p class="pista">os {desenhados} passos desenhados antes do '
            f'erro continuam na trilha, e o código abaixo marca onde '
            f'a execução parou.</p>')


def estado(resultado: Resultado, indice: int) -> str:
    """Tabela de variaveis do passo, ou o confronto lado a lado."""
    if resultado.comparacao is not None:
        return _confronto(resultado)

    partes = ['<p class="rotulo">estado no passo</p>']
    passo = resultado.passo(indice)
    if passo is None:
        pista = ("antes do primeiro passo" if resultado.total
                 else "nenhum pixel foi plotado")
        return "\n".join(partes + [f'<p class="pista">{pista}</p>'])

    anterior = resultado.passo(indice - 1)
    variaveis = anterior.variaveis if isinstance(anterior, Passo) else {}

    partes.append(_variavel("pixel", f"({passo.x}, {passo.y})",
                            mudou=True, classe="pixel"))
    if not passo.escrito:
        partes.append(_variavel("descartado", "fora da tela", mudou=True))
    for nome, valor in passo.variaveis.items():
        mudou = variaveis.get(nome, _AUSENTE) != valor
        partes.append(_variavel(nome, formata_valor(valor), mudou))
    return "\n".join(partes)


_AUSENTE = object()


def _variavel(nome: str, valor: str, mudou: bool, classe: str = "") -> str:
    """Uma linha nome/valor da tabela de estado."""
    classes = " ".join(filter(None, ("variavel", classe,
                                     "mudou" if mudou else "")))
    return (f'<div class="{classes}"><span class="nome">{escape(nome)}</span>'
            f'<span class="valor">{escape(valor)}</span></div>')


def _confronto(resultado: Resultado) -> str:
    """Comparacao numerica dos dois algoritmos confrontados."""
    from motor.analise import analisa

    a, b = resultado.confrontados or ()
    perfil_a = analisa(a, referencia=(*resultado.p0, *resultado.p1))
    perfil_b = analisa(b, referencia=(*resultado.p0, *resultado.p1))

    def desvio(valor: float | None) -> str:
        return f"{valor:.3f}" if valor is not None else "-"

    linhas = [
        ("passos", perfil_a.passos, perfil_b.passos),
        ("pixels", perfil_a.pixels, perfil_b.pixels),
        ("repetidos", perfil_a.repetidos, perfil_b.repetidos),
        ("aritmética", perfil_a.aritmetica, perfil_b.aritmetica),
        ("desvio máx", desvio(perfil_a.desvio_maximo),
         desvio(perfil_b.desvio_maximo)),
    ]
    celulas = "".join(
        f'<div class="variavel"><span class="nome">{escape(rotulo)}</span>'
        f'<span class="valor" style="color:{tema.IDEAL}">{esquerda}</span>'
        f'<span class="valor" style="color:{tema.SINAL}">{direita}</span>'
        f"</div>"
        for rotulo, esquerda, direita in linhas)
    return (f'<p class="rotulo">lado a lado</p>'
            f'<div class="variavel"><span class="nome"></span>'
            f'<span class="valor" style="color:{tema.IDEAL}">'
            f"{escape(a.rotulo)}</span>"
            f'<span class="valor" style="color:{tema.SINAL}">'
            f"{escape(b.rotulo)}</span></div>{celulas}")


def codigo(resultado: Resultado, indice: int) -> str:
    """Codigo-fonte do alvo com a linha corrente e o perfil por linha."""
    partes = ['<p class="rotulo">código em execução</p>']
    fonte = _fonte(resultado, indice)
    if fonte is None or not fonte.linhas:
        return "\n".join(partes + ['<p class="pista">sem código para '
                                   "exibir</p>"])

    passo = resultado.passo(indice)
    linha_ativa = passo.linha if isinstance(passo, Passo) else None
    contagens = _contagens(resultado, fonte.funcao)

    if linha_ativa is not None:
        centro = linha_ativa - fonte.primeira_linha
    else:
        centro = _linha_do_raise(fonte)
    inicio = max(0, centro - LINHAS_DE_CONTEXTO)
    fim = min(len(fonte.linhas), centro + LINHAS_DE_CONTEXTO + 1)

    corpo = []
    for deslocamento in range(inicio, fim):
        numero = fonte.primeira_linha + deslocamento
        plots = contagens.get(numero, 0)
        marca = f"{plots:>5}" if plots else "    ·"
        atual = " atual" if numero == linha_ativa else ""
        corpo.append(
            f'<span class="linha{atual}">'
            f'<span class="num">{numero:>4}</span>'
            f'<span class="plots">{marca}</span>  '
            f"{escape(fonte.linhas[deslocamento])}</span>")

    return "\n".join(partes + [
        '<div class="fonte"><pre>' + "\n".join(corpo) + "</pre></div>",
        '<p class="pista">a coluna do meio conta quantos pixels cada '
        "linha plotou na execução inteira.</p>"])


def _linha_do_raise(fonte) -> int:
    """Indice da linha que levanta o exercicio, ou o meio da funcao.

    Sem passo capturado, o trecho util do codigo e justamente onde a
    execucao para: a linha do ``raise NotImplementedError``.
    """
    for indice, linha in enumerate(fonte.linhas):
        if "raise NotImplementedError" in linha:
            return indice
    return len(fonte.linhas) // 2


def _fonte(resultado: Resultado, indice: int):
    """Codigo-fonte a exibir: o do passo, ou o da funcao alvo."""
    rastro = resultado.rastro
    if rastro is None:
        return None
    passo = resultado.passo(indice)
    if isinstance(passo, Passo):
        return rastro.fonte_do_passo(passo)
    if rastro.fontes:
        return next(iter(rastro.fontes.values()))
    return _fonte_do_alvo(resultado)


def _fonte_do_alvo(resultado: Resultado):
    """Le o codigo da funcao alvo mesmo sem nenhum passo capturado."""
    from motor.tracador import _le_fonte

    try:
        funcao = resultado.algoritmo.funcao()
    except Exception:  # noqa: BLE001 - o modulo pode estar quebrado
        return None
    return _le_fonte(funcao.__code__, funcao.__name__)


def _contagens(resultado: Resultado, funcao: str) -> dict[int, int]:
    """Quantas vezes cada linha do codigo plotou um pixel."""
    contagens: dict[int, int] = {}
    if resultado.rastro is None:
        return contagens
    for passo in resultado.rastro.passos:
        if passo.funcao == funcao:
            contagens[passo.linha] = contagens.get(passo.linha, 0) + 1
    return contagens


def rotulos_do_catalogo(
        estados: dict[str, str]) -> dict[str, list[tuple[str, str]]]:
    """Opcoes da lista de algoritmos, agrupadas por familia.

    O estado de cada exercicio entra no proprio rotulo, para que a lista
    responda de imediato depois de uma recarga.

    Args:
        estados: Mapa ``chave -> "pronto" | "pendente" | "erro"``.

    Returns:
        Mapa ``familia -> [(rotulo, chave), ...]``, na ordem do catalogo.
    """
    from .catalogo import CATALOGO

    marcas = {"pendente": "  ·  a fazer", "erro": "  ·  erro"}
    grupos: dict[str, list[tuple[str, str]]] = {}
    for item in CATALOGO:
        rotulo = item.nome + marcas.get(estados.get(item.chave, ""), "")
        grupos.setdefault(item.familia, []).append((rotulo, item.chave))
    return grupos
