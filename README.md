🌎 Convergencia Territorial — MVP

✅ BLOQUE INICIAL PARA AÑADIR AL README (crear carpeta y estructura)
# 🗂️ Estructura requerida del proyecto (antes de ejecutar el MVP)

Para correr correctamente este MVP, el usuario debe **crear una carpeta en el Escritorio** con la siguiente estructura exacta:



C:\Users\TU_USUARIO\Desktop\convergencia_territorio
│
├── inputs
│ └── shapes
│ ├── Consejo_Comunitario_Titulado
│ ├── Resguardo_Indigena_Formalizado
│ ├── Zonas_de_Reserva_Campesina_Constituida
│ ├── Zonas_en_conflicto
│ └── MGN2024_00_COLOMBIA
│
├── outputs
│ ├── mapas
│ ├── tablas
│ ├── micrositio
│ └── llm
│
├── proyecto_convergencia_territorios
│ └── venv\ (entorno virtual generado por el usuario)
│
├── conv.py
├── requirements.txt
└── README.md


## 📌 Importante

- **La carpeta `inputs/shapes/` NO se incluye en GitHub** porque contiene los archivos geográficos oficiales (shapefiles) que son pesados.
- El usuario debe **descargar las shapes desde las fuentes oficiales** listadas más abajo en este README.
- El script `conv.py` está preparado para tomar automáticamente los insumos desde:



inputs/shapes/


- Las carpetas dentro de `outputs/` se generan solas cuando se corre el script por primera vez.

## 🔧 Antes de ejecutar

1. Crear la carpeta `convergencia_territorio` en el escritorio.
2. Descargar las shapes oficiales y colocarlas en `inputs/shapes/` respetando los nombres.
3. Crear un entorno virtual dentro de `proyecto_convergencia_territorios/`.
4. Instalar dependencias:



pip install -r requirements.txt


5. Ejecutar:



python conv.py


El sistema generará:
- Mapas interactivos (completo y versión ligera)
- Tablas geográficas integradas por departamento
- JSON para el micrositio
- HTML final del micrositio dentro de `outputs/micrositio/`


__________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________

🌎 Convergencia Territorial — MVP
Ministerio de Minas y Energía • Hackatón “Desafío Inteligente”

Este repositorio contiene el MVP funcional para la identificación, análisis y visualización de convergencias territoriales en Colombia entre:

Zonas de Reserva Campesina (ZRC)

Resguardos Indígenas

Consejos Comunitarios Titulados

Zonas afectadas por Conflicto Armado (CFA)

Departamentos (MGN 2024)

El proyecto genera:

✔ Mapas interactivos (versión completa y liviana)
✔ Tablas integradas por departamento
✔ Archivos JSON para micrositio
✔ Micrositio en HTML listo para GitHub Pages
✔ Análisis automático generado por LLM (opcional)

📁 Estructura del proyecto
convergencia_territorio/
│
├── conv.py                     # Script principal
├── requirements.txt            # Librerías Python
├── README.md                   # Este documento
├── docs/
│   └── index.html              # Micrositio para GitHub Pages
│
├── inputs/
│   └── shapes/                 # SHP oficiales (usuario debe descargarlos)
│
├── outputs/
│   ├── mapas/                  # Mapas interactivos generados
│   ├── tablas/                 # Tablas y Excel
│   ├── micrositio/             # JSON para el micrositio
│   └── llm/                    # Análisis automático opcional
│
└── proyecto_convergencia_territorios/venv  # Entorno virtual (ignorado por Git)

🔽 Shapes requeridas (NO se incluyen en el repositorio)

Para cumplir lineamientos de GitHub y evitar subir archivos pesados, los shapefiles no se incluyen.
El usuario debe descargarlos y ubicarlos en:

inputs/shapes/


Carpetas esperadas:

ADMINISTRATIVO/
COLOMBIA/
Consejo_Comunitario_Titulado/
Cruces/
Resguardo_Indigena_Formalizado/
Zonas_de_Reserva_Campesina_Constituida/
Zonas_en_conflicto/


Estos provienen de:

IGAC

MinInterior

ANT

Agencia Nacional de Tierras

Datos abiertos oficiales del Estado

MGN 2024 del DANE

Capas institucionales del reto (si aplica)

⚠️ Importante:
Cada carpeta debe contener los archivos típicos de un SHP: .shp, .dbf, .shx, .prj, etc.

