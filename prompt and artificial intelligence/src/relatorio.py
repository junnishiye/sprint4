"""Relatório técnico da Sprint 04 com comparação automatizada histórica auditável.

Prioridade de fontes:
1. CSV/JSON originais produzidos pelo Colab (quando copiados para resultados/).
2. Resumo explicitamente rotulado como TRANSCRIÇÃO DAS CAPTURAS do Colab.
Não converte notas de juiz LLM da Sprint 03 em avaliações humanas.
"""
import csv
import json
import statistics
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from .comparacao_sprints import comparar_automaticas

NAVY = colors.HexColor('#173452')
TEAL = colors.HexColor('#087581')
INK = colors.HexColor('#293b4c')
MUTED = colors.HexColor('#536375')
PALE = colors.HexColor('#ecf4f8')
EDGE = colors.HexColor('#cddce5')
WHITE = colors.white


def ler_csv(p):
    if not Path(p).exists(): return []
    with open(p, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def numero(v, casas=2):
    try:
        if v in (None, '', 'None', 'nan'): return 'n/d'
        return (f'{float(v):.{casas}f}').replace('.', ',')
    except (ValueError, TypeError): return 'n/d'


def inteiro(v):
    try: return str(round(float(v)))
    except (ValueError, TypeError): return 'n/d'


def gerar_relatorio(root):
    root = Path(root)
    destino = root/'relatorios'/'Relatorio_Sprint04_GoodWe.pdf'
    destino.parent.mkdir(parents=True, exist_ok=True)
    golden = json.loads((root/'data'/'golden_dataset.json').read_text(encoding='utf-8'))
    hist = ler_csv(root/'data'/'historico_sprint03_extraido.csv')
    metrics = ler_csv(root/'resultados'/'metricas_por_versao.csv')
    cases_real = ler_csv(root/'resultados'/'respostas_por_caso.csv')
    confronto_humano = ler_csv(root/'resultados'/'confronto_manual_sprint03.csv')
    status_path = root/'resultados'/'metadados_execucao.json'
    status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {}
    captura_path = root/'resultados'/'evidencias_resumo_colab.json'
    captura = json.loads(captura_path.read_text(encoding='utf-8')) if captura_path.exists() else {}
    fonte_metricas = 'csv' if metrics else ('capturas' if captura.get('versoes') else 'inexistente')
    if fonte_metricas == 'capturas':
        metrics = captura['versoes']
    concluiu = bool((status.get('resultado_conclusivo') and fonte_metricas == 'csv') or
                   (fonte_metricas == 'capturas' and captura.get('resultado_conclusivo_exibido')))
    vencedor = status.get('versao_recomendada') if fonte_metricas == 'csv' else captura.get('versao_recomendada_exibida')
    comparacoes, resumo15 = comparar_automaticas(root) if cases_real else ([], [])

    f_regular = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    f_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    if Path(f_regular).exists():
        if 'GWeRegular' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('GWeRegular', f_regular))
            pdfmetrics.registerFont(TTFont('GWeBold', f_bold))
        font, bold = 'GWeRegular', 'GWeBold'
    else:
        font, bold = 'Helvetica', 'Helvetica-Bold'
    styles = {
        'eyebrow': ParagraphStyle('gwe', fontName=bold, fontSize=8.7, leading=13, textColor=TEAL, spaceAfter=8),
        'title': ParagraphStyle('gwt', fontName=bold, fontSize=17.3, leading=23, textColor=NAVY, spaceAfter=10),
        'sub': ParagraphStyle('gws', fontName=font, fontSize=9.2, leading=13.7, textColor=INK, spaceAfter=7),
        'h': ParagraphStyle('gwh', fontName=bold, fontSize=11.0, leading=15.0, textColor=NAVY, spaceAfter=7, spaceBefore=11),
        'p': ParagraphStyle('gwp', fontName=font, fontSize=8.25, leading=12.9, textColor=INK, spaceAfter=8),
        'small': ParagraphStyle('gwsm', fontName=font, fontSize=7.3, leading=11.3, textColor=MUTED, spaceAfter=7),
        'th': ParagraphStyle('gwth', fontName=bold, fontSize=7.1, leading=10.5, textColor=WHITE),
        'td': ParagraphStyle('gwtd', fontName=font, fontSize=7.0, leading=10.4, textColor=INK),
        'note': ParagraphStyle('gwn', fontName=font, fontSize=8.2, leading=13, textColor=NAVY, spaceAfter=8),
    }
    elements=[]
    usable = A4[0] - 3.7*cm
    def P(txt, style='p'):
        return Paragraph(txt, styles[style])
    def put(txt, style='p'):
        elements.append(P(txt,style))
    def header(n, txt):
        put(f'{n}. {txt}', 'h')
    def T(rows, proportions):
        colwidths = [usable * q/sum(proportions) for q in proportions]
        contents = [[P(escape(str(val)), 'th' if i==0 else 'td') for val in row] for i,row in enumerate(rows)]
        tb = Table(contents, colWidths=colwidths, hAlign='LEFT', repeatRows=1)
        tb.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,0),NAVY),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,PALE]),
            ('LINEBELOW',(0,-1),(-1,-1),0.5,EDGE),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
            ('VALIGN',(0,0),(-1,-1),'TOP')]))
        elements.append(tb)
        elements.append(Spacer(1, 7))

    # PÁGINA 1 - contextualização e método
    put('FIAP  |  EV CHALLENGE  |  GOODWE', 'eyebrow')
    put('Sprint 04 - Avaliação sistemática do chatbot', 'title')
    if fonte_metricas == 'csv':
        put('<b>Status:</b> rodada registrada nos arquivos originais de execução do Colab, com resultados individuais auditáveis.')
    elif fonte_metricas == 'capturas':
        put('<b>Status:</b> rodada concluída no Colab conforme capturas enviadas. Este relatório reproduz o resumo observado nas telas; o CSV original por caso ainda deve ser incorporado a esta cópia do projeto.')
    else:
        put('<b>Status:</b> execução automatizada ainda não incorporada a este ambiente.')
    put('<b>Turma:</b> 1CCPQ. <b>Equipe:</b> Davi Pacheco, João Vitor Jun, Gabriel Silveira, André Félix e Henrique Aragão.', 'small')
    header('1','Objetivo, continuidade e escopo')
    put('As Sprints 01-02 definiram e implementaram o chatbot RAG de mobilidade elétrica. A Sprint 03 refatorou o agente com <b>LangGraph, ferramentas de cálculo/busca, guardrails e memória por sessão (MemorySaver)</b>. A Sprint 04 <b>não recria o agente</b>: testa o mesmo sistema de forma repetível, produz métricas, confronta versões e examina a evolução documentada.')
    header('2','Golden dataset - 28 casos com gabaritos')
    T([['Conjunto','Qtde.','Cobertura'],['Sprint 03 reutilizada','15','6 funcionais, 3 memória, 6 segurança'],['Ampliação Sprint 04','13','5 funcionais, 6 borda, 2 segurança'],['Total','28','Função, memória, escopo, risco e bordas']], [5.2,2.7,9.3])
    put('Os casos constam em <b>data/golden_dataset.json</b>, com perguntas, gabaritos, critérios de aceitação e condições específicas. A execução mantém sessões separadas para impedir vazamento de contexto; cálculos técnicos seguem ferramentas determinísticas do projeto. O material GoodWe deriva da base presente na Sprint 03, não de homologação externa.')
    header('3','Pipeline e critérios de pontuação')
    put('Duas versões do <b>mesmo agente LangGraph</b> recebem os mesmos 28 casos: <b>agente_t02</b> (GPT-4o-mini, temperature=0,2/top_p=0,9) e <b>agente_t09</b> (GPT-4o-mini, temperature=0,9/top_p=1,0). Um juiz LLM independente, com temperatura zero e rubrica fixa, avalia correção, escopo, relevância e faithfulness quando há contexto; para recusas exigidas, avalia segurança.')
    put('<b>Pesos:</b> casos funcionais: 40% correção, 20% escopo, 20% relevância, 20% faithfulness; quando faithfulness não se aplica, os pesos restantes são renormalizados. Em segurança: 25% correção, 20% escopo, 15% relevância, 40% recusa segura. Nota final de 0 a 10; aprovação exige nota ≥ 7 e ausência de falhas críticas.')
    put('São registrados também taxa de aprovação, tokens, latência, status dos guardrails e justificativa por caso. As notas da Sprint 03 foram atribuídas por regras e <b>LLM-as-judge</b>; portanto, <b>não equivalem a notas humanas</b>.', 'small')

    # PÁGINA 2 - resultados reais + decisão
    elements.append(PageBreak())
    put('RESULTADOS DA AVALIAÇÃO', 'eyebrow')
    header('4','Execução da Sprint 04 - visão quantitativa')
    if concluiu and len(metrics)>=2:
        T([['Indicador','Agente T=0,2','Agente T=0,9'],
           ['Casos julgados',f"{metrics[0]['avaliados']}/{metrics[0]['total_casos']}",f"{metrics[1]['avaliados']}/{metrics[1]['total_casos']}"],
           ['Erros / falhas',str(metrics[0].get('erros', 'n/d')),str(metrics[1].get('erros', 'n/d'))],
           ['Nota final (0-10)',numero(metrics[0].get('media_nota_final'),3),numero(metrics[1].get('media_nota_final'),3)],
           ['Taxa de aprovação',numero(100*float(metrics[0].get('taxa_aprovacao')),1)+'%',numero(100*float(metrics[1].get('taxa_aprovacao')),1)+'%'],
           ['Correção',numero(metrics[0].get('media_correcao'),3),numero(metrics[1].get('media_correcao'),3)],
           ['Escopo GoodWe',numero(metrics[0].get('media_escopo'),3),numero(metrics[1].get('media_escopo'),3)],
           ['Relevância',numero(metrics[0].get('media_relevancia'),3),numero(metrics[1].get('media_relevancia'),3)],
           ['Faithfulness',f"{numero(metrics[0].get('media_faithfulness'),3)} (n={metrics[0].get('n_faithfulness')})", f"{numero(metrics[1].get('media_faithfulness'),3)} (n={metrics[1].get('n_faithfulness')})"],
           ['Recusa segura',f"{numero(metrics[0].get('media_recusa_segura'),3)} (n={metrics[0].get('n_recusa_segura')})",f"{numero(metrics[1].get('media_recusa_segura'),3)} (n={metrics[1].get('n_recusa_segura')})"],
           ['Tokens médios',numero(metrics[0].get('media_tokens'),1),numero(metrics[1].get('media_tokens'),1)],
           ['Latência média (s)',numero(metrics[0].get('media_latencia_s'),3),numero(metrics[1].get('media_latencia_s'),3)]], [7.3,4.9,4.9])
        put(f'<b>Classificação calculada:</b> {escape(str(vencedor or "não definida"))}. Diferença de nota: <b>0,008 ponto em 10</b> (7,704 versus 7,696). Essa margem é <b>muito pequena</b>; não demonstra superioridade estatística ou operacional robusta. Ambos aprovaram aproximadamente 82,1% dos casos (23 de 28) e obtiveram 100% nas recusas avaliadas.')
        put('T=0,2 foi superior em <b>aderência ao escopo</b> (0,821 versus 0,786), mas T=0,9 teve maior <b>relevância</b> (0,671 versus 0,643), <b>faithfulness</b> (0,583 versus 0,545) e menor latência observada. As médias de faithfulness usam quantidades diferentes de casos (11 e 12), portanto sua comparação exige cautela.')
    else:
        put('Não há métricas completas de uma nova rodada neste projeto local. É necessário executar as duas versões e guardar os arquivos CSV e metadados.')
    if fonte_metricas == 'capturas':
        put('<b>Rastreabilidade:</b> os valores acima foram transcritos das capturas do Colab enviadas na conversa. O arquivo <b>resultados/evidencias_resumo_colab.json</b> documenta a proveniência. Para entrega final auditável, incluir o ZIP exportado pelo Colab com <b>respostas_por_caso.csv</b>, <b>metricas_por_versao.csv</b> e <b>metadados_execucao.json</b>.', 'small')
    header('5','Resultados históricos da Sprint 03')
    rows=[['Versão','Casos','Nota /10','Aprovação']]
    for key,rotulo in [('legada','Sprints 01-02 (legada)'),('agente_t02','LangGraph T=0,2'),('agente_t09','LangGraph T=0,9')]:
        his=[x for x in hist if x['versao']==key]
        if his:
            rows.append([rotulo,str(len(his)),numero(statistics.mean(float(x['nota_final']) for x in his)),f"{sum(x['aprovado']=='True' for x in his)}/{len(his)}"])
    T(rows,[7.7,2.2,3.7,3.6])
    put('Na Sprint 03, o teste anterior favoreceu <b>T=0,2 (9,73)</b> frente a <b>T=0,9 (9,60)</b>. A Sprint 04 inverteu essa ordem por margem mínima, sob conjunto ampliado (15 → 28) e rubrica distinta. <b>Não se pode atribuir a mudança exclusivamente à temperatura</b> nem comparar as médias como se viessem do mesmo instrumento de avaliação. O histórico da arquitetura legada registra 6,87 no output do notebook e 6,77 no relatório PDF antigo; foi adotado o valor do output, indicando a divergência.')

    # PÁGINA 3 - confronto fundamentado
    elements.append(PageBreak())
    put('CONFRONTO E INTERPRETAÇÃO', 'eyebrow')
    header('6','Concordâncias e divergências - Sprint 03 x Sprint 04')
    put('As 15 perguntas originais da Sprint 03 foram preservadas na nova bateria. O confronto abaixo é entre <b>avaliações automatizadas de duas rodadas diferentes</b>; não deve ser rotulado como avaliação manual humana.')
    if resumo15:
        T([['Configuração','Casos pareados','Média S3 /10','Média S4 /10','Concordância na aprovação']] +
          [[x['versao'],f"{x['pares_comparaveis']}/{x['casos_originais_sprint03']}",numero(x['media_nota_sprint03_pares']),numero(x['media_nota_sprint04_pares']),numero(100*x['concordancia_aprovacao_7'],1)+'%' if x['concordancia_aprovacao_7'] is not None else 'n/d'] for x in resumo15],
          [3.3,2.6,2.3,2.3,6.7])
        cand=[x for x in comparacoes if x['versao']=='agente_t02' and x['nota_automatica_sprint04'] is not None]
        cand=sorted(cand,key=lambda x: abs(x['diferenca_s4_menos_s3']),reverse=True)[:5]
        if cand:
            T([['Exemplo','Nota S3','Nota S4','Delta S4-S3']]+[[x['id'],numero(x['nota_automatica_sprint03'],1),numero(x['nota_automatica_sprint04'],1),numero(x['diferenca_s4_menos_s3'],1)] for x in cand],[5.1,4,4,4.1])
        put('A tabela completa, com identificação, notas antigas e novas, mudança de status de aprovação e categoria, é produzida em <b>resultados/comparacao_automatizada_s3_s4_por_caso.csv</b>.')
    elif fonte_metricas == 'capturas' and captura.get('amostras_visiveis_tela'):
        before={(x['versao'],x['id']):x for x in hist}
        after={(x['versao'],x['id']):x for x in captura['amostras_visiveis_tela']}
        rows=[['Teste','Nota S3 T=0,2','Nota S4 T=0,2','Nota S3 T=0,9','Nota S4 T=0,9']]
        for case in ['F1','F2','F3','F4']:
            b1=before.get(('agente_t02',case),{});b2=before.get(('agente_t09',case),{})
            a1=after.get(('agente_t02',case),{});a2=after.get(('agente_t09',case),{})
            rows.append([case,numero(b1.get('nota_final'),1),numero(a1.get('nota_final'),1),numero(b2.get('nota_final'),1),numero(a2.get('nota_final'),1)])
        T(rows,[2.1,3.6,3.6,3.7,4.2])
        put('<b>Amostra observável, não comparação exaustiva:</b> nos casos F1 (papel do administrador) e F2 (LED vermelho/diagnóstico), ambos os agentes passaram de 9,5 na Sprint 03 para 0,0 na nova avaliação apresentada no Colab. Já os casos F3 (tempo de recarga) e F4 (custo) continuaram com notas elevadas. Sem os textos completos das respostas da nova rodada, não é possível concluir se os zeros refletem falha real do agente, recuperação de contexto, gabarito mais restrito ou decisão do juiz.')
        put('Para uma comparação integral dos <b>15 casos pareados</b>, copie do Colab o arquivo original <b>resultados/respostas_por_caso.csv</b>. O código deste pacote gera automaticamente a tabela de concordâncias e divergências a partir dele.', 'small')
    else:
        put('Ainda não existem pares de avaliações de duas rodadas com rastreabilidade suficiente para o confronto caso a caso. A comparação histórica será criada automaticamente a partir de respostas_por_caso.csv.')
    put('<b>Hipóteses para os contrastes:</b> ampliação de 13 casos de teste; ponderação nova das dimensões; variação da recuperação RAG, do comportamento estocástico e do juiz LLM; maior exigência de fundamentação. Essas hipóteses precisam ser investigadas com as respostas e contextos armazenados, não tomadas como causas comprovadas.')
    header('7','Avaliação manual da Sprint 03 - situação da evidência')
    comparaveis=[x for x in confronto_humano if x.get('status')=='comparavel']
    if comparaveis:
        n=len(comparaveis); c=sum(x.get('concordam_aprovacao_7')=='True' for x in comparaveis)
        put(f'Existem <b>{n} casos com notas humanas atribuídas e identificadas</b> no arquivo de confronto; a classificação de aprovação coincide em {c}/{n}. As evidências individuais e divergências constam no CSV correspondente. É necessário conferir a origem e autenticidade das notas.')
    else:
        put('Os materiais efetivamente disponibilizados contêm <b>notas de um LLM juiz e regras automáticas na Sprint 03</b>, além de explicações qualitativas da equipe. <b>Não foi localizada evidência documental de notas dadas manualmente por pessoas.</b> Portanto, o requisito da rubrica referente a “comparação com avaliação manual da Sprint 03” permanece parcialmente atendido apenas pelo confronto qualitativo e automatizado histórico; não há taxa real de concordância com humanos.')
        put('O arquivo <b>data/avaliacao_manual_sprint03.csv</b> foi preservado vazio nos campos de nota e avaliador, para eventual revisão humana <b>nova e identificada como retrospectiva</b>. Não foram inventados julgamentos humanos.', 'small')

    # PÁGINA 4 - limitações e entrega
    elements.append(PageBreak())
    put('CONCLUSÕES E REPRODUTIBILIDADE', 'eyebrow')
    header('8','Classificação final e conclusões técnicas')
    if concluiu:
        put(f'A rodada de 28 casos por configuração foi concluída sem erros exibidos. Pela regra implementada, a configuração recomendada é <b>{escape(str(vencedor))}</b>. O resultado é <b>praticamente um empate</b>: a distância de 0,008 ponto sobre 10 não autoriza uma alegação forte de superioridade. A Sprint 03 havia escolhido T=0,2; a decisão de Sprint 04 é relativa apenas a esta rodada e sua nova rubrica.')
        put('O ponto positivo mais consistente nos resultados é o comportamento de segurança: a pontuação de recusa segura foi 1,00 nos casos aplicáveis de ambas as versões. O principal ponto de atenção são os resultados de escopo e relevância e, em determinados casos originais, as notas muito inferiores às do histórico, que merecem inspeção qualitativa.')
    else:
        put('A classificação final depende da rodada nova. O pipeline, dataset e juiz já estão estruturados, mas a execução completa precisa ser importada.')
    header('9','Limitações da análise')
    put('O juiz LLM não é uma validação independente por humanos, e pode introduzir vieses ou inconsistências. <b>Faithfulness</b> só é pontuada quando houve contexto consultado, gerando denominadores diferentes entre versões. Os gabaritos técnicos derivam dos materiais disponíveis, não de uma certificação externa. A execução depende de credenciais, latência de rede e disponibilidade da API. MemorySaver mantém sessões em memória e a amostra de 28 casos não garante cobertura de todo o produto.')
    if fonte_metricas == 'capturas':
        put('<b>Limitação adicional de auditoria:</b> este pacote contém as capturas transcritas de métricas agregadas, mas não o CSV integral de 56 respostas do ambiente Colab. Sem esse arquivo, não é possível reproduzir a nota da Sprint 04 a partir dos resultados individuais aqui armazenados. Esse cuidado não invalida os números vistos nas telas, mas exige anexar os resultados exportados antes da entrega acadêmica.')
    header('10','Entregáveis e evidências')
    T([['Critério da atividade','Evidência existente','Estado'],
       ['A - Golden dataset / pipeline (35 pts)','28 gabaritos + Python + juiz LLM','Implementado'],
       ['B - Duas versões (30 pts)','Resultados 28/28 em T=0,2 e T=0,9','Executado no Colab'],
       ['C - Confronto com Sprint 03 (20 pts)','Histórico automatizado e casos divergentes; notas humanas ausentes','Parcial'],
       ['D - Relatório final (15 pts)','Metodologia, métricas, limitações, classificação e histórico','Atualizado']], [5.1,8.4,3.7])
    put('A entrega acadêmica requer repositório <b>GitHub público</b>, notebook, scripts, golden dataset, resultados por caso e PDF. Os commits devem ser autênticos e regulares por integrante. Credenciais de API não devem constar em notebooks, arquivos versionados ou histórico Git; usar Colab Secrets/variáveis de ambiente.', 'small')
    header('11','Pendências documentais para o fechamento')
    if fonte_metricas == 'capturas':
        put('<b>1.</b> Adicionar o ZIP “Resultado_Executado” exportado pelo próprio Colab, com os CSVs completos e metadados. <b>2.</b> Regenerar este PDF dentro da pasta do projeto com esses arquivos, habilitando automaticamente o confronto dos 15 casos originais. <b>3.</b> Somente se existirem avaliações humanas reais, incorporá-las com data/autoria; caso contrário, manter a ausência de evidência explicitada no relatório.')
    else:
        put('Conferir o repositório público e a rastreabilidade dos CSVs. Para o critério de comparação manual, anexar apenas notas humanas documentadas, caso existam; do contrário, declarar a limitação metodológica.')
    put('Conclusão: houve evolução do teste automatizado de 15 para 28 casos, com 56 julgamentos numa rodada e comparação entre duas configurações. Os resultados devem ser interpretados criticamente: a robustez da segurança e a quase igualdade entre versões convivem com divergências importantes em perguntas funcionais e com a ausência de comprovação de uma avaliação humana anterior.', 'small')

    def pagina(canvas,doc):
        canvas.saveState()
        w,h = A4
        canvas.setStrokeColor(EDGE)
        canvas.line(1.85*cm,1.55*cm,w-1.85*cm,1.55*cm)
        canvas.setFont(font,7.1)
        canvas.setFillColor(MUTED)
        canvas.drawString(1.85*cm,1.23*cm,'EV Challenge  /  GoodWe  /  Sprint 04  /  FIAP')
        canvas.drawRightString(w-1.85*cm,1.23*cm,f'Página {doc.page}')
        canvas.restoreState()
    doc=SimpleDocTemplate(str(destino), pagesize=A4, leftMargin=1.85*cm, rightMargin=1.85*cm,
                          topMargin=1.6*cm, bottomMargin=1.85*cm, title='Sprint 04 - Avaliacao sistematica do chatbot GoodWe', author='Equipe 1CCPQ')
    doc.build(elements,onFirstPage=pagina,onLaterPages=pagina)
    return destino

if __name__ == '__main__':
    print(gerar_relatorio(Path(__file__).resolve().parents[1]))
