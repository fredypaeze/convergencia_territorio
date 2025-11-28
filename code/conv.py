# ============================================================
# MVP MICROSITIO – CONVERGENCIA DE FIGURAS TERRITORIALES
# Ministerio de Minas y Energía – Proyecto de Convergencia
#
# ESTRUCTURA DE CARPETAS REQUERIDA
# --------------------------------
# C:\Users\fredy\Desktop\proyecti_convergencia\
#   ├─ inputs\
#   │   └─ shapes\
#   │       ├─ Consejo_Comunitario_Titulado\Consejo_Comunitario_Titulado.shp
#   │       ├─ Resguardo_Indigena_Formalizado\Resguardo_Indigena_Formalizado.shp
#   │       ├─ Zonas_de_Reserva_Campesina_Constituida\Zonas_de_Reserva_Campesina_Constituida.shp
#   │       ├─ Zonas_en_conflicto\Municipios_2025_join.shp
#   │       └─ MGN2024_00_COLOMBIA\...
#   └─ outputs\
#       ├─ tablas\
#       ├─ mapas\
#       ├─ micrositio\
#       └─ llm\
#
# EJECUCIÓN
# ---------
# - Instala las librerías una vez en tu entorno:
#   pip install geopandas folium shapely tabulate requests python-dotenv
# - Luego ejecuta este script. Genera:
#   - Tablas (Excel + JSON) en outputs/tablas y outputs/micrositio
#   - Mapas HTML (full y light) en outputs/mapas
#   - Micrositio index.html en outputs/micrositio
#   - (Opcional) análisis de texto en outputs/llm
# ============================================================

import os
import warnings

import geopandas as gpd
import pandas as pd
import numpy as np
import folium

from shapely.geometry import shape
from folium.features import GeoJsonTooltip
from pandas.api.types import is_datetime64_any_dtype, is_datetime64tz_dtype

# Opcionales (para LLM y markdown)
from tabulate import tabulate
import requests
from dotenv import load_dotenv

# ------------------------------------------------------------
# 0. CONFIGURACIÓN BÁSICA
# ------------------------------------------------------------
warnings.filterwarnings("ignore")
load_dotenv()

