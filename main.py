"""
Punto de Entrada Principal (main.py) - Sistema TechCare Solutions.
Implementa interfaz de consola interactiva y suite de pruebas demostrativas automáticas
para verificar la conexión, inserciones, lecturas filtradas, actualizaciones atómicas,
eliminación controlada y cierre seguro de conexión con MongoDB.
"""

import json
import os
import sys
from typing import Any, Dict
from bson import json_util

from database import DatabaseManager
from crud_master import CrudMaster


def cargar_datos_semilla() -> Dict[str, Any]:
    """Carga los datos iniciales de prueba desde data/seed_data.json."""
    ruta_seed = os.path.join(os.path.dirname(__file__), "data", "seed_data.json")
    if os.path.exists(ruta_seed):
        with open(ruta_seed, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"[ALERTA] Archivo seed no encontrado en: {ruta_seed}")
    return {"clientes": [], "ordenes_servicio": []}


def imprimir_separador(titulo: str = "") -> None:
    """Imprime un encabezado legible para salidas de consola."""
    print("\n" + "=" * 75)
    if titulo:
        print(f" >>> {titulo.upper()} <<<")
        print("=" * 75)


def formatear_documento(doc: Dict[str, Any]) -> str:
    """Serializa un documento BSON/Mongo a JSON legible."""
    return json.dumps(json.loads(json_util.dumps(doc)), indent=2, ensure_ascii=False)


