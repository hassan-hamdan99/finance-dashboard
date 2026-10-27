import unicodedata
import re
import pandas as pd
from database import get_session
from models import Category, CategoryRule, SubdivisionRule


# --- Regex para extrair partes de descrições do Nubank ---
PIX_ENVIADO_RE = re.compile(
    r"transfer[eê]ncia enviada pelo pix\s*-\s*(.+?)\s*-\s*[\d./]+",
    re.IGNORECASE,
)
PIX_RECEBIDO_RE = re.compile(
    r"transfer[eê]ncia recebida pelo pix\s*-\s*(.+?)\s*-\s*[\d./]+",
    re.IGNORECASE,
)
BOLETO_RE = re.compile(
    r"pagamento de boleto efetuado\s*-\s*(.+)",
    re.IGNORECASE,
)
DEBITO_RE = re.compile(
    r"compra no d[eé]bito\s*-\s*(.+)",
    re.IGNORECASE,
)

# Regex para detecção de forma de pagamento
PAYMENT_PATTERNS = [
    (re.compile(r"transfer[eê]ncia enviada pelo pix", re.I), "pix"),
    (re.compile(r"transfer[eê]ncia recebida pelo pix", re.I), "pix"),
    (re.compile(r"pagamento de boleto", re.I), "boleto"),
    (re.compile(r"compra no d[eé]bito", re.I), "debito"),
    (re.compile(r"pagamento de fatura", re.I), "boleto"),
]


def _extract_entity(description: str) -> str:
    """Extrai o nome do destinatário/empresa de descrições Nubank."""
    for pattern in [PIX_ENVIADO_RE, PIX_RECEBIDO_RE, BOLETO_RE, DEBITO_RE]:
        match = pattern.search(description)
        if match:
            return match.group(1).strip()
    return ""


def _detect_payment_method(description: str) -> str | None:
    """Detecta forma de pagamento pela descrição."""
    for pattern, method in PAYMENT_PATTERNS:
        if pattern.search(description):
            return method
    return None


