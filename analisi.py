import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DB_FILE = "vasche.db"

TEMP_MIN    = 8.0
TEMP_MAX    = 14.0
TEMP_IDEALE = 12.0

def carica_dati():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT timestamp, vasca, temp, lux
        FROM letture
        ORDER BY timestamp ASC
    """)
    righe = c.fetchall()
    conn.close()

    dati = {
        "VASCA PRINCIPALE": {"time": [], "temp": [], "lux": []},
        "VASCA CALDA":      {"time": [], "temp": [], "lux": []},
        "VASCA FREDDA":     {"time": [], "temp": [], "lux": []},
    }

    for ts, vasca, temp, lux in righe:
        vasca = vasca.strip()
        if vasca in dati:
            dati[vasca]["time"].append(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S"))
            dati[vasca]["temp"].append(temp)
            dati[vasca]["lux"].append(lux)

    return dati

def grafico_temperature(dati, ax):
    colori = {
        "VASCA PRINCIPALE": "#378ADD",
        "VASCA CALDA":      "#E24B4A",
        "VASCA FREDDA":     "#1D9E75",
    }

    for vasca, valori in dati.items():
        if valori["time"]:
            ax.plot(valori["time"], valori["temp"],
                    label=vasca.title(),
                    color=colori[vasca],
                    linewidth=1.8,
                    marker="o", markersize=3)

    # Fasce temperatura
    ax.axhline(TEMP_IDEALE, color="#888780", linewidth=1, linestyle="--", label="Temp. ideale (12°C)")
    ax.axhspan(TEMP_MIN, TEMP_MAX, alpha=0.08, color="#4ec994", label="Range OK (8–14°C)")

    ax.set_title("Temperatura vasche nel tempo", fontsize=13, fontweight="normal", pad=12)
    ax.set_ylabel("°C")
    ax.set_xlabel("")
    ax.legend(fontsize=9, framealpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    ax.grid(axis="y", linewidth=0.5, alpha=0.4)

def grafico_lux(dati, ax):
    valori = dati["VASCA PRINCIPALE"]
    if valori["time"] and any(l is not None for l in valori["lux"]):
        lux_puliti = [l if l is not None else 0 for l in valori["lux"]]
        ax.fill_between(valori["time"], lux_puliti,
                        alpha=0.3, color="#EF9F27")
        ax.plot(valori["time"], lux_puliti,
                color="#EF9F27", linewidth=1.8,
                marker="o", markersize=3)

    ax.set_title("Illuminazione vasca principale", fontsize=13, fontweight="normal", pad=12)
    ax.set_ylabel("Lux")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    ax.grid(axis="y", linewidth=0.5, alpha=0.4)

def grafico_stato_relè(dati, ax):
    principale = dati["VASCA PRINCIPALE"]
    if not principale["time"]:
        return

    stati_caldo  = []
    stati_freddo = []

    for temp in principale["temp"]:
        if temp < TEMP_IDEALE - 0.5:
            stati_caldo.append(1)
            stati_freddo.append(0)
        elif temp > TEMP_IDEALE + 0.5:
            stati_caldo.append(0)
            stati_freddo.append(1)
        else:
            stati_caldo.append(0)
            stati_freddo.append(0)

    ax.step(principale["time"], stati_caldo,
            where="post", color="#E24B4A",
            linewidth=2, label="Relè caldo")
    ax.step(principale["time"], stati_freddo,
            where="post", color="#378ADD",
            linewidth=2, label="Relè freddo", linestyle="--")

    ax.set_title("Stato relè", fontsize=13, fontweight="normal", pad=12)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["OFF", "ON"])
    ax.legend(fontsize=9, framealpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    ax.grid(axis="y", linewidth=0.5, alpha=0.4)

def grafico_distribuzione(dati, ax):
    colori = {
        "VASCA PRINCIPALE": "#378ADD",
        "VASCA CALDA":      "#E24B4A",
        "VASCA FREDDA":     "#1D9E75",
    }

    for vasca, valori in dati.items():
        if valori["temp"]:
            ax.hist(valori["temp"], bins=15,
                    alpha=0.5, color=colori[vasca],
                    label=vasca.title(), edgecolor="none")

    ax.axvline(TEMP_MIN,    color="#888780", linewidth=1, linestyle=":")
    ax.axvline(TEMP_MAX,    color="#888780", linewidth=1, linestyle=":")
    ax.axvline(TEMP_IDEALE, color="#888780", linewidth=1, linestyle="--")

    ax.set_title("Distribuzione temperature", fontsize=13, fontweight="normal", pad=12)
    ax.set_xlabel("°C")
    ax.set_ylabel("Frequenza")
    ax.legend(fontsize=9, framealpha=0.5)
    ax.grid(axis="y", linewidth=0.5, alpha=0.4)

def main():
    dati = carica_dati()

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle("Monitor vasche — riepilogo dati", fontsize=15, fontweight="normal", y=0.98)
    fig.patch.set_facecolor("#f8f8f7")
    for ax in axes.flat:
        ax.set_facecolor("#ffffff")
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_color("#cccccc")

    grafico_temperature(dati,        axes[0, 0])
    grafico_lux(dati,                axes[0, 1])
    grafico_stato_relè(dati,         axes[1, 0])
    grafico_distribuzione(dati,      axes[1, 1])

    plt.tight_layout()
    plt.savefig("vasche_report.png", dpi=150, bbox_inches="tight")
    print("Grafico salvato come vasche_report.png")
    plt.show()

if __name__ == "__main__":
    main()