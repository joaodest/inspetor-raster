"""Testes dos 17 exercicios do laboratorio.

Cada teste fica pulado enquanto a funcao levantar
``NotImplementedError``, e passa a valer sozinho assim que voce a
implementar. Se a funcao existir mas quebrar, o teste falha: um erro de
digitacao nunca deve se disfarcar de exercicio nao comecado.
"""

from __future__ import annotations

import math
import unittest
from collections.abc import Callable

from motor.cores import BRANCO, PRETO, VERMELHO
from motor.exercicios import COM_ERRO, PENDENTE, POR_FUNCAO, estado
from motor.framebuffer import Framebuffer
from motor.recorte import ABAIXO, ACIMA, DENTRO, DIREITA, ESQUERDA, Janela
from motor.transformacoes import aplica


def acesos(quadro: Framebuffer) -> set[tuple[int, int]]:
    """Conjunto de pixels que deixaram de ser fundo."""
    return {(x, y)
            for y in range(quadro.altura)
            for x in range(quadro.largura)
            if quadro.le(x, y) != BRANCO}


def da_cor(quadro: Framebuffer, cor) -> set[tuple[int, int]]:
    """Conjunto de pixels exatamente nesta cor."""
    return {(x, y)
            for y in range(quadro.altura)
            for x in range(quadro.largura)
            if quadro.le(x, y) == cor}


def maior_salto(pixels: list[tuple[int, int]]) -> int:
    """Maior distancia de Chebyshev entre pixels consecutivos."""
    return max((max(abs(bx - ax), abs(by - ay))
                for (ax, ay), (bx, by) in zip(pixels, pixels[1:],
                                              strict=False)),
               default=0)


def distancia_ate_a_reta(px, py, x0, y0, x1, y1) -> float:
    """Distancia perpendicular do ponto ate a reta pelos dois pontos."""
    dx, dy = x1 - x0, y1 - y0
    comprimento = math.hypot(dx, dy)
    if comprimento == 0:
        return math.hypot(px - x0, py - y0)
    return abs(dy * px - dx * py + x1 * y0 - y1 * x0) / comprimento


class BaseDeExercicio(unittest.TestCase):
    """Base que pula o teste enquanto o exercicio nao existir."""

    def exige(self, nome: str) -> Callable:
        """Devolve a funcao do exercicio, ou pula o teste."""
        exercicio = POR_FUNCAO[nome]
        situacao, detalhe = estado(exercicio)
        if situacao == PENDENTE:
            self.skipTest(f"exercicio {exercicio.numero} ({nome}) pendente")
        if situacao == COM_ERRO:
            self.fail(f"{exercicio.assinatura} quebrou na prova: {detalhe}")
        return exercicio.alvo()

    def tela(self, largura: int = 48, altura: int = 32) -> Framebuffer:
        """Framebuffer de trabalho para o teste."""
        return Framebuffer(largura, altura)


