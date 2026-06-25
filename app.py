import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path("gestione_atleti.db")

st.set_page_config(page_title="Gestione Atleti", page_icon="🏥", layout="wide")

LAZIO_CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background:
      linear-gradient(rgba(3,18,40,.88), rgba(3,18,40,.94)),
      radial-gradient(circle at 50% 0%, rgba(120,200,255,.35), transparent 35%),
      linear-gradient(135deg, #06162d 0%, #0a2546 45%, #071a33 100%);
}
[data-testid="stHeader"] { background: rgba(3,18,40,0); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #05162f, #0c2d55); }
.block-container { padding-top: 1.8rem; }
.hero {
    border: 1px solid rgba(135,206,250,.28);
    background: linear-gradient(135deg, rgba(10,43,78,.92), rgba(4,18,40,.92));
    border-radius: 22px;
    padding: 26px 30px;
    margin-bottom: 22px;
    box-shadow: 0 18px 45px rgba(0,0,0,.28);
}
.hero h1 { color: white; margin-bottom: 4px; font-size: 2.25rem; }
.hero p { color: #cceeff; font-size: 1.05rem; margin: 0; }
.metric-card {
    border: 1px solid rgba(135,206,250,.25);
    border-radius: 18px;
    padding: 18px;
    background: rgba(255,255,255,.06);
}
.stButton button {
    border-radius: 12px;
    background: #83cfff;
    color: #05162f;
    border: 0;
    font-weight: 700;
}
</style>
"""
st.markdown(LAZIO_CSS, unsafe_allow_html=True)


def conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS atleta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            sport TEXT,
            ruolo TEXT,
            data_nascita TEXT,
            telefono TEXT,
            email TEXT
        );
        CREATE TABLE IF NOT EXISTS cartella_clinica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id INTEGER NOT NULL,
            anamnesi_remota TEXT,
            anamnesi_prossima TEXT,
            allergie TEXT,
            note TEXT,
            FOREIGN KEY(atleta_id) REFERENCES atleta(id)
        );
        CREATE TABLE IF NOT EXISTS valutazione_morfologica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id INTEGER NOT NULL,
            data_valutazione TEXT,
            altezza REAL,
            peso REAL,
            bmi REAL,
            lateralita TEXT,
            postura TEXT,
            appoggio TEXT,
            massa_muscolare TEXT,
            note TEXT,
            FOREIGN KEY(atleta_id) REFERENCES atleta(id)
        );
        CREATE TABLE IF NOT EXISTS infortunio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id INTEGER NOT NULL,
            data_evento TEXT,
            stagione TEXT,
            distretto TEXT,
            tipo_tessuto TEXT,
            meccanismo TEXT,
            diagnosi TEXT,
            dinamica TEXT,
            esame_obiettivo TEXT,
            trattamento TEXT,
            esami TEXT,
            prognosi_giorni INTEGER,
            note TEXT,
            FOREIGN KEY(atleta_id) REFERENCES atleta(id)
        );
        CREATE TABLE IF NOT EXISTS farmacologia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id INTEGER NOT NULL,
            tipologia TEXT,
            nome_prodotto TEXT,
            principio_attivo TEXT,
            dosaggio TEXT,
            via_somministrazione TEXT,
            frequenza TEXT,
            data_inizio TEXT,
            data_fine TEXT,
            motivo TEXT,
            prescrittore TEXT,
            tue TEXT,
            documentazione TEXT,
            stato_verifica TEXT,
            note TEXT,
            FOREIGN KEY(atleta_id) REFERENCES atleta(id)
        );
        """)


def df_query(query, params=()):
    with conn() as c:
        return pd.read_sql_query(query, c, params=params)


def execute(query, params=()):
    with conn() as c:
        c.execute(query, params)
        c.commit()


def athletes_options():
    df = df_query("SELECT id, cognome || ' ' || nome AS atleta FROM atleta ORDER BY cognome, nome")
    return df


def selected_athlete_id(label="Atleta"):
    df = athletes_options()
    if df.empty:
        st.warning("Inserisci prima almeno un atleta.")
        return None
    choice = st.selectbox(label, df["atleta"].tolist())
    return int(df.loc[df["atleta"] == choice, "id"].iloc[0])

init_db()

st.sidebar.markdown("# Gestione Atleti")
st.sidebar.markdown("SS Lazio medical database")
page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Atleti", "Cartella clinica", "Valutazione morfologica", "Infortuni", "Farmacologia", "Export"],
)