def ejecutar_demostracion_completa(crud: CrudMaster) -> None:
    """
    Ejecuta el ciclo de vida completo de pruebas para validación académica:
    1. Inserción de datos semilla (Clientes y Órdenes con documentos embebidos y referencias).
    2. Consulta de todos los documentos.
    3. Consultas avanzadas con filtros específicos ($gte, estado).
    4. Actualización atómica ($set en estado, $push en historial, $push e $inc en repuestos).
    5. Inserción y eliminación controlada de un documento de prueba específico.
    6. Cálculo de agregaciones analíticas.
    """
    imprimir_separador("Fase 1: Inserción de Datos Ficticios (Create)")
    datos = cargar_datos_semilla()

    print("\n--- 1.1 Inserción de Clientes (con equipos y contacto embebidos) ---")
    crud.create_clientes_bulk(datos.get("clientes", []))

    print("\n--- 1.2 Inserción de Órdenes de Servicio (con checklist, repuestos y trazabilidad) ---")
    crud.create_ordenes_bulk(datos.get("ordenes_servicio", []))

    imprimir_separador("Fase 2: Consultas Generales (Read All)")
    print("\n--- 2.1 Listado de Clientes Registrados ---")
    clientes = crud.read_all_clientes()
    for c in clientes:
        print(f"• ID: {c.get('identificacion')} | Nombre: {c.get('nombre_completo')} | "
              f"Ciudad: {c.get('contacto', {}).get('ciudad')} | Equipos registrados: {len(c.get('equipos', []))}")

    print("\n--- 2.2 Listado General de Órdenes de Servicio ---")
    ordenes = crud.read_all_ordenes()
    for o in ordenes:
        eq = o.get("datos_equipo", {})
        print(f"• Código: {o.get('codigo_orden')} | Estado: {o.get('estado')} | "
              f"Equipo: {eq.get('tipo_equipo')} {eq.get('modelo')} | Costo: ${o.get('costo_total', 0):,.2f}")

    imprimir_separador("Fase 3: Consultas con Filtros Específicos (Read Filtered)")
    print("\n--- 3.1 Filtro por Estado: Órdenes 'EN_REPARACION' ---")
    filtro_reparacion = crud.read_ordenes_by_filtro({"estado": "EN_REPARACION"})
    for o in filtro_reparacion:
        print(f"  -> {o.get('codigo_orden')} | Técnico: {o.get('tecnico_asignado')} | Falla: {o.get('datos_equipo', {}).get('falla_reportada')}")

    print("\n--- 3.2 Filtro por Rango: Costo Total >= $100,000 (Operador $gte) ---")
    filtro_costo = crud.read_ordenes_by_filtro({"costo_total": {"$gte": 100000.0}})
    for o in filtro_costo:
        print(f"  -> {o.get('codigo_orden')} | Costo Total: ${o.get('costo_total'):,.2f}")

    imprimir_separador("Fase 4: Actualización Controlada de Documentos (Update)")
    print("\n--- 4.1 Actualización de Estado con Trazabilidad Atómica ($set y $push) ---")
    codigo_target = "ORD-2026-001"
    crud.update_orden_estado(
        codigo_orden=codigo_target,
        nuevo_estado="COMPLETADO",
        responsable="Ing. Laura Marcela Ríos",
        nota="Mantenimiento preventivo finalizado y pruebas de carga exitosas (CPU Temp max 65°C)."
    )

    print("\n--- 4.2 Incorporación de Nuevo Repuesto y Recálculo Atómico de Costo ($push y $inc) ---")
    nuevo_repuesto = {
        "codigo": "ACC-ALM-01",
        "descripcion": "Pad térmico disipador para unidad NVMe SSD",
        "cantidad": 1,
        "precio_unitario": 20000.0,
        "subtotal": 20000.0
    }
    crud.add_repuesto_to_orden(codigo_target, nuevo_repuesto)

    print(f"\n--- 4.3 Verificación del documento actualizado '{codigo_target}' ---")
    orden_actualizada = crud.read_orden_by_codigo(codigo_target)
    if orden_actualizada:
        print(f"Estado Actual: {orden_actualizada.get('estado')}")
        print(f"Nuevo Costo Total: ${orden_actualizada.get('costo_total'):,.2f}")
        print(f"Eventos en Historial: {len(orden_actualizada.get('historial_estados', []))}")
        print("Último evento registrado:", orden_actualizada.get("historial_estados", [])[-1])

    imprimir_separador("Fase 5: Eliminación Controlada de Registro de Prueba (Delete)")
    print("\n--- 5.1 Creación de Orden Temporal de Prueba ---")
    orden_prueba = {
        "codigo_orden": "ORD-TEST-999",
        "cliente_identificacion": "CLI-1001",
        "datos_equipo": {
            "numero_serie": "SN-TEST-000",
            "tipo_equipo": "Dispositivo de Calibración de Prueba",
            "modelo": "Tester Pro v1",
            "falla_reportada": "Registro transitorio para validar eliminación controlada"
        },
        "tecnico_asignado": "Técnico de Laboratorio",
        "estado": "EN_DIAGNOSTICO",
        "prioridad": "BAJA",
        "checklist_diagnostico": [],
        "repuestos_utilizados": [],
        "costo_total": 0.0,
        "historial_estados": []
    }
    crud.create_orden(orden_prueba)

    print("\n--- 5.2 Verificación de existencia previa ---")
    existe_antes = crud.read_orden_by_codigo("ORD-TEST-999")
    print(f"¿Existe antes de eliminar?: {'SÍ' if existe_antes else 'NO'}")

    print("\n--- 5.3 Ejecución de eliminación puntual mediante criterio específico ---")
    crud.delete_orden_by_codigo("ORD-TEST-999")

    print("\n--- 5.4 Confirmación posterior (no afecta a los datos principales) ---")
    existe_despues = crud.read_orden_by_codigo("ORD-TEST-999")
    print(f"¿Existe después de eliminar?: {'SÍ' if existe_despues else 'NO (Eliminado con éxito)'}")

    imprimir_separador("Fase 6: Agregación Analítica NoSQL (Group & Sum)")
    metricas = crud.get_metricas_ordenes()
    print("Métricas calculadas por estado de orden de servicio:")
    for m in metricas:
        print(f"• Estado: {m['_id']} | Total Órdenes: {m['total_ordenes']} | "
              f"Total Facturado: ${m['costo_acumulado']:,.2f} | Promedio: ${m['costo_promedio']:,.2f}")