class ProvasDeReta:
    """Propriedades que qualquer rasterizador de reta deve cumprir."""

    NOME = ""

    def reta(self):
        """Funcao sob teste."""
        return self.exige(self.NOME)

    def testa_liga_as_duas_extremidades(self):
        traca = self.reta()
        quadro = self.tela()
        traca(4, 3, 40, 26, PRETO, 1, quadro)
        pixels = acesos(quadro)
        self.assertIn((4, 3), pixels)
        self.assertIn((40, 26), pixels)

    def testa_quantidade_e_o_eixo_dominante(self):
        traca = self.reta()
        quadro = self.tela()
        traca(4, 3, 40, 26, PRETO, 1, quadro)
        esperado = max(abs(40 - 4), abs(26 - 3)) + 1
        self.assertEqual(len(acesos(quadro)), esperado)

    def testa_traco_nao_tem_lacuna(self):
        traca = self.reta()
        quadro = self.tela()
        traca(2, 30, 45, 2, PRETO, 1, quadro)
        pixels = sorted(acesos(quadro))
        self.assertLessEqual(maior_salto(pixels), 1)

    def testa_pixels_ficam_colados_na_reta_exata(self):
        traca = self.reta()
        quadro = self.tela()
        traca(3, 4, 44, 27, PRETO, 1, quadro)
        limite = math.sqrt(2) / 2
        for x, y in acesos(quadro):
            self.assertLessEqual(distancia_ate_a_reta(x, y, 3, 4, 44, 27),
                                 limite + 1e-9)

    def testa_reta_horizontal_e_exata(self):
        traca = self.reta()
        quadro = self.tela()
        traca(5, 10, 20, 10, PRETO, 1, quadro)
        self.assertEqual(acesos(quadro), {(x, 10) for x in range(5, 21)})

    def testa_reta_vertical_e_exata(self):
        traca = self.reta()
        quadro = self.tela()
        traca(7, 4, 7, 20, PRETO, 1, quadro)
        self.assertEqual(acesos(quadro), {(7, y) for y in range(4, 21)})

    def testa_diagonal_perfeita_e_exata(self):
        traca = self.reta()
        quadro = self.tela()
        traca(2, 2, 12, 12, PRETO, 1, quadro)
        self.assertEqual(acesos(quadro), {(n, n) for n in range(2, 13)})

    def testa_pontos_coincidentes_acendem_um_pixel(self):
        traca = self.reta()
        quadro = self.tela()
        traca(9, 9, 9, 9, PRETO, 1, quadro)
        self.assertEqual(acesos(quadro), {(9, 9)})

    def testa_funciona_nos_quatro_sentidos(self):
        traca = self.reta()
        for destino in ((44, 28), (2, 28), (44, 2), (2, 2)):
            with self.subTest(destino=destino):
                quadro = self.tela()
                traca(24, 16, *destino, PRETO, 1, quadro)
                self.assertIn((24, 16), acesos(quadro))
                self.assertIn(destino, acesos(quadro))

    def testa_devolve_a_contagem_de_pixels(self):
        traca = self.reta()
        quadro = self.tela()
        devolvido = traca(5, 10, 20, 10, PRETO, 1, quadro)
        self.assertEqual(devolvido, 16)

    def testa_recorta_o_que_sai_da_tela(self):
        traca = self.reta()
        quadro = self.tela()
        traca(-20, 16, 80, 16, PRETO, 1, quadro)
        self.assertEqual(acesos(quadro), {(x, 16) for x in range(48)})


class TestaRetaDDA(ProvasDeReta, BaseDeExercicio):
    """Exercicio 1."""

    NOME = "reta_dda"


class TestaRetaBresenham(ProvasDeReta, BaseDeExercicio):
    """Exercicio 2, mais as garantias proprias do metodo."""

    NOME = "reta_bresenham"

    def testa_nao_repete_pixel(self):
        traca = self.reta()
        quadro = self.tela()
        devolvido = traca(3, 4, 44, 27, PRETO, 1, quadro)
        self.assertEqual(devolvido, len(acesos(quadro)))


class TestaRetangulo(BaseDeExercicio):
    """Exercicio 3."""

    def testa_acende_os_quatro_cantos(self):
        retangulo = self.exige("retangulo")
        quadro = self.tela()
        retangulo(5, 4, 20, 12, PRETO, 1, quadro)
        pixels = acesos(quadro)
        for canto in ((5, 4), (24, 4), (5, 15), (24, 15)):
            self.assertIn(canto, pixels)

    def testa_perimetro_tem_o_tamanho_certo(self):
        retangulo = self.exige("retangulo")
        quadro = self.tela()
        retangulo(5, 4, 20, 12, PRETO, 1, quadro)
        self.assertEqual(len(acesos(quadro)), 2 * 20 + 2 * 12 - 4)

    def testa_interior_fica_vazio(self):
        retangulo = self.exige("retangulo")
        quadro = self.tela()
        retangulo(5, 4, 20, 12, PRETO, 1, quadro)
        self.assertEqual(quadro.le(15, 10), BRANCO)


