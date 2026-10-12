"""Instancias de extensiones, creadas sin app para evitar imports circulares."""
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
cors = CORS()
