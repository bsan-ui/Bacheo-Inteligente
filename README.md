# Baches Inteligentes — demo académica

Prototipo con Streamlit, Pandas, SQLite (`sqlite3`, biblioteca estándar de Python) y pytest. Utiliza datos sintéticos. No usa SQLAlchemy, PostgreSQL, scikit-learn, Plotly ni GeoPandas.

## Requisitos
Python 3.10+ y pip. SQLite ya viene incluido con Python; no necesitas instalar un servidor ni un controlador adicional.

## Instalar y ejecutar
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

La base de datos se crea automáticamente como `baches.db` en la carpeta desde la que ejecutas Streamlit. No la borres si quieres conservar tus reportes. Para mostrar o inspeccionar las tablas, abre el archivo con DB Browser for SQLite o utiliza el comando `python ver_base_datos.py` si incluyes ese script.

## Pruebas
```bash
python -m pytest -v
```

## Credenciales de demo
Usuario `admin`; contraseña predeterminada `Demo-2026!`. Solo para entorno local de prueba.

## Funcionalidades
- Registro de reportes ficticios con folio generado mediante UUID.
- Puntuación ponderada explicable y revisión de variables.
- Consulta de estado e historial de seguimiento.
- Panel administrativo con filtros, métricas y exportación CSV.
- Persistencia local con SQL directo mediante `sqlite3`.
- Semilla de cuatro reportes sintéticos cuando la base está vacía.

## Limitaciones
El inicio de sesión es una demostración, no autenticación de producción. La regla de prioridad no es un modelo predictivo validado. No introducir datos personales reales.
