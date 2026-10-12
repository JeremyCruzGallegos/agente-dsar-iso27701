# ai_engine/search_engine.py
import os
import re
import json
import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, 'documentos')
DATA_DIR = os.path.join(BASE_DIR, 'data')
INDEX_PATH = os.path.join(DATA_DIR, 'faiss.index')
META_PATH = os.path.join(DATA_DIR, 'chunks.json')
DIM = 384

_model = None
_index = None
_chunks = []


def _get_model():
    global _model
    if _model is None:
        # Modelo multilingüe (entiende español), corre local
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _model


def _leer_archivo(ruta):
    if ruta.endswith('.pdf'):
        return "\n".join(p.extract_text() or "" for p in PdfReader(ruta).pages)
    with open(ruta, encoding='utf-8') as f:
        return f.read()


def _dividir(texto, tam=500, solape=50):
    trozos = (texto[i:i + tam] for i in range(0, len(texto), tam - solape))
    return [t for t in trozos if t.strip()]


def _texto_para_vector(chunk):
    """Agrega el nombre del documento al texto para que cada trozo 'sepa' de quién es."""
    nombre = chunk['fuente'].replace('_', ' ').replace('.txt', '').replace('.pdf', '')
    return nombre + ': ' + chunk['texto']


def construir_indice():
    """Lee ai_engine/documentos, genera vectores y guarda el índice."""
    global _index, _chunks
    _chunks = []
    for nombre in sorted(os.listdir(DOCS_DIR)):
        if nombre.endswith(('.pdf', '.txt')):
            for c in _dividir(_leer_archivo(os.path.join(DOCS_DIR, nombre))):
                _chunks.append({'texto': c, 'fuente': nombre})
    if not _chunks:
        raise ValueError('No hay documentos .txt/.pdf en ' + DOCS_DIR)

    vectores = _get_model().encode(
        [_texto_para_vector(c) for c in _chunks],
        normalize_embeddings=True)
    _index = faiss.IndexFlatIP(DIM)  # similitud coseno
    _index.add(np.array(vectores, dtype='float32'))

    os.makedirs(DATA_DIR, exist_ok=True)
    faiss.write_index(_index, INDEX_PATH)
    with open(META_PATH, 'w', encoding='utf-8') as f:
        json.dump(_chunks, f, ensure_ascii=False)
    return len(_chunks)


def _asegurar_indice():
    global _index, _chunks
    if _index is None:
        if not os.path.exists(INDEX_PATH):
            construir_indice()
        else:
            _index = faiss.read_index(INDEX_PATH)
            with open(META_PATH, encoding='utf-8') as f:
                _chunks = json.load(f)


def buscar_pii_vectorial(query_text, k=5):
    """Búsqueda por significado. Devuelve lista de {texto, fuente, score}."""
    _asegurar_indice()
    vector = _get_model().encode([query_text], normalize_embeddings=True)
    scores, ids = _index.search(np.array(vector, dtype='float32'),
                                min(k, _index.ntotal))
    return [
        {'texto': _chunks[i]['texto'], 'fuente': _chunks[i]['fuente'],
         'score': float(s)}
        for s, i in zip(scores[0], ids[0]) if i != -1
    ]


def buscar_exacta(termino):
    """Búsqueda literal (DNI, correo, nombre), solo coincidencias completas."""
    _asegurar_indice()
    patron = re.compile(r'(?<!\w)' + re.escape(termino) + r'(?!\w)', re.IGNORECASE)
    return [
        {'texto': c['texto'], 'fuente': c['fuente'], 'score': 1.0}
        for c in _chunks if patron.search(c['texto'])
    ]


def _mostrar(resultados):
    for r in resultados:
        texto = r['texto'].replace('\n', ' ')[:90]
        print(f"  {r['score']:.3f} | {r['fuente']} | {texto}")


if __name__ == '__main__':
    print('Chunks indexados:', construir_indice())

    consultas = [
        'correo electrónico de Juan Pérez',
        'teléfono de María Torres',
        'cuánto tiempo guardan mis datos',
        'problemas con el internet que se corta',
        'cliente que no quiere publicidad',
        'familiares mencionados',
    ]
    for q in consultas:
        print(f"\n[Semántica] {q}")
        _mostrar(buscar_pii_vectorial(q, k=3))

    print('\n[Exacta] 72839102')
    _mostrar(buscar_exacta('72839102'))