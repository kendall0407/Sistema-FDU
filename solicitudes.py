from decimal import Decimal, InvalidOperation
from conexion import ObtenerConexion
import pyodbc

# Ids del catálogo EstadoSolicitud
ESTADO_REGISTRADA = 1
ESTADO_INFO_ADICIONAL = 2
ESTADO_ELIMINADA = 3

# Estados que permiten cada operación
ESTADOS_MODIFICABLES = (ESTADO_REGISTRADA, ESTADO_INFO_ADICIONAL)
ESTADOS_ELIMINABLES = (ESTADO_REGISTRADA,)
ESTADOS_EVALUABLES = (ESTADO_REGISTRADA,)

# Columnas que la persona solicitante ingresa (todas obligatorias).
# Los nombres coinciden con las columnas de la tabla Solicitudes.
CAMPOS = (
    "NombreSolicitante",
    "Carne",
    "CorreoElectronico",
    "NumeroCelular",
    "rol_id",
    "MontoSolicitado",
    "InformacionBancaria",
    "NombreActividad",
    "Justificacion",
    "LineaAccion",
)

# Lectura interna: solo columnas de Solicitudes, con ids (la usan las validaciones)
COLUMNAS_INTERNAS = (
    "IdSolicitud, usuario_id, estado_id, " + ", ".join(CAMPOS)
)

# Lectura para mostrar al usuario: nombres de estado y posición en lugar de ids
SELECT_DETALLE = """
    SELECT s.IdSolicitud, s.usuario_id,
           s.NombreSolicitante, s.Carne, s.CorreoElectronico,
           s.NumeroCelular, r.nombre AS rol, s.MontoSolicitado,
           s.InformacionBancaria, s.NombreActividad, s.Justificacion,
           s.LineaAccion, e.nombre AS estado, s.observaciones,
           s.fecha_creacion, s.fecha_modificacion
    FROM Solicitudes s
    JOIN Rol r ON r.id = s.rol_id
    JOIN EstadoSolicitud e ON e.id = s.estado_id
"""

ESTADO_ACTIVO = 1  # Mismo valor que en el módulo de usuarios

# Roles (mismos ids que en el módulo de usuarios)
ROL_ESTUDIANTE = 1
ROL_ESTUDIANTE_GRADUADO = 2
ROL_MIEMBRO_COMITE = 3
ROL_ASISTENTE_CIC = 4
ROL_ADMINISTRATIVO = 5

# Roles permitidos por función
ROLES_CREAR = {ROL_ESTUDIANTE, ROL_ESTUDIANTE_GRADUADO, ROL_ADMINISTRATIVO}
ROLES_STAFF = {ROL_MIEMBRO_COMITE, ROL_ASISTENTE_CIC, ROL_ADMINISTRATIVO}
ROLES_SOLO_PROPIAS = {ROL_ESTUDIANTE, ROL_ESTUDIANTE_GRADUADO}


def _ObtenerRol(cursor, correo):
    if not correo:
        return None

    cursor.execute(
        "SELECT rol_id FROM Usuario WHERE correo = ? AND estado_id = ? AND bloqueado = 0",
        (correo, ESTADO_ACTIVO)
    )
    fila = cursor.fetchone()
    return fila[0] if fila else None


def _PuedeGestionarSolicitud(rol, propietario_id, usuario_id):
    if rol in ROLES_STAFF:
        return True
    if rol in ROLES_SOLO_PROPIAS:
        return propietario_id == usuario_id
    return False

def _Mapear(cursor, filas):
    columnas = [columna[0] for columna in cursor.description]
    return [dict(zip(columnas, fila)) for fila in filas]


def _ValidarDatos(cursor, datos):
    faltantes = [campo for campo in CAMPOS if datos.get(campo) in (None, "")]
    if faltantes:
        return False, "Los campos obligatorios deben completarse: " + ", ".join(faltantes)

    if "@" not in str(datos["CorreoElectronico"]):
        return False, "El correo no es válido"

    cursor.execute("SELECT id FROM Rol WHERE id = ?", (datos["rol_id"],))
    if cursor.fetchone() is None:
        return False, "La posición seleccionada no existe"

    try:
        monto = Decimal(str(datos["MontoSolicitado"]))
    except InvalidOperation:
        return False, "El monto solicitado no es válido"

    if monto <= 0:
        return False, "El monto solicitado debe ser mayor que cero"

    cursor.execute(
        "SELECT MontoMaximo FROM LineaAccion WHERE IdLineaAccion = ?",
        (datos["LineaAccion"],)
    )
    linea = cursor.fetchone()

    if linea is None:
        return False, "La línea de acción seleccionada no existe"

    if monto > linea[0]:
        return False, f"El monto solicitado supera el máximo de la línea de acción (₡{linea[0]:,.2f})"

    return True, ""