class TestaCircunferencia(BaseDeExercicio):
    """Exercicio 4."""

    def desenha(self, raio: int = 10) -> tuple[Framebuffer, set]:
        """Desenha uma circunferencia centrada na tela."""
        circunferencia = self.exige("circunferencia")
        quadro = self.tela()
        circunferencia(24, 16, raio, PRETO, 1, quadro)
        return quadro, acesos(quadro)

    def testa_todo_pixel_fica_sobre_o_raio(self):
        _quadro, pixels = self.desenha(10)
        self.assertTrue(pixels)
        for x, y in pixels:
            distancia = math.hypot(x - 24, y - 16)
            self.assertLess(abs(distancia - 10), 1.0)

    def testa_traco_e_simetrico_nos_oito_octantes(self):
        _quadro, pixels = self.desenha(10)
        for x, y in pixels:
            dx, dy = x - 24, y - 16
            for espelho in ((-dx, dy), (dx, -dy), (-dx, -dy),
                            (dy, dx), (-dy, dx), (dy, -dx), (-dy, -dx)):
                self.assertIn((24 + espelho[0], 16 + espelho[1]), pixels)

    def testa_acende_os_quatro_extremos(self):
        _quadro, pixels = self.desenha(10)
        for extremo in ((34, 16), (14, 16), (24, 26), (24, 6)):
            self.assertIn(extremo, pixels)

    def testa_centro_nao_e_pintado(self):
        quadro, _pixels = self.desenha(10)
        self.assertEqual(quadro.le(24, 16), BRANCO)


class TestaElipse(BaseDeExercicio):
    """Exercicio 5."""

    def testa_pixels_satisfazem_a_equacao(self):
        elipse = self.exige("elipse")
        quadro = self.tela()
        elipse(24, 16, 16, 9, PRETO, 1, quadro)
        pixels = acesos(quadro)
        self.assertTrue(pixels)
        for x, y in pixels:
            valor = ((x - 24) / 16) ** 2 + ((y - 16) / 9) ** 2
            self.assertLess(abs(valor - 1.0), 0.35)

    def testa_acende_os_quatro_extremos(self):
        elipse = self.exige("elipse")
        quadro = self.tela()
        elipse(24, 16, 16, 9, PRETO, 1, quadro)
        pixels = acesos(quadro)
        for extremo in ((40, 16), (8, 16), (24, 25), (24, 7)):
            self.assertIn(extremo, pixels)


class TestaBezier(BaseDeExercicio):
    """Exercicio 6."""

    def testa_comeca_e_termina_nas_ancoras(self):
        bezier = self.exige("bezier_cubica")
        quadro = self.tela()
        bezier((4, 28), (12, 2), (36, 30), (44, 4), PRETO, 1, 40, quadro)
        pixels = acesos(quadro)
        self.assertIn((4, 28), pixels)
        self.assertIn((44, 4), pixels)

    def testa_curva_nao_sai_pontilhada(self):
        bezier = self.exige("bezier_cubica")
        quadro = self.tela()
        bezier((4, 28), (12, 2), (36, 30), (44, 4), PRETO, 1, 12, quadro)
        colunas: dict[int, list[int]] = {}
        for x, y in acesos(quadro):
            colunas.setdefault(x, []).append(y)
        presentes = sorted(colunas)
        self.assertEqual(presentes, list(range(presentes[0],
                                               presentes[-1] + 1)))


