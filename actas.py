
from conexion import ObtenerConexion


ROL_ASISTENTE_CIC = 4
ESTADO_ACTIVO = 1

ROLES_GESTIONAR_ACTAS = {
    ROL_ASISTENTE_CIC
}


def _ObtenerRol(cursor, usuario_id):

    if not usuario_id:
        return None

    cursor.execute("""
        SELECT rol_id
        FROM Usuario
        WHERE id = ?
          AND estado_id = ?
          AND bloqueado = 0
    """, (usuario_id, ESTADO_ACTIVO))

    fila = cursor.fetchone()

    return fila[0] if fila else None


def CrearActa(id_sesion, contenido, usuario_id):

    conexion = None

    try:

        # Validar identificador de sesión
        if not isinstance(id_sesion, int) or id_sesion <= 0:
            return False, "El identificador de la sesión no es válido."

        # Validar contenido
        if not isinstance(contenido, str) or not contenido.strip():
            return False, "El contenido del acta es obligatorio."

        contenido = contenido.strip()

        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_ACTAS:
            return False, "No tiene permisos para registrar actas."

        # Verificar que la sesión exista
        cursor.execute("""
            SELECT Estado
            FROM Sesion
            WHERE IdSesion = ?
        """, (id_sesion,))

        sesion = cursor.fetchone()

        if not sesion:
            return False, "La sesión indicada no existe."

        # Verificar que la sesión no esté cancelada
        if sesion[0] == "CANCELADA":
            return False, "No se puede registrar un acta para una sesión cancelada."

        # Verificar que no exista un acta para esa sesión
        cursor.execute("""
            SELECT 1
            FROM Acta
            WHERE IdSesion = ?
        """, (id_sesion,))

        if cursor.fetchone():
            return False, "Esta sesión ya tiene un acta registrada."

        # Registrar acta
        cursor.execute("""
            INSERT INTO Acta (
                IdSesion,
                Contenido,
                UsuarioResponsable
            )
            OUTPUT INSERTED.IdActa
            VALUES (?, ?, ?)
        """, (
            id_sesion,
            contenido,
            usuario_id
        ))

        id_acta = cursor.fetchone()[0]

        conexion.commit()

        return True, f"Acta registrada correctamente. ID: {id_acta}"

    except Exception as e:

        if conexion:
            conexion.rollback()

        return False, f"Error al registrar el acta: {str(e)}"

    finally:

        if conexion:
            conexion.close()


def ConsultarActa(id_acta=None, usuario_id=None):

    conexion = None

    try:

        # Validar identificador si se proporciona
        if id_acta is not None:
            if not isinstance(id_acta, int) or id_acta <= 0:
                return False, "El identificador del acta no es válido."

        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_ACTAS:
            return False, "No tiene permisos para consultar actas."

        # Consultar un acta específica
        if id_acta is not None:

            cursor.execute("""
                SELECT
                    A.IdActa,
                    A.IdSesion,
                    A.Contenido,
                    A.FechaCreacion,
                    A.FechaModificacion,
                    A.UsuarioResponsable,
                    U.nombre,
                    U.apellidos,
                    S.Fecha,
                    S.HoraInicio,
                    S.HoraFin,
                    S.Estado
                FROM Acta A
                INNER JOIN Usuario U
                    ON A.UsuarioResponsable = U.id
                INNER JOIN Sesion S
                    ON A.IdSesion = S.IdSesion
                WHERE A.IdActa = ?
            """, (id_acta,))

            fila = cursor.fetchone()

            if not fila:
                return False, "No se encontró el acta indicada."

            acta = {
                "IdActa": fila[0],
                "IdSesion": fila[1],
                "Contenido": fila[2],
                "FechaCreacion": fila[3],
                "FechaModificacion": fila[4],
                "UsuarioResponsable": fila[5],
                "NombreResponsable": f"{fila[6]} {fila[7]}",
                "FechaSesion": fila[8],
                "HoraInicio": fila[9],
                "HoraFin": fila[10],
                "EstadoSesion": fila[11]
            }

            return True, acta

        # Consultar todas las actas
        cursor.execute("""
            SELECT
                A.IdActa,
                A.IdSesion,
                A.Contenido,
                A.FechaCreacion,
                A.FechaModificacion,
                A.UsuarioResponsable,
                U.nombre,
                U.apellidos,
                S.Fecha,
                S.HoraInicio,
                S.HoraFin,
                S.Estado
            FROM Acta A
            INNER JOIN Usuario U
                ON A.UsuarioResponsable = U.id
            INNER JOIN Sesion S
                ON A.IdSesion = S.IdSesion
            ORDER BY A.FechaCreacion DESC
        """)

        filas = cursor.fetchall()

        actas = []

        for fila in filas:

            actas.append({
                "IdActa": fila[0],
                "IdSesion": fila[1],
                "Contenido": fila[2],
                "FechaCreacion": fila[3],
                "FechaModificacion": fila[4],
                "UsuarioResponsable": fila[5],
                "NombreResponsable": f"{fila[6]} {fila[7]}",
                "FechaSesion": fila[8],
                "HoraInicio": fila[9],
                "HoraFin": fila[10],
                "EstadoSesion": fila[11]
            })

        return True, actas

    except Exception as e:

        return False, f"Error al consultar las actas: {str(e)}"

    finally:

        if conexion:
            conexion.close()


def ModificarActa(id_acta, contenido, usuario_id):

    conexion = None

    try:

        # Validar identificador
        if not isinstance(id_acta, int) or id_acta <= 0:
            return False, "El identificador del acta no es válido."

        # Validar contenido
        if not isinstance(contenido, str) or not contenido.strip():
            return False, "El contenido del acta es obligatorio."

        contenido = contenido.strip()

        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_ACTAS:
            return False, "No tiene permisos para modificar actas."

        # Verificar que el acta exista
        cursor.execute("""
            SELECT IdActa
            FROM Acta
            WHERE IdActa = ?
        """, (id_acta,))

        if not cursor.fetchone():
            return False, "El acta indicada no existe."

        # Modificar contenido y fecha de modificación
        cursor.execute("""
            UPDATE Acta
            SET Contenido = ?,
                FechaModificacion = SYSDATETIME()
            WHERE IdActa = ?
        """, (
            contenido,
            id_acta
        ))

        conexion.commit()

        return True, "Acta modificada correctamente."

    except Exception as e:

        if conexion:
            conexion.rollback()

        return False, f"Error al modificar el acta: {str(e)}"

    finally:

        if conexion:
            conexion.close()




def EliminarActa(id_acta, usuario_id):

    conexion = None

    try:

        # Validar identificador
        if not isinstance(id_acta, int) or id_acta <= 0:
            return False, "El identificador del acta no es válido."

        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_ACTAS:
            return False, "No tiene permisos para eliminar actas."

        # Verificar que el acta exista y esté activa
        cursor.execute("""
            SELECT Estado
            FROM Acta
            WHERE IdActa = ?
        """, (id_acta,))

        fila = cursor.fetchone()

        if not fila:
            return False, "El acta indicada no existe."

        if fila[0] == "CANCELADA":
            return False, "El acta ya se encuentra cancelada."

        # Actualizar estado y fecha de modificación
        cursor.execute("""
            UPDATE Acta
            SET Estado = 'CANCELADA',
                FechaModificacion = SYSDATETIME()
            WHERE IdActa = ?
        """, (id_acta,))

        conexion.commit()

        return True, "Acta cancelada correctamente."

    except Exception as e:

        if conexion:
            conexion.rollback()

        return False, f"Error al eliminar el acta: {str(e)}"

    finally:

        if conexion:
            conexion.close()
