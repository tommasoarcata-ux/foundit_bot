import sqlite3
from datetime import datetime
from config import DB_PATH
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("CREATE TABLE IF NOT EXISTS numeri (numero TEXT PRIMARY KEY,nome TEXT NOT NULL,spam_score INTEGER DEFAULT 0,approvato INTEGER DEFAULT 0,user_id INTEGER,data TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS spam_votes (numero TEXT,user_id INTEGER,PRIMARY KEY (numero,user_id))")
        con.commit()
def _con():
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row; return con
def cerca_numero(numero):
    with _con() as con:
        row=con.execute("SELECT * FROM numeri WHERE numero=? AND approvato=1",(numero,)).fetchone()
    return dict(row) if row else None
def aggiungi_numero(numero,nome,user_id):
    try:
        with _con() as con:
            con.execute("INSERT INTO numeri (numero,nome,user_id,data,approvato) VALUES (?,?,?,?,0)",(numero,nome,user_id,datetime.now().strftime("%d/%m/%Y")))
            con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
def segnala_spam(numero,user_id):
    with _con() as con:
        try:
            con.execute("INSERT INTO spam_votes (numero,user_id) VALUES (?,?)",(numero,user_id))
            con.execute("UPDATE numeri SET spam_score=spam_score+1 WHERE numero=?",(numero,))
            con.execute("INSERT OR IGNORE INTO numeri (numero,nome,spam_score,approvato,data) VALUES (?,'Sconosciuto',1,1,?)",(numero,datetime.now().strftime("%d/%m/%Y")))
            con.commit()
        except sqlite3.IntegrityError:
            pass
        row=con.execute("SELECT spam_score FROM numeri WHERE numero=?",(numero,)).fetchone()
    return row["spam_score"] if row else 0
def approva_numero(numero):
    with _con() as con:
        con.execute("UPDATE numeri SET approvato=1 WHERE numero=?",(numero,)); con.commit()
def elimina_numero(numero):
    with _con() as con:
        con.execute("DELETE FROM numeri WHERE numero=?",(numero,))
        con.execute("DELETE FROM spam_votes WHERE numero=?",(numero,)); con.commit()
def get_pending():
    with _con() as con:
        rows=con.execute("SELECT * FROM numeri WHERE approvato=0").fetchall()
    return [dict(r) for r in rows]
def get_all_numbers():
    with _con() as con:
        rows=con.execute("SELECT * FROM numeri").fetchall()
    return [dict(r) for r in rows]
def get_stats():
    with _con() as con:
        t=con.execute("SELECT COUNT(*) FROM numeri").fetchone()[0]
        a=con.execute("SELECT COUNT(*) FROM numeri WHERE approvato=1").fetchone()[0]
        p=con.execute("SELECT COUNT(*) FROM numeri WHERE approvato=0").fetchone()[0]
        s=con.execute("SELECT COUNT(*) FROM numeri WHERE spam_score>=3").fetchone()[0]
    return {"totale":t,"approvati":a,"pending":p,"spam":s}