# Carpeta base del proyecto
BASE_DIR   = r"C:\Users\fredy\Desktop\convergencia_territorio"
INPUT_DIR  = os.path.join(BASE_DIR, "inputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
SHAPES_DIR = os.path.join(INPUT_DIR, "shapes")

# Subcarpetas de salida
TABLAS_DIR = os.path.join(OUTPUT_DIR, "tablas")
MAPAS_DIR  = os.path.join(OUTPUT_DIR, "mapas")
MICRO_DIR  = os.path.join(OUTPUT_DIR, "micrositio")
LLM_DIR    = os.path.join(OUTPUT_DIR, "llm")

os.makedirs(TABLAS_DIR, exist_ok=True)
os.makedirs(MAPAS_DIR,  exist_ok=True)
os.makedirs(MICRO_DIR,  exist_ok=True)
os.makedirs(LLM_DIR,    exist_ok=True)

# Rutas de SHP (manteniendo la lógica que ya usabas)
CC_PATH  = os.path.join(SHAPES_DIR, "Consejo_Comunitario_Titulado", "Consejo_Comunitario_Titulado.shp")
RES_PATH = os.path.join(SHAPES_DIR, "Resguardo_Indigena_Formalizado", "Resguardo_Indigena_Formalizado.shp")
ZRC_PATH = os.path.join(SHAPES_DIR, "Zonas_de_Reserva_Campesina_Constituida", "Zonas_de_Reserva_Campesina_Constituida.shp")
CFA_PATH = os.path.join(SHAPES_DIR, "Zonas_en_conflicto", "Municipios_2025_join.shp")

CO_PATH  = os.path.join(SHAPES_DIR, "COLOMBIA", "COLOMBIA.shp")
DEP_PATH = os.path.join(SHAPES_DIR, "ADMINISTRATIVO", "MGN_ADM_DPTO_POLITICO.shp")


# ------------------------------------------------------------
# 1. FUNCIONES AUXILIARES GENERALES
# ------------------------------------------------------------
def formato_col(x):
    """Formatea números como 12.345 (miles con punto). Solo para impresión/texto."""
    if isinstance(x, (int, float, np.integer, np.floating)):
        return "{:,.0f}".format(x).replace(",", ".")
    return x


def fix_dates_any(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Convierte columnas datetime a texto para evitar problemas al exportar a JSON/GeoJSON."""
    gdf = gdf.copy()
    for col in gdf.columns:
        if is_datetime64_any_dtype(gdf[col]) or is_datetime64tz_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)
    return gdf


def limpiar_geometrias(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Repara geometrías inválidas aplicando buffer(0)."""
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.buffer(0)
    return gdf


# ------------------------------------------------------------
# 2. CARGA Y PREPARACIÓN DE CAPAS
# ------------------------------------------------------------
def cargar_capas_base():
    """Carga las capas geográficas desde inputs/shapes."""
    print("Cargando capas geográficas desde:", SHAPES_DIR)
    cc  = gpd.read_file(CC_PATH)
    res = gpd.read_file(RES_PATH)
    zrc = gpd.read_file(ZRC_PATH)
    cfa = gpd.read_file(CFA_PATH)
    dep = gpd.read_file(DEP_PATH)
    return cc, res, zrc, cfa, dep


def preparar_capas_geom(cc, res, zrc, cfa, dep):
    """Limpieza básica de geometrías para todas las capas."""
    cc  = limpiar_geometrias(cc)
    res = limpiar_geometrias(res)
    zrc = limpiar_geometrias(zrc)
    cfa = limpiar_geometrias(cfa)
    dep = limpiar_geometrias(dep)
    return cc, res, zrc, cfa, dep


def reproyectar_a_3116(*capas):
    """Reproyecta todas las capas a EPSG:3116 (MAGNA-SIRGAS / Colombia Bogotá)."""
    reproj = [g.to_crs(3116) for g in capas]
    return reproj


def calcular_areas_km2(cc_3116, res_3116, zrc_3116, cfa_3116):
    """Calcula área_km2 para las capas temáticas (no departamentos)."""
    for gdf in (cc_3116, res_3116, zrc_3116, cfa_3116):
        gdf["area_km2"] = gdf.geometry.area / 1e6
    return cc_3116, res_3116, zrc_3116, cfa_3116


# ------------------------------------------------------------
# 3. CORTES POR DEPARTAMENTO Y RANKING
# ------------------------------------------------------------
def cortar_por_departamento(cc_3116, res_3116, zrc_3116, cfa_3116, dep_3116):
    """Intersecta cada capa temática con departamentos y calcula área_km2 en cada corte."""
    campos_dep = ["dpto_cnmbr", "geometry"]

    zrc_dep = gpd.overlay(zrc_3116, dep_3116[campos_dep], how="intersection")
    res_dep = gpd.overlay(res_3116, dep_3116[campos_dep], how="intersection")
    cc_dep  = gpd.overlay(cc_3116,  dep_3116[campos_dep], how="intersection")
    cfa_dep = gpd.overlay(cfa_3116, dep_3116[campos_dep], how="intersection")

    for gdf in (zrc_dep, res_dep, cc_dep, cfa_dep):
        gdf["area_km2"] = gdf.geometry.area / 1e6

    return zrc_dep, res_dep, cc_dep, cfa_dep


def construir_ranking_departamental(zrc_dep, res_dep, cc_dep, cfa_dep):
    """Construye tabla de conteos y áreas por departamento para cada figura."""
    # Conteos
    ranking_zrc = zrc_dep.groupby("dpto_cnmbr").size().rename("n_zrc")
    ranking_res = res_dep.groupby("dpto_cnmbr").size().rename("n_res")
    ranking_cc  = cc_dep.groupby("dpto_cnmbr").size().rename("n_cc")
    ranking_cfa = cfa_dep.groupby("dpto_cnmbr").size().rename("n_cfa")

    # Áreas
    area_zrc = zrc_dep.groupby("dpto_cnmbr")["area_km2"].sum().rename("area_zrc_km2")
    area_res = res_dep.groupby("dpto_cnmbr")["area_km2"].sum().rename("area_res_km2")
    area_cc  = cc_dep.groupby("dpto_cnmbr")["area_km2"].sum().rename("area_cc_km2")
    area_cfa = cfa_dep.groupby("dpto_cnmbr")["area_km2"].sum().rename("area_cfa_km2")

    ranking_dep = pd.concat(
        [ranking_zrc, ranking_res, ranking_cc, ranking_cfa,
         area_zrc, area_res, area_cc, area_cfa],
        axis=1
    ).fillna(0)

    ranking_dep = ranking_dep.sort_values("area_res_km2", ascending=False)
    print("Ranking departamental construido. Filas:", ranking_dep.shape[0])
    return ranking_dep


# ------------------------------------------------------------
# 4. CÁLCULO DE SUPERPOSICIONES
# ------------------------------------------------------------
def _overlay_geom(gdf1, gdf2):
    """Overlay de dos capas usando solo geometría."""
    return gpd.overlay(gdf1[["geometry"]], gdf2[["geometry"]], how="intersection")


def _superficie_por_departamento(inter_geom, dep_3116, nombre_col):
    """Intersecta la geometría de superposición con departamentos y suma área_km2_inter."""
    inter_dep = gpd.overlay(
        inter_geom,
        dep_3116[["dpto_cnmbr", "geometry"]],
        how="intersection"
    )
    inter_dep["area_km2_inter"] = inter_dep.geometry.area / 1e6
    serie = inter_dep.groupby("dpto_cnmbr")["area_km2_inter"].sum().rename(nombre_col)
    return serie


def calcular_superposiciones(zrc_3116, res_3116, cc_3116, cfa_3116, dep_3116):
    """
    Calcula áreas de superposición entre:
    - ZRC ∩ Resguardos
    - ZRC ∩ CC
    - ZRC ∩ CFA
    - Resguardos ∩ CC
    - Resguardos ∩ CFA
    - CC ∩ CFA
    Devuelve tabla_super por dpto.
    """
    # 1. Intersecciones geométricas
    zrc_res_inter = _overlay_geom(zrc_3116, res_3116)
    zrc_cc_inter  = _overlay_geom(zrc_3116, cc_3116)
    zrc_cfa_inter = _overlay_geom(zrc_3116, cfa_3116)
    res_cc_inter  = _overlay_geom(res_3116, cc_3116)
    res_cfa_inter = _overlay_geom(res_3116, cfa_3116)
    cc_cfa_inter  = _overlay_geom(cc_3116,  cfa_3116)

    # 2. Asignar departamento y sumar áreas
    area_zrc_res = _superficie_por_departamento(zrc_res_inter, dep_3116, "area_zrc_res_km2")
    area_zrc_cc  = _superficie_por_departamento(zrc_cc_inter,  dep_3116, "area_zrc_cc_km2")
    area_zrc_cfa = _superficie_por_departamento(zrc_cfa_inter, dep_3116, "area_zrc_cfa_km2")
    area_res_cc  = _superficie_por_departamento(res_cc_inter,  dep_3116, "area_res_cc_km2")
    area_res_cfa = _superficie_por_departamento(res_cfa_inter, dep_3116, "area_res_cfa_km2")
    area_cc_cfa  = _superficie_por_departamento(cc_cfa_inter,  dep_3116, "area_cc_cfa_km2")

    tabla_super = pd.concat(
        [area_zrc_res, area_zrc_cc, area_zrc_cfa,
         area_res_cc, area_res_cfa, area_cc_cfa],
        axis=1
    ).fillna(0)

    tabla_super["area_total_super_km2"] = (
        tabla_super["area_zrc_res_km2"] +
        tabla_super["area_zrc_cc_km2"] +
        tabla_super["area_zrc_cfa_km2"] +
        tabla_super["area_res_cc_km2"] +
        tabla_super["area_res_cfa_km2"] +
        tabla_super["area_cc_cfa_km2"]
    )

    tabla_super = tabla_super.sort_values("area_total_super_km2", ascending=False)
    print("Tabla de superposiciones construida. Filas:", tabla_super.shape[0])
    return tabla_super


# ------------------------------------------------------------
# 5. TABLAS FINALES Y EXPORTACIÓN (EXCEL + JSON)
# ------------------------------------------------------------
def construir_tabla_final(ranking_dep, tabla_super):
    """Une ranking_dep y tabla_super en una sola tabla por departamento."""
    tabla_final = ranking_dep.join(tabla_super, how="left").fillna(0)
    print("Tabla final construida. Filas:", tabla_final.shape[0])
    return tabla_final


def exportar_tablas(tabla_super, tabla_final):
    """Exporta tablas a Excel y JSON para el micrositio."""
    path_super_xlsx = os.path.join(TABLAS_DIR, "tabla_superposicion_departamento.xlsx")
    path_final_num  = os.path.join(TABLAS_DIR, "tabla_final_geografica_numeric.xlsx")
    path_final_form = os.path.join(TABLAS_DIR, "tabla_final_geografica_formateada.xlsx")
    path_json_min   = os.path.join(MICRO_DIR,  "tabla_final_min.json")

    # Versiones formateadas
    tabla_super_form = tabla_super.applymap(formato_col)
    tabla_final_form = tabla_final.applymap(formato_col)

    tabla_super_form.to_excel(path_super_xlsx)
    tabla_final.to_excel(path_final_num)
    tabla_final_form.to_excel(path_final_form)

    # JSON mínimo para frontend
    cols_min = [
        "n_zrc", "n_res", "n_cc", "n_cfa",
        "area_zrc_km2", "area_res_km2", "area_cc_km2", "area_cfa_km2",
        "area_zrc_res_km2", "area_zrc_cc_km2", "area_zrc_cfa_km2",
        "area_res_cc_km2", "area_res_cfa_km2", "area_cc_cfa_km2",
        "area_total_super_km2"
    ]
    tabla_min = tabla_final[cols_min].reset_index()
    tabla_min.to_json(path_json_min, orient="records", force_ascii=False, indent=2)

    print("Tablas exportadas en:", TABLAS_DIR)
    print("JSON para micrositio en:", path_json_min)


# ------------------------------------------------------------
# 6. MAPAS INTERACTIVOS (FULL Y LIGHT)
# ------------------------------------------------------------
def construir_mapa_full(dep_3116, zrc_3116, res_3116, cc_3116, cfa_3116, tabla_final):
    """Mapa multicapas detallado (no optimizado para web masiva)."""
    dep_map = dep_3116.to_crs(4326).copy()
    zrc_map = zrc_3116.to_crs(4326).copy()
    res_map = res_3116.to_crs(4326).copy()
    cc_map  = cc_3116.to_crs(4326).copy()
    cfa_map = cfa_3116.to_crs(4326).copy()

    # Unir tabla_final por departamento
    dep_map = dep_map.merge(
        tabla_final,
        how="left",
        left_on="dpto_cnmbr",
        right_index=True
    ).fillna(0)

    # Columnas *_txt para tooltips
    for col in tabla_final.columns:
        dep_map[col + "_txt"] = dep_map[col].apply(formato_col)

    dep_map = fix_dates_any(dep_map)
    zrc_map = fix_dates_any(zrc_map)
    res_map = fix_dates_any(res_map)
    cc_map  = fix_dates_any(cc_map)
    cfa_map = fix_dates_any(cfa_map)

    m = folium.Map(
        location=[4.5, -74.1],
        zoom_start=5.2,
        tiles="CartoDB positron"
    )

    # Departamentos (resumen)
    folium.GeoJson(
        dep_map,
        name="Departamentos (resumen por dpto)",
        style_function=lambda x: {
            "fillColor": "#ffffff",
            "color": "#555555",
            "weight": 1,
            "fillOpacity": 0.1
        },
        highlight_function=lambda x: {
            "fillColor": "#ffffe0",
            "color": "#000000",
            "weight": 2,
            "fillOpacity": 0.4
        },
        tooltip=GeoJsonTooltip(
            fields=[
                "dpto_cnmbr",
                "n_zrc_txt", "n_res_txt", "n_cc_txt", "n_cfa_txt",
                "area_zrc_km2_txt", "area_res_km2_txt", "area_cc_km2_txt", "area_cfa_km2_txt",
                "area_zrc_res_km2_txt", "area_zrc_cc_km2_txt", "area_zrc_cfa_km2_txt",
                "area_res_cc_km2_txt", "area_res_cfa_km2_txt",
                "area_cc_cfa_km2_txt",
                "area_total_super_km2_txt"
            ],
            aliases=[
                "Departamento:",
                "N° ZRC:",
                "N° Resguardos:",
                "N° Consejos:",
                "N° CFA:",
                "Área ZRC (km²):",
                "Área Resguardos (km²):",
                "Área CC (km²):",
                "Área CFA (km²):",
                "Área ZRC∩Res (km²):",
                "Área ZRC∩CC (km²):",
                "Área ZRC∩CFA (km²):",
                "Área Res∩CC (km²):",
                "Área Res∩CFA (km²):",
                "Área CC∩CFA (km²):",
                "Área total superpuesta (km²):"
            ]
        )
    ).add_to(m)

    # ZRC
    folium.GeoJson(
        zrc_map,
        name="Zonas de Reserva Campesina (ZRC)",
        style_function=lambda x: {
            "fillColor": "#52ee2b",
            "color": "#52ee2b",
            "weight": 1,
            "fillOpacity": 0.25
        },
        highlight_function=lambda x: {
            "fillColor": "#52ee2b",
            "color": "#318316",
            "weight": 2,
            "fillOpacity": 0.45
        },
        tooltip=GeoJsonTooltip(
            fields=["NOMBRE_ZON", "DEPARTAMEN", "MUNICIPIOS", "Año", "area_km2"],
            aliases=["ZRC:", "Departamento (original):", "Municipios:", "Año acto:", "Área (km²):"]
        )
    ).add_to(m)

    # Resguardos
    folium.GeoJson(
        res_map,
        name="Resguardos Indígenas",
        style_function=lambda x: {
            "fillColor": "#1aa0e3",
            "color": "#1aa0e3",
            "weight": 1,
            "fillOpacity": 0.25
        },
        highlight_function=lambda x: {
            "fillColor": "#1aa0e3",
            "color": "#002199",
            "weight": 2,
            "fillOpacity": 0.45
        },
        tooltip=GeoJsonTooltip(
            fields=["NOMBRE", "PUEBLO", "DEPARTAMEN", "MUNICIPIO", "AREA_TOTAL", "area_km2"],
            aliases=["Resguardo:", "Pueblo:", "Departamento (original):", "Municipio:", "Área fuente (ha):", "Área calculada (km²):"]
        )
    ).add_to(m)

    # Consejos Comunitarios
    folium.GeoJson(
        cc_map,
        name="Consejos Comunitarios Titulados",
        style_function=lambda x: {
            "fillColor": "#eb31b9",
            "color": "#eb31b9",
            "weight": 1,
            "fillOpacity": 0.25
        },
        highlight_function=lambda x: {
            "fillColor": "#eb31b9",
            "color": "#5a004b",
            "weight": 2,
            "fillOpacity": 0.45
        },
        tooltip=GeoJsonTooltip(
            fields=["NOMBRE", "DEPARTAMEN", "MUNICIPIO", "AREA_TOTAL", "area_km2"],
            aliases=["Consejo:", "Departamento (original):", "Municipio:", "Área fuente (ha):", "Área calculada (km²):"]
        )
    ).add_to(m)

    # CFA
    folium.GeoJson(
        cfa_map,
        name="Zonas en Conflicto Armado (CFA)",
        style_function=lambda x: {
            "fillColor": "#e31a1c",
            "color": "#e31a1c",
            "weight": 1,
            "fillOpacity": 0.25
        },
        highlight_function=lambda x: {
            "fillColor": "#e31a1c",
            "color": "#99000d",
            "weight": 2,
            "fillOpacity": 0.45
        },
        tooltip=GeoJsonTooltip(
            fields=["MpNombre", "Departamen", "Municipio", "MpCategor", "MpAltitud", "MpArea"],
            aliases=[
                "Municipio (CFA):",
                "Departamento:",
                "Municipio (Divipola):",
                "Categoría:",
                "Altitud:",
                "Área oficial (km²):"
            ],
            localize=True
        )
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    output_map_full = os.path.join(MAPAS_DIR, "mapa_multicapas_superposicion_full.html")
    m.save(output_map_full)
    print("Mapa FULL creado en:", output_map_full)


def construir_mapa_light(dep_3116, zrc_3116, res_3116, cc_3116, cfa_3116, tabla_final):
    """Mapa multicapas simplificado (geometrías simplificadas, menos columnas)."""
    # Simplificar geometrías en EPSG:3116
    dep_s = dep_3116.copy()
    dep_s["geometry"] = dep_s.geometry.simplify(1500)

    zrc_s = zrc_3116.copy()
    zrc_s["geometry"] = zrc_s.geometry.simplify(1000)

    res_s = res_3116.copy()
    res_s["geometry"] = res_s.geometry.simplify(1000)

    cc_s = cc_3116.copy()
    cc_s["geometry"] = cc_s.geometry.simplify(1000)

    cfa_s = cfa_3116.copy()
    cfa_s["geometry"] = cfa_s.geometry.simplify(1000)

    # Pasar a WGS84
    dep_map = dep_s.to_crs(4326)
    zrc_map = zrc_s.to_crs(4326)
    res_map = res_s.to_crs(4326)
    cc_map  = cc_s.to_crs(4326)
    cfa_map = cfa_s.to_crs(4326)

    # Unir tabla_final con departamentos
    dep_map = dep_map.merge(
        tabla_final,
        how="left",
        left_on="dpto_cnmbr",
        right_index=True
    ).fillna(0)

    # *_txt para tooltips
    for col in tabla_final.columns:
        dep_map[col + "_txt"] = dep_map[col].apply(formato_col)

    # Fix fechas
    dep_map = fix_dates_any(dep_map)
    zrc_map = fix_dates_any(zrc_map)
    res_map = fix_dates_any(res_map)
    cc_map  = fix_dates_any(cc_map)
    cfa_map = fix_dates_any(cfa_map)

    # Dejar solo columnas necesarias
    dep_keep = ["dpto_cnmbr"] + [c for c in dep_map.columns if c.endswith("_txt")] + ["geometry"]
    dep_map = dep_map[dep_keep]

    zrc_keep = ["NOMBRE_ZON", "DEPARTAMEN", "MUNICIPIOS", "Año", "area_km2", "geometry"]
    res_keep = ["NOMBRE", "PUEBLO", "DEPARTAMEN", "MUNICIPIO", "AREA_TOTAL", "area_km2", "geometry"]
    cc_keep  = ["NOMBRE", "DEPARTAMEN", "MUNICIPIO", "AREA_TOTAL", "area_km2", "geometry"]
    cfa_keep = ["MpNombre", "Departamen", "Municipio", "MpCategor", "MpAltitud", "MpArea", "geometry"]

    zrc_map = zrc_map[zrc_keep]
    res_map = res_map[res_keep]
    cc_map  = cc_map[cc_keep]
    cfa_map = cfa_map[cfa_keep]

    m_light = folium.Map(
        location=[4.5, -74.1],
        zoom_start=5.2,
        tiles="CartoDB positron"
    )

    # Departamentos
    folium.GeoJson(
        dep_map,
        name="Departamentos (resumen por dpto)",
        style_function=lambda x: {
            "fillColor": "#ffffff",
            "color": "#555555",
            "weight": 1,
            "fillOpacity": 0.1
        },
        highlight_function=lambda x: {
            "fillColor": "#ffffe0",
            "color": "#000000",
            "weight": 2,
            "fillOpacity": 0.4
        },
        tooltip=GeoJsonTooltip(
            fields=[
                "dpto_cnmbr",
                "n_zrc_txt", "n_res_txt", "n_cc_txt", "n_cfa_txt",
                "area_zrc_km2_txt", "area_res_km2_txt", "area_cc_km2_txt", "area_cfa_km2_txt",
                "area_zrc_res_km2_txt", "area_zrc_cc_km2_txt", "area_zrc_cfa_km2_txt",
                "area_res_cc_km2_txt", "area_res_cfa_km2_txt",
                "area_cc_cfa_km2_txt",
                "area_total_super_km2_txt"
            ],
            aliases=[
                "Departamento:",
                "N° ZRC:",
                "N° Resguardos:",
                "N° Consejos:",
                "N° CFA:",
                "Área ZRC (km²):",
                "Área Resguardos (km²):",
                "Área CC (km²):",
                "Área CFA (km²):",
                "Área ZRC∩Res (km²):",
                "Área ZRC∩CC (km²):",
                "Área ZRC∩CFA (km²):",
                "Área Res∩CC (km²):",
                "Área Res∩CFA (km²):",
                "Área CC∩CFA (km²):",
                "Área total superpuesta (km²):"
            ]
        )
    ).add_to(m_light)

    # ZRC
    folium.GeoJson(
        zrc_map,
        name="Zonas de Reserva Campesina (ZRC)",
        style_function=lambda x: {
            "fillColor": "#57e719",
            "color": "#57e719",
            "weight": 1,
            "fillOpacity": 0.25
        },
        tooltip=GeoJsonTooltip(
            fields=["NOMBRE_ZON", "DEPARTAMEN", "MUNICIPIOS", "Año", "area_km2"],
            aliases=["ZRC:", "Departamento:", "Municipios:", "Año:", "Área (km²):"]
        )
    ).add_to(m_light)

    # Resguardos
    folium.GeoJson(
        res_map,
        name="Resguardos Indígenas",
        style_function=lambda x: {
            "fillColor": "#1aa3e3",
            "color": "#1aa3e3",
            "weight": 1,
            "fillOpacity": 0.25
        },
        tooltip=GeoJsonTooltip(
            fields=["NOMBRE", "PUEBLO", "DEPARTAMEN", "MUNICIPIO", "AREA_TOTAL", "area_km2"],
            aliases=["Resguardo:", "Pueblo:", "Departamento:", "Municipio:", "Área (ha):", "Área (km²):"]
        )
    ).add_to(m_light)

    # CC
    folium.GeoJson(
        cc_map,
        name="Consejos Comunitarios Titulados",
        style_function=lambda x: {
            "fillColor": "#e313c0",
            "color": "#e313c0",
            "weight": 1,
            "fillOpacity": 0.25
        },
        tooltip=GeoJsonTooltip(
            fields=["NOMBRE", "DEPARTAMEN", "MUNICIPIO", "AREA_TOTAL", "area_km2"],
            aliases=["Consejo:", "Departamento:", "Municipio:", "Área (ha):", "Área (km²):"]
        )
    ).add_to(m_light)

    # CFA
    folium.GeoJson(
        cfa_map,
        name="Zonas en Conflicto Armado (CFA)",
        style_function=lambda x: {
            "fillColor": "#e31a1c",
            "color": "#e31a1c",
            "weight": 1,
            "fillOpacity": 0.25
        },
        tooltip=GeoJsonTooltip(
            fields=["MpNombre", "Departamen", "Municipio", "MpCategor", "MpAltitud", "MpArea"],
            aliases=[
                "Municipio (CFA):",
                "Departamento:",
                "Municipio (Divipola):",
                "Categoría:",
                "Altitud:",
                "Área oficial (km²):"
            ],
            localize=True
        )
    ).add_to(m_light)

    folium.LayerControl(collapsed=False).add_to(m_light)

    output_map_light = os.path.join(MAPAS_DIR, "mapa_multicapas_superposicion_light.html")
    m_light.save(output_map_light)
    print("Mapa LIGHT creado en:", output_map_light)


# ------------------------------------------------------------
# 7. LLM (OPCIONAL) – ANÁLISIS AUTOMÁTICO
# ------------------------------------------------------------
def configurar_llm():
    """Configura el endpoint de Hugging Face desde variables de entorno."""
    api_key = os.getenv("HF_API_KEY", "")
    if not api_key:
        print("HF_API_KEY no encontrado en .env – el análisis LLM será omitido.")
        return None, None

    api_url = "https://api-inference.huggingface.co/models/google/gemma-1.1-7b-it"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    return api_url, headers


def llamar_llm(prompt: str, api_url: str, headers: dict, max_tokens: int = 700) -> str:
    """Llama al modelo en Hugging Face. Devuelve texto generado o cadena vacía si falla."""
    if not api_url or not headers:
        return ""

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.3,
            "do_sample": True,
            "top_p": 0.9,
            "return_full_text": False
        }
    }

    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
    except requests.HTTPError:
        print("⚠️ Error al llamar al modelo de Hugging Face.")
        try:
            print("Status code:", resp.status_code)
            print("Respuesta (primeros 500 caracteres):")
            print(resp.text[:500])
        except Exception:
            pass
        return ""

    data = resp.json()
    if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
        return data[0]["generated_text"]
    return str(data)


def generar_analisis_llm(tabla_final: pd.DataFrame) -> str:
    """Genera un análisis narrativo usando LLM (si hay API key)."""
    api_url, headers = configurar_llm()
    if not api_url:
        return ""

    resumen_head = tabla_final.head(10).to_markdown()
    resumen_stats = tabla_final.describe().to_markdown()

    prompt = f"""
Eres un analista de datos territoriales del Ministerio de Minas y Energía de Colombia.
Tienes una tabla llamada 'tabla_final' con indicadores por departamento sobre cuatro figuras territoriales:
- Zonas de Reserva Campesina (ZRC)
- Resguardos Indígenas
- Consejos Comunitarios de comunidades negras
- Zonas afectadas por conflicto armado (CFA)

Cada fila es un departamento e incluye conteos, áreas y áreas de superposición.
[HEAD]
{resumen_head}

[DESCRIBE]
{resumen_stats}

Escribe un análisis narrado, claro y conciso (500-900 palabras) para un micrositio público.
Explica qué mide la tabla, resalta patrones y departamentos críticos, y la utilidad para planeación y transición energética.
No repitas literalmente los números.
"""
    texto = llamar_llm(prompt, api_url, headers)
    if texto:
        path_txt = os.path.join(LLM_DIR, "analisis_llm.txt")
        with open(path_txt, "w", encoding="utf-8") as f:
            f.write(texto)
        print("Análisis LLM guardado en:", path_txt)
    else:
        print("No se obtuvo respuesta del LLM.")
    return texto


# ------------------------------------------------------------
# 8. MICROSITIO – index.html
# ------------------------------------------------------------
def construir_micrositio(tabla_final: pd.DataFrame, texto_explicativo: str = None):
    """
    Construye el archivo index.html del micrositio, incrustando el mapa LIGHT
    y un bloque de texto explicativo (del LLM o generado automáticamente).
    """
    if texto_explicativo is None or not texto_explicativo.strip():
        # Borrador simple con top 5 y total
        top5 = tabla_final.sort_values("area_total_super_km2", ascending=False).head(5)
        total_super = tabla_final["area_total_super_km2"].sum()

        top5_str = "\n".join(
            [f"- {idx}: {formato_col(val)} km²"
             for idx, val in top5["area_total_super_km2"].items()]
        )

        texto_explicativo = f"""
Este mapa muestra la superposición de cuatro figuras territoriales en Colombia:
Zonas de Reserva Campesina (ZRC), Resguardos Indígenas, Consejos Comunitarios de
comunidades negras y municipios categorizados por conflicto armado (CFA).

En conjunto, se identifican aproximadamente {formato_col(total_super)} km² con algún tipo de
superposición entre estas figuras. Los departamentos con mayor área superpuesta son:

{top5_str}

Estos territorios concentran retos especiales de gobernanza, planeación y
ordenamiento territorial, fundamentales para avanzar en la transición energética con
enfoque territorial y diferencial.
""".strip()

    mapa_rel = "../mapas/mapa_multicapas_superposicion_light.html"
    salida_html = os.path.join(MICRO_DIR, "index.html")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Micrositio – Convergencia de figuras territoriales</title>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
        }}
        header {{
            background: #003366;
            color: white;
            padding: 16px 24px;
        }}
        header h1 {{
            margin: 0;
            font-size: 20px;
        }}
        main {{
            display: flex;
            flex-direction: row;
            gap: 16px;
            padding: 16px;
            box-sizing: border-box;
            height: calc(100vh - 72px);
        }}
        .mapa-container {{
            flex: 2;
            min-width: 0;
        }}
        .mapa-container iframe {{
            width: 100%;
            height: 100%;
            border: none;
            box-shadow: 0 0 8px rgba(0,0,0,0.15);
        }}
        .texto-container {{
            flex: 1;
            min-width: 280px;
            background: white;
            padding: 16px;
            box-shadow: 0 0 8px rgba(0,0,0,0.1);
            overflow-y: auto;
        }}
        .texto-container h2 {{
            margin-top: 0;
            font-size: 18px;
            color: #003366;
        }}
        .texto-container p {{
            line-height: 1.5;
            font-size: 14px;
            text-align: justify;
        }}
        pre {{
            white-space: pre-wrap;
            font-family: inherit;
            font-size: 14px;
        }}
        @media (max-width: 900px) {{
            main {{
                flex-direction: column;
                height: auto;
            }}
            .mapa-container {{
                height: 400px;
            }}
        }}
    </style>
