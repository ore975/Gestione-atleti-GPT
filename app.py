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
                st.rerun()
