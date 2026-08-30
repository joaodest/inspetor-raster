"""Sistema visual do inspetor: paleta, tipografia e CSS.

Duas materias convivem na tela e nunca trocam de papel:

* o **chassi**, em grafite, e o instrumento: trilhos, controles, numeros
  e codigo;
* a **prancheta**, em papel claro, e a imagem: so ela mostra pixel,
  grade e cor de verdade.

A separacao e tecnica, nao decorativa. A cor plotada precisa ser lida
como ela e, e isso so acontece sobre um fundo neutro claro. Toda cor
daqui codifica estado (passo atual, geometria exata, divergencia entre
algoritmos); nenhuma e enfeite.

As familias tipograficas usam ``gr.themes.Font``, que declara a fonte
sem publicar arquivo nenhum. ``LocalFont`` faria o Gradio servir
``.woff2`` inexistentes nesta maquina (quatro erros 404 antes de cair na
fonte do sistema mesmo assim), e uma lista de textos simples quebra a
comparacao de temas do Gradio 6 dentro de ``launch()``.
"""

from __future__ import annotations

import gradio as gr

FUNDO = "#14161b"
PAINEL = "#1a1d24"
PAINEL_ALTO = "#20242d"
SULCO = "#101217"
CAMPO = "#232833"
LINHA = "#272c36"
LINHA_FORTE = "#39404e"

TEXTO = "#e8ebf1"
TEXTO_MEDIO = "#a6aebd"
TEXTO_FRACO = "#868fa1"
TEXTO_INVERSO = "#14161b"

SINAL = "#ff6a3d"
SINAL_FUNDO = "#2a1a13"
IDEAL = "#57a0ff"
OK = "#46c78a"
ALERTA = "#f0b429"
ERRO = "#ff5d55"

PAPEL = (248, 249, 251)
GRADE = (226, 231, 239)
GRADE_FORTE = (198, 206, 219)
TINTA = (16, 19, 24)
IDEAL_NO_PAPEL = (47, 111, 208)
SINAL_NO_PAPEL = (224, 74, 31)
DIVERGENCIA_A = (47, 111, 208)
DIVERGENCIA_B = (209, 64, 28)
PAPEL_AVISO = (237, 240, 246)
TEXTO_NO_PAPEL = (92, 100, 114)

TONS = {
    "neutro": TEXTO_MEDIO,
    "bom": OK,
    "alerta": ALERTA,
    "ruim": ERRO,
}

PILHA_UI = ('"Segoe UI Variable Text", "Segoe UI", system-ui, '
            "-apple-system, sans-serif")
PILHA_MONO = ('"Cascadia Mono", "Cascadia Code", Consolas, '
              '"SF Mono", ui-monospace, monospace')


def tema() -> gr.themes.Base:
    """Tema base do Gradio alinhado ao chassi do instrumento."""
    return gr.themes.Base(
        font=[gr.themes.Font("Segoe UI Variable Text"),
              gr.themes.Font("Segoe UI"), gr.themes.Font("sans-serif")],
        font_mono=[gr.themes.Font("Cascadia Mono"),
                   gr.themes.Font("Consolas"),
                   gr.themes.Font("monospace")],
        radius_size=gr.themes.sizes.radius_sm,
    ).set(
        body_background_fill=FUNDO,
        body_text_color=TEXTO,
        body_text_color_subdued=TEXTO_FRACO,
        block_background_fill=PAINEL,
        block_border_color=LINHA,
        block_label_text_color=TEXTO_FRACO,
        block_title_text_color=TEXTO_FRACO,
        block_shadow="none",
        border_color_primary=LINHA,
        panel_background_fill=PAINEL,
        input_background_fill=CAMPO,
        input_border_color=LINHA_FORTE,
        button_primary_background_fill=SINAL,
        button_primary_background_fill_hover="#ff8154",
        button_primary_text_color=TEXTO_INVERSO,
        button_secondary_background_fill=CAMPO,
        button_secondary_background_fill_hover=PAINEL_ALTO,
        button_secondary_text_color=TEXTO,
        slider_color=SINAL,
    )