🧭 En esta versión del MVP los shapes se cargan localmente

Los geoservicios oficiales (WFS / WMS) aún no cuentan con endpoints estables o no existen para todas las capas del reto, por lo cual la carga debe hacerse desde archivos locales.

Esto se explica también para el jurado.

🚀 Mejora prevista para la siguiente etapa

En una siguiente fase se plantea:

✔ Integrar una capa de ingesta automática mediante:

Conexión a geoservicios existentes (WFS/WMS)

Descarga programada de fuentes institucionales oficiales

Pipeline de actualización periódica

Validación automática de integridad de datos

(sin mencionar webscraping, ni nada sensible)

✔ Convertir el MVP en:

Un pipeline reproducible (Airflow, Github Actions o n8n)

Un API liviana para el micrositio

Un sistema auto-actualizable

Esto permite:

Actualización automática de los mapas

Regeneración silenciosa del micrositio

Trazabilidad y control de calidad del dato

▶️ Cómo ejecutar el proyecto
1️⃣ Crear entorno virtual
python -m venv proyecto_convergencia_territorios


Activar:

proyecto_convergencia_territorios\Scripts\activate

2️⃣ Instalar dependencias
pip install -r requirements.txt

3️⃣ Verificar shapes en inputs/shapes/

Debes tener todas las capas oficiales en sus carpetas correspondientes.

4️⃣ Ejecutar el script principal
python conv.py


El script generará:

outputs/mapas/
outputs/tablas/
outputs/micrositio/

🌐 Micrositio en GitHub Pages

Github Pages muestra automáticamente:

👉 docs/index.html

Una vez subido el repo:

Settings → Pages

Source → "Deploy from branch"

Branch: main

Folder: /docs

Save

Tu sitio quedará en:

https://<tuusuario>.github.io/convergencia_territorio

📌 Licencia y uso

Uso institucional para el reto Hackatón del Ministerio de Minas y Energía.

Fuentes de datos oficiales del Estado Colombiano.

No se incluyen datos sensibles.

✨ Resultado

Este MVP consolida, procesa, cruza y visualiza múltiples capas territoriales, permitiendo un análisis claro de convergencias espaciales que facilitan:

Planeación territorial

Transición energética

Identificación de complejidades regulatorias

Priorización de regiones estratégicas
_____________________________________________________________________________________________________________________________________________________________

“Shapes requeridas (NO se incluyen en el repositorio)”

📚 Fuentes oficiales de datos geográficos

Las capas utilizadas en este proyecto provienen exclusivamente de fuentes oficiales del Estado colombiano, publicadas en la plataforma Datos Abiertos Colombia o entregadas por entidades públicas para el reto.

Se utilizan las siguientes:

1. Comunidades Negras — Consejos Comunitarios Titulados

Fuente oficial:
🔗 https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/Consejo-Comunitario-Titulado/6k7a-ched/about_data

Entidad responsable:
Ministerio del Interior — Dirección de Asuntos para Comunidades Negras

2. Resguardos Indígenas Legalizados (Resguardo Indígena Formalizado)

Fuente oficial:
🔗 https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/Resguardo-Ind-gena-Formalizado/pyj2-wbse/about_data

Entidad responsable:
Ministerio del Interior — Dirección de Asuntos Indígenas, ROM y Minorías

3. Zonas de Reserva Campesina Constituidas (ZRC)

Fuente oficial:
🔗 https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/Zonas-de-Reserva-Campesina-Constituida/d4p8-npuu/about_data

Entidad responsable:
Agencia Nacional de Tierras (ANT)

4. Departamentos — División político-administrativa (MGN 2024)

Fuente oficial:
🔗 Publicación institucional del DANE (Marco Geoestadístico Nacional)

Entidad responsable:
Departamento Administrativo Nacional de Estadística — DANE

🌱 Por qué las shapes no se incluyen en el repositorio

Los archivos geográficos (.shp, .dbf, .prj, .shx) pueden superar fácilmente decenas de MB.
GitHub no recomienda incluir estos insumos pesados; además:

Algunas capas se actualizan periódicamente en sus portales oficiales.

Los repositorios deben mantenerse livianos para facilitar su uso y despliegue.

Es mejor que el usuario descargue siempre la versión vigente desde la fuente oficial.

El script conv.py está preparado para cargar automáticamente estas capas siempre que se ubiquen en:

inputs/shapes/
