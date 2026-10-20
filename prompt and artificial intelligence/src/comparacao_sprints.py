"""Confronto quantitativo auditavel entre juizes AUTOMATICOS das Sprints 03/04.

Nao descreve as notas da Sprint03 como manuais/humanas.
So compara casos da Sprint03 com novas notas quando existe CSV original da execucao.
"""
import csv
from pathlib import Path
from .metricas import salvar_csv


def _ler_csv(caminho):
    if not Path(caminho).exists():
        return []
    with open(caminho, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def _numero(v):
    try:
        if v in (None, '', 'None', 'nan'):
            return None
        return float(str(v).replace(',', '.'))
    except (ValueError, TypeError):
        return None


def comparar_automaticas(root):
    """Retorna (comparacao_por_caso, resumo_por_versao) apenas se houver resultados reais.

    Nao considera amostras transcritas de imagens como CSV integral.
    """
    root = Path(root)
    historico = _ler_csv(root/'data'/'historico_sprint03_extraido.csv')
    novas = _ler_csv(root/'resultados'/'respostas_por_caso.csv')
    if not historico or not novas:
        return [], []
    antes = {(x['versao'], x['id']): x for x in historico}
    linhas = []
    for nova in novas:
        key = (nova.get('versao'), nova.get('id'))
        antiga = antes.get(key)
        if not antiga: continue
        nota_antiga = _numero(antiga.get('nota_final'))
        nota_nova = _numero(nova.get('nota_final')) if nova.get('status') == 'avaliado' else None
        if nota_antiga is None: continue
        linhas.append({
            'versao': key[0], 'id': key[1], 'categoria': nova.get('categoria', ''),
            'nota_automatica_sprint03': nota_antiga,
            'nota_automatica_sprint04': nota_nova,
            'diferenca_s4_menos_s3': round(nota_nova-nota_antiga, 3) if nota_nova is not None else None,
            'mesmo_resultado_aprovacao_7': (nota_nova >= 7) == (nota_antiga >= 7) if nota_nova is not None else None,
            'status_comparacao': 'comparavel' if nota_nova is not None else 'sem_julgamento_s4',
            'metodo_antigo': 'regras + LLM juiz; NAO e avaliacao humana',
            'metodo_novo': 'regras + juiz LLM; NAO e avaliacao humana',
        })
    resumo = []
    for versao in sorted({x['versao'] for x in linhas}):
        dados = [x for x in linhas if x['versao'] == versao]
        pares = [x for x in dados if x['nota_automatica_sprint04'] is not None]
        resumo.append({
            'versao': versao,
            'casos_originais_sprint03': len(dados),
            'pares_comparaveis': len(pares),
            'media_nota_sprint03_pares': round(sum(x['nota_automatica_sprint03'] for x in pares)/len(pares), 3) if pares else None,
            'media_nota_sprint04_pares': round(sum(x['nota_automatica_sprint04'] for x in pares)/len(pares), 3) if pares else None,
            'concordancia_aprovacao_7': round(sum(x['mesmo_resultado_aprovacao_7'] for x in pares)/len(pares), 3) if pares else None,
            'metodos': 'automatico x automatico (nao humano)',
        })
    if linhas:
        salvar_csv(root/'resultados'/'comparacao_automatizada_s3_s4_por_caso.csv', linhas)
        salvar_csv(root/'resultados'/'comparacao_automatizada_s3_s4_resumo.csv', resumo)
    return linhas, resumo