CSS = f"""
.gradio-container {{
    background: {FUNDO};
    max-width: 100% !important;
    padding: 0 !important;
    font-family: {PILHA_UI};
}}
footer {{ display: none !important; }}

/* ---------- cabecalho ---------- */
.cabecalho {{
    display: flex; align-items: baseline; gap: 26px;
    padding: 14px 22px 13px;
    border-bottom: 1px solid {LINHA};
}}
.cabecalho .marca {{
    font-size: 15px; font-weight: 700; color: {TEXTO};
    letter-spacing: -0.01em; white-space: nowrap;
}}
.cabecalho .disciplina {{
    font-size: 12px; color: {TEXTO_FRACO}; white-space: nowrap;
}}
.cabecalho .chamada {{
    font-family: {PILHA_MONO}; font-size: 12px; color: {TEXTO_MEDIO};
    flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}}
.cabecalho .selo {{
    font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; white-space: nowrap;
}}

/* ---------- trilhos ---------- */
.trilho {{
    background: {PAINEL} !important;
    border-right: 1px solid {LINHA};
    padding: 18px 16px 26px !important;
    gap: 0 !important;
}}
.trilho-direito {{ border-right: none; border-left: 1px solid {LINHA}; }}
.palco {{ padding: 16px 22px 24px !important; gap: 12px !important; }}

.trilho .block, .trilho-direito .block, .palco .block {{
    background: transparent !important; border: none !important;
    padding: 0 !important; box-shadow: none !important;
}}
.trilho .form, .trilho-direito .form, .palco .form {{
    background: transparent !important; border: none !important;
    box-shadow: none !important; gap: 8px;
}}

.rotulo {{
    font-size: 11px; font-weight: 700; letter-spacing: 0.09em;
    text-transform: uppercase; color: {TEXTO_FRACO};
    margin: 0 0 9px; padding-top: 16px;
    border-top: 1px solid {LINHA};
}}
.rotulo.primeiro {{ padding-top: 2px; border-top: none; }}
.trilho-direito .rotulo {{ margin-top: 18px; }}

.trilho label > span, .palco label > span {{
    font-size: 11px !important; font-weight: 600 !important;
    letter-spacing: 0.05em; color: {TEXTO_FRACO} !important;
    margin-bottom: 3px !important;
}}

/* ---------- catalogo de algoritmos ---------- */
.catalogo .wrap, .catalogo > div, .catalogo fieldset {{
    display: flex !important; flex-direction: column !important;
    align-items: stretch !important; gap: 1px !important;
}}
.catalogo label {{
    background: transparent !important; border: none !important;
    padding: 5px 9px !important; border-radius: 3px;
    width: 100%; cursor: pointer; transition: background 90ms ease;
    box-shadow: none !important;
}}
.catalogo label:hover {{ background: {PAINEL_ALTO} !important; }}
.catalogo label.selected {{ background: {CAMPO} !important; }}
.catalogo input[type="radio"] {{ display: none !important; }}
.catalogo label > span {{
    font-size: 13px !important; font-weight: 400 !important;
    letter-spacing: 0 !important; text-transform: none !important;
    color: {TEXTO_MEDIO} !important; margin: 0 !important;
}}
.catalogo label.selected > span {{
    color: {TEXTO} !important; font-weight: 600 !important;
}}

/* ---------- caixas de marcar ---------- */
.palco input[type="checkbox"] + span,
.palco .checkbox-container span {{
    font-size: 12.5px !important; font-weight: 400 !important;
    letter-spacing: 0 !important; text-transform: none !important;
    color: {TEXTO_MEDIO} !important;
}}
.palco .catalogo-zoom label > span {{
    font-size: 12.5px !important; text-transform: none !important;
    letter-spacing: 0 !important;
}}

/* ---------- prancheta ---------- */
.prancheta img {{
    image-rendering: pixelated;
    display: block; border-radius: 2px;
}}
.prancheta, .prancheta .block, .prancheta .image-container,
.prancheta .image-frame {{
    background: {SULCO} !important; border: none !important;
    padding: 0 !important;
}}
.prancheta .icon-buttons,
.prancheta .download-link,
.prancheta .image-button-row, .prancheta button[aria-label],
.prancheta .source-selection, .prancheta .top-panel {{
    display: none !important;
}}

/* ---------- transporte ---------- */
.transporte {{
    display: flex !important; flex-wrap: nowrap !important;
    align-items: center !important; gap: 6px !important;
}}
.transporte button {{
    flex: 0 0 auto !important; width: auto !important;
    white-space: nowrap; padding: 7px 14px !important;
    font-size: 12.5px !important; font-weight: 600 !important;
    min-width: 0 !important;
}}
.transporte .leitura {{
    flex: 0 0 132px !important; width: 132px !important;
    min-width: 132px !important; overflow: hidden;
}}
.contador {{
    font-family: {PILHA_MONO}; font-size: 13px; color: {TEXTO};
    font-variant-numeric: tabular-nums; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}}
.transporte .velocidade {{
    flex: 1 1 auto !important; min-width: 170px !important;
    padding-left: 14px;
}}
.acoes {{ gap: 8px !important; }}

code {{
    font-family: {PILHA_MONO}; font-size: 0.92em;
    background: {SULCO}; color: {TEXTO};
    padding: 1px 4px; border-radius: 2px;
}}

/* ---------- perfil analitico ---------- */
.medida {{
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 12px; padding: 5px 0 1px;
}}
.medida .nome {{ font-size: 12.5px; color: {TEXTO_MEDIO}; }}
.medida .valor {{
    font-family: {PILHA_MONO}; font-size: 13px; font-weight: 700;
    font-variant-numeric: tabular-nums; white-space: nowrap;
}}
.detalhe {{
    font-size: 11px; line-height: 1.4; color: {TEXTO_FRACO};
    margin: 0 0 4px; padding-bottom: 5px;
    border-bottom: 1px solid {LINHA};
}}

/* ---------- estado no passo ---------- */
.variavel {{
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 10px; padding: 2px 0;
    font-family: {PILHA_MONO}; font-size: 12.5px;
    font-variant-numeric: tabular-nums;
}}
.variavel .nome {{ color: {TEXTO_FRACO}; }}
.variavel .valor {{
    color: {TEXTO_MEDIO}; min-width: 72px; text-align: right;
}}
.variavel.mudou .valor {{ color: {SINAL}; }}
.variavel.pixel {{
    padding-bottom: 6px; margin-bottom: 4px;
    border-bottom: 1px solid {LINHA};
}}
.variavel.pixel .nome {{ color: {TEXTO}; font-weight: 700; }}
.variavel.pixel .valor {{ color: {SINAL}; font-weight: 700; }}

/* ---------- codigo ---------- */
.fonte {{
    background: {SULCO}; border: 1px solid {LINHA}; border-radius: 3px;
    padding: 9px 0; overflow-x: auto;
}}
.fonte pre {{
    margin: 0; font-family: {PILHA_MONO}; font-size: 11.5px;
    line-height: 1.6; color: {TEXTO_MEDIO}; white-space: pre;
}}
.fonte .linha {{ display: block; padding: 0 12px; }}
.fonte .linha.atual {{ background: {SINAL_FUNDO}; color: {TEXTO}; }}
.fonte .num {{ color: {LINHA_FORTE}; }}
.fonte .plots {{ color: {TEXTO_FRACO}; }}
.fonte .linha.atual .num, .fonte .linha.atual .plots {{
    color: {SINAL}; font-weight: 700;
}}

/* ---------- textos de apoio ---------- */
.aviso {{ font-size: 12.5px; line-height: 1.6; color: {TEXTO_MEDIO}; }}
.aviso strong {{ color: {TEXTO}; }}
.aviso .arquivo {{
    font-family: {PILHA_MONO}; font-size: 12px; color: {SINAL};
}}
.roteiro {{ margin: 12px 0 0; padding: 0 0 0 18px; }}
.roteiro li {{
    font-size: 12.5px; line-height: 1.55; color: {TEXTO};
    padding: 6px 0 6px 2px;
}}
.roteiro li + li {{ border-top: 1px solid {LINHA}; }}
.resumo {{
    font-size: 12.5px; line-height: 1.6; color: {TEXTO_MEDIO}; margin: 0;
}}
.pista {{
    font-size: 11.5px; line-height: 1.5; color: {TEXTO_FRACO};
    margin: 0;
}}
"""
