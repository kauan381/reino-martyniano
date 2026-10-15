#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publica um ato no portal do Reino: marca atos.json como sancionado/publicado.

Uso:  publicar_ato.py <DESIGNADOR>  (ex.: AL.02.2026)

Nao altera o documento em si — apenas transita o registro no atos.json de
"minuta" para "sancionado" e grava a data de publicacao. Idempotente: se ja
estiver publicado, nao mexe.
"""
import datetime
import json
import sys

ATOS = '/home/usuario/Reino/reino-martyniano/data/atos.json'


def publicar(designador, agora=None):
    agora = agora or datetime.datetime.now().isoformat(timespec='seconds')
    atos = json.load(open(ATOS, encoding='utf-8'))
    alvo = None
    for a in atos:
        if a.get('designador') == designador:
            alvo = a
            break
    if alvo is None:
        return None
    if not alvo.get('publicado'):
        alvo['publicado'] = True
        alvo['estado'] = 'sancionado'
        alvo['publicado_em'] = agora
        alvo.pop('aguarda', None)
        json.dump(atos, open(ATOS, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
        return 'publicado'
    return 'ja-publicado'


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('uso: publicar_ato.py <DESIGNADOR>')
        sys.exit(2)
    r = publicar(sys.argv[1])
    if r is None:
        print('NAO ACHOU %s' % sys.argv[1])
        sys.exit(1)
    print('%s -> %s' % (sys.argv[1], r))
