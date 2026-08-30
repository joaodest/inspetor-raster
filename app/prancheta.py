"""Desenho da prancheta: framebuffer ampliado mais as camadas de leitura.

A imagem final tem sempre o mesmo tamanho, ``864 x 576``, mude o zoom
que mudar. Quem muda e a janela de pixels recortada do framebuffer: 96
colunas no ajuste, 48 no 2x, 24 no 4x. Manter a saida fixa e o que
permite mapear o clique do navegador de volta para a grade sem depender
de como o CSS dimensionou a imagem.

Duas camadas se somam ao pixel:

* a **grade**, desenhada com aresta dura para nao borrar o pixel;
* as **marcacoes** (reta exata, cursor do passo, alcas), desenhadas com
  antisserrilhamento em uma camada tres vezes maior e reduzida depois,
  para que a geometria continua nao seja confundida com pixel aceso.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from motor.framebuffer import Framebuffer

from . import tema

LARGURA_DA_GRADE = 96
ALTURA_DA_GRADE = 64
LARGURA_DA_SAIDA = 864
ALTURA_DA_SAIDA = 576
SUPERAMOSTRAGEM = 3
RAIO_DA_ALCA = 9

FATORES = {"ajustar": 1, "2x": 2, "4x": 4}


def janela(fator: int, foco: tuple[int, int]) -> tuple[int, int, int, int]:
    """Regiao da grade visivel em um dado zoom, centrada no foco.

    Args:
        fator: 1, 2 ou 4.
        foco: Pixel que deve ficar no centro quando houver recorte.

    Returns:
        Tupla ``(origem_x, origem_y, largura, altura)`` em pixels da grade.
    """
    largura = max(1, LARGURA_DA_GRADE // fator)
    altura = max(1, ALTURA_DA_GRADE // fator)
    origem_x = max(0, min(LARGURA_DA_GRADE - largura, foco[0] - largura // 2))
    origem_y = max(0, min(ALTURA_DA_GRADE - altura, foco[1] - altura // 2))
    return origem_x, origem_y, largura, altura


def para_grade(x: float, y: float, fator: int,
               foco: tuple[int, int]) -> tuple[int, int]:
    """Converte um clique na imagem em coordenada da grade."""
    origem_x, origem_y, largura, altura = janela(fator, foco)
    zoom_x = LARGURA_DA_SAIDA / largura
    zoom_y = ALTURA_DA_SAIDA / altura
    coluna = origem_x + int(x // zoom_x)
    linha = origem_y + int(y // zoom_y)
    return (max(0, min(LARGURA_DA_GRADE - 1, coluna)),
            max(0, min(ALTURA_DA_GRADE - 1, linha)))


def renderiza(quadro: Framebuffer, *, fator: int = 1,
              foco: tuple[int, int] = (48, 32),
              grade: bool = True,
              reta_exata: tuple[tuple[int, int],
                                tuple[int, int]] | None = None,
              cursor: tuple[int, int] | None = None,
              alcas: tuple[tuple[int, int], tuple[int, int]] | None = None,
              aviso: tuple[str, str, str] | None = None) -> Image.Image:
    """Monta a imagem da prancheta pronta para exibicao.

    Args:
        quadro: Framebuffer a exibir.
        fator: Nivel de zoom (1, 2 ou 4).
        foco: Pixel que centraliza a janela quando ha recorte.
        grade: Liga a grade de pixels.
        reta_exata: Segmento matematico de referencia, em coordenadas da
            grade, ou ``None``.
        cursor: Pixel do passo corrente, ou ``None``.
        alcas: Par de pontos arrastaveis, ou ``None``.
        aviso: Trio ``(titulo, arquivo, explicacao)`` da faixa de
            exercicio pendente, ou ``None``.

    Returns:
        Imagem RGB de ``864 x 576``.
    """
    origem_x, origem_y, largura, altura = janela(fator, foco)
    zoom = LARGURA_DA_SAIDA // largura

    base = Image.frombytes("RGB", quadro.dimensoes, bytes(quadro.pixels))
    base = base.crop((origem_x, origem_y, origem_x + largura,
                      origem_y + altura))
    base = base.resize((LARGURA_DA_SAIDA, ALTURA_DA_SAIDA), Image.NEAREST)

    if grade and zoom >= 5:
        _desenha_grade(base, zoom, largura, altura)

    camada = Image.new("RGBA", (LARGURA_DA_SAIDA * SUPERAMOSTRAGEM,
                                ALTURA_DA_SAIDA * SUPERAMOSTRAGEM),
                       (0, 0, 0, 0))
    pincel = ImageDraw.Draw(camada)
    escala = zoom * SUPERAMOSTRAGEM

    def no_papel(ponto: tuple[int, int]) -> tuple[float, float]:
        """Centro do pixel na camada superamostrada."""
        return ((ponto[0] - origem_x + 0.5) * escala,
                (ponto[1] - origem_y + 0.5) * escala)

    if reta_exata is not None:
        pincel.line([no_papel(reta_exata[0]), no_papel(reta_exata[1])],
                    fill=(*tema.IDEAL_NO_PAPEL, 255),
                    width=SUPERAMOSTRAGEM * 2)

    if cursor is not None:
        canto_x = (cursor[0] - origem_x) * escala
        canto_y = (cursor[1] - origem_y) * escala
        folga = max(SUPERAMOSTRAGEM, escala // 4)
        pincel.rectangle(
            [canto_x - folga, canto_y - folga,
             canto_x + escala + folga, canto_y + escala + folga],
            outline=(*tema.SINAL_NO_PAPEL, 255),
            width=max(3, SUPERAMOSTRAGEM + 2))

    if alcas is not None:
        for nome, ponto in zip(("p0", "p1"), alcas, strict=True):
            _desenha_alca(pincel, no_papel(ponto), nome)

    camada = camada.resize((LARGURA_DA_SAIDA, ALTURA_DA_SAIDA),
                           Image.LANCZOS)
    base = Image.alpha_composite(base.convert("RGBA"), camada).convert("RGB")

    if aviso is not None:
        _desenha_aviso(base, aviso)
    return base


def _desenha_grade(imagem: Image.Image, zoom: int, colunas: int,
                   linhas: int) -> None:
    """Traca a grade de pixels com aresta dura sobre a imagem ampliada."""
    pincel = ImageDraw.Draw(imagem)
    for coluna in range(colunas + 1):
        x = min(coluna * zoom, LARGURA_DA_SAIDA - 1)
        pincel.line([(x, 0), (x, ALTURA_DA_SAIDA)], fill=tema.GRADE)
    for linha in range(linhas + 1):
        y = min(linha * zoom, ALTURA_DA_SAIDA - 1)
        pincel.line([(0, y), (LARGURA_DA_SAIDA, y)], fill=tema.GRADE)


def _desenha_alca(pincel: ImageDraw.ImageDraw, centro: tuple[float, float],
                  nome: str) -> None:
    """Desenha uma alca arrastavel com seu rotulo."""
    x, y = centro
    raio = RAIO_DA_ALCA * SUPERAMOSTRAGEM
    pincel.ellipse([x - raio, y - raio, x + raio, y + raio],
                   fill=(*tema.PAPEL, 235),
                   outline=(*tema.SINAL_NO_PAPEL, 255),
                   width=SUPERAMOSTRAGEM + 2)
    pincel.ellipse([x - raio / 3, y - raio / 3, x + raio / 3, y + raio / 3],
                   fill=(*tema.SINAL_NO_PAPEL, 255))
    fonte = _fonte(11 * SUPERAMOSTRAGEM)
    pincel.text((x, y - raio - 9 * SUPERAMOSTRAGEM), nome, anchor="mm",
                fill=(*tema.SINAL_NO_PAPEL, 255), font=fonte)


def _desenha_aviso(imagem: Image.Image, aviso: tuple[str, str, str]) -> None:
    """Escreve a faixa de exercicio pendente sobre a prancheta."""
    titulo, arquivo, explicacao = aviso
    pincel = ImageDraw.Draw(imagem)
    meio = ALTURA_DA_SAIDA // 2
    pincel.rectangle([0, meio - 52, LARGURA_DA_SAIDA, meio + 52],
                     fill=tema.PAPEL_AVISO)
    pincel.line([(0, meio - 52), (LARGURA_DA_SAIDA, meio - 52)],
                fill=tema.GRADE_FORTE)
    pincel.line([(0, meio + 52), (LARGURA_DA_SAIDA, meio + 52)],
                fill=tema.GRADE_FORTE)
    pincel.text((LARGURA_DA_SAIDA // 2, meio - 22), titulo, anchor="mm",
                fill=tema.TINTA, font=_fonte(19, negrito=True))
    pincel.text((LARGURA_DA_SAIDA // 2, meio + 6), arquivo, anchor="mm",
                fill=tema.SINAL_NO_PAPEL, font=_fonte(14, mono=True))
    pincel.text((LARGURA_DA_SAIDA // 2, meio + 32), explicacao, anchor="mm",
                fill=tema.TEXTO_NO_PAPEL, font=_fonte(13))


_cache_de_fontes: dict[tuple[int, bool, bool], ImageFont.FreeTypeFont] = {}

_ARQUIVOS = {
    (False, False): ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"),
    (True, False): ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    (False, True): ("CascadiaMono.ttf", "consola.ttf",
                    "DejaVuSansMono.ttf"),
}


def _fonte(tamanho: int, negrito: bool = False,
           mono: bool = False) -> ImageFont.FreeTypeFont:
    """Carrega uma fonte do sistema, com queda para a embutida do PIL."""
    chave = (tamanho, negrito, mono)
    if chave in _cache_de_fontes:
        return _cache_de_fontes[chave]
    candidatos = _ARQUIVOS.get((negrito, mono), _ARQUIVOS[(False, False)])
    for arquivo in candidatos:
        try:
            fonte = ImageFont.truetype(arquivo, tamanho)
            break
        except OSError:
            continue
    else:  # pragma: no cover - sistema sem nenhuma das fontes
        fonte = ImageFont.load_default(tamanho)
    _cache_de_fontes[chave] = fonte
    return fonte
