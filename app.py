import streamlit as st
from notion_client import Client

st.set_page_config(
    page_title="Club de Libro — Votación",
    page_icon="📚",
    layout="wide",
)

# ── Estilos ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .book-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    }
    .book-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 4px;
        color: #111827;
    }
    .book-author {
        font-size: 0.9rem;
        color: #6b7280;
        margin-bottom: 8px;
    }
    .book-meta {
        font-size: 0.8rem;
        color: #9ca3af;
        margin-bottom: 10px;
    }
    .book-desc {
        font-size: 0.85rem;
        color: #374151;
        margin-bottom: 16px;
        line-height: 1.5;
    }
    .vote-count {
        font-size: 1.4rem;
        font-weight: 800;
        color: #4f46e5;
    }
    .vote-label {
        font-size: 0.75rem;
        color: #9ca3af;
    }
</style>
""", unsafe_allow_html=True)

# ── Notion client ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_notion_client():
    return Client(auth=st.secrets["NOTION_TOKEN"])

def get_books():
    notion = get_notion_client()
    db_id = st.secrets["NOTION_DATABASE_ID"]
    results = notion.databases.query(database_id=db_id)
    books = []
    for page in results["results"]:
        props = page["properties"]

        def text(prop):
            items = props.get(prop, {}).get("rich_text", [])
            return items[0]["plain_text"] if items else ""

        def title(prop):
            items = props.get(prop, {}).get("title", [])
            return items[0]["plain_text"] if items else ""

        def number(prop):
            return props.get(prop, {}).get("number") or 0

        def select(prop):
            s = props.get(prop, {}).get("select")
            return s["name"] if s else ""

        books.append({
            "id": page["id"],
            "libro": title("Libro"),
            "autor": text("Autor"),
            "sugerido_por": text("Sugerido por"),
            "genero": select("Género"),
            "descripcion": text("Descripción"),
            "votos": number("Total de votos"),
        })

    books.sort(key=lambda b: b["votos"], reverse=True)
    return books

def vote(page_id: str, current_votes: int):
    notion = get_notion_client()
    notion.pages.update(
        page_id=page_id,
        properties={"Total de votos": {"number": current_votes + 1}},
    )

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("📚 Club de Libro — Elige el próximo")
st.caption("Vota por el libro que quieres leer. Los votos se guardan en tiempo real.")

st.divider()

try:
    books = get_books()
except Exception as e:
    st.error(f"No se pudo conectar con Notion: {e}")
    st.stop()

if not books:
    st.info("No hay libros en la base de datos todavía.")
    st.stop()

cols_per_row = 3
rows = [books[i:i + cols_per_row] for i in range(0, len(books), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row, gap="medium")
    for col, book in zip(cols, row):
        with col:
            with st.container(border=True):
                st.markdown(f"**{book['libro']}**")
                st.caption(f"✍️ {book['autor']}" if book["autor"] else "")

                meta_parts = []
                if book["genero"]:
                    meta_parts.append(f"🏷️ {book['genero']}")
                if book["sugerido_por"]:
                    meta_parts.append(f"👤 {book['sugerido_por']}")
                if meta_parts:
                    st.caption("  ·  ".join(meta_parts))

                if book["descripcion"]:
                    desc = book["descripcion"]
                    if len(desc) > 150:
                        desc = desc[:150] + "…"
                    st.markdown(f"<small>{desc}</small>", unsafe_allow_html=True)

                st.markdown(f"### {book['votos']} 🗳️")

                if st.button("Votar", key=book["id"], use_container_width=True, type="primary"):
                    vote(book["id"], book["votos"])
                    st.success("¡Voto registrado!")
                    st.rerun()
