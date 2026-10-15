#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APLICATIVO LOCAL — o Portal do Reino Martyniano em janela própria.

Levanta o servidor do Portal (se estiver apagado) e abre a porta em uma
janela nativa dedicada, sem aba de navegador e sem barra de endereço.

uso:  portal_app.py
"""
import os
import sys
import time
import subprocess

for _dp in ("/usr/lib/python3/dist-packages", "/usr/lib/python3.11/dist-packages"):
    if _dp not in sys.path and os.path.isdir(_dp):
        sys.path.append(_dp)

CASA = "/home/usuario/Reino/reino-martyniano"
PORTA = 5010
PY = "/home/usuario/.venv/bin/python"
URL = "http://127.0.0.1:%d/" % PORTA
TITULO = "Portal do Reino Martyniano — Diário Oficial"


def no_ar():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        try:
            s.connect(("127.0.0.1", PORTA))
            return True
        except Exception:
            return False


def bombear():
    if no_ar():
        return None
    p = subprocess.Popen(
        [PY, "app.py"],
        cwd=CASA,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(60):
        time.sleep(0.5)
        if no_ar():
            return p
    raise SystemExit("O Portal não acendeu: o servidor não atendeu na porta %d." % PORTA)


def main():
    # Gravar o diário do aplicativo: sem isso nao ha onde medir falha de janela.
    try:
        _log = open("/tmp/portal-app.log", "a", buffering=1)
        sys.stdout = _log
        sys.stderr = _log
    except Exception:
        pass
    print("\n=== abertura %s ===" % time.strftime("%d/%m/%Y %H:%M:%S"))
    bombear()
    import webview
    webview.create_window(
        TITULO,
        URL,
        width=1380,
        height=860,
        min_size=(980, 640),
        background_color="#f5f0e6",
    )
    webview.start()


if __name__ == "__main__":
    main()
