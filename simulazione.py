import sqlite3
import random
import time
from datetime import datetime

DB_FILE     = "vasche.db"
TEMP_IDEALE = 12.0

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS letture (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            vasca     TEXT,
            temp      REAL,
            lux       REAL,
            stato     TEXT
        )
    """)
    conn.commit()
    return conn

def stato_temperatura(temp):
    if temp < 8.0:    return "TROPPO FREDDA"
    elif temp > 14.0: return "TROPPO CALDA"
    else:             return "OK"

def simula(conn, temp_principale, temp_calda, temp_fredda, lux):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c = conn.cursor()

    dati = [
        ("VASCA PRINCIPALE", temp_principale, lux),
        ("VASCA CALDA",      temp_calda,      None),
        ("VASCA FREDDA",     temp_fredda,     None),
    ]

    for vasca, temp, l in dati:
        stato = stato_temperatura(temp)
        c.execute("""
            INSERT INTO letture (timestamp, vasca, temp, lux, stato)
            VALUES (?, ?, ?, ?, ?)
        """, (ts, vasca, temp, l, stato))

        # Stampa come il monitor seriale
        lux_str = f"{l:.1f} lux" if l is not None else "N/A"
        print(f"[{vasca:<16}] Temp: {temp:.1f} C | Luce: {lux_str:<12} | {stato}")

    conn.commit()

def main():
    conn = init_db()

    print("=== SIMULATORE VASCHE ===")
    print("Premi Ctrl+C per fermare\n")

    # Temperatura di partenza
    temp_principale = 12.0
    temp_calda      = 15.0
    temp_fredda     =  9.0
    lux             = 300.0

    try:
        ciclo = 0
        while True:
            ciclo += 1
            print(f"--- ciclo {ciclo} ---")

            # Simula variazioni graduali e casuali
            temp_principale += random.uniform(-0.8, 0.8)
            temp_calda      += random.uniform(-0.5, 0.5)
            temp_fredda     += random.uniform(-0.5, 0.5)
            lux             += random.uniform(-30, 30)

            # Mantieni valori in range realistico
            temp_principale = max(6.0,  min(16.0, temp_principale))
            temp_calda      = max(13.0, min(20.0, temp_calda))
            temp_fredda     = max(4.0,  min(11.0, temp_fredda))
            lux             = max(50.0, min(800.0, lux))

            # Logica relè
            if temp_principale < TEMP_IDEALE - 0.5:
                print(">>> AZIONE: Aprire fonte CALDA")
            elif temp_principale > TEMP_IDEALE + 0.5:
                print(">>> AZIONE: Aprire fonte FREDDA")
            else:
                print(">>> AZIONE: Nessuna azione necessaria")

            simula(conn, temp_principale, temp_calda, temp_fredda, lux)
            print()

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSimulazione terminata.")
        print(f"Dati salvati in {DB_FILE}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()