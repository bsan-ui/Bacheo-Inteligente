import pytest
from models.bache import Bache
from services.prioridad import evaluar_bache

def ejemplo(**cambios):
    datos=dict(folio="TEST-0001",ubicacion="Calle ficticia",zona="Prueba",tamano=3,profundidad=3,riesgo_vial=3,trafico=3)
    datos.update(cambios)
    return Bache(**datos)

def test_puntuacion_dentro_de_rango():
    b=evaluar_bache(ejemplo())
    assert 0 <= b.puntuacion <= 100

def test_riesgo_extremo_es_emergencia():
    assert evaluar_bache(ejemplo(profundidad=5,riesgo_vial=4,tamano=1,trafico=1)).nivel == "Emergencia"

def test_rechaza_valor_fuera_de_rango():
    with pytest.raises(ValueError): evaluar_bache(ejemplo(tamano=6))

def test_todos_minimos_es_prioridad_baja():
    b=evaluar_bache(ejemplo(tamano=1,profundidad=1,riesgo_vial=1,trafico=1))
    assert b.puntuacion == 0 and b.nivel == "Prioridad baja"

def test_todos_maximos_es_emergencia():
    b=evaluar_bache(ejemplo(tamano=5,profundidad=5,riesgo_vial=5,trafico=5))
    assert b.puntuacion == 100 and b.nivel == "Emergencia"
