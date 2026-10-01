"""
Análisis Cooperativa de Caficultores de Anserma - 2025 vs 2024
Autor: Anderson Mateo Iglesias Suarez

Lee los CSV de la carpeta datos/, calcula los indicadores del análisis
y guarda las gráficas en graficos/. Ejecutar desde la raíz del proyecto:

    python scripts/analisis.py
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
GRAF = RAIZ / "graficos"
GRAF.mkdir(exist_ok=True)

# Paleta inspirada en el café
C24 = "#C8B6A6"   # 2024: tono claro
C25 = "#5D4037"   # 2025: tono oscuro
VERDE = "#558B2F" # acento (AAA, valores positivos)
ROJO = "#B5523B"
GRIS = "#6B6B6B"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlepad": 12,
    "figure.dpi": 150, "savefig.bbox": "tight",
})


def miles(x):
    """Formato colombiano de miles: 1.234.567"""
    return f"{x:,.0f}".replace(",", ".")


def guardar(fig, nombre):
    fig.savefig(GRAF / nombre, facecolor="white")
    plt.close(fig)


def var(a, b):
    return (b - a) / a * 100


# ----------------------------------------------------------------------
# 1. Compras de café por producto
# ----------------------------------------------------------------------
compras = pd.read_csv(DATOS / "compras_cafe_por_producto.csv")
compras["precio_kg_2024"] = compras.valor_2024 / compras.kg_2024
compras["precio_kg_2025"] = compras.valor_2025 / compras.kg_2025
compras["var_kg_%"] = var(compras.kg_2024, compras.kg_2025)
compras["var_precio_%"] = var(compras.precio_kg_2024, compras.precio_kg_2025)
compras["part_valor_2024_%"] = compras.valor_2024 / compras.valor_2024.sum() * 100
compras["part_valor_2025_%"] = compras.valor_2025 / compras.valor_2025.sum() * 100

# Gráfica 1: variación de kilos comprados por producto
d = compras.sort_values("var_kg_%")
fig, ax = plt.subplots(figsize=(8, 4.2))
colores = [VERDE if v > 0 else C25 for v in d["var_kg_%"]]
ax.barh(d.producto, d["var_kg_%"], color=colores)
for y, v in enumerate(d["var_kg_%"]):
    ax.text(v + (1.5 if v > 0 else -1.5), y, f"{v:+.0f}%", va="center",
            ha="left" if v > 0 else "right", fontsize=9)
ax.axvline(0, color=GRIS, lw=0.8)
ax.set_xlim(-80, 60)
ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_title("Variación de kilos comprados, 2025 frente a 2024")
guardar(fig, "01_variacion_kilos_comprados.png")

# Gráfica 2: precio promedio por kilo comprado (sin pasillas ni cacao para comparar café)
d = compras[~compras.producto.isin(["Cacao"])].copy()
fig, ax = plt.subplots(figsize=(8, 4.2))
x = range(len(d))
ax.bar([i - 0.2 for i in x], d.precio_kg_2024, 0.4, color=C24, label="2024")
ax.bar([i + 0.2 for i in x], d.precio_kg_2025, 0.4, color=C25, label="2025")
for i, (a, b) in enumerate(zip(d.precio_kg_2024, d.precio_kg_2025)):
    ax.text(i + 0.2, b + 300, f"+{var(a, b):.0f}%", ha="center", fontsize=8.5, color=C25)
ax.set_xticks(list(x))
etiquetas = {"Estándar T1": "T1", "Estándar T2": "T2", "Estándar T3": "T3", "Pergamino AAA": "AAA",
             "Pergamino cereza": "Cereza", "Pergamino húmedo": "Húmedo",
             "Pasillas, guayaba y media cara": "Pasillas"}
ax.set_xticklabels([etiquetas[p] for p in d.producto], fontsize=9.5)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: "$" + miles(v)))
ax.set_title("Precio promedio pagado por kilo")
ax.legend(frameon=False)
guardar(fig, "02_precio_promedio_kilo.png")

# Gráfica 3: participación del AAA en el valor de las compras
fam = compras.groupby("familia")[["valor_2024", "valor_2025"]].sum()
fam = fam / fam.sum() * 100
orden = ["Pergamino AAA", "Pergamino estándar", "Cereza y húmedo", "Pasillas", "Cacao"]
fam = fam.loc[orden]
col_fam = [VERDE, C25, "#8D6E63", C24, "#D9CBBE"]
fig, ax = plt.subplots(figsize=(8, 2.8))
for j, anio in enumerate(["valor_2025", "valor_2024"]):
    izq = 0
    for k, f in enumerate(orden):
        v = fam.loc[f, anio]
        ax.barh(j, v, left=izq, color=col_fam[k], label=f if j == 0 else None)
        if v > 6:
            ax.text(izq + v / 2, j, f"{v:.0f}%", ha="center", va="center",
                    color="white" if k < 3 else "black", fontsize=9, fontweight="bold")
        izq += v
ax.set_yticks([0, 1]); ax.set_yticklabels(["2025", "2024"])
ax.set_xlim(0, 100); ax.set_xticks([])
ax.spines["bottom"].set_visible(False); ax.spines["left"].set_visible(False)
ax.legend(ncol=5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.05), fontsize=8.5)
ax.set_title("¿Cómo se repartió el dinero de las compras de café?")
guardar(fig, "03_composicion_valor_compras.png")

# ----------------------------------------------------------------------
# 2. Ventas por familia de producto
# ----------------------------------------------------------------------
ventas = pd.read_csv(DATOS / "ventas_cafe_por_producto.csv")
vf = ventas.groupby("familia")[["kg_2024", "valor_2024", "kg_2025", "valor_2025"]].sum()
vf["part_2024_%"] = vf.valor_2024 / vf.valor_2024.sum() * 100
vf["part_2025_%"] = vf.valor_2025 / vf.valor_2025.sum() * 100

orden_v = ["Excelso", "Pergamino", "Pasillas", "Cacao", "Especiales", "Consumo"]
vf = vf.loc[orden_v]
col_v = [C25, C24, "#8D6E63", "#D9CBBE", VERDE, "#A1887F"]
fig, ax = plt.subplots(figsize=(8, 2.8))
for j, anio in enumerate(["part_2025_%", "part_2024_%"]):
    izq = 0
    for k, f in enumerate(orden_v):
        v = vf.loc[f, anio]
        ax.barh(j, v, left=izq, color=col_v[k], label=f if j == 0 else None)
        if v > 5:
            ax.text(izq + v / 2, j, f"{v:.0f}%", ha="center", va="center",
                    color="white" if k in (0, 2) else "black", fontsize=9, fontweight="bold")
        izq += v
ax.set_yticks([0, 1]); ax.set_yticklabels(["2025", "2024"])
ax.set_xlim(0, 100); ax.set_xticks([])
ax.spines["bottom"].set_visible(False); ax.spines["left"].set_visible(False)
ax.legend(ncol=6, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.05), fontsize=8.5)
ax.set_title("¿Qué vendió la cooperativa? Participación en el valor de las ventas")
guardar(fig, "04_mezcla_ventas.png")

# Gráfica 5: volumen vs valor de las ventas (índice 2024 = 100)
tot = ventas[["kg_2024", "valor_2024", "kg_2025", "valor_2025"]].sum()
fig, axs = plt.subplots(1, 2, figsize=(8, 3.4))
for ax, (a, b, titulo, fmt) in zip(axs, [
        (tot.kg_2024 / 1e6, tot.kg_2025 / 1e6, "Kilos vendidos (millones)", "{:.2f}"),
        (tot.valor_2024 / 1e9, tot.valor_2025 / 1e9, "Valor vendido (miles de millones $)", "{:.1f}")]):
    ax.bar(["2024", "2025"], [a, b], color=[C24, C25], width=0.55)
    for i, v in enumerate([a, b]):
        ax.text(i, v * 1.02, fmt.format(v).replace(".", ","), ha="center", fontsize=10)
    ax.set_title(titulo, fontsize=10.5)
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.text(0.5, -0.2, f"{var(a, b):+.1f}%".replace(".", ","), transform=ax.transAxes,
            ha="center", fontsize=11, fontweight="bold", color=ROJO if b < a else VERDE)
fig.suptitle("Menos kilos, más valor", fontweight="bold", y=1.03)
guardar(fig, "05_volumen_vs_valor_ventas.png")

# ----------------------------------------------------------------------
# 3. Sucursales
# ----------------------------------------------------------------------
asoc = pd.read_csv(DATOS / "asociados_y_delegados.csv")
fert = pd.read_csv(DATOS / "fertilizante_por_sucursal.csv")
cred = pd.read_csv(DATOS / "creditos_colocados_2025.csv")
cart = pd.read_csv(DATOS / "cartera_por_sucursal_dic2025.csv")
inc = pd.read_csv(DATOS / "incentivo_125_kilo_2025.csv")

suc = (asoc.merge(fert, on="sucursal").merge(cred, on="sucursal")
          .merge(cart[["sucursal", "valor_vencido", "valor_total"]], on="sucursal")
          .merge(inc.rename(columns={"beneficiarios": "benef_incentivo", "valor": "valor_incentivo"}),
                 on="sucursal"))
suc["var_sacos_%"] = var(suc.sacos_2024, suc.sacos_2025)
suc["precio_saco_2025"] = suc.valor_2025 / suc.sacos_2025
suc["cartera_vencida_%"] = suc.valor_vencido / suc.valor_total * 100
suc["incentivo_por_benef"] = suc.valor_incentivo / suc.benef_incentivo
suc["kg_vendidos_2025_aprox"] = suc.valor_incentivo / 125
suc["part_asociados_%"] = suc.asociados_habiles / suc.asociados_habiles.sum() * 100

# Gráfica 6: tablero de sucursales (4 paneles)
fig, axs = plt.subplots(2, 2, figsize=(9, 6))
nombres = suc.sucursal
paneles = [
    (axs[0, 0], suc.asociados_habiles, "Asociados hábiles", lambda v: miles(v), C25),
    (axs[0, 1], suc.kg_vendidos_2025_aprox / 1e3, "Café vendido por asociados 2025 (miles de kg)*",
     lambda v: miles(v), C25),
    (axs[1, 0], suc.sacos_2025, "Sacos de fertilizante vendidos 2025", lambda v: miles(v), C25),
    (axs[1, 1], suc["cartera_vencida_%"], "Cartera vencida (% del saldo)",
     lambda v: f"{v:.1f}%".replace(".", ","), None),
]
for ax, serie, titulo, fmt, color in paneles:
    cols = color if color else [ROJO if v > 3 else C24 for v in serie]
    ax.bar(nombres, serie, color=cols)
    for i, v in enumerate(serie):
        ax.text(i, v * 1.03, fmt(v), ha="center", fontsize=8.5)
    ax.set_title(titulo, fontsize=10)
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", labelsize=8.5)
    ax.set_ylim(0, serie.max() * 1.18)
fig.text(0.01, -0.01, "*Estimado a partir del incentivo de $125 por kilo vendido en 2025.",
         fontsize=8, color=GRIS)
fig.suptitle("Las cinco sucursales", fontweight="bold")
fig.tight_layout()
guardar(fig, "06_tablero_sucursales.png")

# ----------------------------------------------------------------------
# 4. Salud financiera
# ----------------------------------------------------------------------
bal = pd.read_csv(DATOS / "estado_situacion_financiera.csv")
g = bal.groupby("grupo")[["valor_2024", "valor_2025"]].sum()
cta = bal.set_index("cuenta")

ind = {}
for a in ["2024", "2025"]:
    col = f"valor_{a}"
    ac, pc = g.loc["Activo corriente", col], g.loc["Pasivo corriente", col]
    activo = ac + g.loc["Activo no corriente", col]
    pasivo = pc + g.loc["Pasivo no corriente", col]
    dep = cta.loc["Café en depósito", col]          # café de terceros: está igual en activo y pasivo
    deuda_banc = cta.loc["Obligaciones financieras CP", col] + cta.loc["Obligaciones financieras LP", col]
    ind[a] = {
        "Razón corriente": ac / pc,
        "Razón corriente sin café en depósito": (ac - dep) / (pc - dep),
        "Endeudamiento total %": pasivo / activo * 100,
        "Endeudamiento sin café en depósito %": (pasivo - dep) / (activo - dep) * 100,
        "Efectivo": cta.loc["Efectivo y equivalentes", col],
        "Inventarios propios": cta.loc["Inventarios", col],
        "Deuda bancaria": deuda_banc,
        "Patrimonio": g.loc["Patrimonio", col],
        "Aportes sociales + capital mínimo": cta.loc["Aportes sociales", col] + cta.loc["Capital mínimo irreducible", col],
        "Reservas": cta.loc["Reservas", col],
    }
ind = pd.DataFrame(ind)
ind["variacion_%"] = var(ind["2024"], ind["2025"])

# Gráfica 7: cuatro cifras del balance
items = ["Efectivo", "Inventarios propios", "Deuda bancaria", "Patrimonio"]
fig, axs = plt.subplots(1, 4, figsize=(10, 3.2))
for ax, it in zip(axs, items):
    a, b = ind.loc[it, "2024"] / 1e9, ind.loc[it, "2025"] / 1e9
    ax.bar(["2024", "2025"], [a, b], color=[C24, C25], width=0.6)
    for i, v in enumerate([a, b]):
        ax.text(i, v + max(a, b) * 0.03, f"{v:.1f}".replace(".", ","), ha="center", fontsize=9.5)
    ax.set_title(it, fontsize=10)
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_ylim(0, max(a, b) * 1.2)
    v = var(ind.loc[it, "2024"], ind.loc[it, "2025"])
    ax.text(0.5, -0.18, f"{v:+.0f}%", transform=ax.transAxes, ha="center",
            fontweight="bold", color=GRIS)
fig.suptitle("Balance: cifras clave (miles de millones de pesos)", fontweight="bold", y=1.04)
fig.tight_layout()
guardar(fig, "07_balance_cifras_clave.png")

# Gráfica 8: de dónde vino y a dónde fue el efectivo en 2025
flujo = pd.read_csv(DATOS / "flujo_efectivo_resumen.csv").set_index("actividad")
pasos = [("Caja inicial", ind.loc["Efectivo", "2024"]),
         ("Operación", flujo.loc["Operación", "valor_2025"]),
         ("Inversión", flujo.loc["Inversión", "valor_2025"]),
         ("Financiación\n(pago de deudas)", flujo.loc["Financiación", "valor_2025"])]
fig, ax = plt.subplots(figsize=(8, 3.8))
acum = 0
for i, (n, v) in enumerate(pasos):
    if i == 0:
        ax.bar(i, v / 1e9, color=C24); acum = v
        ax.text(i, v / 1e9 + 0.15, f"{v/1e9:.1f}".replace(".", ","), ha="center")
    else:
        base = acum if v > 0 else acum + v
        ax.bar(i, abs(v) / 1e9, bottom=base / 1e9, color=VERDE if v > 0 else ROJO)
        ax.text(i, (base + abs(v)) / 1e9 + 0.15, f"{v/1e9:+.1f}".replace(".", ","), ha="center")
        acum += v
ax.bar(len(pasos), acum / 1e9, color=C25)
ax.text(len(pasos), acum / 1e9 + 0.15, f"{acum/1e9:.1f}".replace(".", ","), ha="center", fontweight="bold")
ax.set_xticks(range(len(pasos) + 1))
ax.set_xticklabels([p[0] for p in pasos] + ["Caja final"], fontsize=9)
ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.set_ylim(0, 11)
ax.set_title("Movimiento del efectivo en 2025 (miles de millones de pesos)")
guardar(fig, "08_movimiento_efectivo.png")

# ----------------------------------------------------------------------
# 5. Lo que volvió al caficultor
# ----------------------------------------------------------------------
soc = pd.read_csv(DATOS / "programas_sociales_2025.csv").sort_values("valor")
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.barh(soc.programa, soc.valor / 1e6, color=C25)
for y, v in enumerate(soc.valor / 1e6):
    ax.text(v + 15, y, "$" + miles(v) + " M", va="center", fontsize=9)
ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
ax.set_xlim(0, soc.valor.max() / 1e6 * 1.25)
ax.tick_params(axis="y", labelsize=9)
ax.set_title("Recursos que llegaron a los caficultores (millones de pesos)")
guardar(fig, "09_programas_caficultor.png")

# ----------------------------------------------------------------------
# 6. El reto: cuota anual del acuerdo PAS frente al excedente operacional
# ----------------------------------------------------------------------
res = pd.read_csv(DATOS / "resultados_seleccionados.csv").set_index("concepto")
CUOTA_PAS = 1_204_000_000
exc_op = res.loc["Excedente operacional"]
fig, ax = plt.subplots(figsize=(7, 3.4))
ax.bar(["Excedente operacional\n2024", "Excedente operacional\n2025"],
       [exc_op.valor_2024 / 1e6, exc_op.valor_2025 / 1e6], color=[C24, C25], width=0.5)
ax.axhline(CUOTA_PAS / 1e6, color=ROJO, ls="--", lw=1.5)
ax.text(1.32, CUOTA_PAS / 1e6 + 25, "Cuota anual acuerdo\nPAS: $1.204 M", color=ROJO, fontsize=9, ha="left")
for i, v in enumerate([exc_op.valor_2024 / 1e6, exc_op.valor_2025 / 1e6]):
    ax.text(i, v + 20, "$" + miles(v) + " M", ha="center", fontsize=9.5)
ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.set_xlim(-0.5, 2.1); ax.set_ylim(0, 1750)
ax.set_title("El reto de los próximos años (millones de pesos)")
guardar(fig, "10_reto_acuerdo_pas.png")

# ----------------------------------------------------------------------
# Exportar tablas de resultados
# ----------------------------------------------------------------------
salida = RAIZ / "datos" / "resultados"
salida.mkdir(exist_ok=True)
compras.round(2).to_csv(salida / "indicadores_compras.csv", index=False)
vf.round(2).to_csv(salida / "indicadores_ventas_familia.csv")
suc.round(2).to_csv(salida / "indicadores_sucursales.csv", index=False)
ind.round(2).to_csv(salida / "indicadores_financieros.csv")

if __name__ == "__main__":
    pd.set_option("display.width", 200, "display.max_columns", 30)
    print(compras[["producto", "precio_kg_2024", "precio_kg_2025", "var_kg_%", "var_precio_%",
                   "part_valor_2024_%", "part_valor_2025_%"]].round(1))
    print(vf.round(1))
    print(suc[["sucursal", "var_sacos_%", "precio_saco_2025", "cartera_vencida_%",
               "incentivo_por_benef", "kg_vendidos_2025_aprox", "part_asociados_%"]].round(1))
    print(ind.round(2))
    print("Cuota PAS / excedente operacional 2025:", round(CUOTA_PAS / exc_op.valor_2025 * 100, 1), "%")
    print("Gráficas en:", GRAF)
