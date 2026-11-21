# 🕳️ Baches Inteligentes — Alcaldía Xochimilco

Prototipo académico de **Sistema de Apoyo a la Decisión (DSS)** enfocado en el reporte ciudadano, la priorización técnica, la estimación de riesgo vial, el cálculo de insumos de bacheo y la organización de rutas de mantenimiento en la **Alcaldía Xochimilco, Ciudad de México**.

Desarrollado en Python con **Streamlit**, **Pandas** y **PostgreSQL** (alojado en Render) con respaldo automático en **SQLite**, integrando Programación Orientada a Objetos, Estructuras de Datos, Bases de Datos Relacionales y Cálculo Integral.

---

## ✨ Funcionalidades Principales

### Portal Ciudadano
* **Captura enfocada en Xochimilco:** Selección dinámica de colonias y barrios de la demarcación (*Barrio San Pedro, Barrio Xaltocan, Santa Cruz Acalpixca, San Gregorio Atlapulco, Santiago Tulyehualco* y *Ampliación Tepepan / La Noria*) que despliega automáticamente sus vialidades principales, además de un campo de referencia opcional.
* **Evaluación guiada con intervalos y factor hidráulico:** Escala de 1 a 5 apoyada en una guía visual cotidiana de intervalos de referencia para tamaño, profundidad, peligro vial y flujo vehicular, más un indicador específico de cercanía a coladeras, registros de drenaje o fugas de agua.
* **Privacidad desde el diseño:** Incluye un **Aviso de Privacidad Simplificado** alineado al principio de minimización de datos (LPDPPSOCDMX). El sistema no solicita ni almacena datos personales identificables; únicamente registra información técnica de infraestructura vial pública y entrega un folio anónimo (`B-XXXXXXXX`).
* **Filtro preventivo de duplicados:** Antes de guardar, verifica en tiempo real si ya existe un reporte activo en la misma colonia y calle con dimensiones similares. Muestra los folios coincidentes y permite al ciudadano confirmar explícitamente si se trata de otro bache distinto.
* **Consulta de seguimiento y análisis de riesgo:** Permite revisar con el folio el índice de urgencia (0–100), la probabilidad de expansión o nuevo bache a 30 días, el riesgo acumulado de incidente vial entre las 6:00 y 22:00 h, la gráfica de área de riesgo en 24 horas y la bitácora de atención.

### Panel Administrativo
* **Acceso operativo con cierre de sesión:** Autenticación de demostración con botón de cierre de sesión en cabecera y barra lateral, registrando al usuario responsable en cada actualización.
* **Tablero analítico y exportación:** Métricas en vivo (reportes activos, emergencias y urgencia promedio), **dos gráficas en paralelo** —barras apiladas por colonia y nivel de prioridad con colores tipo semáforo (`pd.crosstab`) y gráfica de dispersión de profundidad contra urgencia (color por prioridad y tamaño por extensión física)—, tabla resumen y descarga directa en **CSV** para Excel.
* **Ruta para cuadrillas (Lista Simplemente Enlazada):** Genera el orden secuencial de paradas por colonia priorizando los casos más urgentes mediante las clases `NodoBache` y `ListaEnlazadaRuta`.
* **Inspección en campo por medidas reales y cálculo de material:** Permite capturar las mediciones verificadas en sitio (largo y ancho del cajeo en cm, profundidad en cm, aforo en vehículos por minuto, criterio físico de peligro vial y costo unitario editable por tonelada). Convierte automáticamente las medidas a la escala 1–5, calcula el área ($\text{m}^2$), el volumen con 15 % por compactación, la mezcla asfáltica requerida (kg, toneladas y costales de 25 kg) y el gasto estimado en MXN, registrando el resumen técnico en la bitácora y en el historial auditable de prioridad.
* **Historial de reparados:** Resguarda de forma permanente los expedientes cerrados junto con sus bitácoras de estado y cambios de prioridad.

---

## 🧮 Modelo Técnico y Matemático

* **Priorización explicable (0 a 100):** Cada variable en escala de 1 a 5 se normaliza mediante `(calificación − 1) / 4` y se pondera: **peligro vial (35 %)**, **profundidad (30 %)**, **tráfico (20 %)** y **tamaño (15 %)**. La presencia de red hidráulica o fuga suma **+8 puntos** (tope en 100). Todo reporte con profundidad 5 y peligro ≥ 4, o puntuación ≥ 85, se clasifica automáticamente como **Emergencia**.
* **Cálculo de mezcla asfáltica y costo en inspección:** A partir del cajeo rectangular medido en sitio (`largo × ancho × profundidad`), se agrega un **15 % por compactación y merma**, se aplica una densidad de referencia de **2,350 kg/m³** para obtener kilogramos, toneladas y costales de 25 kg, y se multiplica por el costo unitario editable por tonelada.
* **Cálculo Integral (Regla del Trapecio):**
  * *Deterioro a 30 días:* Integra numéricamente una función de densidad exponencial `f(x) = λ × e^(−λ × x)` cuya tasa `λ` depende de la profundidad, el tráfico y el factor hidráulico.
  * *Riesgo horario vial:* Integra una curva bimodal con picos de flujo vehicular alrededor de las 8:00 y 19:00 horas dentro de la ventana de 6:00 a 22:00 horas.
* **Persistencia relacional:** Tres tablas vinculadas por llave foránea `folio` (`baches`, `seguimiento` e `historial_prioridad`) con restricciones `CHECK (1 a 5)`, transacciones completas (*commit/rollback*) y consultas parametrizadas contra inyección SQL.

---

## 📂 Estructura del Proyecto

```text
bacheo-inteligente/
├── app.py                      # Interfaz web en Streamlit (Portal ciudadano y Panel administrativo)
├── requirements.txt            # Dependencias (streamlit, pandas, psycopg2-binary, python-dotenv)
├── README.md                   # Documentación principal del repositorio
├── models/
│   ├── bache.py                # Clase Bache (POO) con validaciones de integridad y rangos (1–5)
│   ├── entidades.py            # Clases BacheDB, SeguimientoDB e HistorialPrioridadDB
│   └── lista_enlazada.py       # Lista Simplemente Enlazada (NodoBache y ListaEnlazadaRuta)
├── database/
│   └── db.py                   # Conexión dual PostgreSQL (Render) / SQLite local y creación de tablas
├── services/
│   ├── prioridad.py            # Regla ponderada de puntuación, factor hidráulico y candado de Emergencia
│   ├── mediciones.py           # Conversión de medidas reales a escala 1–5 y cálculo de asfalto y costo
│   ├── reportes.py             # CRUD transaccional, detector de duplicados y catálogo de Xochimilco
│   ├── seguimiento.py          # Gestión del ciclo de vida de estados y bitácora operativa
│   └── seed.py                 # Carga automática de 4 reportes iniciales de demostración en Xochimilco
├── analytics/
│   ├── tablas.py               # Conversión a DataFrames de Pandas y agrupaciones ejecutivas
│   └── prediccion.py           # Integración numérica por Regla del Trapecio y modelos de riesgo
└── security/
    └── auth.py                 # Validación de credenciales para el entorno demostrativo
