import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path('gestione_atleti.db')

st.set_page_config(page_title='Gestione Atleti', page_icon='🏥', layout='wide')

CSS = '''
<style>
.stApp { background:#f5f8fc; color:#102033; }
section[data-testid="stSidebar"] { background:#071d3a; }
section[data-testid="stSidebar"] * { color:white !important; }
.card {background:white; padding:22px; border-radius:16px; box-shadow:0 4px 18px rgba(0,0,0,.08); border:1px solid #e8eef6; margin-bottom:16px;}
.header {background:linear-gradient(135deg,#061b38,#0b4f91); color:white; padding:28px; border-radius:20px; margin-bottom:20px;}
.header h1 {margin:0; font-size:38px;}
.header p {font-size:17px; margin-top:8px;}
.small {color:#5b6b7c; font-size:14px;}
.badge {display:inline-block; padding:5px 10px; border-radius:999px; background:#e7f2ff; color:#005da8; font-weight:600; margin-right:6px;}
</style>
'''
st.markdown(CSS, unsafe_allow_html=True)


def conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS atleti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        sport TEXT,
        ruolo TEXT,
        data_nascita TEXT,
        telefono TEXT,
        email TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS cartelle (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        atleta_id INTEGER NOT NULL,
        data_visita TEXT,
        anamnesi_remota TEXT,
        anamnesi_prossima TEXT,
        allergie TEXT,
        esame_obiettivo TEXT,
        diagnosi TEXT,
        trattamento TEXT,
        richieste_esami TEXT,
        prognosi TEXT,
        note TEXT,
        FOREIGN KEY(atleta_id) REFERENCES atleti(id)
    )''')
    c.commit(); c.close()


def df_query(q, params=()):
    c = conn(); df = pd.read_sql_query(q, c, params=params); c.close(); return df


def execute(q, params=()):
    c = conn(); cur = c.cursor(); cur.execute(q, params); c.commit(); last = cur.lastrowid; c.close(); return last

init_db()

st.sidebar.markdown('## Gestione Atleti')
st.sidebar.markdown('SS Lazio medical database')
menu = st.sidebar.radio('Menu', ['Dashboard', 'Atleti', 'Nuovo atleta', 'Cartella clinica'])

st.markdown('<div class="header"><h1>Gestione Atleti</h1><p>Ricerca rapida atleti e cartella clinica individuale.</p></div>', unsafe_allow_html=True)

atleti = df_query('SELECT * FROM atleti ORDER BY cognome, nome')

if menu == 'Dashboard':
    cartelle = df_query('SELECT * FROM cartelle')
    c1, c2, c3 = st.columns(3)
    c1.metric('Atleti registrati', len(atleti))
    c2.metric('Cartelle cliniche', len(cartelle))
    c3.metric('Visite recenti', len(cartelle))
    st.markdown('<div class="card"><h3>Accesso rapido</h3><p>Usa il menu <b>Atleti</b> per cercare un atleta e aprire la sua cartella clinica.</p></div>', unsafe_allow_html=True)
    if len(atleti):
        st.dataframe(atleti[['id','cognome','nome','sport','ruolo','telefono','email']], use_container_width=True, hide_index=True)
    else:
        st.info('Nessun atleta inserito. Vai su “Nuovo atleta”.')

elif menu == 'Nuovo atleta':
    st.subheader('Nuovo atleta')
    with st.form('nuovo_atleta'):
        col1, col2 = st.columns(2)
        nome = col1.text_input('Nome')
        cognome = col2.text_input('Cognome')
        sport = col1.text_input('Sport', value='Calcio')
        ruolo = col2.text_input('Ruolo')
        data_nascita = col1.date_input('Data nascita', value=date(2000,1,1))
        telefono = col1.text_input('Telefono')
        email = col2.text_input('Email')
        ok = st.form_submit_button('Salva atleta')
        if ok:
            if not nome or not cognome:
                st.error('Nome e cognome sono obbligatori.')
            else:
                execute('INSERT INTO atleti(nome,cognome,sport,ruolo,data_nascita,telefono,email) VALUES(?,?,?,?,?,?,?)',
                        (nome,cognome,sport,ruolo,str(data_nascita),telefono,email))
                st.success('Atleta salvato. Vai su “Atleti” per aprire la cartella clinica.')
                st.rerun()

elif menu == 'Atleti':
    st.subheader('Elenco e ricerca atleti')
    q = st.text_input('Cerca per nome, cognome, ruolo o sport', placeholder='es. Rossi, difensore, calcio...')
    view = atleti.copy()
    if q and len(view):
        mask = view.apply(lambda r: q.lower() in ' '.join([str(x).lower() for x in r.values]), axis=1)
        view = view[mask]
    if len(view) == 0:
        st.warning('Nessun atleta trovato.')
    else:
        st.dataframe(view[['id','cognome','nome','sport','ruolo','data_nascita','telefono','email']], use_container_width=True, hide_index=True)
        st.markdown('### Apri atleta')
        labels = [f"{r['id']} - {r['cognome']} {r['nome']} ({r.get('ruolo') or '-'})" for _, r in view.iterrows()]
        scelta = st.selectbox('Seleziona atleta', labels)
        atleta_id = int(scelta.split(' - ')[0])
        atleta = atleti[atleti.id == atleta_id].iloc[0]
        st.markdown(f'<div class="card"><h2>{atleta.cognome} {atleta.nome}</h2><span class="badge">{atleta.sport or "Sport non indicato"}</span><span class="badge">{atleta.ruolo or "Ruolo non indicato"}</span><p class="small">Tel: {atleta.telefono or "-"} | Email: {atleta.email or "-"}</p></div>', unsafe_allow_html=True)
        cartelle = df_query('SELECT * FROM cartelle WHERE atleta_id=? ORDER BY data_visita DESC, id DESC', (atleta_id,))
        st.markdown('### Cartella clinica')
        if len(cartelle):
            for _, r in cartelle.iterrows():
                with st.expander(f"{r['data_visita']} - {r['diagnosi'] or 'Valutazione clinica'}"):
                    st.write('**Anamnesi patologica remota**')
                    st.write(r['anamnesi_remota'] or '-')
                    st.write('**Anamnesi patologica prossima**')
                    st.write(r['anamnesi_prossima'] or '-')
                    st.write('**Allergie**')
                    st.write(r['allergie'] or '-')
                    st.write('**Esame obiettivo**')
                    st.write(r['esame_obiettivo'] or '-')
                    st.write('**Diagnosi**')
                    st.write(r['diagnosi'] or '-')
                    st.write('**Trattamento**')
                    st.write(r['trattamento'] or '-')
                    st.write('**Richieste esami**')
                    st.write(r['richieste_esami'] or '-')
                    st.write('**Prognosi**')
                    st.write(r['prognosi'] or '-')
        else:
            st.info('Nessuna valutazione clinica inserita per questo atleta.')

elif menu == 'Cartella clinica':
    st.subheader('Nuova valutazione / cartella clinica')
    if len(atleti) == 0:
        st.warning('Inserisci prima almeno un atleta.')
    else:
        labels = [f"{r['id']} - {r['cognome']} {r['nome']}" for _, r in atleti.iterrows()]
        scelta = st.selectbox('Atleta', labels)
        atleta_id = int(scelta.split(' - ')[0])
        with st.form('cartella'):
            data_visita = st.date_input('Data valutazione', value=date.today())
            anamnesi_remota = st.text_area('Anamnesi patologica remota', height=90)
            anamnesi_prossima = st.text_area('Anamnesi patologica prossima', height=90)
            allergie = st.text_area('Allergie', height=70)
            esame_obiettivo = st.text_area('Esame obiettivo', height=120)
            diagnosi = st.text_area('Diagnosi', height=80)
            trattamento = st.text_area('Trattamento', height=100)
            richieste_esami = st.text_area('Eventuali richieste esami', placeholder='RMN, RX, ECO, TC, esami ematici...', height=90)
            prognosi = st.text_input('Prognosi')
            note = st.text_area('Note', height=80)
            ok = st.form_submit_button('Salva cartella clinica')
            if ok:
                execute('''INSERT INTO cartelle(atleta_id,data_visita,anamnesi_remota,anamnesi_prossima,allergie,esame_obiettivo,diagnosi,trattamento,richieste_esami,prognosi,note)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                        (atleta_id,str(data_visita),anamnesi_remota,anamnesi_prossima,allergie,esame_obiettivo,diagnosi,trattamento,richieste_esami,prognosi,note))
                st.success('Cartella clinica salvata.')
                st.rerun()import sqlite3
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
