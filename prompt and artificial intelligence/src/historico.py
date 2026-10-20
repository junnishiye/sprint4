"""Reprocessa somente resultados REALMENTE preservados nas saidas da Sprint 03.
Nao executa LLM, nem calcula as 5 metricas novas sem as respostas integrais.
"""
import csv
from collections import defaultdict
from pathlib import Path
from .metricas import salvar_csv

ROOT=Path(__file__).resolve().parents[1]


def gerar_tabelas_historicas():
    with (ROOT/'data/historico_sprint03_extraido.csv').open(newline='',encoding='utf-8-sig') as f:
        dados=list(csv.DictReader(f))
    por_versao=defaultdict(list)
    por_caso=defaultdict(dict)
    for r in dados:
        v=r['versao']; por_versao[v].append(r)
        por_caso[r['id']][v] = float(r['nota_final'])
    resumo=[]
    for v,rr in sorted(por_versao.items()):
        n=len(rr)
        resumo.append({'versao':v,'casos_historicos':n,
                       'nota_media_sprint03':round(sum(float(x['nota_final']) for x in rr)/n,3),
                       'taxa_aprovacao_sprint03':round(sum(x['aprovado']=='True' for x in rr)/n,4),
                       'tokens_medios_sprint03':round(sum(float(x['tokens']) for x in rr)/n,1),
                       'latencia_media_sprint03':round(sum(float(x['latencia_s']) for x in rr)/n,3)})
    comparacao=[]
    for k,notas in sorted(por_caso.items()):
        if len(notas)!=3:raise ValueError(f'Falta comparacao historica em {k}')
        comparacao.append({'id':k,'sprint03_legada':notas['legada'],
                           'sprint03_agente_t02':notas['agente_t02'],'sprint03_agente_t09':notas['agente_t09'],
                           'diferenca_t02_menos_legada':round(notas['agente_t02']-notas['legada'],2),
                           'diferenca_t02_menos_t09':round(notas['agente_t02']-notas['agente_t09'],2)})
    saida=ROOT/'resultados';saida.mkdir(exist_ok=True)
    salvar_csv(saida/'reprocessamento_historico_por_versao.csv',resumo)
    salvar_csv(saida/'reprocessamento_historico_caso_a_caso.csv',comparacao)
    return resumo,comparacao

if __name__=='__main__':
    r,_=gerar_tabelas_historicas()
    for x in r:print(x)
