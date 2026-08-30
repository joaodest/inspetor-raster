"""Suite de testes do laboratorio.

Rode a partir da raiz do projeto::

    python -m unittest discover -s testes -t .

Os testes do nucleo (cores, framebuffer, imagem, instrumentacao) devem
passar sempre. Os testes de exercicio ficam marcados como pulados
enquanto a funcao correspondente levantar ``NotImplementedError``, e
comecam a valer sozinhos assim que voce a implementar.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