def CrearSolicitud(usuario_id, monto, informacion_bancaria,
                   nombre_actividad, justificacion, linea_accion):

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        # 1. Obtener los datos del usuario autenticado
        cursor.execute(
            """
            SELECT nombre, apellidos, identificacion,
                   correo, telefono, rol_id
            FROM Usuario
            WHERE id = ?
              AND estado_id = 1
              AND bloqueado = 0
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        if usuario is None:
            return False, "Usuario no encontrado o inactivo"

        nombre_solicitante = f"{usuario[0]} {usuario[1]}"
        carne = usuario[2]
        correo = usuario[3]
        celular = usuario[4]
        rol_id = usuario[5]

        # 2. Verificar permisos del usuario
        if rol_id not in ROLES_CREAR:
            return False, "No tienes permiso para crear solicitudes"

        # 3. Preparar los datos de la solicitud
        datos = {
            "NombreSolicitante": nombre_solicitante,
            "Carne": carne,
            "CorreoElectronico": correo,
            "NumeroCelular": celular,
            "rol_id": rol_id,
            "MontoSolicitado": monto,
            "InformacionBancaria": informacion_bancaria,
            "NombreActividad": nombre_actividad,
            "Justificacion": justificacion,
            "LineaAccion": linea_accion,
        }

        # 4. Validar los datos de la solicitud
        valido, mensaje = _ValidarDatos(cursor, datos)

        if not valido:
            return False, mensaje

        # 5. Registrar la solicitud en la base de datos
        cursor.execute(
            """
            INSERT INTO Solicitudes
            (
                usuario_id,
                NombreSolicitante,
                Carne,
                CorreoElectronico,
                NumeroCelular,
                MontoSolicitado,
                InformacionBancaria,
                NombreActividad,
                Justificacion,
                LineaAccion,
                estado_id,
                rol_id,
                fecha_creacion
            )
            OUTPUT INSERTED.IdSolicitud
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSDATETIME())
            """,
            (
                usuario_id,
                nombre_solicitante,
                carne,
                correo,
                celular,
                monto,
                informacion_bancaria,
                nombre_actividad,
                justificacion,
                linea_accion,
                ESTADO_REGISTRADA,
                rol_id
            )
        )

        id_nuevo = cursor.fetchone()[0]

        conexion.commit()

        return True, id_nuevo

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al crear la solicitud: {error}"

    finally:
        cursor.close()
        conexion.close()



def BuscarSolicitudes(criterio, correo_solicitante):
    if not criterio:
        return False, "Debe indicar un identificador o nombre de solicitante"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        rol = _ObtenerRol(cursor, correo_solicitante)
        if rol not in ROLES_STAFF:
            return False, "No tienes permiso para buscar solicitudes"

        if str(criterio).isdigit():
            cursor.execute(
                SELECT_DETALLE + " WHERE s.IdSolicitud = ? ORDER BY s.IdSolicitud",
                (int(criterio),)
            )
        else:
            cursor.execute(
                SELECT_DETALLE + " WHERE s.NombreSolicitante LIKE ? ORDER BY s.IdSolicitud",
                (f"%{criterio}%",)
            )

        filas = cursor.fetchall()

        if not filas:
            return False, "No se encontraron solicitudes que coincidan con la búsqueda"

        return True, _Mapear(cursor, filas)

    except pyodbc.Error as error:
        return False, f"Error al buscar solicitudes: {error}"

    finally:
        cursor.close()
        conexion.close()

def ModificarSolicitud(id_solicitud, usuario_id, cambios, correo_solicitante):
    if not cambios:
        return False, "No hay campos para actualizar"

    no_editables = [campo for campo in cambios if campo not in CAMPOS]
    if no_editables:
        return False, "Campos no editables: " + ", ".join(no_editables)

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            f"SELECT {COLUMNAS_INTERNAS} FROM Solicitudes WHERE IdSolicitud = ?",
            (id_solicitud,)
        )
        fila = cursor.fetchone()

        if fila is None:
            return False, "Solicitud no encontrada"

        actual = _Mapear(cursor, [fila])[0]

        rol = _ObtenerRol(cursor, correo_solicitante)
        if not _PuedeGestionarSolicitud(rol, actual["usuario_id"], usuario_id):
            return False, "No tiene permisos para modificar esta solicitud"

        if actual["estado_id"] not in ESTADOS_MODIFICABLES:
            return False, "La solicitud no puede modificarse en su estado actual"

        # Se valida la solicitud completa tal como quedaría después del cambio
        datos = {campo: actual[campo] for campo in CAMPOS}
        datos.update(cambios)

        valido, mensaje = _ValidarDatos(cursor, datos)
        if not valido:
            return False, mensaje

        # Si el Comité había pedido información adicional y ya se completó, vuelve a REGISTRADA
        if actual["estado_id"] == ESTADO_INFO_ADICIONAL:
            nuevo_estado = ESTADO_REGISTRADA
        else:
            nuevo_estado = actual["estado_id"]

        columnas = list(cambios.keys())
        asignaciones = ", ".join(f"{campo} = ?" for campo in columnas)

        cursor.execute(
            f"""
            UPDATE Solicitudes
            SET {asignaciones},
                estado_id = ?,
                fecha_modificacion = SYSDATETIME()
            WHERE IdSolicitud = ?
            """,
            [cambios[campo] for campo in columnas] + [nuevo_estado, id_solicitud]
        )

        conexion.commit()
        return True, "Solicitud modificada correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al modificar la solicitud: {error}"

    finally:
        cursor.close()
        conexion.close()


def EliminarSolicitud(id_solicitud, usuario_id, correo_solicitante):
    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            "SELECT usuario_id, estado_id FROM Solicitudes WHERE IdSolicitud = ?",
            (id_solicitud,)
        )
        fila = cursor.fetchone()

        if fila is None:
            return False, "Solicitud no encontrada"

        propietario_id, estado_id = fila

        rol = _ObtenerRol(cursor, correo_solicitante)
        if not _PuedeGestionarSolicitud(rol, propietario_id, usuario_id):
            return False, "No tiene permisos para eliminar esta solicitud"

        if estado_id not in ESTADOS_ELIMINABLES:
            return False, "La solicitud no puede eliminarse en su estado actual"

        # Baja lógica: la solicitud se conserva con estado ELIMINADA
        cursor.execute(
            """
            UPDATE Solicitudes
            SET estado_id = ?,
                fecha_modificacion = SYSDATETIME()
            WHERE IdSolicitud = ?
            """,
            (ESTADO_ELIMINADA, id_solicitud)
        )

        conexion.commit()
        return True, "Solicitud eliminada correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al eliminar la solicitud: {error}"

    finally:
        cursor.close()
        conexion.close()


def PedirInformacionAdicional(id_solicitud, observaciones, correo_solicitante):
    if not observaciones or not observaciones.strip():
        return False, "Debe indicar qué información debe agregarse, corregirse o completarse"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        rol = _ObtenerRol(cursor, correo_solicitante)
        if rol not in ROLES_STAFF:
            return False, "No tienes permiso para pedir información adicional"

        cursor.execute(
            "SELECT estado_id FROM Solicitudes WHERE IdSolicitud = ?",
            (id_solicitud,)
        )
        fila = cursor.fetchone()

        if fila is None:
            return False, "Solicitud no encontrada"

        if fila[0] not in ESTADOS_EVALUABLES:
            return False, "No se puede pedir información adicional en el estado actual"

        cursor.execute(
            """
            UPDATE Solicitudes
            SET estado_id = ?,
                observaciones = ?,
                fecha_modificacion = SYSDATETIME()
            WHERE IdSolicitud = ?
            """,
            (ESTADO_INFO_ADICIONAL, observaciones.strip(), id_solicitud)
        )

        conexion.commit()
        return True, "Se solicitó información adicional correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al solicitar información adicional: {error}"

    finally:
        cursor.close()
        conexion.close()