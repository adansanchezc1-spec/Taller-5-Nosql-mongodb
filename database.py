"""
Módulo de Gestión de Conexión a MongoDB (DatabaseManager).
Aplica principios SOLID (SRP), patrones Singleton y Factory, y manejo defensivo de excepciones.
"""

import os
import sys
from typing import Optional, Tuple
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    ConfigurationError,
    PyMongoError,
)

# Cargar variables de entorno desde el archivo .env
load_dotenv()


class DatabaseManager:
    """
    Gestor centralizado de la conexión a MongoDB.
    Garantiza una única instancia de conexión (Singleton) y administra
    el ciclo de vida del cliente de base de datos.
    """

    _instance: Optional["DatabaseManager"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    _is_mock: bool = False

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_connection_params(cls) -> Tuple[str, str, int, bool]:
        """Obtiene y valida los parámetros de conexión desde variables de entorno."""
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGO_DB_NAME", "techcare_db")
        timeout_ms = int(os.getenv("MONGO_TIMEOUT_MS", "3000"))
        use_mock_fallback = os.getenv("USE_MOCK_FALLBACK", "true").lower() in ("true", "1", "yes")
        return mongo_uri, db_name, timeout_ms, use_mock_fallback

    def connect(self, custom_uri: Optional[str] = None, force_mock: bool = False) -> Database:
        """
        Establece la conexión con el servidor MongoDB o activa el fallback seguro.
        
        Args:
            custom_uri: URI opcional para pruebas de desconexión o endpoints alternativos.
            force_mock: Si es True, fuerza el uso de mongomock.
            
        Returns:
            Instancia de Database de MongoDB.
            
        Raises:
            ConnectionFailure: Si no es posible conectar y no está activo el fallback.
        """
        if force_mock:
            return self._init_mock("Modo Simulación (Mock) forzado para pruebas unitarias.")

        uri, db_name, timeout_ms, use_mock = self.get_connection_params()
        target_uri = custom_uri or uri

        try:
            print(f"[CONEXIÓN] Intentando conectar a MongoDB en: {self._mask_uri(target_uri)} ...")
            client = MongoClient(
                target_uri,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
            )
            # Verificación activa con comando ping (falla rápido si el servidor no responde)
            try:
                client.admin.command("ping")
            except Exception:
                client.close()
                raise
            self._client = client
            self._db = client[db_name]
            self._is_mock = False
            print(f"[CONEXIÓN EXITOSA] Conectado a MongoDB Server real. Base de datos activa: '{db_name}'.")
            return self._db

        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            print(f"[ALERTA DE CONEXIÓN] No se pudo conectar al servidor MongoDB: {err}")
            if use_mock and not custom_uri:
                return self._init_mock(
                    "Servidor local/Atlas no disponible. Activando 'mongomock' "
                    "para demostración académica continua sin interrupciones."
                )
            raise ConnectionFailure(
                f"Error crítico al conectar a MongoDB ({target_uri}): {err}"
            ) from err

        except ConfigurationError as err:
            print(f"[ERROR DE CONFIGURACIÓN] Cadena URI no válida: {err}")
            raise

        except PyMongoError as err:
            print(f"[ERROR PYMONGO INESPERADO] {err}")
            raise

    def _init_mock(self, reason: str) -> Database:
        """Inicializa un cliente en memoria mongomock para contingencia académica."""
        import mongomock

        _, db_name, _, _ = self.get_connection_params()
        print(f"[MODO CONTINGENCIA] {reason}")
        self._client = mongomock.MongoClient()
        self._db = self._client[db_name]
        self._is_mock = True
        return self._db

    def get_database(self) -> Database:
        """Retorna la base de datos activa. Si no está conectada, inicia la conexión."""
        if self._db is None:
            return self.connect()
        return self._db

    def is_mock_active(self) -> bool:
        """Indica si el gestor está operando sobre el motor mock en memoria."""
        return self._is_mock

    @property
    def is_mock(self) -> bool:
        """Propiedad para verificar si está activo el modo mock."""
        return self._is_mock

    def close(self) -> None:
        """Cierra de forma controlada y segura la conexión con el servidor MongoDB."""
        if self._client is not None:
            try:
                self._client.close()
                print("[CONEXIÓN] Conexión con MongoDB cerrada exitosamente.")
            except Exception as e:
                print(f"[ERROR AL CERRAR] Error cerrando el cliente de MongoDB: {e}")
            finally:
                self._client = None
                self._db = None
                self._is_mock = False

    @staticmethod
    def _mask_uri(uri: str) -> str:
        """Enmascara credenciales en la URI para trazabilidad y seguridad en logs."""
        if "@" in uri:
            prefix = uri.split("@")[0]
            suffix = uri.split("@")[1]
            if "://" in prefix:
                proto, credentials = prefix.split("://")
                return f"{proto}://*****:*****@{suffix}"
        return uri
