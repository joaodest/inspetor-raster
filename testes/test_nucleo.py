"""Testes do nucleo do motor: cores, framebuffer e imagem."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from motor.cores import BRANCO, PRETO, VERMELHO, Cor, limita, mistura
from motor.framebuffer import Framebuffer
from motor.imagem import (
    carrega_ppm,
    para_base64_png,
    para_png,
    para_ppm,
    salva_ppm,
)
from motor.tela import cria_tela, le_pixel, limpa, plota


class TestaCor(unittest.TestCase):
    """Modelo de cor e conversoes."""

    def testa_limita_restringe_ao_intervalo(self):
        self.assertEqual(limita(-40), 0)
        self.assertEqual(limita(300), 255)
        self.assertEqual(limita(127.6), 128)

    def testa_de_hex_aceita_tres_e_seis_digitos(self):
        self.assertEqual(Cor.de_hex("#fff"), BRANCO)
        self.assertEqual(Cor.de_hex("ff0000"), Cor(255, 0, 0))

    def testa_de_hex_recusa_texto_invalido(self):
        with self.assertRaises(ValueError):
            Cor.de_hex("#12345")

    def testa_para_hex_e_o_inverso_de_de_hex(self):
        self.assertEqual(Cor.de_hex(VERMELHO.para_hex()), VERMELHO)

    def testa_invertida_e_involutiva(self):
        self.assertEqual(VERMELHO.invertida().invertida(), VERMELHO)

    def testa_em_cinza_zera_a_saturacao(self):
        cinza = VERMELHO.em_cinza()
        self.assertEqual(cinza.r, cinza.g)
        self.assertEqual(cinza.g, cinza.b)

    def testa_mistura_respeita_os_extremos(self):
        self.assertEqual(mistura(PRETO, BRANCO, 0.0), PRETO)
        self.assertEqual(mistura(PRETO, BRANCO, 1.0), BRANCO)
        self.assertEqual(mistura(PRETO, BRANCO, 0.5), Cor(128, 128, 128))

    def testa_mistura_limita_o_fator(self):
        self.assertEqual(mistura(PRETO, BRANCO, 5.0), BRANCO)
        self.assertEqual(mistura(PRETO, BRANCO, -5.0), PRETO)


class TestaFramebuffer(unittest.TestCase):
    """Escrita, leitura e limites do buffer de quadro."""

    def setUp(self):
        self.quadro = Framebuffer(8, 5)

    def testa_nasce_com_a_cor_de_fundo(self):
        self.assertEqual(self.quadro.le(0, 0), BRANCO)
        self.assertEqual(self.quadro.le(7, 4), BRANCO)

    def testa_recusa_dimensao_nao_positiva(self):
        with self.assertRaises(ValueError):
            Framebuffer(0, 5)

    def testa_plota_escreve_e_confirma(self):
        self.assertTrue(self.quadro.plota(3, 2, VERMELHO))
        self.assertEqual(self.quadro.le(3, 2), VERMELHO)

    def testa_plota_descarta_fora_dos_limites(self):
        self.assertFalse(self.quadro.plota(-1, 0, PRETO))
        self.assertFalse(self.quadro.plota(8, 0, PRETO))
        self.assertFalse(self.quadro.plota(0, 5, PRETO))
        self.assertIsNone(self.quadro.le(99, 99))

    def testa_pixels_vizinhos_nao_sao_afetados(self):
        self.quadro.plota(3, 2, PRETO)
        self.assertEqual(self.quadro.le(2, 2), BRANCO)
        self.assertEqual(self.quadro.le(4, 2), BRANCO)
        self.assertEqual(self.quadro.le(3, 1), BRANCO)
        self.assertEqual(self.quadro.le(3, 3), BRANCO)

    def testa_instantaneo_e_restaura(self):
        marco = self.quadro.instantaneo()
        self.quadro.plota(1, 1, PRETO)
        self.quadro.restaura(marco)
        self.assertEqual(self.quadro.le(1, 1), BRANCO)

    def testa_restaura_recusa_tamanho_errado(self):
        with self.assertRaises(ValueError):
            self.quadro.restaura(b"curto demais")

    def testa_copia_e_independente(self):
        clone = self.quadro.copia()
        clone.plota(0, 0, PRETO)
        self.assertEqual(self.quadro.le(0, 0), BRANCO)


class TestaTelaAtiva(unittest.TestCase):
    """Funcoes auxiliares que trabalham sobre a tela corrente."""

    def setUp(self):
        self.quadro = cria_tela(10, 10)

    def testa_plota_usa_a_tela_ativa(self):
        plota(4, 4, VERMELHO)
        self.assertEqual(le_pixel(4, 4), VERMELHO)

    def testa_plota_devolve_a_contagem_de_pixels(self):
        self.assertEqual(plota(1, 1, PRETO), 1)
        self.assertEqual(plota(-5, 1, PRETO), 0)

    def testa_espessura_acende_uma_vizinhanca(self):
        limpa()
        acesos = plota(5, 5, PRETO, espessura=3)
        self.assertGreater(acesos, 1)
        self.assertEqual(le_pixel(5, 5), PRETO)

    def testa_alvo_explicito_nao_toca_a_tela_ativa(self):
        outro = Framebuffer(4, 4)
        plota(0, 0, PRETO, alvo=outro)
        self.assertEqual(outro.le(0, 0), PRETO)
        self.assertEqual(le_pixel(0, 0), BRANCO)


class TestaImagem(unittest.TestCase):
    """Serializacao PPM e PNG."""

    def setUp(self):
        self.quadro = Framebuffer(4, 3, BRANCO)
        self.quadro.plota(1, 1, VERMELHO)

    def testa_ppm_tem_cabecalho_e_corpo(self):
        dados = para_ppm(self.quadro)
        self.assertTrue(dados.startswith(b"P6\n4 3\n255\n"))
        self.assertEqual(len(dados), len(b"P6\n4 3\n255\n") + 4 * 3 * 3)

    def testa_ppm_faz_ida_e_volta(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = salva_ppm(self.quadro, Path(pasta) / "t.ppm")
            lido = carrega_ppm(destino)
        self.assertEqual(lido.dimensoes, self.quadro.dimensoes)
        self.assertEqual(lido.le(1, 1), VERMELHO)

    def testa_png_tem_assinatura_e_fim(self):
        dados = para_png(self.quadro)
        self.assertTrue(dados.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertTrue(dados.endswith(b"IEND\xaeB`\x82"))

    def testa_base64_png_e_texto_ascii(self):
        texto = para_base64_png(self.quadro)
        self.assertIsInstance(texto, str)
        texto.encode("ascii")


if __name__ == "__main__":
    unittest.main()
