# Configurar en Windows

1. Instala Python 3.11+, Docker Desktop y Ollama.
2. Ejecuta `docker compose up -d postgres`.
3. Ejecuta `py -3.12 iniciar.py --demo`.
4. Ejecuta `ollama pull qwen2.5:3b` para generar conclusiones.
5. Carga el corpus siguiendo [Base de datos normativa](BASE_DE_DATOS_NORMATIVA.md).

Si ya existía `backend/.env`, confirma que `DATABASE_URL` apunte a PostgreSQL. Las claves no deben
subirse a Git. Para comprobar la instalación usa `.\.venv\Scripts\python.exe scripts\check_ai.py`.