# Categorias alinhadas com a planilha do usuário
DEFAULT_RULES = {
    "Faturas": [
        "pagamento de fatura", "pagamento fatura", "fatura cartao",
        "banco ibi", "pjbank", "hipercard", "losango",
        "cetelem", "midway", "realize cfi", "dmcard",
        "portoseg", "bradescard", "luizacred", "aymore",
    ],
    "Mercado": [
        "supermercado", "mercado", "hortifruti", "acougue", "feira",
        "padaria", "panificadora", "confeitaria",
        "bistek", "angeloni", "giassi", "forte",
        "assai", "atacadao", "carrefour", "extra", "pao de acucar",
        "big ", "sam's", "costco", "hortifruit", "sacolao", "quitanda",
        "frutaria", "natural da terra",
    ],
    "Sair/Comer fora": [
        "ifood", "uber eats", "rappi", "ze delivery",
        "restaurante", "lanchonete", "pizza", "burger", "sushi",
        "mcdonald", "subway", "starbucks", "cafe", "cafeteria",
        "boteco", "churrascaria", "hamburguer",
        "food", "almoco", "jantar", "sorveteria", "acai",
        "izakaya", "padaria artesanal",
    ],
    "Transporte": [
        "uber ", "99 ", "99app", "99pop", "cabify", "lyft", "taxi",
        "posto", "combustivel", "gasolina", "alcool", "diesel", "shell",
        "ipiranga", "petrobras", "br distribuidora",
        "estacionamento", "parking", "zona azul", "pedagio", "sem parar",
        "metro", "onibus", "bilhete unico", "vlt", "trem",
    ],
    "Pets": [
        "petlove", "petz", "cobasi", "pet shop", "petshop",
        "veterinari", "vet ", "clinica vet", "hospital vet",
        "racao", "pet", "canil",
    ],
    "Assinaturas": [
        "netflix", "spotify", "disney", "hbo", "amazon prime",
        "youtube premium", "apple", "google one", "icloud",
        "assinatura", "subscription",
        "steam", "playstation", "xbox", "nintendo", "xsolla",
        "dropbox", "github", "chatgpt",
    ],
    "Moradia": [
        "aluguel", "condominio", "iptu", "agua ", "esgoto",
        "energia", "eletricidade", "luz ", "celpe", "cemig", "enel", "cpfl",
        "celesc", "copel", "equatorial", "energisa", "light ",
        "gas ", "comgas", "internet", "fibra", "wifi",
        "manutencao", "reforma", "material construcao", "leroy", "telhanorte",
        "prefeitura", "faxina", "diarista",
        "celular", "telefone", "vivo", "claro", "tim ", "oi ",
    ],
    "Saúde": [
        "farmacia", "drogaria", "droga raia", "drogasil", "pague menos",
        "hospital", "clinica", "medico", "dentista", "oftalmologista",
        "laboratorio", "exame", "consulta", "plano de saude", "unimed",
        "amil", "sulamerica", "hapvida", "notredame",
        "fisioterapia", "psicolog", "nutricion", "health",
        "preco popular",
    ],
    "Educação": [
        "escola", "faculdade", "universidade", "curso", "udemy", "coursera",
        "alura", "rocketseat", "livro", "livraria", "saraiva",
        "mensalidade", "matricula",
    ],
    "Salário": [
        "salario", "folha", "pgto folha", "holerite", "remuneracao",
        "adiantamento salarial", "decimo terceiro", "13o salario",
        "ferias", "pgt salario", "pagamento salario",
    ],
    "Lazer": [
        "cinema", "teatro", "show ", "ingresso", "evento",
        "viagem", "hotel", "airbnb", "booking", "decolar",
        "latam", "gol ", "azul ", "passagem", "aeroporto",
        "bar ", "cerveja", "chopp", "balada",
        "parque", "museu", "jogo", "futebol",
    ],
    "Investimentos": [
        "aplicacao cdb", "aplicacao lci", "aplicacao lca",
        "tesouro direto", "fundo de investimento",
        "btg", "xp investimento", "rico ", "clear ",
    ],
    "Outros": [
        "magazine luiza", "magalu", "americanas", "shopee",
        "mercado livre", "mercadopago",
        "aliexpress", "shein", "renner", "riachuelo", "c&a", "zara",
        "nike", "adidas", "centauro", "netshoes", "kabum", "pichau",
        "amazon", "submarino",
        "seguro", "porto seguro", "bradesco seguros",
        "contador", "contabil", "advocacia", "cartorio",
        "doacao",
    ],
}


def _normalize(text: str) -> str:
    """Remove acentos e converte para minúsculas."""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _load_rules_from_db():
    """Carrega regras do banco de dados."""
    session = get_session()
    rules = session.query(CategoryRule).order_by(CategoryRule.priority.desc()).all()
    result = {}
    for rule in rules:
        cat = session.get(Category, rule.category_id)
        if cat:
            keyword = _normalize(rule.keyword)
            result[keyword] = cat.id
    session.close()
    return result


def _get_category_map():
    """Retorna mapa de nome → id das categorias."""
    session = get_session()
    categories = session.query(Category).all()
    cat_map = {c.name: c.id for c in categories}
    cat_name_map = {c.id: c.name for c in categories}
    session.close()
    return cat_map, cat_name_map


def _match_keywords(text_normalized: str, cat_map: dict) -> int | None:
    """Tenta casar texto com keywords das regras padrão."""
    for cat_name, keywords in DEFAULT_RULES.items():
        for keyword in keywords:
            if _normalize(keyword) in text_normalized:
                return cat_map.get(cat_name)
    return None


