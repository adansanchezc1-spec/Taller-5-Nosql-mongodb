"""
Módulo de Operaciones CRUD en MongoDB (CrudMaster).
Cumple con principios SOLID (SRP, OCP, DIP), Clean Code y estándares PEP 8.
Gestiona las colecciones 'clientes' y 'ordenes_servicio' mediante consultas atómicas,
operadores de actualización ($set, $push, $inc) y validaciones de integridad referencial.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
try:
    from bson import ObjectId
except ImportError:
    class ObjectId(str):  # type: ignore
        pass
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from database import DatabaseManager


class CrudMaster:
    """
    Controlador de operaciones CRUD sobre las colecciones del sistema de servicio técnico.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Inicializa las referencias a colecciones de MongoDB.
        Inyección de dependencias para permitir testing con mocks o base de datos real.
        """
        self.db_manager = db_manager or DatabaseManager()
        self.db = self.db_manager.get_database()
        self.col_clientes: Collection = self.db["clientes"]
        self.col_ordenes: Collection = self.db["ordenes_servicio"]

    # =========================================================================
    # 1. OPERACIONES DE CREACIÓN (CREATE)
    # =========================================================================

    def create_cliente(self, cliente_data: Dict[str, Any]) -> Optional[str]:
        """
        Inserta un nuevo cliente en la colección 'clientes'.
        
        Args:
            cliente_data: Diccionario con datos del cliente y equipos embebidos.
            
        Returns:
            ID del documento insertado en formato String.
        """
        try:
            # Validar unicidad de identificación
            ident = cliente_data.get("identificacion")
            if not ident:
                raise ValueError("El campo 'identificacion' es obligatorio para crear un cliente.")

            existente = self.col_clientes.find_one({"identificacion": ident})
            if existente:
                print(f"[CREATE OMITIDO] El cliente con identificación '{ident}' ya se encuentra registrado.")
                return str(existente["_id"])

            resultado = self.col_clientes.insert_one(cliente_data)
            doc_id = str(resultado.inserted_id)
            print(f"[CREATE CLIENTE ÉXITO] Cliente '{cliente_data.get('nombre_completo')}' insertado con _id: {doc_id}")
            return doc_id
        except PyMongoError as err:
            print(f"[ERROR PYMONGO AL INSERTAR CLIENTE] {err}")
            return None

    def create_clientes_bulk(self, lista_clientes: List[Dict[str, Any]]) -> List[str]:
        """Inserta múltiples documentos de clientes por lote."""
        ids_insertados = []
        try:
            # Filtrar los que no existan previamente
            clientes_a_insertar = []
            for cli in lista_clientes:
                ident = cli.get("identificacion")
                if ident and not self.col_clientes.find_one({"identificacion": ident}):
                    clientes_a_insertar.append(cli)

            if clientes_a_insertar:
                res = self.col_clientes.insert_many(clientes_a_insertar)
                ids_insertados = [str(_id) for _id in res.inserted_ids]
                print(f"[CREATE BULK CLIENTES] {len(ids_insertados)} clientes insertados con éxito.")
            else:
                print("[CREATE BULK CLIENTES] Todos los clientes ya existían previamente.")
            return ids_insertados
        except PyMongoError as err:
            print(f"[ERROR PYMONGO EN INSERCIÓN MASIVA DE CLIENTES] {err}")
            return []

    def create_orden(self, orden_data: Dict[str, Any]) -> Optional[str]:
        """
        Inserta una nueva orden de servicio con documentos embebidos y referencia a cliente.
        """
        try:
            codigo = orden_data.get("codigo_orden")
            if not codigo:
                raise ValueError("El campo 'codigo_orden' es obligatorio.")

            existente = self.col_ordenes.find_one({"codigo_orden": codigo})
            if existente:
                print(f"[CREATE OMITIDO] La orden '{codigo}' ya existe en la base de datos.")
                return str(existente["_id"])

            # Validar integridad referencial con el cliente
            cli_id = orden_data.get("cliente_identificacion")
            if cli_id and not self.col_clientes.find_one({"identificacion": cli_id}):
                print(f"[ADVERTENCIA] La orden referencia al cliente '{cli_id}', que aún no existe en 'clientes'.")

            # Garantizar timestamp de fecha si no está presente
            if "fecha_ingreso" not in orden_data:
                orden_data["fecha_ingreso"] = datetime.now(timezone.utc).isoformat()

            res = self.col_ordenes.insert_one(orden_data)
            doc_id = str(res.inserted_id)
            print(f"[CREATE ORDEN ÉXITO] Orden '{codigo}' creada correctamente con _id: {doc_id}")
            return doc_id
        except PyMongoError as err:
            print(f"[ERROR PYMONGO AL CREAR ORDEN] {err}")
            return None

    def create_ordenes_bulk(self, lista_ordenes: List[Dict[str, Any]]) -> List[str]:
        """Inserta múltiples órdenes de servicio por lote."""
        try:
            ordenes_nuevas = []
            for ord_doc in lista_ordenes:
                codigo = ord_doc.get("codigo_orden")
                if codigo and not self.col_ordenes.find_one({"codigo_orden": codigo}):
                    ordenes_nuevas.append(ord_doc)

            if ordenes_nuevas:
                res = self.col_ordenes.insert_many(ordenes_nuevas)
                ids = [str(_id) for _id in res.inserted_ids]
                print(f"[CREATE BULK ÓRDENES] {len(ids)} órdenes insertadas exitosamente.")
                return ids
            print("[CREATE BULK ÓRDENES] Las órdenes ya existían previamente.")
            return []
        except PyMongoError as err:
            print(f"[ERROR PYMONGO EN INSERCIÓN MASIVA DE ÓRDENES] {err}")
            return []

    # =========================================================================
    # 2. OPERACIONES DE CONSULTA (READ)
    # =========================================================================

    def read_all_clientes(self) -> List[Dict[str, Any]]:
        """Consulta y retorna todos los documentos de la colección 'clientes'."""
        try:
            clientes = list(self.col_clientes.find({}))
            print(f"[READ ALL CLIENTES] Total recuperados: {len(clientes)}")
            return clientes
        except PyMongoError as err:
            print(f"[ERROR PYMONGO EN READ CLIENTES] {err}")
            return []

    def read_all_ordenes(self) -> List[Dict[str, Any]]:
        """Consulta y retorna todas las órdenes de servicio."""
        try:
            ordenes = list(self.col_ordenes.find({}))
            print(f"[READ ALL ÓRDENES] Total recuperadas: {len(ordenes)}")
            return ordenes
        except PyMongoError as err:
            print(f"[ERROR PYMONGO EN READ ÓRDENES] {err}")
            return []

    def read_orden_by_codigo(self, codigo_orden: str) -> Optional[Dict[str, Any]]:
        """Busca una orden específica por su identificador de negocio único."""
        try:
            orden = self.col_ordenes.find_one({"codigo_orden": codigo_orden})
            if orden:
                print(f"[READ ÉXITO] Orden encontrada: {codigo_orden}")
            else:
                print(f"[READ] No se encontró ninguna orden con el código: {codigo_orden}")
            return orden
        except PyMongoError as err:
            print(f"[ERROR PYMONGO EN BÚSQUEDA DE ORDEN] {err}")
            return None

    def read_ordenes_by_filtro(self, filtro: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Realiza consultas avanzadas mediante filtros y operadores de MongoDB
        (ej: {'estado': 'EN_REPARACION'}, {'costo_total': {'$gte': 100000}}).
        """
        try:
            resultados = list(self.col_ordenes.find(filtro))
            print(f"[READ CON FILTRO] Criterio {filtro} -> Resultados encontrados: {len(resultados)}")
            return resultados
        except PyMongoError as err:
            print(f"[ERROR PYMONGO EN FILTRO DE ÓRDENES] {err}")
            return []

    # =========================================================================
    # 3. OPERACIONES DE ACTUALIZACIÓN (UPDATE)
    # =========================================================================

    def update_orden_estado(
        self,
        codigo_orden: str,
        nuevo_estado: str,
        responsable: str,
        nota: str = ""
    ) -> bool:
        """
        Actualiza el estado de una orden seleccionada y registra la trazabilidad
        atómica en su lista embebida 'historial_estados' mediante $push y $set.
        """
        try:
            nuevo_evento = {
                "estado": nuevo_estado,
                "fecha": datetime.now(timezone.utc).isoformat(),
                "responsable": responsable,
                "nota": nota
            }
            resultado = self.col_ordenes.update_one(
                {"codigo_orden": codigo_orden},
                {
                    "$set": {"estado": nuevo_estado},
                    "$push": {"historial_estados": nuevo_evento}
                }
            )
            if resultado.matched_count == 0:
                print(f"[UPDATE FALLIDO] No se encontró la orden '{codigo_orden}' para actualizar.")
                return False

            print(
                f"[UPDATE ÉXITO] Orden '{codigo_orden}' actualizada al estado '{nuevo_estado}' "
                f"con evento registrado en historial_estados."
            )
            return True
        except PyMongoError as err:
            print(f"[ERROR PYMONGO AL ACTUALIZAR ESTADO DE ORDEN] {err}")
            return False

    def add_repuesto_to_orden(
        self,
        codigo_orden: str,
        repuesto: Dict[str, Any]
    ) -> bool:
        """
        Agrega un nuevo repuesto o servicio a la lista embebida 'repuestos_utilizados'
        e incrementa atómicamente el 'costo_total' utilizando los operadores $push e $inc.
        """
        try:
            subtotal = repuesto.get("subtotal", 0.0)
            if subtotal <= 0:
                subtotal = repuesto.get("cantidad", 1) * repuesto.get("precio_unitario", 0.0)
                repuesto["subtotal"] = subtotal

            resultado = self.col_ordenes.update_one(
                {"codigo_orden": codigo_orden},
                {
                    "$push": {"repuestos_utilizados": repuesto},
                    "$inc": {"costo_total": subtotal}
                }
            )
            if resultado.matched_count == 0:
                print(f"[UPDATE FALLIDO] Orden '{codigo_orden}' no encontrada para agregar repuesto.")
                return False

            print(
                f"[UPDATE ÉXITO] Repuesto '{repuesto.get('descripcion')}' agregado a la orden '{codigo_orden}'. "
                f"Costo total incrementado en ${subtotal:,.2f}."
            )
            return True
        except PyMongoError as err:
            print(f"[ERROR PYMONGO AL AGREGAR REPUESTO] {err}")
            return False

    def update_cliente_contacto(
        self,
        identificacion: str,
        nuevo_telefono: Optional[str] = None,
        nuevo_email: Optional[str] = None
    ) -> bool:
        """Actualiza campos embebidos en el subdocumento 'contacto' del cliente."""
        try:
            update_fields = {}
            if nuevo_telefono:
                update_fields["contacto.telefono"] = nuevo_telefono
            if nuevo_email:
                update_fields["contacto.email"] = nuevo_email

            if not update_fields:
                print("[UPDATE OMITIDO] No se suministraron campos de contacto para modificar.")
                return False

            res = self.col_clientes.update_one(
                {"identificacion": identificacion},
                {"$set": update_fields}
            )
            if res.matched_count == 0:
                print(f"[UPDATE FALLIDO] Cliente '{identificacion}' no encontrado.")
                return False

            print(f"[UPDATE CLIENTE ÉXITO] Contacto de '{identificacion}' actualizado correctamente.")
            return True
        except PyMongoError as err:
            print(f"[ERROR PYMONGO AL ACTUALIZAR CLIENTE] {err}")
            return False

    # =========================================================================
    # 4. OPERACIONES DE ELIMINACIÓN (DELETE)
    # =========================================================================

    def delete_orden_by_codigo(self, codigo_orden: str) -> bool:
        """
        Elimina un documento de prueba de forma controlada mediante un criterio de búsqueda específico.
        No ejecuta eliminaciones masivas destructivas sobre la colección.
        """
        try:
            # Validación previa de existencia
            existente = self.col_ordenes.find_one({"codigo_orden": codigo_orden})
            if not existente:
                print(f"[DELETE CONTROLADO] La orden '{codigo_orden}' no existe. Ningún registro afectado.")
                return False

            resultado = self.col_ordenes.delete_one({"codigo_orden": codigo_orden})
            if resultado.deleted_count > 0:
                print(f"[DELETE ÉXITO] Orden de prueba '{codigo_orden}' eliminada de forma controlada y segura.")
                return True
            return False
        except PyMongoError as err:
            print(f"[ERROR PYMONGO AL ELIMINAR ORDEN] {err}")
            return False

    # =========================================================================
    # 5. AGREGACIONES Y ANÁLISIS (BONUS NOSQL)
    # =========================================================================

    def get_metricas_ordenes(self) -> List[Dict[str, Any]]:
        """
        Ejecuta un pipeline de agregación para calcular métricas por estado:
        Total de órdenes, costo promedio y recaudación acumulada.
        Demuestra la potencia del motor de agregación de MongoDB.
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$estado",
                    "total_ordenes": {"$sum": 1},
                    "costo_acumulado": {"$sum": "$costo_total"},
                    "costo_promedio": {"$avg": "$costo_total"}
                }
            },
            {"$sort": {"total_ordenes": -1}}
        ]
        try:
            return list(self.col_ordenes.aggregate(pipeline))
        except PyMongoError as err:
            print(f"[ERROR EN AGREGACIÓN] {err}")
            return []

    # =========================================================================
    # MÉTODOS BASE COMPATIBLES CON LA PLANTILLA INICIAL
    # =========================================================================

    def create(self, data: Dict[str, Any], tipo: str = "orden") -> Optional[str]:
        """Interfaz polimórfica para creación de documentos."""
        if tipo == "cliente":
            return self.create_cliente(data)
        return self.create_orden(data)

    def read(self, filtro: Optional[Dict[str, Any]] = None, tipo: str = "orden") -> List[Dict[str, Any]]:
        """Interfaz polimórfica para consulta de documentos."""
        if tipo == "cliente":
            return list(self.col_clientes.find(filtro or {}))
        return list(self.col_ordenes.find(filtro or {}))

    def update(self, codigo_orden: str, nuevo_estado: str, responsable: str = "Sistema") -> bool:
        """Interfaz polimórfica para actualización de estado."""
        return self.update_orden_estado(codigo_orden, nuevo_estado, responsable)

    def delete(self, codigo_orden: str) -> bool:
        """Interfaz polimórfica para eliminación controlada."""
        return self.delete_orden_by_codigo(codigo_orden)