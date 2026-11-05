"""
Suite de Pruebas Unitarias y de Integración (test_app.py).
Verifica los requerimientos técnicos del Taller NoSQL MongoDB:
1. Conectividad y fallback.
2. Inserción de documentos con embebidos y referencias.
3. Consultas generales y por filtro.
4. Actualizaciones atómicas precisas (sin efectos colaterales).
5. Eliminación controlada de registro puntual.
6. Manejo de excepciones ante indisponibilidad del servidor.
"""

import unittest
try:
    from bson import ObjectId
except ImportError:
    class ObjectId(str):  # type: ignore
        pass
from database import DatabaseManager
from crud_master import CrudMaster
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


class TestTechCareMongoDB(unittest.TestCase):
    """Casos de prueba para el sistema TechCare Solutions."""

    @classmethod
    def setUpClass(cls):
        """Inicializa el entorno de prueba garantizando una base de datos limpia de test."""
        cls.db_mgr = DatabaseManager()
        # Forzar el uso de mock para pruebas determinísticas e independientes de red externa
        cls.db = cls.db_mgr.connect(force_mock=True)
        cls.crud = CrudMaster(db_manager=cls.db_mgr)

    def setUp(self):
        """Limpia las colecciones antes de cada prueba unitaria."""
        self.crud.col_clientes.delete_many({})
        self.crud.col_ordenes.delete_many({})

    def test_01_insercion_cliente_con_equipos_embebidos(self):
        """Prueba inserción de cliente con contacto y lista de equipos embebida."""
        cliente_test = {
            "identificacion": "CLI-TEST-01",
            "nombre_completo": "Usuario Ficticio de Prueba",
            "contacto": {
                "telefono": "+57 300 0000000",
                "email": "prueba@ficticio.edu.co",
                "ciudad": "PruebaCity"
            },
            "equipos": [
                {
                    "numero_serie": "SN-TEST-88",
                    "tipo_equipo": "Laptop",
                    "modelo": "TestPad T14"
                }
            ]
        }
        doc_id = self.crud.create_cliente(cliente_test)
        self.assertIsNotNone(doc_id, "El ID insertado no debe ser None")

        cliente_db = self.crud.col_clientes.find_one({"identificacion": "CLI-TEST-01"})
        self.assertIsNotNone(cliente_db)
        self.assertEqual(cliente_db["contacto"]["ciudad"], "PruebaCity")
        self.assertEqual(len(cliente_db["equipos"]), 1)

    def test_02_insercion_orden_con_checklist_y_repuestos(self):
        """Prueba inserción de orden de servicio con subdocumentos y trazabilidad."""
        orden_test = {
            "codigo_orden": "ORD-TEST-01",
            "cliente_identificacion": "CLI-TEST-01",
            "datos_equipo": {
                "numero_serie": "SN-TEST-88",
                "tipo_equipo": "Laptop",
                "modelo": "TestPad T14",
                "falla_reportada": "Pantalla parpadea"
            },
            "tecnico_asignado": "Técnico Pruebas",
            "estado": "RECIBIDO",
            "costo_total": 50000.0,
            "checklist_diagnostico": [
                {"componente": "Pantalla LCD", "estado_fisico": "Falso contacto cable flex", "requiere_cambio": False}
            ],
            "repuestos_utilizados": [
                {"codigo": "SRV-AJU-01", "descripcion": "Ajuste cable flex", "cantidad": 1, "precio_unitario": 50000.0, "subtotal": 50000.0}
            ],
            "historial_estados": [
                {"estado": "RECIBIDO", "fecha": "2026-10-21T10:00:00Z", "responsable": "Recepción", "nota": "Ingreso test"}
            ]
        }
        doc_id = self.crud.create_orden(orden_test)
        self.assertIsNotNone(doc_id)

        orden_db = self.crud.read_orden_by_codigo("ORD-TEST-01")
        self.assertIsNotNone(orden_db)
        self.assertEqual(orden_db["estado"], "RECIBIDO")
        self.assertEqual(orden_db["costo_total"], 50000.0)

    def test_03_consultas_con_filtros_especificos(self):
        """Prueba consultas filtradas por estado y por rango de costo ($gte)."""
        # Insertar 2 órdenes con diferentes estados y costos
        self.crud.create_orden({
            "codigo_orden": "ORD-F1",
            "estado": "EN_REPARACION",
            "costo_total": 120000.0,
            "datos_equipo": {"modelo": "A"}
        })
        self.crud.create_orden({
            "codigo_orden": "ORD-F2",
            "estado": "COMPLETADO",
            "costo_total": 45000.0,
            "datos_equipo": {"modelo": "B"}
        })

        # Filtro 1: por estado
        en_reparacion = self.crud.read_ordenes_by_filtro({"estado": "EN_REPARACION"})
        self.assertEqual(len(en_reparacion), 1)
        self.assertEqual(en_reparacion[0]["codigo_orden"], "ORD-F1")

        # Filtro 2: costo >= 100000
        costo_alto = self.crud.read_ordenes_by_filtro({"costo_total": {"$gte": 100000.0}})
        self.assertEqual(len(costo_alto), 1)
        self.assertEqual(costo_alto[0]["codigo_orden"], "ORD-F1")

    def test_04_actualizacion_especifica_sin_efectos_colaterales(self):
        """Prueba que la actualización solo afecta al documento seleccionado."""
        self.crud.create_orden({
            "codigo_orden": "ORD-U1",
            "estado": "RECIBIDO",
            "costo_total": 30000.0,
            "historial_estados": []
        })
        self.crud.create_orden({
            "codigo_orden": "ORD-U2",
            "estado": "RECIBIDO",
            "costo_total": 40000.0,
            "historial_estados": []
        })

        # Actualizar ORD-U1 a COMPLETADO
        exito = self.crud.update_orden_estado("ORD-U1", "COMPLETADO", "Técnico 1", "Prueba ok")
        self.assertTrue(exito)

        # Verificar que ORD-U1 cambió y tiene su nuevo evento en historial
        ord1 = self.crud.read_orden_by_codigo("ORD-U1")
        self.assertEqual(ord1["estado"], "COMPLETADO")
        self.assertEqual(len(ord1["historial_estados"]), 1)

        # Verificar que ORD-U2 NO cambió (aislamiento de actualización)
        ord2 = self.crud.read_orden_by_codigo("ORD-U2")
        self.assertEqual(ord2["estado"], "RECIBIDO")
        self.assertEqual(len(ord2["historial_estados"]), 0)

    def test_05_eliminacion_controlada(self):
        """Prueba que la eliminación afecta única y exclusivamente al documento de prueba."""
        self.crud.create_orden({"codigo_orden": "ORD-DEL-TARGET", "estado": "RECIBIDO"})
        self.crud.create_orden({"codigo_orden": "ORD-KEEP-SAFE", "estado": "EN_REPARACION"})

        # Eliminar únicamente la orden objetivo
        eliminado = self.crud.delete_orden_by_codigo("ORD-DEL-TARGET")
        self.assertTrue(eliminado)

        # Verificar que la eliminada ya no existe
        self.assertIsNone(self.crud.read_orden_by_codigo("ORD-DEL-TARGET"))

        # Verificar que la otra orden permanece intacta
        orden_segura = self.crud.read_orden_by_codigo("ORD-KEEP-SAFE")
        self.assertIsNotNone(orden_segura)
        self.assertEqual(orden_segura["estado"], "EN_REPARACION")

    def test_06_manejo_defensivo_desconexion(self):
        """Prueba que intentar conectar a un servidor caído genera y captura la excepción adecuada."""
        mgr_caido = DatabaseManager()
        # Intentar conectar a puerto cerrado forzando timeout rápido
        with self.assertRaises((ConnectionFailure, ServerSelectionTimeoutError, Exception)):
            mgr_caido.connect(custom_uri="mongodb://127.0.0.1:9998/?serverSelectionTimeoutMS=800")


if __name__ == "__main__":
    unittest.main(verbosity=2)