class TestaPreenchimento(BaseDeExercicio):
    """Exercicios 7, 8 e 9."""

    QUADRADO = ((8, 6), (36, 6), (36, 24), (8, 24))

    def com_moldura(self) -> Framebuffer:
        """Tela com um retangulo de contorno ja desenhado."""
        from motor.primitivas import poligono

        quadro = self.tela()
        try:
            poligono(self.QUADRADO, PRETO, 1, True, quadro)
        except NotImplementedError:
            self.skipTest("depende de uma reta implementada "
                          "(exercicio 1 ou 2)")
        return quadro

    def testa_flood_fill_pinta_o_interior(self):
        flood_fill = self.exige("flood_fill")
        quadro = self.com_moldura()
        flood_fill(22, 15, VERMELHO, 4, quadro)
        self.assertEqual(quadro.le(22, 15), VERMELHO)
        self.assertEqual(quadro.le(9, 7), VERMELHO)

    def testa_flood_fill_nao_vaza_para_fora(self):
        flood_fill = self.exige("flood_fill")
        quadro = self.com_moldura()
        flood_fill(22, 15, VERMELHO, 4, quadro)
        self.assertEqual(quadro.le(0, 0), BRANCO)
        self.assertEqual(quadro.le(47, 31), BRANCO)

    def testa_flood_fill_preserva_o_contorno(self):
        flood_fill = self.exige("flood_fill")
        quadro = self.com_moldura()
        flood_fill(22, 15, VERMELHO, 4, quadro)
        self.assertEqual(quadro.le(8, 6), PRETO)

    def testa_flood_fill_para_se_a_cor_ja_e_a_pedida(self):
        flood_fill = self.exige("flood_fill")
        quadro = self.com_moldura()
        flood_fill(22, 15, VERMELHO, 4, quadro)
        self.assertEqual(flood_fill(22, 15, VERMELHO, 4, quadro), 0)

    def testa_preenche_contorno_respeita_a_borda(self):
        preenche = self.exige("preenche_contorno")
        quadro = self.com_moldura()
        preenche(22, 15, VERMELHO, PRETO, 4, quadro)
        self.assertEqual(quadro.le(22, 15), VERMELHO)
        self.assertEqual(quadro.le(8, 6), PRETO)
        self.assertEqual(quadro.le(0, 0), BRANCO)

    def testa_varredura_preenche_a_area_do_poligono(self):
        preenche = self.exige("preenche_poligono")
        quadro = self.tela()
        preenche(self.QUADRADO, VERMELHO, quadro)
        pintados = da_cor(quadro, VERMELHO)
        self.assertGreater(len(pintados), 400)
        self.assertIn((22, 15), pintados)
        self.assertNotIn((2, 2), pintados)

    def testa_varredura_fica_dentro_da_caixa(self):
        preenche = self.exige("preenche_poligono")
        quadro = self.tela()
        preenche(self.QUADRADO, VERMELHO, quadro)
        for x, y in da_cor(quadro, VERMELHO):
            self.assertTrue(8 <= x <= 36, f"coluna {x} fora da caixa")
            self.assertTrue(6 <= y <= 24, f"linha {y} fora da caixa")


class TestaTransformacoes(BaseDeExercicio):
    """Exercicios 10 a 14."""

    def testa_translacao_desloca_o_ponto(self):
        translacao = self.exige("translacao")
        self.assertEqual(aplica(translacao(5, -3), (10, 10)), (15, 7))

    def testa_translacao_nula_e_a_identidade(self):
        translacao = self.exige("translacao")
        self.assertEqual(aplica(translacao(0, 0), (7, 9)), (7, 9))

    def testa_escala_multiplica_as_coordenadas(self):
        escala = self.exige("escala")
        self.assertEqual(aplica(escala(2, 3), (4, 5)), (8, 15))

    def testa_escala_uniforme_quando_falta_o_segundo_fator(self):
        escala = self.exige("escala")
        self.assertEqual(aplica(escala(2), (4, 5)), (8, 10))

    def testa_rotacao_de_noventa_graus(self):
        rotacao = self.exige("rotacao")
        x, y = aplica(rotacao(90), (1, 0))
        self.assertAlmostEqual(x, 0.0, places=9)
        self.assertAlmostEqual(y, 1.0, places=9)

    def testa_rotacao_completa_volta_ao_ponto(self):
        rotacao = self.exige("rotacao")
        x, y = aplica(rotacao(360), (3, 7))
        self.assertAlmostEqual(x, 3.0, places=6)
        self.assertAlmostEqual(y, 7.0, places=6)

    def testa_cisalhamento_em_x_depende_de_y(self):
        cisalhamento = self.exige("cisalhamento")
        self.assertEqual(aplica(cisalhamento(2, 0), (1, 3)), (7, 3))

    def testa_cisalhamento_em_y_depende_de_x(self):
        cisalhamento = self.exige("cisalhamento")
        self.assertEqual(aplica(cisalhamento(0, 2), (3, 1)), (3, 7))

    def testa_reflexao_nos_tres_modos(self):
        reflexao = self.exige("reflexao")
        self.assertEqual(aplica(reflexao("x"), (4, 5)), (4, -5))
        self.assertEqual(aplica(reflexao("y"), (4, 5)), (-4, 5))
        self.assertEqual(aplica(reflexao("origem"), (4, 5)), (-4, -5))

    def testa_reflexao_recusa_eixo_desconhecido(self):
        reflexao = self.exige("reflexao")
        with self.assertRaises(ValueError):
            reflexao("diagonal")