def menu_interactivo(crud: CrudMaster, db_mgr: DatabaseManager) -> None:
    """Presenta el menú interactivo para el usuario de consola."""
    while True:
        imprimir_separador("TechCare Solutions - Sistema de Gestión MongoDB")
        print("1. Ejecutar Demostración Completa Automatizada (Recomendado para pruebas)")
        print("2. Consultar todos los Clientes")
        print("3. Consultar todas las Órdenes de Servicio")
        print("4. Buscar Orden por Código")
        print("5. Filtrar Órdenes por Estado")
        print("6. Actualizar Estado de una Orden")
        print("7. Insertar una Orden de Prueba")
        print("8. Eliminar Orden de Prueba por Código")
        print("9. Probar Comportamiento de Desconexión / Error de Servidor")
        print("0. Salir y Cerrar Conexión de forma segura")
        print("=" * 75)

        opcion = input("Seleccione una opción (0-9): ").strip()

        if opcion == "1":
            ejecutar_demostracion_completa(crud)
        elif opcion == "2":
            clientes = crud.read_all_clientes()
            print(f"\n--- Total de Clientes: {len(clientes)} ---")
            for c in clientes:
                print(formatear_documento(c))
        elif opcion == "3":
            ordenes = crud.read_all_ordenes()
            print(f"\n--- Total de Órdenes: {len(ordenes)} ---")
            for o in ordenes:
                print(formatear_documento(o))
        elif opcion == "4":
            codigo = input("Ingrese el código de la orden (ej. ORD-2026-001): ").strip()
            ord_doc = crud.read_orden_by_codigo(codigo)
            if ord_doc:
                print(formatear_documento(ord_doc))
        elif opcion == "5":
            estado = input("Ingrese el estado a filtrar (RECIBIDO, EN_REPARACION, COMPLETADO): ").strip().upper()
            res = crud.read_ordenes_by_filtro({"estado": estado})
            print(f"\nResultados con estado '{estado}': {len(res)}")
            for r in res:
                print(f"• Código: {r.get('codigo_orden')} | Equipo: {r.get('datos_equipo', {}).get('modelo')} | Costo: ${r.get('costo_total'):,.2f}")
        elif opcion == "6":
            codigo = input("Código de la orden a actualizar: ").strip()
            nuevo_est = input("Nuevo estado (RECIBIDO, EN_DIAGNOSTICO, EN_REPARACION, COMPLETADO, ENTREGADO): ").strip().upper()
            resp = input("Nombre del responsable técnico: ").strip() or "Técnico de Turno"
            nota = input("Observación técnica: ").strip() or "Actualización manual desde consola"
            crud.update_orden_estado(codigo, nuevo_est, resp, nota)
        elif opcion == "7":
            codigo = input("Código para la nueva orden de prueba (ej. ORD-PRUEBA-01): ").strip()
            doc_nuevo = {
                "codigo_orden": codigo,
                "cliente_identificacion": "CLI-1001",
                "datos_equipo": {
                    "numero_serie": "SN-MANUAL-01",
                    "tipo_equipo": "Consola / Accesorio",
                    "modelo": "Equipo Ficticio de Prueba",
                    "falla_reportada": "Prueba manual de inserción"
                },
                "tecnico_asignado": "Técnico Manual",
                "estado": "RECIBIDO",
                "costo_total": 0.0,
                "checklist_diagnostico": [],
                "repuestos_utilizados": [],
                "historial_estados": []
            }
            crud.create_orden(doc_nuevo)
        elif opcion == "8":
            codigo = input("Código de la orden a eliminar de forma controlada: ").strip()
            crud.delete_orden_by_codigo(codigo)
        elif opcion == "9":
            probar_desconexion()
        elif opcion == "0":
            print("\nFinalizando aplicación...")
            db_mgr.close()
            print("Sesión terminada. ¡Hasta luego!")
            sys.exit(0)
        else:
            print("[OPCIÓN NO VÁLIDA] Por favor ingrese un número del 0 al 9.")


def probar_desconexion() -> None:
    """
    Prueba el comportamiento defensivo de la aplicación cuando el servidor
    de base de datos no está disponible (Cumple Requerimiento 7).
    """
    imprimir_separador("Prueba de Resiliencia ante Desconexión")
    print("Simulando intento de conexión a un endpoint inexistente (mongodb://127.0.0.1:9999)...")
    try:
        mgr_prueba = DatabaseManager()
        # Forzar conexión a puerto inalcanzable con timeout corto
        mgr_prueba.connect(custom_uri="mongodb://127.0.0.1:9999/?serverSelectionTimeoutMS=1500")
    except Exception as exc:
        print(f"[CAPTURA DE EXCEPCIÓN CONTROLADA] El sistema atrapó exitosamente el fallo sin colapsar:")
        print(f"Tipo de excepción: {type(exc).__name__}")
        print(f"Detalle técnico: {exc}")
        print("[VERIFICACIÓN EXITOSA] El manejo de errores de conexión responde según lo estipulado.")


def main() -> None:
    """Punto de inicio de ejecución."""
    db_mgr = DatabaseManager()
    try:
        db = db_mgr.connect()
        crud = CrudMaster(db_manager=db_mgr)

        # Si se pasa el argumento '--auto', ejecuta directamente la demostración y sale
        if "--auto" in sys.argv:
            print("[MODO AUTOMÁTICO DETECTADO] Ejecutando suite completa de pruebas...")
            ejecutar_demostracion_completa(crud)
            db_mgr.close()
            return

        # Modo interactivo por defecto
        menu_interactivo(crud, db_mgr)

    except KeyboardInterrupt:
        print("\n[INTERRUPCIÓN MANUAL] Cerrando conexión...")
        db_mgr.close()
    except Exception as e:
        print(f"\n[ERROR CRÍTICO EN APLICACIÓN] {e}")
        db_mgr.close()


if __name__ == "__main__":
    main()