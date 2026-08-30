"""Testes do rastreador e do perfil analitico.

Estes testes usam algoritmos escritos aqui dentro, nao os exercicios do
motor: o que esta sob teste e a instrumentacao, e ela precisa passar
mesmo com o laboratorio inteiro por fazer.
"""

from __future__ import annotations

import unittest

from motor.analise import analisa, compara
from motor.cores import PRETO
from motor.framebuffer import Framebuffer
from motor.tela import plota
from motor.tracador import LimiteDePassos, formata_valor, rastreia


def risca_reta(quantidade: int, alvo: Framebuffer) -> int:
    """Algoritmo de teste: uma linha horizontal com erro inteiro."""
    erro = 0
    acesos = 0
    for coluna in range(quantidade):
        erro += 2
        acesos += plota(coluna, 3, PRETO, 1, alvo)
    return acesos


def risca_com_float(quantidade: int, alvo: Framebuffer) -> int:
    """Algoritmo de teste que carrega uma variavel de ponto flutuante."""
    posicao = 0.0
    acesos = 0
    for _ in range(quantidade):
        acesos += plota(round(posicao), 5, PRETO, 1, alvo)
        posicao += 1.5
    return acesos


def nunca_para(alvo: Framebuffer) -> None:
    """Algoritmo de teste que nao termina sozinho."""
    while True:
        plota(0, 0, PRETO, 1, alvo)


def quebra(alvo: Framebuffer) -> None:
    """Algoritmo de teste que levanta uma excecao no meio."""
    plota(1, 1, PRETO, 1, alvo)
    raise ValueError("erro proposital")


class TestaRastreador(unittest.TestCase):
    """Captura de passos, variaveis e codigo-fonte."""

    def setUp(self):
        self.quadro = Framebuffer(20, 10)

    def testa_captura_um_passo_por_chamada(self):
        rastro = rastreia(risca_reta, 6, self.quadro)
        self.assertEqual(len(rastro.passos), 6)
        self.assertIsNone(rastro.erro)
        self.assertEqual(rastro.retorno, 6)

    def testa_passos_guardam_a_posicao_escrita(self):
        rastro = rastreia(risca_reta, 4, self.quadro)
        self.assertEqual([p.posicao for p in rastro.passos],
                         [(0, 3), (1, 3), (2, 3), (3, 3)])

    def testa_captura_as_variaveis_locais(self):
        rastro = rastreia(risca_reta, 3, self.quadro)
        variaveis = rastro.passos[2].variaveis
        self.assertEqual(variaveis["erro"], 6)
        self.assertEqual(variaveis["coluna"], 2)

    def testa_captura_a_linha_e_a_funcao(self):
        rastro = rastreia(risca_reta, 2, self.quadro)
        passo = rastro.passos[0]
        self.assertEqual(passo.funcao, "risca_reta")
        fonte = rastro.fonte_do_passo(passo)
        self.assertIsNotNone(fonte)
        indice = fonte.indice_da_linha(passo.linha)
        self.assertIn("plota(", fonte.linhas[indice])

    def testa_marca_pixels_descartados(self):
        pequeno = Framebuffer(3, 10)
        rastro = rastreia(risca_reta, 6, pequeno)
        self.assertEqual(len(rastro.passos), 6)
        self.assertEqual(len(rastro.escritos), 3)

    def testa_guarda_a_excecao_sem_propagar(self):
        rastro = rastreia(quebra, self.quadro)
        self.assertIsInstance(rastro.erro, ValueError)
        self.assertTrue(rastro.falhou)
        self.assertFalse(rastro.pendente)
        self.assertEqual(len(rastro.passos), 1)

    def testa_reconhece_exercicio_pendente(self):
        def pendente(_alvo):
            raise NotImplementedError("EXERCICIO 0")

        rastro = rastreia(pendente, self.quadro)
        self.assertTrue(rastro.pendente)
        self.assertFalse(rastro.falhou)

    def testa_trava_de_seguranca_interrompe_laco_infinito(self):
        rastro = rastreia(nunca_para, self.quadro, limite_de_passos=500)
        self.assertTrue(rastro.interrompido)
        self.assertIsInstance(rastro.erro, LimiteDePassos)
        self.assertEqual(len(rastro.passos), 500)

    def testa_nao_captura_fora_de_um_rastro(self):
        plota(0, 0, PRETO, 1, self.quadro)
        rastro = rastreia(risca_reta, 2, self.quadro)
        self.assertEqual(len(rastro.passos), 2)


