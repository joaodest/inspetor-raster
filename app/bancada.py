"""Bancada Raster: ver o algoritmo desenhar, passo a passo, com numeros.

CONTRATO DA DIRECAO
-------------------
TESE: um algoritmo de rasterizacao nao se entende lendo o codigo, se
entende vendo o erro acumulado decidir o proximo pixel. A bancada
recusa a janela de preview que so mostra o resultado pronto.

MUNDO: instrumento de medicao. Chassi grafite com filetes de 1 px,
numeros em monoespacada tabular, controles planos; e uma prancheta de
papel claro onde a cor plotada aparece como ela e. Cor so existe com
significado: laranja e o passo atual, azul e a geometria exata, os dois
juntos sao a divergencia entre algoritmos.

HISTORIA: escolho o algoritmo, clico para mover os pontos, dou play e
vejo o pixel nascer enquanto as variaveis do meu proprio codigo mudam
ao lado, na linha que as escreveu.

PRIMEIRA VISTA: prancheta ocupando o centro com a grade visivel,
transporte embaixo, perfil analitico a direita; se o exercicio ainda
nao foi feito, o roteiro dele ocupa o lugar dos numeros.

FORMA: aplicacao Gradio de pagina unica, modo Operate, sem sorteio de
direcao por ser pedido estreito e precisamente especificado.
"""

from __future__ import annotations

import time
from pathlib import Path

import gradio as gr

from motor.imagem import salva_png

from . import nucleo, paineis, prancheta, tema
from .catalogo import POR_CHAVE
from .prancheta import ALTURA_DA_GRADE, FATORES, LARGURA_DA_GRADE

ALGORITMO_INICIAL = "dda"
P0_INICIAL = (14, 46)
P1_INICIAL = (82, 18)
QUADROS_POR_SEGUNDO = 24