class TestaRecorte(BaseDeExercicio):
    """Exercicios 15, 16 e 17."""

    JANELA = Janela(10, 8, 30, 22)

    def testa_codigo_de_regiao_dentro_e_zero(self):
        codigo_regiao = self.exige("codigo_regiao")
        self.assertEqual(codigo_regiao(20, 15, self.JANELA), DENTRO)

    def testa_codigo_de_regiao_nos_quatro_lados(self):
        codigo_regiao = self.exige("codigo_regiao")
        self.assertEqual(codigo_regiao(2, 15, self.JANELA), ESQUERDA)
        self.assertEqual(codigo_regiao(40, 15, self.JANELA), DIREITA)
        self.assertEqual(codigo_regiao(20, 2, self.JANELA), ABAIXO)
        self.assertEqual(codigo_regiao(20, 30, self.JANELA), ACIMA)

    def testa_codigo_de_regiao_combina_nos_cantos(self):
        codigo_regiao = self.exige("codigo_regiao")
        self.assertEqual(codigo_regiao(2, 2, self.JANELA),
                         ESQUERDA | ABAIXO)
        self.assertEqual(codigo_regiao(40, 30, self.JANELA),
                         DIREITA | ACIMA)

    def testa_segmento_interno_passa_inteiro(self):
        recorta = self.exige("recorta_linha")
        self.assertEqual(recorta(12, 10, 28, 20, self.JANELA),
                         (12, 10, 28, 20))

    def testa_segmento_externo_e_rejeitado(self):
        recorta = self.exige("recorta_linha")
        self.assertIsNone(recorta(0, 0, 5, 3, self.JANELA))
        self.assertIsNone(recorta(0, 40, 40, 45, self.JANELA))

    def testa_segmento_cortado_termina_na_borda(self):
        recorta = self.exige("recorta_linha")
        sobrou = recorta(0, 15, 45, 15, self.JANELA)
        self.assertIsNotNone(sobrou)
        x0, _y0, x1, _y1 = sobrou
        self.assertAlmostEqual(min(x0, x1), 10, places=6)
        self.assertAlmostEqual(max(x0, x1), 30, places=6)

    def testa_poligono_recortado_cabe_na_janela(self):
        recorta = self.exige("recorta_poligono")
        sobrou = recorta(((0, 0), (45, 0), (45, 40), (0, 40)), self.JANELA)
        self.assertTrue(sobrou)
        for x, y in sobrou:
            self.assertTrue(self.JANELA.contem(x, y), f"({x}, {y}) escapou")

    def testa_poligono_interno_nao_muda_de_area(self):
        recorta = self.exige("recorta_poligono")
        original = [(12, 10), (28, 10), (28, 20), (12, 20)]
        sobrou = recorta(original, self.JANELA)
        self.assertEqual(len(sobrou), 4)
        for ponto in original:
            self.assertIn(ponto, [(round(x), round(y)) for x, y in sobrou])


if __name__ == "__main__":
    unittest.main()
