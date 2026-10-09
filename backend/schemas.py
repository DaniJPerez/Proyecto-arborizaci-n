"""Modelos Pydantic: definen y validan los datos que entran y salen de la API.

Las reglas replican las restricciones (CHECK) de la base de datos, para que el
usuario reciba el error ANTES de llegar a Supabase, con un mensaje claro.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Zona = Literal["Patio central", "Entrada principal", "Zona deportiva", "Bloques académicos", "Otra"]
Etapa = Literal["Plántula", "Juvenil", "Adulto", "Senescente"]
Interferencia = Literal[
    "Ninguna",
    "Levantamiento de pisos",
    "Afectación de muros",
    "Cables eléctricos",
    "Otra infraestructura",
]
Estado = Literal["sano", "riesgo", "critico"]
TipoFoto = Literal["completo", "detalle", "adicional"]


# ------------------------------- Autenticación -------------------------------
class LoginIn(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class SesionOut(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    user_id: str
    email: str | None = None


# --------------------------------- Catálogos ---------------------------------
class Especie(BaseModel):
    id: int
    nombre_comun: str
    nombre_cientifico: str


class Institucion(BaseModel):
    id: str
    nombre: str
    nombre_corto: str
    prefijo: str
    lat: float
    lng: float


class ObservacionCatalogo(BaseModel):
    codigo: str
    grupo: Literal["follaje", "tronco", "raiz", "plagas"]
    etiqueta: str
    orden: int


class Catalogos(BaseModel):
    especies: list[Especie]
    instituciones: list[Institucion]
    observaciones: list[ObservacionCatalogo]


# ----------------------------------- Árboles -----------------------------------
class ArbolCrear(BaseModel):
    """Lo que envía el formulario del frontend (pasos 1, 3 y 4 del prototipo)."""

    institucion_id: str
    zona: Zona
    zona_otra: str | None = None
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    especie_id: int
    dap_cm: float = Field(gt=0, description="Diámetro a la altura del pecho, en cm")
    altura_m: float = Field(gt=0, le=25, description="Altura total, máximo 25 m")
    copa_m: float = Field(gt=0, description="Diámetro de copa, en m")
    etapa: Etapa
    interferencia: Interferencia
    interferencia_otra: str | None = None
    observaciones: list[str] = Field(
        default_factory=list, description="Códigos de las casillas marcadas, p. ej. f_manchas"
    )

    @field_validator("zona_otra", "interferencia_otra")
    @classmethod
    def _limpiar_texto(cls, v: str | None) -> str | None:
        v = v.strip() if v else v
        return v or None

    @model_validator(mode="after")
    def _textos_otra(self):
        if self.zona == "Otra" and not self.zona_otra:
            raise ValueError("Si la zona es 'Otra', escribe cuál en zona_otra")
        if self.interferencia == "Otra infraestructura" and not self.interferencia_otra:
            raise ValueError("Si la interferencia es 'Otra infraestructura', escribe cuál en interferencia_otra")
        return self


class ArbolResumen(BaseModel):
    """Una fila de la vista `arboles_resumen` (lista de árboles y semáforo)."""

    id: str
    codigo: str
    institucion_id: str
    prefijo: str
    nombre_corto: str
    zona: str
    zona_otra: str | None = None
    lat: float
    lng: float
    nombre_comun: str
    nombre_cientifico: str
    dap_cm: float
    altura_m: float
    copa_m: float
    etapa: str
    interferencia: str
    interferencia_otra: str | None = None
    registrado_en: datetime
    n_observaciones: int
    estado: Estado


class ObservacionOut(BaseModel):
    codigo: str
    grupo: str
    etiqueta: str


class FotoOut(BaseModel):
    id: str
    tipo: TipoFoto
    url: str | None = Field(default=None, description="URL firmada temporal (1 hora)")


class ArbolDetalle(ArbolResumen):
    observaciones: list[ObservacionOut]
    fotos: list[FotoOut]


class Calculos(BaseModel):
    codigo: str
    nombre_comun: str
    dap_cm: float
    altura_m: float
    densidad_madera: float
    biomasa_aerea_kg: float
    biomasa_raiz_kg: float
    biomasa_total_kg: float
    carbono_kg: float
    co2_kg: float
    o2_kg: float
    metodo: str
    advertencia: str


# --------------------------------- Estadísticas ---------------------------------
class ConteoInstitucion(BaseModel):
    prefijo: str
    nombre_corto: str
    total: int


class ConteoEspecie(BaseModel):
    nombre_comun: str
    total: int


class Promedios(BaseModel):
    dap_cm: float | None = None
    altura_m: float | None = None
    copa_m: float | None = None


class TotalesAmbientales(BaseModel):
    biomasa_total_kg: float = 0
    carbono_kg: float = 0
    co2_kg: float = 0
    o2_kg: float = 0


class Estadisticas(BaseModel):
    total: int
    por_estado: dict[str, int]
    por_institucion: list[ConteoInstitucion]
    por_etapa: dict[str, int]
    especies_frecuentes: list[ConteoEspecie]
    promedios: Promedios
    totales_ambientales: TotalesAmbientales
