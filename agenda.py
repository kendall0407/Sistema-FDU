
from conexion import ObtenerConexion
from sesion import _ObtenerRol, ROLES_GESTIONAR_AGENDA

# Roles
ROL_ESTUDIANTE = 1
ROL_ESTUDIANTE_GRADUADO = 2
ROL_MIEMBRO_COMITE = 3
ROL_ASISTENTE_CIC = 4
ROL_ADMINISTRATIVO = 5

# Roles permitidos
ROLES_GESTIONAR_AGENDA = {
    ROL_ASISTENTE_CIC,
    ROL_ADMINISTRATIVO
}

ROLES_CONSULTAR_AGENDA = {
    ROL_MIEMBRO_COMITE,
    ROL_ASISTENTE_CIC,
    ROL_ADMINISTRATIVO
}

ESTADO_PROGRAMADO = "PROGRAMADO"
ESTADO_CANCELADO = "CANCELADO"


def RegistrarAgendaSesion(id_sesion, id_solicitud, orden, usuario_id, observaciones=None, tema=None):

    conexion = None
    cursor = None

    try:

        # 1. Validar datos obligatorios.
        if not id_sesion or not orden or not usuario_id:
            return False, "Faltan datos obligatorios para registrar el punto de agenda."

        # Debe existir una solicitud o un tema, pero no ambos.
        if id_solicitud is None and (tema is None or not tema.strip()):
            return False, "Debe indicar una solicitud o un tema para el punto de agenda."

        if id_solicitud is not None and tema is not None:
            return False, "Debe indicar una solicitud o un tema, no ambos."

        try:
            id_sesion = int(id_sesion)
            orden = int(orden)

            if id_sesion <= 0 or orden <= 0:
                return False, "El identificador de sesión y el orden deben ser positivos."

            if id_solicitud is not None:
                id_solicitud = int(id_solicitud)

                if id_solicitud <= 0:
                    return False, "El identificador de solicitud debe ser positivo."

        except (ValueError, TypeError):
            return False, "Los identificadores y el orden deben ser números."

        # 2. Conectar con la base de datos.
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 3. Verificar permisos.
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_AGENDA:
            return False, "No tiene permisos para gestionar agendas."

        # 4. Verificar que la sesión exista.
        cursor.execute("""
            SELECT IdSesion
            FROM Sesion
            WHERE IdSesion = ?
        """, (id_sesion,))

        if not cursor.fetchone():
            return False, "La sesión indicada no existe."

        # 5. Verificar que la solicitud exista, si se proporcionó.
        if id_solicitud is not None:

            cursor.execute("""
                SELECT IdSolicitud
                FROM Solicitudes
                WHERE IdSolicitud = ?
            """, (id_solicitud,))

            if not cursor.fetchone():
                return False, "La solicitud indicada no existe."

        # 6. Registrar el punto en la agenda.
        cursor.execute("""
            INSERT INTO AgendaSesion (
                IdSesion,
                IdSolicitud,
                Tema,
                Orden,
                Observaciones
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            id_sesion,
            id_solicitud,
            tema,
            orden,
            observaciones
        ))

        # 7. Confirmar cambios.
        conexion.commit()

        return True, "Punto agregado a la agenda correctamente."

    except Exception as error:

        if conexion:
            conexion.rollback()

        return False, f"Error al registrar el punto de agenda: {error}"

    finally:

        if cursor:
            cursor.close()

        if conexion:
            conexion.close()




def ConsultarAgendaSesion(id_sesion, usuario_id):

    conexion = None
    cursor = None

    try:

        # 1. Validar datos obligatorios.
        if not id_sesion or not usuario_id:
            return False, "Debe proporcionar el ID de la sesión y el usuario."

        try:
            id_sesion = int(id_sesion)

            if id_sesion <= 0:
                return False, "El ID de la sesión no es válido."

        except (ValueError, TypeError):
            return False, "El ID de la sesión debe ser un número."

        # 2. Conectar con la base de datos.
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 3. Verificar permisos.
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_CONSULTAR_AGENDA:
            return False, "No tiene permisos para consultar agendas."

        # 4. Verificar que la sesión exista.
        cursor.execute("""
            SELECT IdSesion
            FROM Sesion
            WHERE IdSesion = ?
        """, (id_sesion,))

        if not cursor.fetchone():
            return False, "La sesión indicada no existe."

        # 5. Consultar los puntos de agenda.
        cursor.execute("""
            SELECT
                a.IdAgenda,
                a.IdSesion,
                a.IdSolicitud,
                a.Estado AS EstadoAgenda,
                a.Tema,
                a.Orden,
                a.Observaciones,
                s.NombreSolicitante,
                s.NombreActividad,
                s.MontoSolicitado,
                s.Justificacion,
                e.nombre AS EstadoSolicitud
                

            FROM AgendaSesion a

            LEFT JOIN Solicitudes s
                ON a.IdSolicitud = s.IdSolicitud

            LEFT JOIN EstadoSolicitud e
                ON s.estado_id = e.id

            WHERE a.IdSesion = ?

            ORDER BY a.Orden ASC
        """, (id_sesion,))

        filas = cursor.fetchall()

        # 6. Verificar resultados.
        if not filas:
            return False, "La sesión no tiene puntos registrados en su agenda."

        # 7. Organizar resultados.
        columnas = [columna[0] for columna in cursor.description]

        agenda = [
            dict(zip(columnas, fila))
            for fila in filas
        ]

        return True, agenda

    except Exception as error:

        return False, f"Error al consultar la agenda: {error}"

    finally:

        if cursor:
            cursor.close()

        if conexion:
            conexion.close()




def ModificarAgendaSesion(id_agenda, cambios, usuario_id):

    conexion = None
    cursor = None

    try:

        # 1. Validar datos obligatorios.
        if not id_agenda or not usuario_id:
            return False, "Debe proporcionar el ID de agenda y el usuario."

        try:
            id_agenda = int(id_agenda)

            if id_agenda <= 0:
                return False, "El ID de agenda no es válido."

        except (ValueError, TypeError):
            return False, "El ID de agenda debe ser un número."

        if not isinstance(cambios, dict) or not cambios:
            return False, "Debe proporcionar campos para modificar."

        # 2. Definir campos permitidos.
        CAMPOS_MODIFICABLES = {
            "IdSolicitud",
            "Tema",
            "Orden",
            "Observaciones"
        }

        if not set(cambios.keys()).issubset(CAMPOS_MODIFICABLES):
            return False, "Uno o más campos no pueden modificarse."

        # 3. Conectar con la base de datos.
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 4. Verificar permisos.
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_AGENDA:
            return False, "No tiene permisos para modificar la agenda."

        # 5. Consultar el punto de agenda.
        cursor.execute("""
            SELECT IdSesion, IdSolicitud, Tema, Orden, Observaciones, Estado
            FROM AgendaSesion
            WHERE IdAgenda = ?
        """, (id_agenda,))

        agenda = cursor.fetchone()

        if not agenda:
            return False, "El punto de agenda no existe."

        if agenda.Estado == ESTADO_CANCELADO:
            return False, "No se puede modificar un punto de agenda cancelado."

        id_sesion = agenda.IdSesion

        # Obtener los valores actuales.
        id_solicitud_final = agenda.IdSolicitud
        tema_final = agenda.Tema

        # Aplicar los cambios solicitados.
        if "IdSolicitud" in cambios:
            id_solicitud_final = cambios["IdSolicitud"]

        if "Tema" in cambios:
            tema_final = cambios["Tema"]

        # 6. Validar que exista una solicitud o un tema, pero no ambos.
        if id_solicitud_final is None:

            if not isinstance(tema_final, str) or not tema_final.strip():
                return False, "Debe indicar un tema cuando no existe una solicitud."

            tema_final = tema_final.strip()

        else:

            if tema_final is not None:
                return False, "Un punto de agenda no puede tener una solicitud y un tema al mismo tiempo."

            try:
                id_solicitud_final = int(id_solicitud_final)

                if id_solicitud_final <= 0:
                    return False, "El ID de solicitud no es válido."

            except (ValueError, TypeError):
                return False, "El ID de solicitud debe ser un número."

            # Verificar que la solicitud exista y no esté eliminada.
            cursor.execute("""
                SELECT IdSolicitud
                FROM Solicitudes
                WHERE IdSolicitud = ?
                  AND estado_id IN (1, 2)
            """, (id_solicitud_final,))

            if not cursor.fetchone():
                return False, "La solicitud no existe o está eliminada."

            # Verificar que no esté agregada a la misma sesión.
            cursor.execute("""
                SELECT IdAgenda
                FROM AgendaSesion
                WHERE IdSesion = ?
                  AND IdSolicitud = ?
                  AND IdAgenda <> ?
            """, (id_sesion, id_solicitud_final, id_agenda))

            if cursor.fetchone():
                return False, "La solicitud ya está incluida en esta agenda."

        # 7. Validar el orden.
        if "Orden" in cambios:

            try:
                orden = int(cambios["Orden"])

                if orden <= 0:
                    return False, "El orden debe ser un número positivo."

                cambios["Orden"] = orden

            except (ValueError, TypeError):
                return False, "El orden debe ser un número."

            cursor.execute("""
                SELECT IdAgenda
                FROM AgendaSesion
                WHERE IdSesion = ?
                  AND Orden = ?
                  AND IdAgenda <> ?
            """, (id_sesion, orden, id_agenda))

            if cursor.fetchone():
                return False, "El orden indicado ya está ocupado."

        # 8. Normalizar los valores de solicitud y tema.
        if "IdSolicitud" in cambios:
            cambios["IdSolicitud"] = id_solicitud_final

        if "Tema" in cambios:
            cambios["Tema"] = tema_final

        # 9. Preparar actualización.
        actualizaciones = []
        parametros = []

        for campo, valor in cambios.items():
            actualizaciones.append(f"{campo} = ?")
            parametros.append(valor)

        actualizaciones.append("FechaModificacion = SYSDATETIME()")
        parametros.append(id_agenda)

        # 10. Ejecutar actualización.
        consulta = f"""
            UPDATE AgendaSesion
            SET {", ".join(actualizaciones)}
            WHERE IdAgenda = ?
        """

        cursor.execute(consulta, parametros)

        conexion.commit()

        return True, "Punto de agenda modificado correctamente."

    except Exception as error:

        if conexion:
            conexion.rollback()

        return False, f"Error al modificar el punto de agenda: {error}"

    finally:

        if cursor:
            cursor.close()

        if conexion:
            conexion.close()




def EliminarAgendaSesion(id_agenda, usuario_id):

    conexion = None
    cursor = None

    try:

        # 1. Validar datos obligatorios.
        if not id_agenda or not usuario_id:
            return False, "Debe proporcionar el ID de agenda y el usuario."

        try:
            id_agenda = int(id_agenda)

            if id_agenda <= 0:
                return False, "El ID de agenda no es válido."

        except (ValueError, TypeError):
            return False, "El ID de agenda debe ser un número."

        # 2. Conectar con la base de datos.
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 3. Verificar permisos.
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_AGENDA:
            return False, "No tiene permisos para cancelar puntos de agenda."

        # 4. Consultar el punto de agenda.
        cursor.execute("""
            SELECT Estado
            FROM AgendaSesion
            WHERE IdAgenda = ?
        """, (id_agenda,))

        agenda = cursor.fetchone()

        if not agenda:
            return False, "El punto de agenda no existe."

        # 5. Verificar que no esté cancelado.
        if agenda.Estado == ESTADO_CANCELADO:
            return False, "El punto de agenda ya está cancelado."

        # 6. Cancelar el punto de agenda.
        cursor.execute("""
            UPDATE AgendaSesion
            SET Estado = ?,
                FechaModificacion = SYSDATETIME()
            WHERE IdAgenda = ?
        """, (ESTADO_CANCELADO, id_agenda))

        # 7. Confirmar cambios.
        conexion.commit()

        return True, "Punto de agenda cancelado correctamente."

    except Exception as error:

        if conexion:
            conexion.rollback()

        return False, f"Error al cancelar el punto de agenda: {error}"

    finally:

        if cursor:
            cursor.close()

        if conexion:
            conexion.close()
