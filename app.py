import os, json, uuid, hashlib, datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, 'data')
os.makedirs(DATA, exist_ok=True)
CIDAD = os.path.join(DATA, 'cidadaos.json')
DOC = os.path.join(DATA, 'documentos.json')
ATOS = os.path.join(DATA, 'atos.json')

app = Flask(__name__)
app.secret_key = 'reino-martyniano-estado-digital'

def ler(arq, default):
    if not os.path.exists(arq):
        return default
    try:
        return json.load(open(arq))
    except Exception:
        return default

def ler_atos():
    """Os atos preparados pelo Oficio de Publicacao, em ordem de designador."""
    return ler(ATOS, [])


def atos_publicados():
    """So o que tem despacho de Sua Majestade.

    Trava do rito (29/09/2026): o Diario Oficial so mostra ato com
    'publicado': true. Minuta que aguarda despacho NAO aparece -- a
    caixa vermelha (audiencia) precede a publicacao. Sem esta trava,
    bastava escrever o ato e ele vazava para o Diario sem sancao.
    """
    return [a for a in ler_atos() if a.get("publicado") is True]

def salvar(arq, dados):
    json.dump(dados, open(arq, 'w'), ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html', est=ler_estado())

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        doc_pessoal = request.form.get('doc', '').strip()
        if not nome or not doc_pessoal:
            flash('Preencha nome e documento pessoal.', 'erro')
        else:
            cidadaos = ler(CIDAD, {})
            # verifica se já existe
            for c in cidadaos.values():
                if c.get('doc') == doc_pessoal:
                    flash('Já existe um cidadão com este documento.', 'erro')
                    break
            else:
                cid = 'RM-' + uuid.uuid4().hex[:8].upper()
                ts = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
                cidadaos[cid] = {'id': cid, 'nome': nome, 'doc': doc_pessoal, 'data': ts}
                salvar(CIDAD, cidadaos)
                session['cid'] = cid
                return redirect(url_for('cidadao', cid=cid))
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cid = request.form.get('id', '').strip().upper()
        cidadaos = ler(CIDAD, {})
        if cid in cidadaos:
            session['cid'] = cid
            return redirect(url_for('cidadao', cid=cid))
        flash('ID de cidadão não encontrado.', 'erro')
    return render_template('login.html')

@app.route('/cidadao/<cid>')
def cidadao(cid):
    cidadaos = ler(CIDAD, {})
    if cid not in cidadaos:
        flash('Cidadão não encontrado.', 'erro')
        return redirect(url_for('index'))
    c = cidadaos[cid]
    docs = [d for d in ler(DOC, {}).values() if d.get('cidad_id') == cid]
    return render_template('cidadao.html', c=c, docs=docs)

@app.route('/cidadao/<cid>/documento', methods=['POST'])
def emitir_documento(cid):
    tipo = request.form.get('tipo', 'Certidão de Cidadania')
    doc_id = 'DOC-' + uuid.uuid4().hex[:10].upper()
    ts = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    docs = ler(DOC, {})
    docs[doc_id] = {'id': doc_id, 'cidad_id': cid, 'tipo': tipo, 'data': ts,
                    'hash': hashlib.sha256(doc_id.encode()).hexdigest()[:16]}
    salvar(DOC, docs)
    return redirect(url_for('cidadao', cid=cid))

@app.route('/validar', methods=['GET', 'POST'])
def validar():
    resultado = None
    if request.method == 'POST':
        doc_id = request.form.get('doc', '').strip().upper()
        docs = ler(DOC, {})
        if doc_id in docs:
            d = docs[doc_id]
            cidadaos = ler(CIDAD, {})
            nome = cidadaos.get(d['cidad_id'], {}).get('nome', 'desconhecido')
            resultado = {'valido': True, 'doc': d, 'nome': nome}
        else:
            resultado = {'valido': False, 'doc': doc_id}
    return render_template('validar.html', resultado=resultado)

def ler_estado():
    return ler(os.path.join(DATA, 'estado.json'), {})

@app.route('/diario-oficial')
def diario():
    return render_template('diario.html', est=ler_estado(), atos=atos_publicados())


@app.route('/diario-oficial/maquete')
def diario_maquete():
    """Maquete da cabeca e do fecho do ato, para julgamento do Rei.
    Nao altera nenhum ato publicado."""
    return render_template('maquete_diario.html')


@app.route('/diario-oficial/maquete-tintas')
def diario_maquete_tintas():
    """As tintas em teste sobre papel marfim. Nao altera ato publicado."""
    return render_template('maquete_tintas.html')


@app.route('/diario-oficial/tintas')
def diario_tintas():
    """Tintas em tamanho de leitura, com o brasao em fundo transparente."""
    return render_template('maquete_tintas2.html')


@app.route('/diario-oficial/<designador>')
def ato_publicado(designador):
    """A pagina do ato publicado, na FORMA DO DIARIO OFICIAL.

    Forma aprovada pelo Rei em 29/09/2026 (skill reino/forma-do-ato-publicado):
    papel marfim, tinta ferro-galica, tamanho de leitura, com cabeca (selo,
    orgao, titulo, epigrafe) e fecho (fe publica + integridade).

    O template do ato traz so o CORPO. Aqui ele e vestido com a folha.
    """
    import re as _re
    atos = atos_publicados()
    ato = next((a for a in atos if a.get("designador") == designador), None)
    if not ato:
        abort(404)
    pagina = ato.get("pagina") or (designador + ".html")
    bruto = render_template('atos/' + pagina, est=ler_estado(), ato=ato)

    # O corpo real vem marcado no template entre <!-- CORPO --> e <!-- /CORPO -->.
    # Nada de regex estrutural sobre a base: recortamos so entre os marcadores.
    m = _re.search(r"<!--\s*CORPO\s*-->(.*?)<!--\s*/CORPO\s*-->", bruto, _re.S)
    if not m:
        abort(500, description="Template do ato sem os marcadores <!-- CORPO --> / <!-- /CORPO -->.")
    corpo = m.group(1).strip()

    return render_template(
        '_folha_ato.html',
        TITULO=ato.get("titulo") or designador,
        EMENTA=ato.get("ementa") or "",
        DESIGNADOR=designador,
        HASH=(ato.get("sha256") or "")[:32],
        CORPO=corpo,
    )

@app.route('/leis')
def leis():
    return render_template('leis.html', est=ler_estado())

@app.route('/ministerios')
def ministerios():
    return render_template('ministerios.html', est=ler_estado())

@app.route('/noticias')
def noticias():
    return render_template('noticias.html', est=ler_estado())

@app.route('/busca')
def busca():
    q = request.args.get('q', '').lower().strip()
    mapa = {
        'diario': '/diario-oficial', 'oficial': '/diario-oficial',
        'lei': '/leis', 'ato': '/leis', 'decreto': '/leis', 'constitui': '/leis', 'norma': '/leis', 'estatuto': '/leis',
        'ministerio': '/ministerios', 'ministro': '/ministerios',
        'noticia': '/noticias', 'comunica': '/noticias', 'pronuncia': '/noticias',
        'institui': '/instituicoes', 'poder': '/instituicoes', 'conselho': '/instituicoes',
        'quem somos': '/quem-somos', 'quem': '/quem-somos', 'somos': '/quem-somos',
        'historia': '/nossa-historia', 'história': '/nossa-historia', 'passado': '/nossa-historia', 'fundacao': '/nossa-historia', 'fundação': '/nossa-historia',
        'monarquia': '/a-monarquia', 'rei': '/a-monarquia', 'coroa': '/a-monarquia', 'casa real': '/a-monarquia', 'dinastia': '/a-monarquia',
        'microestado': '/o-microestado', 'paraestatal': '/o-microestado',
        'faq': '/perguntas-frequentes', 'pergunta': '/perguntas-frequentes',
        'duvida': '/perguntas-frequentes', 'serio': '/perguntas-frequentes',
        'rpg': '/perguntas-frequentes', 'jogo': '/perguntas-frequentes',
        'seita': '/perguntas-frequentes', 'golpe': '/perguntas-frequentes', 'soberania': '/o-microestado', 'territorio': '/o-microestado', 'território': '/o-microestado',
        'cidadao': '/registro', 'cidadania': '/registro', 'documento': '/registro', 'identidade': '/registro', 'passaporte': '/registro',
    }
    for k, destino in mapa.items():
        if k in q:
            return redirect(destino)
    flash('Não encontrei uma seção exata — veja os destaques abaixo.', 'erro')
    return redirect(url_for('index'))

@app.route('/instituicoes')
def instituicoes():
    return render_template('instituicoes.html', est=ler_estado())


# ============================================================
# PAGINAS INSTITUCIONAIS — Conheca o Reino
# Acrescentadas em setembro de 2026, na fusao do portal
# institucional novo com este Estado Digital. Nao substituem
# nenhuma funcao: cidadania, documentos e validacao seguem
# intactos. Apenas dao casa aos textos institucionais.
# ============================================================

@app.route('/quem-somos')
def quem_somos():
    return render_template('quem-somos.html', est=ler_estado())


@app.route('/nossa-historia')
def nossa_historia():
    return render_template('nossa-historia.html', est=ler_estado())


@app.route('/a-monarquia')
def a_monarquia():
    return render_template('a-monarquia.html', est=ler_estado())


@app.route('/o-microestado')
def o_microestado():
    return render_template('o-microestado.html', est=ler_estado())


@app.route('/a-espiritualidade')
def a_espiritualidade():
    return render_template('a-espiritualidade.html', est=ler_estado())


@app.route('/as-guerras-patrioticas')
def as_guerras_patrioticas():
    return render_template('as-guerras-patrioticas.html', est=ler_estado())


@app.route('/simbolos-nacionais')
def simbolos_nacionais():
    return render_template('simbolos-nacionais.html', est=ler_estado())


@app.route('/ciencia-javenista')
def ciencia_javenista():
    return render_template('ciencia-javenista.html', est=ler_estado())


@app.route('/perguntas-frequentes')
def perguntas_frequentes():
    return render_template('perguntas-frequentes.html')


@app.route('/logout')
def logout():
    session.pop('cid', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5010, debug=False)