def _foco(resultado: nucleo.Resultado, passo: int) -> tuple[int, int]:
    """Pixel que centraliza a janela quando ha zoom.

    Segue o passo corrente durante a reproducao e cai no meio do
    segmento quando nao ha passo, de modo que aproximar nunca perde de
    vista o que esta acontecendo.
    """
    corrente = resultado.passo(passo)
    if corrente is not None:
        return corrente.x, corrente.y
    return ((resultado.p0[0] + resultado.p1[0]) // 2,
            (resultado.p0[1] + resultado.p1[1]) // 2)


def _imagem(resultado: nucleo.Resultado, passo: int, zoom: str,
            grade: bool, exata: bool):
    """Renderiza a prancheta no estado pedido."""
    quadro = nucleo.quadro_no_passo(resultado, passo)
    corrente = resultado.passo(passo)
    aviso = None
    if resultado.pendente:
        modulo, funcao = resultado.algoritmo.alvo
        aviso = (f"{funcao}() ainda não foi implementada",
                 modulo.replace(".", "/") + ".py",
                 "o roteiro está no painel à direita; depois de salvar, "
                 "use recarregar módulos")
    return prancheta.renderiza(
        quadro,
        fator=FATORES.get(zoom, 1),
        foco=_foco(resultado, passo),
        grade=grade,
        reta_exata=((resultado.p0, resultado.p1)
                    if exata and resultado.algoritmo.usa_referencia else None),
        cursor=(corrente.x, corrente.y) if corrente is not None else None,
        alcas=(resultado.p0, resultado.p1),
        aviso=aviso,
    )


def _contador(resultado: nucleo.Resultado, passo: int) -> str:
    """Leitura do transporte, em numeros tabulares."""
    if resultado.total == 0:
        texto = "confronto estático"
        if not resultado.comparacao:
            texto = "sem passos"
        return f'<div class="contador">{texto}</div>'
    return f'<div class="contador">{passo:>4} / {resultado.total}</div>'


def _monta(resultado: nucleo.Resultado, passo: int, zoom: str, grade: bool,
           exata: bool) -> tuple:
    """Produz a tupla completa de saidas da interface.

    Os seis botoes de transporte entram aqui porque uma entrada de
    confronto nao tem trilha para percorrer: eles precisam aparecer
    desligados, e nao ligados e inertes.
    """
    percorrivel = resultado.total > 0
    return (
        _imagem(resultado, passo, zoom, grade, exata),
        paineis.cabecalho(resultado),
        paineis.perfil(resultado),
        paineis.estado(resultado, passo),
        paineis.codigo(resultado, passo),
        gr.update(maximum=max(resultado.total, 1), value=passo,
                  interactive=percorrivel),
        _contador(resultado, passo),
        *(gr.update(interactive=percorrivel) for _ in range(6)),
    )


def _atualiza(chave: str, x0: float, y0: float, x1: float, y1: float,
              espessura: float, passo: float, zoom: str, grade: bool,
              exata: bool, salto: str = "manter") -> tuple:
    """Recalcula tudo a partir dos parametros visiveis na tela."""
    p0 = (_na_grade(x0, LARGURA_DA_GRADE), _na_grade(y0, ALTURA_DA_GRADE))
    p1 = (_na_grade(x1, LARGURA_DA_GRADE), _na_grade(y1, ALTURA_DA_GRADE))
    resultado = nucleo.executa(chave, p0, p1, int(espessura))

    passo = int(passo)
    if salto == "inicio":
        passo = 0
    elif salto == "fim":
        passo = resultado.total
    elif salto == "anterior":
        passo -= 1
    elif salto == "proximo":
        passo += 1
    elif salto == "reexecutar":
        passo = resultado.total
    passo = max(0, min(resultado.total, passo))
    return _monta(resultado, passo, zoom, grade, exata)


def _na_grade(valor: float, limite: int) -> int:
    """Restringe uma coordenada digitada aos limites da prancheta."""
    return max(0, min(limite - 1, int(valor or 0)))


def _toca(chave: str, x0: float, y0: float, x1: float, y1: float,
          espessura: float, passo: float, zoom: str, grade: bool,
          exata: bool, velocidade: float):
    """Reproduz a trilha do passo corrente ate o fim, quadro a quadro."""
    p0 = (_na_grade(x0, LARGURA_DA_GRADE), _na_grade(y0, ALTURA_DA_GRADE))
    p1 = (_na_grade(x1, LARGURA_DA_GRADE), _na_grade(y1, ALTURA_DA_GRADE))
    resultado = nucleo.executa(chave, p0, p1, int(espessura))
    total = resultado.total
    if total == 0:
        yield _monta(resultado, 0, zoom, grade, exata)
        return

    atual = 0 if int(passo) >= total else int(passo)
    avanco = max(1, round(velocidade / QUADROS_POR_SEGUNDO))
    intervalo = 1.0 / QUADROS_POR_SEGUNDO

    yield _monta(resultado, atual, zoom, grade, exata)
    while atual < total:
        atual = min(total, atual + avanco)
        yield _monta(resultado, atual, zoom, grade, exata)
        time.sleep(intervalo)


def _clique(evento: gr.SelectData, chave: str, x0: float, y0: float,
            x1: float, y1: float, espessura: float, passo: float, zoom: str,
            grade: bool, exata: bool) -> tuple:
    """Move para o clique a alca mais proxima e reexecuta."""
    p0 = (_na_grade(x0, LARGURA_DA_GRADE), _na_grade(y0, ALTURA_DA_GRADE))
    p1 = (_na_grade(x1, LARGURA_DA_GRADE), _na_grade(y1, ALTURA_DA_GRADE))
    resultado = nucleo.executa(chave, p0, p1, int(espessura))

    coluna, linha = evento.index[0], evento.index[1]
    destino = prancheta.para_grade(coluna, linha, FATORES.get(zoom, 1),
                                   _foco(resultado, int(passo)))

    distancia_0 = (destino[0] - p0[0]) ** 2 + (destino[1] - p0[1]) ** 2
    distancia_1 = (destino[0] - p1[0]) ** 2 + (destino[1] - p1[1]) ** 2
    if distancia_0 <= distancia_1:
        p0 = destino
    else:
        p1 = destino

    novo = nucleo.executa(chave, p0, p1, int(espessura))
    return (*_monta(novo, novo.total, zoom, grade, exata),
            p0[0], p0[1], p1[0], p1[1])


def _escolhe(chave: str, familia: str, valores: dict) -> tuple:
    """Mantem uma unica selecao viva entre as listas por familia."""
    return tuple(gr.update(value=chave if nome == familia else None)
                 for nome in valores)


def _salva(chave: str, x0: float, y0: float, x1: float, y1: float,
           espessura: float, passo: float) -> str:
    """Grava a prancheta corrente como PNG na pasta de saidas."""
    p0 = (_na_grade(x0, LARGURA_DA_GRADE), _na_grade(y0, ALTURA_DA_GRADE))
    p1 = (_na_grade(x1, LARGURA_DA_GRADE), _na_grade(y1, ALTURA_DA_GRADE))
    resultado = nucleo.executa(chave, p0, p1, int(espessura))
    quadro = nucleo.quadro_no_passo(resultado, int(passo))
    destino = _pasta_de_saidas() / f"{chave}.png"
    salva_png(quadro, destino)
    return f'<p class="pista">salvo em saidas/{destino.name}</p>'


def _pasta_de_saidas() -> Path:
    """Pasta padrao para os PNG gravados."""
    pasta = Path(__file__).resolve().parent.parent / "saidas"
    pasta.mkdir(exist_ok=True)
    return pasta


def constroi() -> gr.Blocks:
    """Monta a pagina inteira e liga os eventos."""
    estados = nucleo.estados_do_catalogo()
    grupos = paineis.rotulos_do_catalogo(estados)

    with gr.Blocks(title="Bancada Raster", fill_width=True) as pagina:
        cabecalho = gr.HTML()

        with gr.Row(equal_height=False):
            with gr.Column(scale=0, min_width=250, elem_classes="trilho"):
                listas: dict[str, gr.Radio] = {}
                for indice, (familia, opcoes) in enumerate(grupos.items()):
                    gr.HTML(f'<p class="rotulo'
                            f'{" primeiro" if indice == 0 else ""}">'
                            f"{familia}</p>")
                    listas[familia] = gr.Radio(
                        choices=opcoes,
                        value=(ALGORITMO_INICIAL
                               if any(c == ALGORITMO_INICIAL
                                      for _, c in opcoes) else None),
                        show_label=False, container=False,
                        elem_classes="catalogo")

                gr.HTML('<p class="rotulo">parâmetros</p>')
                pista_pontos = gr.HTML()
                with gr.Row():
                    x0 = gr.Number(P0_INICIAL[0], label="p0 x", precision=0,
                                   minimum=0, maximum=LARGURA_DA_GRADE - 1,
                                   min_width=64)
                    y0 = gr.Number(P0_INICIAL[1], label="p0 y", precision=0,
                                   minimum=0, maximum=ALTURA_DA_GRADE - 1,
                                   min_width=64)
                with gr.Row():
                    x1 = gr.Number(P1_INICIAL[0], label="p1 x", precision=0,
                                   minimum=0, maximum=LARGURA_DA_GRADE - 1,
                                   min_width=64)
                    y1 = gr.Number(P1_INICIAL[1], label="p1 y", precision=0,
                                   minimum=0, maximum=ALTURA_DA_GRADE - 1,
                                   min_width=64)
                espessura = gr.Slider(1, 5, 1, step=1, label="espessura")

                gr.HTML('<p class="rotulo">ações</p>')
                with gr.Column(elem_classes="acoes"):
                    recarregar = gr.Button("recarregar módulos", size="sm")
                    salvar = gr.Button("salvar PNG", size="sm",
                                       variant="secondary")
                aviso = gr.HTML(
                    '<p class="pista">edite motor/primitivas.py, salve, '
                    "e recarregue para ver o resultado aqui.</p>")

            with gr.Column(scale=1, elem_classes="palco"):
                with gr.Row():
                    zoom = gr.Radio(list(FATORES), value="ajustar",
                                    label="zoom", scale=0, min_width=230,
                                    elem_classes="catalogo-zoom")
                    grade = gr.Checkbox(True, label="grade", scale=0,
                                        min_width=100)
                    exata = gr.Checkbox(True, label="reta exata", scale=0,
                                        min_width=120)
                    gr.HTML("", scale=1)
                imagem = gr.Image(
                    type="pil", show_label=False, interactive=False,
                    container=False, elem_classes="prancheta",
                    height=prancheta.ALTURA_DA_SAIDA,
                    width=prancheta.LARGURA_DA_SAIDA)
                passo = gr.Slider(0, 1, 0, step=1, label="passo",
                                  interactive=True)
                with gr.Row(elem_classes="transporte"):
                    contador = gr.HTML(min_width=132, elem_classes="leitura")
                    b_inicio = gr.Button("início", size="sm", min_width=0)
                    b_anterior = gr.Button("anterior", size="sm", min_width=0)
                    b_tocar = gr.Button("tocar", size="sm", min_width=0,
                                        variant="primary")
                    b_parar = gr.Button("parar", size="sm", min_width=0)
                    b_proximo = gr.Button("próximo", size="sm", min_width=0)
                    b_fim = gr.Button("fim", size="sm", min_width=0)
                    with gr.Column(elem_classes="velocidade", min_width=180):
                        velocidade = gr.Slider(4, 400, 60, step=1,
                                               label="passos por segundo")

            with gr.Column(scale=0, min_width=430,
                           elem_classes=["trilho", "trilho-direito"]):
                perfil = gr.HTML()
                estado = gr.HTML()
                codigo = gr.HTML()

        parametros = [x0, y0, x1, y1, espessura, passo, zoom, grade, exata]
        saidas = [imagem, cabecalho, perfil, estado, codigo, passo, contador,
                  b_inicio, b_anterior, b_tocar, b_parar, b_proximo, b_fim]

        def escolhido(*valores: str) -> str:
            """Chave viva entre as listas por familia."""
            return next((v for v in valores if v), ALGORITMO_INICIAL)

        def com_algoritmo(salto: str):
            """Adapta ``_atualiza`` a lista de radios por familia."""
            def executor(*argumentos):
                quantidade = len(listas)
                chave = escolhido(*argumentos[:quantidade])
                return _atualiza(chave, *argumentos[quantidade:], salto=salto)
            return executor

        entradas_com_lista = list(listas.values()) + parametros

        def liga(gatilhos, salto="manter", extras=None):
            """Registra um evento que recalcula a pagina inteira."""
            return gr.on(triggers=gatilhos, fn=com_algoritmo(salto),
                         inputs=entradas_com_lista,
                         outputs=(extras or []) + saidas,
                         show_progress="hidden")

        for familia, lista in listas.items():
            lista.input(
                fn=lambda escolha, alvo=familia: _escolhe(
                    escolha, alvo, listas),
                inputs=[lista], outputs=list(listas.values()),
                show_progress="hidden",
            ).then(fn=com_algoritmo("reexecutar"), inputs=entradas_com_lista,
                   outputs=saidas, show_progress="hidden")
            lista.input(fn=_pista, inputs=[lista], outputs=[pista_pontos],
                        show_progress="hidden")

        liga([x0.change, y0.change, x1.change, y1.change,
              espessura.release], "reexecutar")
        liga([zoom.change, grade.change, exata.change])
        liga([passo.input])
        liga([b_inicio.click], "inicio")
        liga([b_anterior.click], "anterior")
        liga([b_proximo.click], "proximo")
        liga([b_fim.click], "fim")

        def tocou(*argumentos):
            """Reproduz a trilha; precisa ser gerador, nao um lambda.

            O Gradio decide se transmite quadro a quadro olhando
            ``inspect.isgeneratorfunction`` do que recebe. Um lambda que
            apenas chama o gerador nao passa nesse teste: o objeto
            gerador chegaria cru na saida e a reproducao nao aconteceria.
            """
            quantidade = len(listas)
            chave = escolhido(*argumentos[:quantidade])
            yield from _toca(chave, *argumentos[quantidade:])

        reproducao = b_tocar.click(
            fn=tocou, inputs=entradas_com_lista + [velocidade],
            outputs=saidas, show_progress="hidden")
        b_parar.click(fn=None, inputs=None, outputs=None,
                      cancels=[reproducao])

        def clicou(evento: gr.SelectData, *argumentos) -> tuple:
            """Repassa o clique na prancheta com a chave resolvida."""
            quantidade = len(listas)
            chave = escolhido(*argumentos[:quantidade])
            return _clique(evento, chave, *argumentos[quantidade:])

        imagem.select(fn=clicou, inputs=entradas_com_lista,
                      outputs=saidas + [x0, y0, x1, y1],
                      show_progress="hidden")

        recarregar.click(fn=_recarrega, inputs=None,
                         outputs=[aviso] + list(listas.values()),
                         show_progress="hidden"
                         ).then(fn=com_algoritmo("reexecutar"),
                                inputs=entradas_com_lista, outputs=saidas,
                                show_progress="hidden")

        salvar.click(fn=lambda *a: _salva(escolhido(*a[:len(listas)]),
                                          *a[len(listas):len(listas) + 6]),
                     inputs=entradas_com_lista, outputs=[aviso],
                     show_progress="hidden")

        pagina.load(fn=com_algoritmo("fim"), inputs=entradas_com_lista,
                    outputs=saidas, show_progress="hidden")
        pagina.load(fn=_pista, inputs=[listas[next(iter(listas))]],
                    outputs=[pista_pontos], show_progress="hidden")

    return pagina


def _pista(chave: str | None) -> str:
    """Explica o que os dois pontos significam no algoritmo escolhido."""
    algoritmo = POR_CHAVE.get(chave or ALGORITMO_INICIAL)
    if algoritmo is None:
        return ""
    return f'<p class="pista">{algoritmo.pontos}</p>'


def _recarrega() -> tuple:
    """Recarrega os modulos do usuario e atualiza os rotulos da lista."""
    erro = nucleo.recarrega()
    estados = nucleo.estados_do_catalogo()
    grupos = paineis.rotulos_do_catalogo(estados)
    prontos = sum(1 for e in estados.values() if e == "pronto")

    if erro:
        mensagem = f'<p class="pista" style="color:{tema.ERRO}">{erro}</p>'
    else:
        mensagem = (f'<p class="pista">módulos recarregados · '
                    f"{prontos} de {len(estados)} entradas rodando</p>")
    return (mensagem,
            *(gr.update(choices=opcoes) for opcoes in grupos.values()))


def executa(porta: int = 7860, abrir: bool = True) -> None:
    """Sobe o servidor local da bancada."""
    constroi().launch(server_name="127.0.0.1", server_port=porta,
                      inbrowser=abrir, theme=tema.tema(), css=tema.CSS,
                      quiet=True, show_error=True)
