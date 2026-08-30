"""Ponto de entrada da Bancada Raster.

Uso::

    python bancada.py            # abre em http://127.0.0.1:7860
    python bancada.py 7900       # em outra porta
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.bancada import executa  # noqa: E402  (precisa do sys.path acima)

if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 7860
    executa(porta=porta)
