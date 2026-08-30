# Bancada Raster

Ambiente para construir um motor gráfico de paint do zero. Você
implementa os algoritmos; a bancada mostra cada pixel nascendo, com as
suas próprias variáveis ao lado, na linha do seu código que as escreveu.

## Comece aqui

```bash
git clone https://github.com/joaodest/bancada-raster.git
cd bancada-raster
pip install -r requirements.txt   # só o Gradio, e só para a bancada
python verifica.py                # 0 / 17
python bancada.py                 # abre em http://127.0.0.1:7860
```

Depois: abra `motor/primitivas.py`, implemente `reta_dda`, salve, e
clique em **recarregar módulos** na bancada. O desenho aparece.

## O que tem aqui

| Peça | O que é |
|---|---|
| `motor/` | O motor gráfico. Zero dependências externas. |
| `app/` | A bancada: interface Gradio que observa o motor. |
| `bancada.py` | Sobe a bancada. |
| `verifica.py` | Painel de progresso dos 17 exercícios, no terminal. |
| `testes/` | 107 testes. Os de exercício ficam pulados até você implementar. |
| `exemplos/` | Dois scripts que usam o motor sem navegador. |

## A função auxiliar central

Tudo no motor termina em uma única chamada:

```python
plota(x, y, cor)
```

Ela escreve um pixel na tela ativa, descarta o que cai fora dos limites
(recorte implícito, então nenhuma primitiva precisa validar coordenadas)
e devolve quantos pixels acendeu. É também o ponto que a bancada
observa: com um rastro aberto, cada chamada vira um passo da trilha.

As demais auxiliares, todas em `motor/tela.py`:

| Função | Para quê |
|---|---|
| `cria_tela(largura, altura, cor_fundo)` | Cria o framebuffer e o torna a tela ativa |
| `plota(x, y, cor, espessura, alvo)` | Acende um pixel (ou um disco, se `espessura > 1`) |
| `plota_disco(x, y, raio, cor)` | Pincel redondo |
| `plota_pontos(pontos, cor)` | Aplica `plota` a uma sequência |
| `le_pixel(x, y)` | Cor de um pixel, ou `None` fora da tela |
| `limpa(cor)` | Pinta a tela inteira |
| `dentro(x, y)` | Testa limites |
| `largura()`, `altura()`, `dimensoes()` | Tamanho da tela |
| `tela(alvo)` | Resolve qual framebuffer usar |

Toda primitiva aceita `alvo=` para desenhar em outro framebuffer sem
mexer na tela ativa. E toda operação de imagem está em `motor/efeitos.py`
(inverter, cinza, espelhar, substituir cor, mesclar) e `motor/imagem.py`
(salvar PNG e PPM, sem Pillow).

## Sistema de coordenadas

Origem `(0, 0)` no canto superior esquerdo, `x` cresce para a direita,
`y` cresce para baixo. É a convenção de qualquer dispositivo raster, e a
razão de uma rotação positiva parecer horária na prancheta.

## Os 17 exercícios

| # | Arquivo | Função |
|---|---|---|
| 1 | `motor/primitivas.py` | `reta_dda` |
| 2 | `motor/primitivas.py` | `reta_bresenham` |
| 3 | `motor/primitivas.py` | `retangulo` |
| 4 | `motor/primitivas.py` | `circunferencia` |
| 5 | `motor/primitivas.py` | `elipse` |
| 6 | `motor/primitivas.py` | `bezier_cubica` |
| 7 | `motor/preenchimento.py` | `flood_fill` |
| 8 | `motor/preenchimento.py` | `preenche_contorno` |
| 9 | `motor/preenchimento.py` | `preenche_poligono` |
| 10 | `motor/transformacoes.py` | `translacao` |
| 11 | `motor/transformacoes.py` | `escala` |
| 12 | `motor/transformacoes.py` | `rotacao` |
| 13 | `motor/transformacoes.py` | `cisalhamento` |
| 14 | `motor/transformacoes.py` | `reflexao` |
| 15 | `motor/recorte.py` | `codigo_regiao` |
| 16 | `motor/recorte.py` | `recorta_linha` |
| 17 | `motor/recorte.py` | `recorta_poligono` |

