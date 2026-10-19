#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o site estático (docs/) do portal do Reino para o GitHub Pages."""
import os, re, json, shutil, sys

BASE = '/home/usuario/Reino/reino-martyniano'
DOCS = os.path.join(BASE, 'docs')
sys.path.insert(0, BASE)
os.chdir(BASE)

from app import app  # noqa: E402

rotas = [
    ('/', 'index.html'),
    ('/diario-oficial', 'diario-oficial/index.html'),
    ('/leis', 'leis/index.html'),
    ('/ministerios', 'ministerios/index.html'),
    ('/instituicoes', 'instituicoes/index.html'),
    ('/noticias', 'noticias/index.html'),
    ('/quem-somos', 'quem-somos/index.html'),
    ('/nossa-historia', 'nossa-historia/index.html'),
    ('/a-monarquia', 'a-monarquia/index.html'),
    ('/o-microestado', 'o-microestado/index.html'),
    ('/a-espiritualidade', 'a-espiritualidade/index.html'),
    ('/as-guerras-patrioticas', 'as-guerras-patrioticas/index.html'),
    ('/simbolos-nacionais', 'simbolos-nacionais/index.html'),
    ('/ciencia-javenista', 'ciencia-javenista/index.html'),
    ('/perguntas-frequentes', 'perguntas-frequentes/index.html'),
]

atos = [a['designador'] for a in json.load(open(os.path.join(BASE, 'data', 'atos.json')))
        if a.get('publicado')]
for d in atos:
    rotas.append(('/diario-oficial/' + d, 'diario-oficial/' + d + '/index.html'))


def ajustar(html, prefix):
    def repl(m):
        attr, path = m.group(1), m.group(2)
        if path == '':
            novo = prefix if prefix else 'index.html'
        else:
            novo = prefix + path
        return '%s="%s"' % (attr, novo)
    return re.sub(r'(href|src)="/([^"]*)"', repl, html)


client = app.test_client()
erros = 0
for url, dest in rotas:
    resp = client.get(url)
    if resp.status_code != 200:
        print('ERRO %s -> %s' % (url, resp.status_code))
        erros += 1
        continue
    html = resp.get_data(as_text=True)
    depth = dest.count('/')
    prefix = '../' * depth if depth > 0 else ''
    html = ajustar(html, prefix)
    path = os.path.join(DOCS, dest)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('OK  %s' % dest)

# copia static
src_static = os.path.join(BASE, 'static')
dst_static = os.path.join(DOCS, 'static')
if os.path.isdir(src_static):
    shutil.copytree(src_static, dst_static, dirs_exist_ok=True)
    print('OK  static/ copiado')

open(os.path.join(DOCS, '.nojekyll'), 'w').close()
print('OK  .nojekyll')
print('erros:', erros)
