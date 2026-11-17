
from decimal import Decimal, InvalidOperation
from conexion import ObtenerConexion


# Roles del sistema
ROL_ESTUDIANTE = 1
ROL_ESTUDIANTE_GRADUADO = 2
ROL_MIEMBRO_COMITE = 3
ROL_ASISTENTE_CIC = 4
ROL_ADMINISTRATIVO = 5

ESTADO_ACTIVO = 1

# Roles autorizados para registrar evaluaciones
ROLES_REGISTRAR_EVALUACION = {
    ROL_MIEMBRO_COMITE,
    ROL_ASISTENTE_CIC,
    ROL_ADMINISTRATIVO
}


def _ObtenerRol(cursor, usuario_id):
    """
    Obtiene el rol de un usuario activo y no bloqueado.
    """

    cursor.execute("""
        SELECT rol_id
        FROM Usuario
        WHERE id = ?
          AND estado_id = ?
          AND bloqueado = 0
    """, (usuario_id, ESTADO_ACTIVO))

    fila = cursor.fetchone()

    return fila[0] if fila else None


def RegistrarEvaluacion(
    id_sesion,
    id_solicitud,
    decision,
    usuario_id,
    monto_aprobado=None,
    observaciones=None
):
    """
    Registra una evaluación del Comité Técnico para una solicitud
    durante una sesión determinada.
    """

    conexion = None

    try:

        # 1. Validar identificadores
        if not isinstance(id_sesion, int) or id_sesion <= 0:
            return False, "El identificador de sesión no es válido."

        if not isinstance(id_solicitud, int) or id_solicitud <= 0:
            return False, "El identificador de solicitud no es válido."

        if not isinstance(usuario_id, int) or usuario_id <= 0:
            return False, "El usuario no es válido."

        # 2. Validar decisión
        decisiones_validas = {
            "APROBADA",
            "RECHAZADA",
            "INFORMACION_ADICIONAL"
        }

        decision = decision.strip().upper() if isinstance(decision, str) else ""

        if decision not in decisiones_validas:
            return False, "La decisión indicada no es válida."

        # 3. Validar monto aprobado
        if decision == "APROBADA":

            if monto_aprobado is None:
                return False, "Debe indicar el monto aprobado."

            try:
                monto_aprobado = Decimal(str(monto_aprobado))
            except (InvalidOperation, ValueError):
                return False, "El monto aprobado debe ser numérico."

            if not monto_aprobado.is_finite() or monto_aprobado <= 0:
                return False, "El monto aprobado debe ser mayor que cero."

        else:

            if monto_aprobado is not None:
                return False, "Solo las solicitudes aprobadas pueden tener un monto aprobado."

        # 4. Validar observaciones
        if observaciones is not None and not isinstance(observaciones, str):
            return False, "Las observaciones deben ser texto."

        # 5. Conectar con la base de datos
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 6. Verificar permisos del usuario
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_REGISTRAR_EVALUACION:
            return False, "No tiene permisos para registrar evaluaciones."

        # 7. Verificar que la sesión exista
        cursor.execute("""
            SELECT IdSesion
            FROM Sesion
            WHERE IdSesion = ?
        """, (id_sesion,))

        if cursor.fetchone() is None:
            return False, "La sesión indicada no existe."

        # 8. Obtener información de la solicitud y su línea de acción
        cursor.execute("""
            SELECT
                S.MontoSolicitado,
                L.MontoMaximo,
                L.TextoLinea
            FROM Solicitudes S
            INNER JOIN LineaAccion L
                ON S.LineaAccion = L.IdLineaAccion
            WHERE S.IdSolicitud = ?
        """, (id_solicitud,))

        solicitud = cursor.fetchone()

        if solicitud is None:
            return False, "La solicitud indicada no existe."

        monto_solicitado = Decimal(str(solicitud[0]))
        monto_maximo = Decimal(str(solicitud[1]))
        texto_linea = solicitud[2]

        # 9. Validar los límites de aprobación
        if decision == "APROBADA":

            if monto_aprobado > monto_solicitado:
                return False, "El monto aprobado no puede superar el monto solicitado."

            if monto_aprobado > monto_maximo:
                return False, (
                    f"El monto aprobado supera el máximo permitido "
                    f"para la línea '{texto_linea}' (₡{monto_maximo})."
                )

        # 10. Evitar duplicar una evaluación en la misma sesión
        cursor.execute("""
            SELECT IdEvaluacion
            FROM Evaluacion
            WHERE IdSesion = ?
              AND IdSolicitud = ?
        """, (id_sesion, id_solicitud))

        if cursor.fetchone() is not None:
            return False, "Esta solicitud ya tiene una evaluación registrada en esta sesión."

        # 11. Registrar la evaluación
        
        cursor.execute("""
            INSERT INTO Evaluacion (
                IdSesion,
                IdSolicitud,
                Decision,
                MontoAprobado,
                Observaciones,
                EstadoEvaluacion
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            id_sesion,
            id_solicitud,
            decision,
            monto_aprobado,
            observaciones,
            "ACTIVA"
        ))


        conexion.commit()

        return True, "La evaluación fue registrada correctamente."

    except Exception as e:

        if conexion:
            conexion.rollback()

        return False, f"Error al registrar la evaluación: {str(e)}"

    finally:

        if conexion:
            conexion.close()


def ConsultarEvaluacion(usuario_id, id_evaluacion=None):
    """
    Consulta las evaluaciones registradas por el Comité Técnico.

    Si se proporciona id_evaluacion, consulta una evaluación específica.
    Si no se proporciona, devuelve todas las evaluaciones.
    """

    conexion = None

    try:

        # 1. Validar el identificador del usuario
        if not isinstance(usuario_id, int) or usuario_id <= 0:
            return False, "El usuario indicado no es válido."

        # 2. Validar el identificador de evaluación, si se proporciona
        if id_evaluacion is not None:

            if not isinstance(id_evaluacion, int) or id_evaluacion <= 0:
                return False, "El identificador de evaluación no es válido."

        # 3. Conectar con la base de datos
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 4. Verificar los permisos del usuario
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_REGISTRAR_EVALUACION:
            return False, "No tiene permisos para consultar evaluaciones."

        # 5. Construir la consulta
        consulta = """
            SELECT
                E.IdEvaluacion,
                E.IdSesion,
                E.IdSolicitud,
                E.Decision,
                E.MontoAprobado,
                E.Observaciones,
                E.FechaEvaluacion,
                E.FechaModificacion,

                S.Fecha AS FechaSesion,
                S.HoraInicio,
                S.HoraFin,

                SO.NombreSolicitante,
                SO.NombreActividad,
                SO.MontoSolicitado,
                SO.Justificacion,

                L.TextoLinea

            FROM Evaluacion E

            INNER JOIN Sesion S
                ON E.IdSesion = S.IdSesion

            INNER JOIN Solicitudes SO
                ON E.IdSolicitud = SO.IdSolicitud

            INNER JOIN LineaAccion L
                ON SO.LineaAccion = L.IdLineaAccion
        """

        parametros = []

        # 6. Filtrar por evaluación específica, si corresponde
        if id_evaluacion is not None:

            consulta += """
                WHERE E.IdEvaluacion = ?
            """

            parametros.append(id_evaluacion)

        # 7. Ordenar las evaluaciones
        consulta += """
            ORDER BY E.FechaEvaluacion DESC, E.IdEvaluacion DESC
        """

        cursor.execute(consulta, parametros)

        filas = cursor.fetchall()

        # 8. Convertir los resultados en diccionarios
        evaluaciones = []

        for fila in filas:

            evaluacion = {
                "IdEvaluacion": fila[0],
                "IdSesion": fila[1],
                "IdSolicitud": fila[2],
                "Decision": fila[3],
                "MontoAprobado": fila[4],
                "Observaciones": fila[5],
                "FechaEvaluacion": fila[6],
                "FechaModificacion": fila[7],
                "FechaSesion": fila[8],
                "HoraInicio": fila[9],
                "HoraFin": fila[10],
                "NombreSolicitante": fila[11],
                "NombreActividad": fila[12],
                "MontoSolicitado": fila[13],
                "Justificacion": fila[14],
                "LineaAccion": fila[15]
            }

            evaluaciones.append(evaluacion)

        # 9. Devolver resultados
        if id_evaluacion is not None and not evaluaciones:
            return False, "No se encontró la evaluación indicada."

        return True, evaluaciones

    except Exception as e:

        return False, f"Error al consultar las evaluaciones: {str(e)}"

    finally:

        if conexion:
            conexion.close()



def SolicitarInformacionAdicional(
    id_sesion,
    id_solicitud,
    observaciones,
    usuario_id
):
    """
    Registra la solicitud de información adicional realizada
    por el Comité Técnico y actualiza el estado de la solicitud.
    """

    conexion = None

    try:

        # 1. Validar identificadores
        if not isinstance(id_sesion, int) or id_sesion <= 0:
            return False, "El identificador de sesión no es válido."

        if not isinstance(id_solicitud, int) or id_solicitud <= 0:
            return False, "El identificador de solicitud no es válido."

        if not isinstance(usuario_id, int) or usuario_id <= 0:
            return False, "El usuario no es válido."

        # 2. Validar observaciones
        if not isinstance(observaciones, str) or not observaciones.strip():
            return False, "Debe indicar qué información adicional se necesita."

        observaciones = observaciones.strip()

        # 3. Conectar con la base de datos
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 4. Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_REGISTRAR_EVALUACION:
            return False, "No tiene permisos para solicitar información adicional."

        # 5. Verificar que la sesión exista
        cursor.execute("""
            SELECT IdSesion
            FROM Sesion
            WHERE IdSesion = ?
        """, (id_sesion,))

        if cursor.fetchone() is None:
            return False, "La sesión indicada no existe."

        # 6. Verificar que la solicitud exista y obtener su estado
        cursor.execute("""
            SELECT estado_id
            FROM Solicitudes
            WHERE IdSolicitud = ?
        """, (id_solicitud,))

        solicitud = cursor.fetchone()

        if solicitud is None:
            return False, "La solicitud indicada no existe."

        estado_actual = solicitud[0]

        # No permitir solicitudes eliminadas
        if estado_actual == 3:
            return False, "No se puede solicitar información de una solicitud eliminada."

        # 7. Evitar duplicar la evaluación en la misma sesión
        cursor.execute("""
            SELECT IdEvaluacion
            FROM Evaluacion
            WHERE IdSesion = ?
              AND IdSolicitud = ?
        """, (id_sesion, id_solicitud))

        if cursor.fetchone() is not None:
            return False, "Esta solicitud ya fue evaluada en esta sesión."

        # 8. Registrar la evaluación del Comité
        
        cursor.execute("""
            INSERT INTO Evaluacion (
                IdSesion,
                IdSolicitud,
                Decision,
                MontoAprobado,
                Observaciones,
                EstadoEvaluacion
            )
            VALUES (?, ?, ?, NULL, ?, ?)
        """, (
            id_sesion,
            id_solicitud,
            "INFORMACION_ADICIONAL",
            observaciones,
            "ACTIVA"
        ))


        # 9. Actualizar el estado y las observaciones de la solicitud
        cursor.execute("""
            UPDATE Solicitudes
            SET
                estado_id = 2,
                observaciones = ?,
                fecha_modificacion = SYSDATETIME()
            WHERE IdSolicitud = ?
        """, (observaciones, id_solicitud))

        # 10. Confirmar ambas operaciones
        conexion.commit()

        return True, "La solicitud de información adicional fue registrada correctamente."

    except Exception as e:

        if conexion:
            conexion.rollback()

        return False, f"Error al solicitar información adicional: {str(e)}"

    finally:

        if conexion:
            conexion.close()




def ModificarEvaluacion(id_evaluacion, cambios, usuario_id):
    """
    Modifica una evaluación existente del Comité Técnico.

    Campos modificables:
        - Decision
        - MontoAprobado
        - Observaciones

    También actualiza el estado y las observaciones
    de la solicitud relacionada.
    """

    conexion = None

    try:

        # 1. Validar identificadores
        if not isinstance(id_evaluacion, int) or id_evaluacion <= 0:
            return False, "El identificador de evaluación no es válido."

        if not isinstance(usuario_id, int) or usuario_id <= 0:
            return False, "El usuario no es válido."

        # 2. Validar cambios
        if not isinstance(cambios, dict) or not cambios:
            return False, "Debe proporcionar los cambios que desea realizar."

        campos_permitidos = {
            "Decision",
            "MontoAprobado",
            "Observaciones"
        }

        if not set(cambios.keys()).issubset(campos_permitidos):
            return False, "Se intentó modificar un campo no permitido."

        # 3. Conectar con la base de datos
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 4. Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_REGISTRAR_EVALUACION:
            return False, "No tiene permisos para modificar evaluaciones."

        # 5. Obtener evaluación y solicitud relacionada
        cursor.execute("""
            SELECT
                E.IdSolicitud,
                E.Decision,
                E.MontoAprobado,
                E.Observaciones,
                S.MontoSolicitado,
                L.MontoMaximo,
                L.TextoLinea
            FROM Evaluacion E
            INNER JOIN Solicitudes S
                ON E.IdSolicitud = S.IdSolicitud
            INNER JOIN LineaAccion L
                ON S.LineaAccion = L.IdLineaAccion
            WHERE E.IdEvaluacion = ?
        """, (id_evaluacion,))

        evaluacion = cursor.fetchone()

        if evaluacion is None:
            return False, "La evaluación indicada no existe."

        (
            id_solicitud,
            decision_actual,
            monto_actual,
            observaciones_actuales,
            monto_solicitado,
            monto_maximo,
            texto_linea
        ) = evaluacion

        # 6. Obtener los valores nuevos o conservar los actuales
        decision = cambios.get("Decision", decision_actual)

        if not isinstance(decision, str):
            return False, "La decisión debe ser texto."

        decision = decision.strip().upper()

        decisiones_validas = {
            "APROBADA",
            "RECHAZADA",
            "INFORMACION_ADICIONAL"
        }

        if decision not in decisiones_validas:
            return False, "La decisión indicada no es válida."

        monto_aprobado = cambios.get("MontoAprobado", monto_actual)

        observaciones = cambios.get(
            "Observaciones",
            observaciones_actuales
        )

        # 7. Validar monto aprobado
        if decision == "APROBADA":

            if monto_aprobado is None:
                return False, "Debe indicar el monto aprobado."

            try:
                monto_aprobado = Decimal(str(monto_aprobado))
            except (InvalidOperation, ValueError):
                return False, "El monto aprobado debe ser numérico."

            if not monto_aprobado.is_finite() or monto_aprobado <= 0:
                return False, "El monto aprobado debe ser mayor que cero."

            if monto_aprobado > Decimal(str(monto_solicitado)):
                return False, "El monto aprobado no puede superar el monto solicitado."

            if monto_aprobado > Decimal(str(monto_maximo)):
                return False, (
                    f"El monto aprobado supera el máximo permitido "
                    f"para la línea '{texto_linea}'."
                )

        else:
            monto_aprobado = None

        # 8. Validar observaciones
        if observaciones is not None:

            if not isinstance(observaciones, str):
                return False, "Las observaciones deben ser texto."

            observaciones = observaciones.strip()

        # 9. Preparar actualización de evaluación
        cursor.execute("""
            UPDATE Evaluacion
            SET
                Decision = ?,
                MontoAprobado = ?,
                Observaciones = ?,
                FechaModificacion = SYSDATETIME()
            WHERE IdEvaluacion = ?
        """, (
            decision,
            monto_aprobado,
            observaciones,
            id_evaluacion
        ))

        # 10. Actualizar estado de la solicitud relacionada
        nuevo_estado = (
            2 if decision == "INFORMACION_ADICIONAL" else 1
        )

        cursor.execute("""
            UPDATE Solicitudes
            SET
                estado_id = ?,
                observaciones = ?,
                fecha_modificacion = SYSDATETIME()
            WHERE IdSolicitud = ?
        """, (
            nuevo_estado,
            observaciones,
            id_solicitud
        ))

        # 11. Confirmar cambios
        conexion.commit()

        return True, "La evaluación fue modificada correctamente."

    except Exception as e:

        if conexion:
            conexion.rollback()

        return False, f"Error al modificar la evaluación: {str(e)}"

    finally:

        if conexion:
            conexion.close()




def EliminarEvaluacion(id_evaluacion, usuario_id):
    """
    Realiza una eliminación lógica de una evaluación.

    Cambia su estado a CANCELADA y actualiza su fecha
    de modificación, conservando el registro original.
    """

    conexion = None

    try:

        # 1. Validar identificadores
        if not isinstance(id_evaluacion, int) or id_evaluacion <= 0:
            return False, "El identificador de evaluación no es válido."

        if not isinstance(usuario_id, int) or usuario_id <= 0:
            return False, "El usuario no es válido."

        # 2. Conectar con la base de datos
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 3. Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_REGISTRAR_EVALUACION:
            return False, "No tiene permisos para eliminar evaluaciones."

        # 4. Verificar que la evaluación exista
        cursor.execute("""
            SELECT EstadoEvaluacion
            FROM Evaluacion
            WHERE IdEvaluacion = ?
        """, (id_evaluacion,))

        evaluacion = cursor.fetchone()

        if evaluacion is None:
            return False, "La evaluación indicada no existe."

        estado_actual = evaluacion[0]

        # 5. Verificar que no esté cancelada
        if estado_actual == "CANCELADA":
            return False, "La evaluación ya se encuentra cancelada."

        # 6. Realizar eliminación lógica
        cursor.execute("""
            UPDATE Evaluacion
            SET
                EstadoEvaluacion = 'CANCELADA',
                FechaModificacion = SYSDATETIME()
            WHERE IdEvaluacion = ?
              AND EstadoEvaluacion = 'ACTIVA'
        """, (id_evaluacion,))

        # 7. Verificar que se haya actualizado el registro
        if cursor.rowcount == 0:
            conexion.rollback()
            return False, "No fue posible cancelar la evaluación."

        # 8. Confirmar cambios
        conexion.commit()

        return True, "La evaluación fue cancelada correctamente."

    except Exception as e:

        if conexion:
            conexion.rollback()

        return False, f"Error al eliminar la evaluación: {str(e)}"

    finally:

        if conexion:
            conexion.close()
