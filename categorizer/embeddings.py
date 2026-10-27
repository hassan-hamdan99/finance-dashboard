"""
Módulo de categorização por embeddings (Sentence Transformers).
Usado como fallback quando keywords não casam.
Modelo: all-MiniLM-L6-v2 (~90MB, roda em CPU, ~10ms/query)
"""
import numpy as np
import os

_model = None
_cat_embeddings = None
_cat_names = None

CONFIDENCE_THRESHOLD = 0.28

# Descrições semânticas alinhadas com as categorias da planilha
CATEGORY_DESCRIPTIONS = {
    "Mercado": (
        "grocery supermarket market fruit vegetable butcher bakery "
        "supermercado mercado hortifruti padaria acougue feira atacadao "
        "angeloni bistek giassi natural da terra sacolao quitanda"
    ),
    "Sair/Comer fora": (
        "restaurant bar eating out delivery food meal lunch dinner "
        "ifood rappi uber eats pizzaria hamburger sushi cafe cerveja "
        "churrascaria sorveteria acai izakaya boteco lanchonete"
    ),
    "Transporte": (
        "gas station fuel gasoline parking toll uber taxi ride transportation "
        "bus metro posto combustivel gasolina pedagio estacionamento onibus "
        "auto repair car vehicle uber 99"
    ),
    "Moradia": (
        "rent apartment condominium electricity water energy power utility bill "
        "internet gas home housing light IPTU celesc copel enel cpfl "
        "prefeitura saneamento faxina diarista phone mobile celular vivo claro tim"
    ),
    "Pets": (
        "pet cat veterinary petshop pet food petlove petz cobasi animal "
        "veterinario racao gato cat litter vacina felino feline kitten"
    ),
    "Assinaturas": (
        "subscription plan monthly recurring digital service "
        "netflix spotify disney hbo youtube premium apple google icloud "
        "steam playstation xbox github chatgpt dropbox streaming gaming"
    ),
    "Saúde": (
        "health pharmacy hospital clinic doctor dentist lab exam medical healthcare "
        "clinica farmacia drogaria consulta fisioterapia psicologia nutricionista "
        "drogasil droga raia preco popular medicine"
    ),
    "Educação": (
        "education school university course book study tuition college learning "
        "udemy coursera academy training library bookstore livraria carreira"
    ),
    "Faturas": (
        "credit card bill payment invoice fatura cartao pagamento de fatura "
        "banco ibi pjbank hipercard losango cetelem midway realize "
        "bradescard luizacred aymore portoseg dmcard card bill statement"
    ),
    "Salário": (
        "salary wage payroll income monthly payment remuneracao folha "
        "pagamento salario holerite adiantamento decimo terceiro ferias"
    ),
    "Lazer": (
        "entertainment movie cinema theater show concert travel hotel trip "
        "leisure fun recreation party bar nightclub beer cerveja balada "
        "viagem passagem aeroporto parque museu game futebol"
    ),
    "Investimentos": (
        "investment savings deposit fund application RDB CDB treasury bond "
        "yield portfolio aplicacao resgate rendimento poupanca tesouro "
        "dividendo lucro corretora broker"
    ),
    "Outros": (
        "shopping clothes shoes store purchase online electronics fashion "
        "magazine magalu americanas shopee mercado livre amazon "
        "insurance lawyer accounting donation present gift "
        "roupas acessorios casamento presentes doacoes cuidados pessoais"
    ),
}


def _load_model():
    """Carrega modelo sob demanda (lazy loading)."""
    global _model, _cat_embeddings, _cat_names

    if _model is not None:
        return

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    from sentence_transformers import SentenceTransformer

    _model = SentenceTransformer("all-MiniLM-L6-v2")
    _cat_names = list(CATEGORY_DESCRIPTIONS.keys())
    _cat_embeddings = _model.encode(
        list(CATEGORY_DESCRIPTIONS.values()),
        normalize_embeddings=True,
    )


def classify_by_embedding(text: str) -> tuple[str | None, float]:
    _load_model()
    enriched = f"payment to {text}"
    embedding = _model.encode([enriched], normalize_embeddings=True)
    similarities = np.dot(embedding, _cat_embeddings.T)[0]
    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])
    if best_score >= CONFIDENCE_THRESHOLD:
        return _cat_names[best_idx], best_score
    return None, best_score


def classify_batch(texts: list[str]) -> list[tuple[str | None, float]]:
    if not texts:
        return []
    _load_model()
    enriched = [f"payment to {t}" for t in texts]
    embeddings = _model.encode(enriched, normalize_embeddings=True)
    similarities = np.dot(embeddings, _cat_embeddings.T)
    results = []
    for i in range(len(texts)):
        best_idx = int(np.argmax(similarities[i]))
        best_score = float(similarities[i][best_idx])
        if best_score >= CONFIDENCE_THRESHOLD:
            results.append((_cat_names[best_idx], best_score))
        else:
            results.append((None, best_score))
    return results


def is_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False