</head>
<body>
<header>
    <h1>Convergencia de figuras territoriales – MVP Micrositio</h1>
</header>
<main>
    <section class="mapa-container">
        <iframe src="{mapa_rel}" title="Mapa de superposición territorial"></iframe>
    </section>
    <section class="texto-container">
        <h2>¿Qué muestra este mapa?</h2>
        <pre>{texto_explicativo}</pre>
    </section>
</main>
</body>
</html>
"""
    with open(salida_html, "w", encoding="utf-8") as f:
        f.write(html)

    print("Micrositio creado en:", salida_html)


# ------------------------------------------------------------
# 9. FUNCIÓN PRINCIPAL
# ------------------------------------------------------------
def main():
    # 1. Carga
    cc, res, zrc, cfa, dep = cargar_capas_base()

    # 2. Limpieza geométrica
    cc, res, zrc, cfa, dep = preparar_capas_geom(cc, res, zrc, cfa, dep)

    # 3. Reproyección y áreas
    cc_3116, res_3116, zrc_3116, cfa_3116, dep_3116 = reproyectar_a_3116(cc, res, zrc, cfa, dep)
    cc_3116, res_3116, zrc_3116, cfa_3116 = calcular_areas_km2(cc_3116, res_3116, zrc_3116, cfa_3116)

    # 4. Cortes por departamento y ranking
    zrc_dep, res_dep, cc_dep, cfa_dep = cortar_por_departamento(cc_3116, res_3116, zrc_3116, cfa_3116, dep_3116)
    ranking_dep = construir_ranking_departamental(zrc_dep, res_dep, cc_dep, cfa_dep)

    # 5. Superposiciones
    tabla_super = calcular_superposiciones(zrc_3116, res_3116, cc_3116, cfa_3116, dep_3116)

    # 6. Tabla final y exportaciones
    tabla_final = construir_tabla_final(ranking_dep, tabla_super)
    exportar_tablas(tabla_super, tabla_final)

    # 7. Mapas
    construir_mapa_full(dep_3116, zrc_3116, res_3116, cc_3116, cfa_3116, tabla_final)
    construir_mapa_light(dep_3116, zrc_3116, res_3116, cc_3116, cfa_3116, tabla_final)

    # 8. (Opcional) Análisis LLM
    texto_llm = generar_analisis_llm(tabla_final)
    texto_para_micrositio = texto_llm if texto_llm else None

    # 9. Micrositio
    construir_micrositio(tabla_final, texto_para_micrositio)


if __name__ == "__main__":
    main()