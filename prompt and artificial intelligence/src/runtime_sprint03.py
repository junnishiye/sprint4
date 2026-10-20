"""Reaproveita as definicoes REAIS do notebook Sprint 03 sem reconstruir o agente.

Somente os blocos de infraestrutura e definicoes sao executados; demonstracoes
interativas, instalacao de pacotes e executores da Sprint 03 sao ignorados.
Este adaptador exige o notebook de referencia entregue dentro deste repositorio.
"""
import json
import os
from pathlib import Path

BLOCOS = {
    4: None,  # imports e configuracao
    6: None,  # base embutida + PDFs locais opcionais
    7: None,  # indexacao/recuperacao
    9: "chatbot_legado = ChatbotLegado()",  # manter apenas classe e fabrica LLM
    11: None, # guardrails
    13: 'print("Tools registradas:"', # tool registry ja foi definido
    15: "agente = construir_agente()",    # manter apenas construtor
    17: '_s = nova_sessao("teste")',       # evitar chamada de demonstracao
}


def carregar_runtime(raiz: Path, diretorio_pdfs: str = "") -> dict:
    raiz = Path(raiz).resolve()
    arquivo = raiz / "referencias" / "sprint03_goodwe_agentes_final.ipynb"
    if not arquivo.is_file():
        raise FileNotFoundError(f"Notebook original da Sprint 03 nao encontrado: {arquivo}")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY ausente. Configure Colab Secrets ou .env antes da avaliacao real.")
    if diretorio_pdfs:
        # A Sprint 03 oferece PASTA_PDFS por configuracao, ajustada antes do bloco 6.
        os.environ["SPRINT04_PDFS"] = str(Path(diretorio_pdfs).resolve())
    try:
        import langchain_core  # noqa: F401
        import langgraph  # noqa: F401
    except ImportError as e:
        raise RuntimeError("Dependencias LangChain/LangGraph nao instaladas. Veja requirements.txt.") from e
    nb = json.loads(arquivo.read_text(encoding="utf-8"))
    escopo = {"__name__": "_sprint03_runtime", "__file__": str(arquivo)}
    for indice, fim in BLOCOS.items():
        fonte = "".join(nb["cells"][indice]["source"])
        if fim:
            if fim not in fonte:
                raise ValueError(f"Marcador esperado ausente na celula {indice}: {fim}")
            fonte = fonte.split(fim, 1)[0]
        if indice == 6 and diretorio_pdfs:
            fonte = fonte.replace('PASTA_PDFS   = "/content/drive/MyDrive/chatbot_docs"',
                                  f'PASTA_PDFS   = {repr(str(Path(diretorio_pdfs).resolve()))}')
        try:
            exec(compile(fonte, f"{arquivo.name}:celula-{indice}", "exec"), escopo)
        except Exception as e:
            raise RuntimeError(f"Falha ao executar a celula original {indice} da Sprint 03: {e}") from e
    for chave in ("construir_agente", "ChatbotLegado", "conversar", "base_vetorial"):
        if chave not in escopo:
            raise RuntimeError(f"Notebook nao expos recurso esperado: {chave}")
    return escopo


def criar_executor(escopo: dict, versao: str):
    """Retorna uma versao efetiva existente na Sprint 03, sem simulacao."""
    if versao == "agente_t02":
        app = escopo["construir_agente"](temperature=0.2, top_p=0.9)
        return ExecutorAgente(escopo, app, versao)
    if versao == "agente_t09":
        app = escopo["construir_agente"](temperature=0.9, top_p=1.0)
        return ExecutorAgente(escopo, app, versao)
    if versao == "legada":
        return ExecutorLegado(escopo, versao)
    raise ValueError(f"Versao nao suportada: {versao}")


class ExecutorAgente:
    def __init__(self, escopo, app, nome):
        self.e, self.app, self.nome = escopo, app, nome

    def responder(self, pergunta, sessao):
        cfg = {"configurable": {"thread_id": sessao}}
        antes = self.app.get_state(cfg)
        n = len(antes.values.get("messages", [])) if antes and antes.values else 0
        resultado = self.e["conversar"](self.app, pergunta, sessao=sessao, modelo="gpt-4o-mini")
        # Contexto que efetivamente passou pela ferramenta, nao fonte reconstruida.
        depois = self.app.get_state(cfg)
        novas = depois.values.get("messages", [])[n:] if depois and depois.values else []
        try:
            from langchain_core.messages import ToolMessage
            contexto = "\n\n".join(
                str(m.content) for m in novas
                if isinstance(m, ToolMessage) and m.name in (
                    "buscar_base_goodwe", "calcular_tempo_recarga",
                    "estimar_custo_recarga", "dimensionar_eletroposto")
            )
        except Exception:
            contexto = ""
        resultado["contexto_consultado"] = contexto[:15000]
        resultado["origem_contexto"] = "tool_messages_do_turno" if contexto else "nenhum"
        return resultado


class ExecutorLegado:
    def __init__(self, escopo, nome):
        self.e, self.nome, self.por_sessao = escopo, nome, {}

    def responder(self, pergunta, sessao):
        if sessao not in self.por_sessao:
            self.por_sessao[sessao] = self.e["ChatbotLegado"](temperature=0.2)
        instancia = self.por_sessao[sessao]
        res = instancia.perguntar(pergunta)
        res["contexto_consultado"] = "\n\n".join(
            d.page_content for d in self.e["base_vetorial"].buscar(pergunta, k=4))[:15000]
        res["origem_contexto"] = "recuperacao_legada"
        return res
