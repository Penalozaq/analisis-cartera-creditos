"""
Analisis de cartera de creditos - Rebanada Delgada #1

Pregunta: que proporcion de las operaciones cerradas se completo y cual quedo
impaga, y como varia esa proporcion segun la cantidad de cuotas pactadas.

Autor: Agustin Penaloza
Datos: registro propio de operaciones financiadas, anonimizado.
"""

import csv

# ---------- 1. LECTURA DEL ARCHIVO ----------
# El CSV ya viene anonimizado: sin nombres, DNI ni telefonos
with open("operaciones.csv", encoding="utf-8") as archivo:
    operaciones = list(csv.DictReader(archivo))

print(f"Operaciones leidas: {len(operaciones)}")


# ---------- 2. CONTROL DE CONSISTENCIA ----------
# La cantidad de cuotas pactadas tiene que ser coherente con el monto total
# dividido el valor de cada cuota. Donde no coincide, se corrige usando esa
# division, que es un dato verificable, y se deja constancia.

print("\n--- INCONSISTENCIAS DETECTADAS ---")
inconsistencias = 0

for operacion in operaciones:
    cuotas = int(operacion["cantidad_cuotas"])
    pagadas = int(operacion["cuotas_pagadas"])
    monto = float(operacion["monto_total"])
    valor = float(operacion["valor_cuota"])
    cuotas_calculadas = round(monto / valor)

    if pagadas > cuotas:
        inconsistencias += 1
        print(f"Cliente {operacion['cliente_id']}: {pagadas} cuotas pagadas "
              f"sobre {cuotas} pactadas. Monto/valor cuota da "
              f"{cuotas_calculadas}. Se corrige a {cuotas_calculadas}.")
        operacion["cantidad_cuotas"] = str(cuotas_calculadas)

if inconsistencias == 0:
    print("No se detectaron inconsistencias")


# ---------- 3. CLASIFICACION ----------
# No se usa el campo "estado" de la planilla como unica fuente de verdad: su
# carga no es uniforme. La clasificacion se apoya en comparar cuotas pagadas
# contra pactadas, que es un dato duro.

def clasificar(operacion):
    cuotas = int(operacion["cantidad_cuotas"])
    pagadas = int(operacion["cuotas_pagadas"])

    if operacion["es_refinanciacion"] == "si":
        return "refinanciada"
    if pagadas >= cuotas:
        return "completada"
    if operacion["estado_planilla"] == "activo":
        return "en_curso"
    return "abandonada"


for operacion in operaciones:
    operacion["clasificacion"] = clasificar(operacion)

conteo = {}
for operacion in operaciones:
    clase = operacion["clasificacion"]
    conteo[clase] = conteo.get(clase, 0) + 1

print("\n--- CLASIFICACION GENERAL ---")
for clase in sorted(conteo):
    print(f"{clase}: {conteo[clase]}")


# ---------- 4. OPERACIONES CERRADAS ----------
# Criterio JBGE: se excluyen refinanciaciones y operaciones en curso.
# La tasa se calcula solo sobre operaciones que ya terminaron su ciclo.
cerradas = []
for operacion in operaciones:
    if operacion["clasificacion"] in ("completada", "abandonada"):
        cerradas.append(operacion)

print(f"\nOperaciones cerradas analizadas: {len(cerradas)}")


# ---------- 5. TASA DE ABANDONO POR RANGO DE PLAZO ----------

def rango_plazo(cuotas):
    if cuotas <= 15:
        return "Hasta 15 cuotas"
    if cuotas <= 30:
        return "16 a 30 cuotas"
    return "Mas de 30 cuotas"


# Dos contadores por rango: total de operaciones cerradas y cuantas se abandonaron
totales = {}
abandonos = {}

for operacion in cerradas:
    rango = rango_plazo(int(operacion["cantidad_cuotas"]))
    totales[rango] = totales.get(rango, 0) + 1
    if operacion["clasificacion"] == "abandonada":
        abandonos[rango] = abandonos.get(rango, 0) + 1

orden = ["Hasta 15 cuotas", "16 a 30 cuotas", "Mas de 30 cuotas"]

print("\n--- TASA DE ABANDONO POR RANGO DE PLAZO ---")
print(f"{'Rango':<20}{'Cerradas':>10}{'Abandonadas':>14}{'Tasa':>10}")

resultados = []
for rango in orden:
    total = totales.get(rango, 0)
    if total == 0:
        continue
    abandonadas = abandonos.get(rango, 0)
    tasa = abandonadas / total * 100
    resultados.append((rango, total, abandonadas, tasa))
    print(f"{rango:<20}{total:>10}{abandonadas:>14}{tasa:>9.1f}%")

total_cerradas = len(cerradas)
total_abandonos = sum(abandonos.values())
tasa_general = total_abandonos / total_cerradas * 100
print(f"\nTasa general de abandono: {tasa_general:.1f}% "
      f"({total_abandonos} de {total_cerradas})")


# ---------- 6. CAPITAL NO COBRADO ----------
monto_no_cobrado = 0
for operacion in cerradas:
    if operacion["clasificacion"] == "abandonada":
        cuotas = int(operacion["cantidad_cuotas"])
        pagadas = int(operacion["cuotas_pagadas"])
        monto = float(operacion["monto_total"])
        monto_no_cobrado += monto * (cuotas - pagadas) / cuotas

print(f"Monto no cobrado en operaciones abandonadas: ${monto_no_cobrado:,.0f}")


# ---------- 7. GRAFICO ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

etiquetas = [f"{r[0]}\n(n={r[1]})" for r in resultados]
valores = [r[3] for r in resultados]

figura, eje = plt.subplots(figsize=(8, 5))
barras = eje.bar(etiquetas, valores, color=["#6B9BD1", "#E8A33D", "#D1544F"])
eje.set_ylabel("Tasa de abandono (%)")
eje.set_title("El abandono de pagos se concentra en los plazos largos",
              fontsize=13, fontweight="bold")
eje.set_ylim(0, 100)

for barra, valor in zip(barras, valores):
    eje.text(barra.get_x() + barra.get_width() / 2, valor + 2,
             f"{valor:.0f}%", ha="center", fontweight="bold")

eje.spines["top"].set_visible(False)
eje.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig("abandono_por_plazo.png", dpi=150)
print("\nGrafico guardado como abandono_por_plazo.png")