def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Categoriza transações automaticamente.

    Pipeline de 6 camadas:
        1. Valor positivo → Salário (se match keywords) ou Receita
        2. Regras aprendidas do banco (CategoryRule)
        3. Keywords padrão na descrição completa
        4. Regex extrai entidade (Pix/boleto) → keywords na entidade
        5. Embeddings (Sentence Transformers) como fallback
        6. "Outros" se nada casar

    Também detecta: vendor, payment_method.
    """
    if df.empty:
        return df

    cat_map, cat_name_map = _get_category_map()
    db_rules = _load_rules_from_db()
    outros_id = cat_map.get("Outros")

    category_ids = [None] * len(df)
    category_names = [None] * len(df)
    vendors = [None] * len(df)
    payment_methods = [None] * len(df)
    need_embedding = []

    for i, (_, row) in enumerate(df.iterrows()):
        desc = row["description"]
        desc_normalized = _normalize(desc)
        amount = row.get("amount", 0)

        # Detecta vendor e payment_method
        entity = _extract_entity(desc)
        if entity:
            vendors[i] = entity.title()
        payment_methods[i] = _detect_payment_method(desc)

        # 1. Receita (valor positivo) — check Salário keywords first
        if amount > 0:
            salario_matched = False
            salario_keywords = DEFAULT_RULES.get("Salário", [])
            for kw in salario_keywords:
                if _normalize(kw) in desc_normalized:
                    salario_id = cat_map.get("Salário", outros_id)
                    category_ids[i] = salario_id
                    category_names[i] = cat_name_map.get(salario_id, "Salário")
                    salario_matched = True
                    break
            if not salario_matched:
                receita_id = cat_map.get("Receita", outros_id)
                category_ids[i] = receita_id
                category_names[i] = cat_name_map.get(receita_id, "Receita")
            continue

        matched_id = None

        # 2. Regras aprendidas do banco
        for keyword, cat_id in db_rules.items():
            if keyword in desc_normalized:
                matched_id = cat_id
                break

        # 3. Keywords na descrição completa
        if matched_id is None:
            matched_id = _match_keywords(desc_normalized, cat_map)

        # 4. Extrai entidade e tenta keywords nela
        if matched_id is None and entity:
            entity_normalized = _normalize(entity)
            matched_id = _match_keywords(entity_normalized, cat_map)

        if matched_id is not None:
            category_ids[i] = matched_id
            category_names[i] = cat_name_map.get(matched_id, "Outros")
        else:
            need_embedding.append(i)

    # 5. Embedding fallback (batch)
    if need_embedding:
        category_ids, category_names = _apply_embedding_fallback(
            df, need_embedding, category_ids, category_names,
            cat_map, cat_name_map, outros_id
        )

    df = df.copy()
    df["category_id"] = category_ids
    df["category_name"] = category_names
    # Só adiciona vendor/payment se não vieram no parser
    if "vendor" not in df.columns:
        df["vendor"] = vendors
    if "payment_method" not in df.columns:
        df["payment_method"] = payment_methods

    # Auto-fill subdivision from learned rules
    df = apply_subdivision_rules(df)

    return df


def _apply_embedding_fallback(df, indices, category_ids, category_names,
                              cat_map, cat_name_map, outros_id):
    """Aplica categorização por embeddings nos itens não categorizados."""
    try:
        from categorizer.embeddings import classify_batch, is_available
        if not is_available():
            for i in indices:
                category_ids[i] = outros_id
                category_names[i] = "Outros"
            return category_ids, category_names
    except ImportError:
        for i in indices:
            category_ids[i] = outros_id
            category_names[i] = "Outros"
        return category_ids, category_names

    texts = []
    for i in indices:
        desc = df.iloc[i]["description"]
        entity = _extract_entity(desc)
        texts.append(entity if entity else desc)

    results = classify_batch(texts)

    name_to_id = {}
    for cat_name_emb in set(r[0] for r in results if r[0]):
        if cat_name_emb in cat_map:
            name_to_id[cat_name_emb] = cat_map[cat_name_emb]
        else:
            emb_norm = _normalize(cat_name_emb)
            for db_name, db_id in cat_map.items():
                if _normalize(db_name) == emb_norm:
                    name_to_id[cat_name_emb] = db_id
                    break

    for idx, (cat_name_emb, score) in zip(indices, results):
        if cat_name_emb and cat_name_emb in name_to_id:
            cat_id = name_to_id[cat_name_emb]
            category_ids[idx] = cat_id
            category_names[idx] = cat_name_map.get(cat_id, cat_name_emb)
        else:
            category_ids[idx] = outros_id
            category_names[idx] = "Outros"

    return category_ids, category_names


def learn_from_override(description: str, category_id: int):
    """Aprende uma nova regra quando o usuário corrige a categoria."""
    session = get_session()
    entity = _extract_entity(description)
    if entity:
        keyword = _normalize(entity)
        words = [w for w in keyword.split() if len(w) > 2]
        keyword = " ".join(words[:3])
    else:
        keyword = _normalize(description)
        words = [w for w in keyword.split() if len(w) > 2]
        keyword = " ".join(words[:3])

    if not keyword:
        session.close()
        return

    existing = (
        session.query(CategoryRule)
        .filter_by(keyword=keyword, category_id=category_id)
        .first()
    )
    if not existing:
        rule = CategoryRule(
            keyword=keyword, category_id=category_id,
            priority=10, source="learned",
        )
        session.add(rule)
        session.commit()
    session.close()


def get_all_rules():
    """Retorna todas as regras do banco."""
    session = get_session()
    db_rules = session.query(CategoryRule).order_by(CategoryRule.priority.desc()).all()
    cats = {c.id: c.name for c in session.query(Category).all()}
    session.close()

    return [
        {
            "id": r.id,
            "keyword": r.keyword,
            "category_id": r.category_id,
            "category_name": cats.get(r.category_id, "?"),
            "priority": r.priority,
            "source": r.source,
        }
        for r in db_rules
    ]


def add_rule(keyword: str, category_id: int, priority: int = 5):
    """Adiciona uma regra manualmente."""
    session = get_session()
    keyword_norm = _normalize(keyword)
    existing = (
        session.query(CategoryRule)
        .filter_by(keyword=keyword_norm, category_id=category_id)
        .first()
    )
    if existing:
        existing.priority = priority
    else:
        session.add(CategoryRule(
            keyword=keyword_norm, category_id=category_id,
            priority=priority, source="manual",
        ))
    session.commit()
    session.close()


def delete_rule(rule_id: int):
    """Remove uma regra."""
    session = get_session()
    rule = session.get(CategoryRule, rule_id)
    if rule:
        session.delete(rule)
        session.commit()
    session.close()


def learn_subdivision(description: str, person: str, subdivision: str):
    """Aprende uma regra de subdivisão quando o usuário edita uma transação."""
    entity = _extract_entity(description)
    if entity:
        keyword = _normalize(entity)
        words = [w for w in keyword.split() if len(w) > 2]
        keyword = " ".join(words[:3])
    else:
        keyword = _normalize(description)
        words = [w for w in keyword.split() if len(w) > 2]
        keyword = " ".join(words[:3])

    if not keyword or not person:
        return

    session = get_session()
    existing = (
        session.query(SubdivisionRule)
        .filter_by(keyword=keyword, person=person)
        .first()
    )
    if existing:
        existing.subdivision = subdivision
    else:
        session.add(SubdivisionRule(
            keyword=keyword, person=person, subdivision=subdivision,
        ))
    session.commit()
    session.close()


def apply_subdivision_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica regras aprendidas de subdivisão a um DataFrame."""
    if df.empty:
        return df

    session = get_session()
    rules = session.query(SubdivisionRule).all()
    session.close()

    if not rules:
        return df

    df = df.copy()
    for i, row in df.iterrows():
        # Skip if already has a non-default subdivision set
        if row.get("subdivision") and row["subdivision"] != "individual":
            continue
        desc_normalized = _normalize(str(row.get("description", "")))
        person = str(row.get("person", ""))
        for rule in rules:
            if rule.keyword in desc_normalized and rule.person == person:
                df.at[i, "subdivision"] = rule.subdivision
                break

    return df
