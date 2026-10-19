#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Code128 -> SVG (puro, sem dependencia).

Gera codigo de barras Code128 em SVG para o Diario Oficial do Reino
Martyniano. O algoritmo de codificacao (tabela de padroes, set A/B/C,
otimizacao TO_C e checksum modulo 103) e o mesmo do reportlab
(reportlab.graphics.barcode.code128), biblioteca que gera o PDF de
referencia, para que o SVG saia identico ao PDF. Nao desenha barras
com CSS: cada barra e um <rect> com geometria propria.
"""

from string import digits

# ---- tabela de padroes (valor 0..106 -> "BbAb..." ) ------------------------
# Barra = letra maiuscula (A=1, B=2, C=3, D=4 modulos).
# Espaco = letra minuscula (a=1, b=2, c=3, d=4 modulos).
# Alternam sempre barra, espaco, barra, espaco, ... comecando em barra.
_PATTERNS = {
    0: 'BaBbBb', 1: 'BbBaBb', 2: 'BbBbBa', 3: 'AbAbBc', 4: 'AbAcBb',
    5: 'AcAbBb', 6: 'AbBbAc', 7: 'AbBcAb', 8: 'AcBbAb', 9: 'BbAbAc',
    10: 'BbAcAb', 11: 'BcAbAb', 12: 'AaBbCb', 13: 'AbBaCb', 14: 'AbBbCa',
    15: 'AaCbBb', 16: 'AbCaBb', 17: 'AbCbBa', 18: 'BbCbAa', 19: 'BbAaCb',
    20: 'BbAbCa', 21: 'BaCbAb', 22: 'BbCaAb', 23: 'CaBaCa', 24: 'CaAbBb',
    25: 'CbAaBb', 26: 'CbAbBa', 27: 'CaBbAb', 28: 'CbBaAb', 29: 'CbBbAa',
    30: 'BaBaBc', 31: 'BaBcBa', 32: 'BcBaBa', 33: 'AaAcBc', 34: 'AcAaBc',
    35: 'AcAcBa', 36: 'AaBcAc', 37: 'AcBaAc', 38: 'AcBcAa', 39: 'BaAcAc',
    40: 'BcAaAc', 41: 'BcAcAa', 42: 'AaBaCc', 43: 'AaBcCa', 44: 'AcBaCa',
    45: 'AaCaBc', 46: 'AaCcBa', 47: 'AcCaBa', 48: 'CaCaBa', 49: 'BaAcCa',
    50: 'BcAaCa', 51: 'BaCaAc', 52: 'BaCcAa', 53: 'BaCaCa', 54: 'CaAaBc',
    55: 'CaAcBa', 56: 'CcAaBa', 57: 'CaBaAc', 58: 'CaBcAa', 59: 'CcBaAa',
    60: 'CaDaAa', 61: 'BbAdAa', 62: 'DcAaAa', 63: 'AaAbBd', 64: 'AaAdBb',
    65: 'AbAaBd', 66: 'AbAdBa', 67: 'AdAaBb', 68: 'AdAbBa', 69: 'AaBbAd',
    70: 'AaBdAb', 71: 'AbBaAd', 72: 'AbBdAa', 73: 'AdBaAb', 74: 'AdBbAa',
    75: 'BdAbAa', 76: 'BbAaAd', 77: 'DaCaAa', 78: 'BdAaAb', 79: 'AcDaAa',
    80: 'AaAbDb', 81: 'AbAaDb', 82: 'AbAbDa', 83: 'AaDbAb', 84: 'AbDaAb',
    85: 'AbDbAa', 86: 'DaAbAb', 87: 'DbAaAb', 88: 'DbAbAa', 89: 'BaBaDa',
    90: 'BaDaBa', 91: 'DaBaBa', 92: 'AaAaDc', 93: 'AaAcDa', 94: 'AcAaDa',
    95: 'AaDaAc', 96: 'AaDcAa', 97: 'DaAaAc', 98: 'DaAcAa', 99: 'AaCaDa',
    100: 'AaDaCa', 101: 'CaAaDa', 102: 'DaAaCa', 103: 'BaAdAb',
    104: 'BaAbAd', 105: 'BaAbCb', 106: 'BcCaAaB',
}

_STARTA, _STARTB, _STARTC, _STOP = 103, 104, 105, 106

_SETA = {
    ' ': 0, '!': 1, '"': 2, '#': 3, '$': 4, '%': 5, '&': 6, "'": 7,
    '(': 8, ')': 9, '*': 10, '+': 11, ',': 12, '-': 13, '.': 14, '/': 15,
    '0': 16, '1': 17, '2': 18, '3': 19, '4': 20, '5': 21, '6': 22,
    '7': 23, '8': 24, '9': 25, ':': 26, ';': 27, '<': 28, '=': 29,
    '>': 30, '?': 31, '@': 32, 'A': 33, 'B': 34, 'C': 35, 'D': 36,
    'E': 37, 'F': 38, 'G': 39, 'H': 40, 'I': 41, 'J': 42, 'K': 43,
    'L': 44, 'M': 45, 'N': 46, 'O': 47, 'P': 48, 'Q': 49, 'R': 50,
    'S': 51, 'T': 52, 'U': 53, 'V': 54, 'W': 55, 'X': 56, 'Y': 57,
    'Z': 58, '[': 59, '\\': 60, ']': 61, '^': 62, '_': 63,
    'SHIFT': 98, 'TO_C': 99, 'TO_B': 100,
}

_SETB = {
    ' ': 0, '!': 1, '"': 2, '#': 3, '$': 4, '%': 5, '&': 6, "'": 7,
    '(': 8, ')': 9, '*': 10, '+': 11, ',': 12, '-': 13, '.': 14, '/': 15,
    '0': 16, '1': 17, '2': 18, '3': 19, '4': 20, '5': 21, '6': 22,
    '7': 23, '8': 24, '9': 25, ':': 26, ';': 27, '<': 28, '=': 29,
    '>': 30, '?': 31, '@': 32, 'A': 33, 'B': 34, 'C': 35, 'D': 36,
    'E': 37, 'F': 38, 'G': 39, 'H': 40, 'I': 41, 'J': 42, 'K': 43,
    'L': 44, 'M': 45, 'N': 46, 'O': 47, 'P': 48, 'Q': 49, 'R': 50,
    'S': 51, 'T': 52, 'U': 53, 'V': 54, 'W': 55, 'X': 56, 'Y': 57,
    'Z': 58, '[': 59, '\\': 60, ']': 61, '^': 62, '_': 63, '`': 64,
    'a': 65, 'b': 66, 'c': 67, 'd': 68, 'e': 69, 'f': 70, 'g': 71,
    'h': 72, 'i': 73, 'j': 74, 'k': 75, 'l': 76, 'm': 77, 'n': 78,
    'o': 79, 'p': 80, 'q': 81, 'r': 82, 's': 83, 't': 84, 'u': 85,
    'v': 86, 'w': 87, 'x': 88, 'y': 89, 'z': 90, '{': 91, '|': 92,
    '}': 93, '~': 94,
    'SHIFT': 98, 'TO_C': 99, 'TO_A': 101,
}

_SETC = {'%02d' % i: i for i in range(100)}
_SETC['TO_B'] = 100
_SETC['TO_A'] = 101

_SETMAP = {
    'TO_A': (_SETA, _SETB),
    'TO_B': (_SETB, _SETA),
    'TO_C': (_SETC, None),
    'START_A': (_STARTA, _SETA, _SETB),
    'START_B': (_STARTB, _SETB, _SETA),
    'START_C': (_STARTC, _SETC, None),
}
_CSTARTS = ('START_B', 'TO_A', 'TO_B')
_TOS = list(_SETMAP.keys())


def _try_to_c(l):
    """Otimizacao de digitos para Set C (mesma logica do reportlab)."""
    i = 0
    nl = []
    while i < len(l):
        startpos = i
        rl = []
        savings = -1
        while i < len(l):
            if l[i] in _CSTARTS:
                j = i
                break
            elif l[i] == '\xf1':
                rl.append(l[i])
                i += 1
                continue
            elif l[i] in digits and l[i + 1] in digits:
                rl.append(l[i] + l[i + 1])
                i += 2
                savings += 1
                continue
            else:
                if l[i] in digits and l[i + 1] == 'STOP':
                    rrl = []
                    rsavings = -1
                    k = i
                    while k > startpos:
                        if l[k] == '\xf1':
                            rrl.append(l[i])
                            k -= 1
                        elif l[k] in digits and l[k - 1] in digits:
                            rrl.append(l[k - 1] + l[k])
                            rsavings += 1
                            k -= 2
                        else:
                            break
                    rrl.reverse()
                    if rsavings > savings + int(savings >= 0 and (startpos and nl[-1] in _CSTARTS)) - 1:
                        nl += l[startpos]
                        startpos += 1
                        rl = rrl
                        del rrl
                        i += 1
                break
        ta = not (l[i] == 'STOP' or j == i)
        xs = savings >= 0 and (startpos and nl[-1] in _CSTARTS)
        if savings + int(xs) > int(ta):
            if xs:
                toc = nl[-1][:-1] + 'C'
                del nl[-1]
            else:
                toc = 'TO_C'
            nl += [toc] + rl
            if ta:
                nl.append('TO' + l[j][-2:])
            nl.append(l[i])
        else:
            nl += l[startpos:i + 1]
        i += 1
    return nl


def _codificar(value):
    """Devolve a lista de valores (simbolos) do Code128, com checksum e stop."""
    s = value
    l = ['START_B']
    for c in s:
        if c not in _SETB:
            l = l + ['TO_A', c, 'TO_B']
        else:
            l.append(c)
    l.append('STOP')
    l = _try_to_c(l)
    if l[1] in _TOS:
        l[:2] = ['START_' + l[1][-1]]

    start, set_, shset = _SETMAP[l[0]]
    e = [start]
    l = l[1:-1]
    while l:
        c = l[0]
        if c == 'SHIFT':
            e = e + [set_[c], shset[l[1]]]
            l = l[2:]
        elif c in _TOS:
            e.append(set_[c])
            set_, shset = _SETMAP[c]
            l = l[1:]
        else:
            e.append(set_[c])
            l = l[1:]

    c = e[0]
    for i in range(1, len(e)):
        c = c + i * e[i]
    return e + [c % 103, _STOP]


def _barras(value):
    """Devolve lista de (largura_em_modulos) alternando barra/espaco.

    O primeiro elemento e uma barra; a lista alterna barra, espaco, ...
    Termina em barra (o stop termina em barra). Usada para desenhar o SVG.
    """
    simbolos = _codificar(value)
    larguras = []
    for sv in simbolos:
        padrao = _PATTERNS[sv]
        for ch in padrao:
            if 'A' <= ch <= 'Z':
                larguras.append((1, ord(ch) - 64))   # barra
            else:
                larguras.append((0, ord(ch) - 96))   # espaco
    return larguras


def svg_code128(value, altura=48, modulo=1.0, quiet=10, cor='#1c1a18'):
    """Devolve um <svg> inline (sem XML header) com o codigo de barras.

    Cada barra e um <rect> proprio (nada de barras por CSS). A zona de
    silencio (margem) de `quiet` modulos de cada lado garante leitura.
    """
    seq = _barras(value)
    # posicao acumulada em modulos
    retangulos = []
    x = quiet
    for eh_barra, larg in seq:
        if eh_barra:
            retangulos.append(
                '<rect x="%.3f" y="0" width="%.3f" height="%d" fill="%s"/>'
                % (x * modulo, larg * modulo, altura, cor)
            )
        x += larg
    total_modulos = x + quiet
    largura = total_modulos * modulo
    return (
        '<svg class="codigo-barras" viewBox="0 0 %.3f %d" '
        'width="%.3f" height="%d" role="img" '
        'aria-label="Codigo de barras %s" xmlns="http://www.w3.org/2000/svg">'
        '%s</svg>'
    ) % (largura, altura, largura, altura, value, ''.join(retangulos))


def codigo_do_ato(designador, sha256_hex):
    """O codigo legivel do ato: <designador sem pontos>R<10 primeiros do sha>.

    Ex.: 'AL.04.2026' + sha -> 'AL042026R<10 hex maiusculos>'.
    Igual ao codigo do PDF de referencia.
    """
    prefixo = designador.replace('.', '')
    return prefixo + 'R' + (sha256_hex or '')[:10].upper()


if __name__ == '__main__':
    import sys
    codigo = sys.argv[1] if len(sys.argv) > 1 else 'AL042026R37EC953B2E'
    print(svg_code128(codigo))
