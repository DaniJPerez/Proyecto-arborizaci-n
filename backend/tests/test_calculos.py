import math

import pytest

import calculos


def test_biomasa_ejemplo_conocido():
    # DAP 35.5 cm, altura 8.2 m, densidad 0.6 → ~337 kg (calculado a mano)
    r = calculos.calcular(35.5, 8.2, "Mango")
    assert r["biomasa_aerea_kg"] == pytest.approx(337.0, rel=0.01)


def test_cadena_de_calculo_es_coherente():
    r = calculos.calcular(40, 10, "Samán")
    assert r["biomasa_raiz_kg"] == pytest.approx(r["biomasa_aerea_kg"] * calculos.FACTOR_RAIZ, abs=0.02)
    assert r["biomasa_total_kg"] == pytest.approx(r["biomasa_aerea_kg"] + r["biomasa_raiz_kg"], abs=0.02)
    assert r["carbono_kg"] == pytest.approx(r["biomasa_total_kg"] * calculos.FRACCION_CARBONO, abs=0.02)
    assert r["co2_kg"] == pytest.approx(r["carbono_kg"] * 44 / 12, abs=0.05)
    assert r["o2_kg"] == pytest.approx(r["co2_kg"] * 32 / 44, abs=0.05)


def test_mas_grande_significa_mas_biomasa():
    chico = calculos.calcular(10, 3, None)["biomasa_total_kg"]
    grande = calculos.calcular(50, 15, None)["biomasa_total_kg"]
    assert grande > chico > 0


def test_densidad_por_especie(monkeypatch):
    monkeypatch.setitem(calculos.DENSIDADES, "Ceiba", 0.3)
    assert calculos.densidad_madera("Ceiba") == 0.3
    assert calculos.densidad_madera("Especie desconocida") == calculos.DENSIDAD_POR_DEFECTO


@pytest.mark.parametrize(
    "n,esperado",
    [(0, "sano"), (1, "riesgo"), (3, "riesgo"), (4, "critico"), (14, "critico")],
)
def test_estado_semaforo(n, esperado):
    assert calculos.estado_por_observaciones(n) == esperado


def test_no_hay_valores_invalidos():
    r = calculos.calcular(25, 6, "Mango")
    assert all(not math.isnan(v) for v in r.values())