Cada função pendente levanta `NotImplementedError` e traz o roteiro do
algoritmo na própria docstring. A bancada lê esse roteiro e o mostra no
painel da direita enquanto o exercício não sai, então não existe uma
segunda cópia das instruções para desatualizar.

`poligono` e `reta` já vêm prontas: a primeira mostra o estilo esperado
(composição, sem conta própria) e a segunda escolhe sozinha entre
Bresenham e DDA, conforme o que você já implementou.

## O que a bancada mostra

**Prancheta.** Grade de 96 × 64 pixels ampliada, com zoom de 1x a 4x
seguindo o passo corrente. Clique para mover `p0` ou `p1`. O que cada
ponto significa muda com o algoritmo: extremos do segmento, centro e
raio, semente do preenchimento ou ângulo da rotação.

**Perfil analítico.** O que a execução inteira produziu:

- `passos` e `pixels`, e a diferença entre eles (trabalho repetido)
- `duração` medida em execução limpa, sem a sobrecarga do rastreador
- `aritmética`, deduzida dos tipos das suas variáveis: `inteira` ou
  `ponto flutuante`. É por aqui que a diferença entre DDA e Bresenham
  aparece sozinha.
- `continuidade`, a maior distância entre passos consecutivos: mede
  buraco no traço
- `desvio máximo` e `desvio médio` até a reta matemática exata

**Estado no passo.** As variáveis locais do seu código naquele
instante, com o que mudou desde o passo anterior em destaque.

**Código em execução.** A sua função, com a linha que plotou o pixel em
foco marcada, e uma coluna contando quantos pixels cada linha plotou na
execução inteira: um pequeno profiler por linha.

**DDA × Bresenham.** Roda os dois sobre o mesmo segmento e pinta a
divergência: azul onde só o DDA acendeu, vermelho onde só o Bresenham
acendeu, grafite onde os dois concordam.

## Travas de segurança

Um laço infinito no seu algoritmo não trava a bancada. O rastreador
interrompe a execução em 40 000 chamadas a `plota` ou 4 segundos, marca
o rastro como interrompido e ainda mostra tudo o que foi desenhado até
ali. Exceções também não escapam: elas aparecem no painel, ao lado dos
passos que já tinham acontecido.

A trava não pega um laço que nunca chama `plota`. Nesse caso, interrompa
o processo no terminal.

## Testes

```bash
python -m unittest discover -s testes -t .
```

Os testes do núcleo (cores, framebuffer, imagem, rastreador, análise)
passam sempre. Os 59 testes de exercício ficam pulados enquanto a função
levantar `NotImplementedError`, e passam a valer sozinhos assim que você
a implementar. Se a função existir mas quebrar, o teste falha: um erro
de digitação nunca se disfarça de exercício não começado.

## Exemplos

```bash
python exemplos/01_cartao_de_teste.py     # desenha tudo e salva um PNG
python exemplos/02_rastro_no_terminal.py  # o mesmo perfil, sem navegador
python exemplos/02_rastro_no_terminal.py reta_bresenham 2 2 40 14
```

## Convenções de código

- PEP 8 com linhas de até 79 colunas, PEP 257 nas docstrings e PEP 484
  nas anotações de tipo.
- Identificadores em ASCII (`funcao`, `duracao`, `poligono`); texto
  visível em português com acentuação.
- `ruff check .` passa limpo com a configuração do `pyproject.toml`.
  Não rode `ruff format`: as quebras de linha aqui são manuais, para
  manter as 79 colunas com quebras escolhidas à mão, e o formatador
  reescreveria o arquivo inteiro com outras decisões.

## Dependências

O `motor/` não tem nenhuma: só a biblioteca padrão, incluindo o
codificador PNG. A bancada precisa de Gradio 6 (que traz o Pillow junto), usado apenas
para servir a página e desenhar as camadas de leitura sobre a
prancheta. O pino é `>=6` porque o Gradio 6 moveu `theme` e `css` do
construtor de `Blocks` para o `launch()`, e a bancada usa a forma nova.
