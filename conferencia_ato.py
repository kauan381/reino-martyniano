#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conferência do molde v2.0 do Diário Oficial (padrão documental v2.0, seção 10).

Busca a página renderizada de um ato e reporta, item a item:
  1. fonte carregada (Playfair + EB Garamond servidas por @font-face local)
  2. brasão presente (sem quadro, no topo)
  3. cifra presente
  4. chancela presente (nome vigente)
  5. comando PROMULGAMOS (Atos Legislativos/Constitucionais)
  6. hash preenchido (SHA-256 nunca vazio)
  7. código de barras Code128 legível (SVG com barras próprias + número em linha)
  8. bloco de aprovação ausente quando não há ata (aprovacoes)

Uso:  conferencia_ato.py <designador> [url-base]
Ex.:  conferencia_ato.py AL.04.2026
      conferencia_ato.py AL.04.2026 http://127.0.0.1:5010
"""
import re
import sys
import os
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, 'static')
FONTES = os.path.join(STATIC, 'fontes')


def fetch(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return r.read().decode('utf-8')


def main():
    designador = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else 'http://127.0.0.1:5010'
    url = base.rstrip('/') + '/diario-oficial/' + designador

    try:
        html = fetch(url)
    except Exception as e:
        print('FALHA ao buscar %s: %s' % (url, e))
        sys.exit(2)

    ok, n = True, 0

    def check(nome, cond, detalhe=''):
        nonlocal ok, n
        n += 1
        marca = 'PASSA' if cond else 'FALHA'
        if not cond:
            ok = False
        linha = '%s  %s' % (marca, nome)
        if detalhe:
            linha += '  (%s)' % detalhe
        print(linha)

    # 1. fontes servidas por @font-face e arquivos presentes
    tem_playfair = 'PlayfairDisplay-Variable.ttf' in html
    tem_garamond = 'EBGaramond.ttf' in html and 'EBGaramond-Italic.ttf' in html
    pf_ok = os.path.isfile(os.path.join(FONTES, 'PlayfairDisplay-Variable.ttf'))
    eg_ok = os.path.isfile(os.path.join(FONTES, 'EBGaramond.ttf'))
    egi_ok = os.path.isfile(os.path.join(FONTES, 'EBGaramond-Italic.ttf'))
    fontes_ok = tem_playfair and tem_garamond and pf_ok and eg_ok and egi_ok
    check('1. fonte carregada (Playfair + EB Garamond locais)',
          fontes_ok,
          'playfair=%s garamond=%s arquivos=%s' % (tem_playfair, tem_garamond, (pf_ok and eg_ok and egi_ok)))

    # 2. brasão sem quadro no topo
    brasao = ('brasao-ato' in html and 'brasao_transparente.png' in html
              and os.path.isfile(os.path.join(STATIC, 'brasao_transparente.png')))
    check('2. brasão presente', brasao)

    # 3. cifra
    cifra = ('cifra' in html and 'cifra_real_transparente.png' in html
             and os.path.isfile(os.path.join(STATIC, 'cifra_real_transparente.png')))
    check('3. cifra presente', cifra)

    # 4. chancela (nome vigente)
    chancela = ('chancela_coroa_martyniano.png' in html
                and os.path.isfile(os.path.join(STATIC, 'chancela_coroa_martyniano.png')))
    check('4. chancela presente (nome vigente)', chancela)

    # 5. comando PROMULGAMOS (não DECRETAMOS nem singular)
    promulga = 'P R O M U L G A M O S' in html
    decretamos = 'D E C R E T A M O S' in html
    promulga_sing = re.search(r'PROMULGA\b(?!MOS)', html) is not None
    check('5. comando PROMULGAMOS', promulga and not decretamos and not promulga_sing,
          'promulgamos=%s decretamos=%s' % (promulga, decretamos))

    # 6. hash preenchido
    m = re.search(r'SHA-256\s*([0-9a-fA-F]{8,})', html)
    hash_ok = m is not None and len(m.group(1)) >= 16
    check('6. hash preenchido', hash_ok,
          'sha=%s' % (m.group(1)[:16] + '…' if m else 'VAZIO'))

    # 7. código de barras Code128 legível (SVG com barras próprias + número)
    tem_svg = 'class="codigo-barras"' in html
    n_barras = len(re.findall(r'<rect[^>]*x=', html))
    tem_numero = bool(re.search(r'codigo-numero[^>]*>\s*AL\d+', html))
    codigo_barras_ok = tem_svg and n_barras >= 20 and tem_numero
    check('7. código de barras legível (SVG Code128 + número)', codigo_barras_ok,
          'barras=%d numero=%s' % (n_barras, tem_numero))

    # 8. bloco de aprovação ausente (sem ata). Só há <div class="aprovacao"> se houver aprovacoes.
    tem_bloco = bool(re.search(r'<(div|table)[^>]+class="[^"]*aprovacao', html))
    check('8. bloco de aprovação ausente (sem ata)', not tem_bloco,
          'bloco=%s' % ('presente' if tem_bloco else 'ausente'))

    # extras (padrão v2.0 seção 10)
    # 9. nome extinto
    residuo = re.findall(r'\bMartina\b', html)
    check('9. resíduo do nome extinto "Martina"', len(residuo) == 0,
          'ocorrências=%d' % len(residuo))

    # 10. travessão longo só em títulos/incisos; sem emoji
    travessoes = re.findall(r'—', html)
    trav_fora_titulo = [t for t in travessoes]  # contagem simples; o corpo usa h2/h3 com travessão
    emoji = re.findall(r'[\U0001F300-\U0001FAFF\U00002600-\U000027BF]', html)
    check('10. sem emoji', len(emoji) == 0, 'emoji=%d' % len(emoji))

    # 11. corpo à esquerda (sem justify no CSS ativo da folha)
    tem_justify = 'text-align:justify' in html
    check('11. corpo alinhado à esquerda (sem justify)', not tem_justify)

    print()
    print('RESULTADO: %s (%d/%d itens passam)' % ('CONFORME' if ok else 'COM FALHA', sum([
        fontes_ok, brasao, cifra, chancela, (promulga and not decretamos and not promulga_sing),
        hash_ok, codigo_barras_ok, (not tem_bloco), (len(residuo) == 0), (len(emoji) == 0),
        (not tem_justify)]), 11))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    main()