st.markdown("""
<div class="hero">
<h1>Gestione Atleti</h1>
<p>Cartella clinica sportiva, infortuni, farmacologia e statistiche stagionali.</p>
</div>
""", unsafe_allow_html=True)

if page == "Dashboard":
    atleti = df_query("SELECT * FROM atleta")
    inf = df_query("SELECT * FROM infortunio")
    farm = df_query("SELECT * FROM farmacologia")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Atleti", len(atleti))
    c2.metric("Infortuni", len(inf))
    c3.metric("Giorni prognosi", int(inf["prognosi_giorni"].fillna(0).sum()) if not inf.empty else 0)
    c4.metric("Farmaci", len(farm))
    if not inf.empty:
        st.subheader("Statistiche infortuni")
        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(inf, x="distretto", title="Infortuni per distretto")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.histogram(inf, x="tipo_tessuto", title="Infortuni per tessuto")
            st.plotly_chart(fig, use_container_width=True)
        fig = px.histogram(inf, x="meccanismo", title="Meccanismo")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nessun infortunio inserito.")

elif page == "Atleti":
    st.subheader("Nuovo atleta")
    with st.form("form_atleta", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome")
        cognome = c2.text_input("Cognome")
        sport = c1.text_input("Sport", value="Calcio")
        ruolo = c2.text_input("Ruolo")
        data_nascita = c1.date_input("Data nascita", value=date(2000, 1, 1))
        telefono = c2.text_input("Telefono")
        email = st.text_input("Email")
        submit = st.form_submit_button("Salva atleta")
        if submit and nome and cognome:
            execute("INSERT INTO atleta (nome,cognome,sport,ruolo,data_nascita,telefono,email) VALUES (?,?,?,?,?,?,?)",
                    (nome,cognome,sport,ruolo,str(data_nascita),telefono,email))
            st.success("Atleta salvato.")
    st.subheader("Elenco atleti")
    st.dataframe(df_query("SELECT * FROM atleta ORDER BY cognome, nome"), use_container_width=True)

elif page == "Cartella clinica":
    atleta_id = selected_athlete_id()
    if atleta_id:
        with st.form("cartella"):
            anamnesi_remota = st.text_area("Anamnesi patologica remota")
            anamnesi_prossima = st.text_area("Anamnesi patologica prossima")
            allergie = st.text_area("Allergie")
            note = st.text_area("Note")
            if st.form_submit_button("Salva cartella clinica"):
                execute("INSERT INTO cartella_clinica (atleta_id, anamnesi_remota, anamnesi_prossima, allergie, note) VALUES (?,?,?,?,?)",
                        (atleta_id, anamnesi_remota, anamnesi_prossima, allergie, note))
                st.success("Cartella salvata.")
        st.dataframe(df_query("SELECT * FROM cartella_clinica WHERE atleta_id=?", (atleta_id,)), use_container_width=True)

elif page == "Valutazione morfologica":
    atleta_id = selected_athlete_id()
    if atleta_id:
        with st.form("morfologica"):
            data_valutazione = st.date_input("Data valutazione")
            c1, c2, c3 = st.columns(3)
            altezza = c1.number_input("Altezza cm", min_value=0.0, step=0.5)
            peso = c2.number_input("Peso kg", min_value=0.0, step=0.1)
            bmi = round(peso / ((altezza/100)**2), 2) if altezza and peso else 0
            c3.number_input("BMI", value=float(bmi), disabled=True)
            lateralita = st.selectbox("Lateralità", ["", "Destro", "Sinistro", "Ambidestro"])
            postura = st.text_area("Postura")
            appoggio = st.text_area("Appoggio")
            massa_muscolare = st.text_area("Massa muscolare")
            note = st.text_area("Note")
            if st.form_submit_button("Salva valutazione"):
                execute("INSERT INTO valutazione_morfologica (atleta_id,data_valutazione,altezza,peso,bmi,lateralita,postura,appoggio,massa_muscolare,note) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (atleta_id,str(data_valutazione),altezza,peso,bmi,lateralita,postura,appoggio,massa_muscolare,note))
                st.success("Valutazione salvata.")
        st.dataframe(df_query("SELECT * FROM valutazione_morfologica WHERE atleta_id=?", (atleta_id,)), use_container_width=True)

elif page == "Infortuni":
    atleta_id = selected_athlete_id()
    if atleta_id:
        with st.form("infortunio"):
            c1, c2, c3 = st.columns(3)
            data_evento = c1.date_input("Data evento")
            stagione = c2.text_input("Stagione", value="2025/2026")
            prognosi_giorni = c3.number_input("Prognosi giorni", min_value=0, step=1)
            distretto = st.selectbox("Distretto", ["", "Anca", "Coscia", "Ginocchio", "Gamba", "Caviglia", "Piede", "Spalla", "Gomito", "Polso/Mano", "Colonna", "Altro"])
            tipo_tessuto = st.selectbox("Tipo tessuto", ["", "Muscolare", "Tendineo", "Legamentoso", "Articolare", "Cartilagineo", "Osseo", "Cutaneo", "Neurologico"])
            meccanismo = st.selectbox("Meccanismo", ["", "Contatto", "Non contatto", "Overuse", "Trauma diretto", "Recidiva"])
            diagnosi = st.text_input("Diagnosi")
            dinamica = st.text_area("Dinamica evento")
            esame_obiettivo = st.text_area("Esame obiettivo")
            trattamento = st.text_area("Trattamento")
            esami = st.text_area("Esami diagnostici eseguiti")
            note = st.text_area("Note")
            if st.form_submit_button("Salva infortunio"):
                execute("INSERT INTO infortunio (atleta_id,data_evento,stagione,distretto,tipo_tessuto,meccanismo,diagnosi,dinamica,esame_obiettivo,trattamento,esami,prognosi_giorni,note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (atleta_id,str(data_evento),stagione,distretto,tipo_tessuto,meccanismo,diagnosi,dinamica,esame_obiettivo,trattamento,esami,prognosi_giorni,note))
                st.success("Infortunio salvato.")
        st.dataframe(df_query("SELECT * FROM infortunio WHERE atleta_id=? ORDER BY data_evento DESC", (atleta_id,)), use_container_width=True)

elif page == "Farmacologia":
    atleta_id = selected_athlete_id()
    if atleta_id:
        with st.form("farmaco"):
            c1, c2 = st.columns(2)
            tipologia = c1.selectbox("Tipologia", ["Farmaco", "Integratore", "Infiltrazione", "Terapia fisica", "Altro"])
            nome_prodotto = c2.text_input("Nome prodotto")
            principio_attivo = c1.text_input("Principio attivo")
            dosaggio = c2.text_input("Dosaggio")
            via_somministrazione = c1.text_input("Via somministrazione")
            frequenza = c2.text_input("Frequenza")
            data_inizio = c1.date_input("Data inizio")
            data_fine = c2.date_input("Data fine")
            motivo = st.text_area("Motivo")
            prescrittore = st.text_input("Prescrittore")
            tue = st.selectbox("TUE", ["Non necessaria", "Presente", "Da valutare", "Assente"])
            documentazione = st.text_area("Documentazione")
            stato_verifica = st.selectbox("Stato verifica antidoping", ["Da verificare", "Consentito", "Vietato in gara", "Vietato sempre", "Richiede TUE"])
            note = st.text_area("Note")
            if st.form_submit_button("Salva farmacologia"):
                execute("INSERT INTO farmacologia (atleta_id,tipologia,nome_prodotto,principio_attivo,dosaggio,via_somministrazione,frequenza,data_inizio,data_fine,motivo,prescrittore,tue,documentazione,stato_verifica,note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (atleta_id,tipologia,nome_prodotto,principio_attivo,dosaggio,via_somministrazione,frequenza,str(data_inizio),str(data_fine),motivo,prescrittore,tue,documentazione,stato_verifica,note))
                st.success("Voce farmacologica salvata.")
        st.dataframe(df_query("SELECT * FROM farmacologia WHERE atleta_id=? ORDER BY data_inizio DESC", (atleta_id,)), use_container_width=True)

elif page == "Export":
    st.subheader("Esportazione Excel")
    tables = ["atleta", "cartella_clinica", "valutazione_morfologica", "infortunio", "farmacologia"]
    output = Path("export_gestione_atleti.xlsx")
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for t in tables:
            df_query(f"SELECT * FROM {t}").to_excel(writer, sheet_name=t[:31], index=False)
    with open(output, "rb") as f:
        st.download_button("Scarica Excel", f, file_name="export_gestione_atleti.xlsx")