class TestaPerfil(unittest.TestCase):
    """Leitura analitica de um rastro."""

    def setUp(self):
        self.quadro = Framebuffer(20, 10)

    def testa_conta_passos_e_pixels(self):
        perfil = analisa(rastreia(risca_reta, 5, self.quadro))
        self.assertEqual(perfil.passos, 5)
        self.assertEqual(perfil.pixels, 5)
        self.assertEqual(perfil.repetidos, 0)

    def testa_classifica_aritmetica_inteira(self):
        perfil = analisa(rastreia(risca_reta, 5, self.quadro))
        self.assertEqual(perfil.aritmetica, "inteira")

    def testa_classifica_ponto_flutuante(self):
        perfil = analisa(rastreia(risca_com_float, 5, self.quadro))
        self.assertEqual(perfil.aritmetica, "ponto flutuante")

    def testa_detecta_lacuna_no_traco(self):
        perfil = analisa(rastreia(risca_com_float, 5, self.quadro))
        self.assertGreater(perfil.maior_salto, 1)
        self.assertFalse(perfil.continuo)

    def testa_traco_contiguo_nao_tem_lacuna(self):
        perfil = analisa(rastreia(risca_reta, 5, self.quadro))
        self.assertTrue(perfil.continuo)

    def testa_conta_descartados(self):
        perfil = analisa(rastreia(risca_reta, 6, Framebuffer(3, 10)))
        self.assertEqual(perfil.descartados, 3)

    def testa_desvio_e_zero_sobre_a_propria_reta(self):
        perfil = analisa(rastreia(risca_reta, 5, self.quadro),
                         referencia=(0, 3, 4, 3))
        self.assertAlmostEqual(perfil.desvio_maximo, 0.0)
        self.assertAlmostEqual(perfil.desvio_medio, 0.0)

    def testa_medidas_saem_rotuladas(self):
        perfil = analisa(rastreia(risca_reta, 5, self.quadro))
        rotulos = [m.rotulo for m in perfil.medidas()]
        self.assertIn("passos", rotulos)
        self.assertIn("aritmética", rotulos)


class TestaComparacao(unittest.TestCase):
    """Confronto entre dois rastros."""

    def testa_tracos_iguais_concordam_totalmente(self):
        a = rastreia(risca_reta, 5, Framebuffer(20, 10))
        b = rastreia(risca_reta, 5, Framebuffer(20, 10))
        diferenca = compara(a, b, "a", "b")
        self.assertTrue(diferenca.identicos)
        self.assertEqual(diferenca.concordancia, 1.0)

    def testa_tracos_diferentes_separam_os_exclusivos(self):
        a = rastreia(risca_reta, 5, Framebuffer(20, 10))
        b = rastreia(risca_com_float, 5, Framebuffer(20, 10))
        diferenca = compara(a, b, "a", "b")
        self.assertFalse(diferenca.identicos)
        self.assertTrue(diferenca.apenas_a)
        self.assertTrue(diferenca.apenas_b)
        self.assertLess(diferenca.concordancia, 1.0)


class TestaFormatacao(unittest.TestCase):
    """Apresentacao dos valores na tabela de estado."""

    def testa_inteiro_sai_sem_ponto(self):
        self.assertEqual(formata_valor(42), "42")

    def testa_float_redondo_mantem_uma_casa(self):
        self.assertEqual(formata_valor(18.0), "18.0")

    def testa_float_quebrado_nao_termina_em_ponto(self):
        texto = formata_valor(18.000000000000004)
        self.assertFalse(texto.endswith("."))
        self.assertTrue(texto.startswith("18"))

    def testa_cor_sai_em_hexadecimal(self):
        self.assertEqual(formata_valor(PRETO), "#000000")

    def testa_booleano_sai_em_portugues(self):
        self.assertEqual(formata_valor(True), "sim")


if __name__ == "__main__":
    unittest.main()
