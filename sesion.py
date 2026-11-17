
from datetime import date, time
from conexion import ObtenerConexion


# Estados
ESTADO_ACTIVO = 1

ESTADO_PROGRAMADA = "PROGRAMADA"
ESTADO_REALIZADA = "REALIZADA"
ESTADO_CANCELADA = "CANCELADA"


# Roles (mismos ids que en el módulo de usuarios)
ROL_ESTUDIANTE = 1
ROL_ESTUDIANTE_GRADUADO = 2
ROL_MIEMBRO_COMITE = 3
ROL_ASISTENTE_CIC = 4
ROL_ADMINISTRATIVO = 5


# Roles permitidos por función
ROLES_REGISTRAR_SESION = {ROL_ASISTENTE_CIC}
ROLES_CONSULTAR_SESION = {
    ROL_MIEMBRO_COMITE,
    ROL_ASISTENTE_CIC,
    ROL_ADMINISTRATIVO
}
ROLES_GESTIONAR_AGENDA = {ROL_ASISTENTE_CIC}
ROLES_GESTIONAR_ACTA = {ROL_ASISTENTE_CIC}


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


def RegistrarSesion(usuario_id, fecha, hora_inicio, participantes, hora_fin=None):

    conexion = None
    cursor = None

    try:

        # 1. Validar datos obligatorios.
        if not usuario_id or not fecha or not hora_inicio:
            return False, "Faltan datos obligatorios para registrar la sesión."

        if not participantes:
            return False, "Debe incluir al menos un participante."

        # 2. Convertir fecha y horas.
        try:
            if isinstance(fecha, str):
                fecha = date.fromisoformat(fecha)

            if isinstance(hora_inicio, str):
                hora_inicio = time.fromisoformat(hora_inicio)

            if isinstance(hora_fin, str):
                hora_fin = time.fromisoformat(hora_fin) if hora_fin.strip() else None

        except ValueError:
            return False, "La fecha o las horas tienen un formato inválido."

        # 3. Validar horario.
        if hora_fin is not None and hora_fin <= hora_inicio:
            return False, "La hora de finalización debe ser posterior a la hora de inicio."

        # 4. Validar participantes.
        try:
            participantes = [int(id_usuario) for id_usuario in participantes]
        except (ValueError, TypeError):
            return False, "Los identificadores de los participantes deben ser números."

        if any(id_usuario <= 0 for id_usuario in participantes):
            return False, "Los identificadores de los participantes no son válidos."

        if len(participantes) != len(set(participantes)):
            return False, "No se permite registrar un participante más de una vez."

        # 5. Conectar con la base de datos.
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 6. Verificar permisos del usuario creador.
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_REGISTRAR_SESION:
            return False, "No tiene permisos para registrar sesiones."

        # 7. Verificar que los participantes sean miembros activos del Comité.
        marcadores = ",".join("?" for _ in participantes)

        cursor.execute(f"""
            SELECT id
            FROM Usuario
            WHERE id IN ({marcadores})
              AND rol_id = ?
              AND estado_id = ?
              AND bloqueado = 0
        """, (*participantes, ROL_MIEMBRO_COMITE, ESTADO_ACTIVO))

        participantes_validos = {fila[0] for fila in cursor.fetchall()}

        if participantes_validos != set(participantes):
            return False, "Uno o más participantes no son miembros activos del Comité Técnico."

        # 8. Registrar sesión.
        cursor.execute("""
            INSERT INTO Sesion (
                Fecha,
                HoraInicio,
                HoraFin,
                Estado,
                UsuarioCreador
            )
            OUTPUT INSERTED.IdSesion
            VALUES (?, ?, ?, ?, ?)
        """, (
            fecha,
            hora_inicio,
            hora_fin,
            ESTADO_PROGRAMADA,
            usuario_id
        ))

        id_sesion = cursor.fetchone()[0]

        # 9. Registrar participantes.
        for id_participante in participantes:

            cursor.execute("""
                INSERT INTO ParticipanteSesion (
                    IdSesion,
                    IdUsuario
                )
                VALUES (?, ?)
            """, (id_sesion, id_participante))

        # 10. Confirmar transacción.
        conexion.commit()

        return True, f"Sesión registrada correctamente. ID: {id_sesion}"

    except Exception as error:

        if conexion:
            conexion.rollback()

        return False, f"Error al registrar la sesión: {error}"

    finally:

        if cursor:
            cursor.close()

        if conexion:
            conexion.close()



def ConsultarSesion(usuario_id, id_sesion=None):

    conexion = None
    cursor = None

    try:

        # 1. Validar el usuario.
        if not usuario_id:
            return False, "Debe proporcionar un usuario válido."

        # 2. Validar el ID de la sesión, si se proporcionó.
        if id_sesion is not None:

            try:
                id_sesion = int(id_sesion)

                if id_sesion <= 0:
                    return False, "El ID de la sesión no es válido."

            except (ValueError, TypeError):
                return False, "El ID de la sesión debe ser un número."

        # 3. Conectar con la base de datos.
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 4. Verificar permisos.
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_CONSULTAR_SESION:
            return False, "No tiene permisos para consultar sesiones."

        # 5. Construir la consulta.
        consulta = """
            SELECT
                s.IdSesion,
                s.Fecha,
                s.HoraInicio,
                s.HoraFin,
                s.Estado,
                s.FechaCreacion,

                s.UsuarioCreador,
                creador.nombre AS NombreCreador,
                creador.apellidos AS ApellidosCreador,

                ps.IdUsuario,
                participante.nombre AS NombreParticipante,
                participante.apellidos AS ApellidosParticipante,
                ps.Asistencia

            FROM Sesion s

            INNER JOIN Usuario creador
                ON s.UsuarioCreador = creador.id

            LEFT JOIN ParticipanteSesion ps
                ON s.IdSesion = ps.IdSesion

            LEFT JOIN Usuario participante
                ON ps.IdUsuario = participante.id
        """

        parametros = ()

        # Si se proporciona un ID, consultar solamente esa sesión.
        if id_sesion is not None:

            consulta += " WHERE s.IdSesion = ?"
            parametros = (id_sesion,)

        consulta += """
            ORDER BY s.Fecha DESC, s.HoraInicio DESC
        """

        cursor.execute(consulta, parametros)

        filas = cursor.fetchall()

        # 6. Verificar si existen resultados.
        if not filas:
            return False, "No se encontraron sesiones."

        # 7. Organizar los resultados.
        sesiones = {}

        for fila in filas:

            id_actual = fila.IdSesion

            # Crear la sesión si todavía no existe.
            if id_actual not in sesiones:

                sesiones[id_actual] = {
                    "IdSesion": fila.IdSesion,
                    "Fecha": fila.Fecha,
                    "HoraInicio": fila.HoraInicio,
                    "HoraFin": fila.HoraFin,
                    "Estado": fila.Estado,
                    "FechaCreacion": fila.FechaCreacion,
                    "UsuarioCreador": fila.UsuarioCreador,
                    "NombreCreador": fila.NombreCreador,
                    "ApellidosCreador": fila.ApellidosCreador,
                    "Participantes": []
                }

            # Agregar los participantes de la sesión.
            if fila.IdUsuario is not None:

                sesiones[id_actual]["Participantes"].append({
                    "IdUsuario": fila.IdUsuario,
                    "Nombre": fila.NombreParticipante,
                    "Apellidos": fila.ApellidosParticipante,
                    "Asistencia": fila.Asistencia
                })

        # 8. Devolver las sesiones organizadas.
        resultado = list(sesiones.values())

        return True, resultado

    except Exception as error:

        return False, f"Error al consultar las sesiones: {error}"

    finally:

        if cursor:
            cursor.close()

        if conexion:
            conexion.close()



def ModificarSesion(id_sesion, cambios, usuario_id):

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

        if not isinstance(cambios, dict) or not cambios:
            return False, "Debe proporcionar al menos un campo para modificar."

        # 2. Definir los campos permitidos.
        CAMPOS_MODIFICABLES = {
            "Fecha",
            "HoraInicio",
            "HoraFin",
            "Estado"
        }

        # 3. Verificar que los campos sean permitidos.
        if not set(cambios.keys()).issubset(CAMPOS_MODIFICABLES):
            return False, "Uno o más campos no pueden ser modificados."

        # 4. Conectar con la base de datos.
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 5. Verificar permisos.
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_AGENDA:
            return False, "No tiene permisos para modificar sesiones."

        # 6. Consultar la sesión actual.
        cursor.execute("""
            SELECT Fecha, HoraInicio, HoraFin, Estado
            FROM Sesion
            WHERE IdSesion = ?
        """, (id_sesion,))

        sesion = cursor.fetchone()

        if not sesion:
            return False, "La sesión que desea modificar no existe."

        fecha = sesion.Fecha
        hora_inicio = sesion.HoraInicio
        hora_fin = sesion.HoraFin
        estado = sesion.Estado

        # 7. Validar y convertir los nuevos valores.
        try:

            if "Fecha" in cambios:

                fecha = cambios["Fecha"]

                if isinstance(fecha, str):
                    fecha = date.fromisoformat(fecha)

                if not isinstance(fecha, date):
                    return False, "La fecha proporcionada no es válida."

            if "HoraInicio" in cambios:

                hora_inicio = cambios["HoraInicio"]

                if isinstance(hora_inicio, str):
                    hora_inicio = time.fromisoformat(hora_inicio)

                if not isinstance(hora_inicio, time):
                    return False, "La hora de inicio no es válida."

            if "HoraFin" in cambios:

                hora_fin = cambios["HoraFin"]

                if isinstance(hora_fin, str):
                    hora_fin = time.fromisoformat(hora_fin) if hora_fin.strip() else None

                if hora_fin is not None and not isinstance(hora_fin, time):
                    return False, "La hora de finalización no es válida."

        except ValueError:
            return False, "La fecha o las horas tienen un formato inválido."

        # 8. Validar el estado.
        if "Estado" in cambios:

            estado = cambios["Estado"]

            if estado not in {
                ESTADO_PROGRAMADA,
                ESTADO_REALIZADA,
                ESTADO_CANCELADA
            }:
                return False, "El estado proporcionado no es válido."

        # 9. Validar el horario.
        if hora_fin is not None and hora_fin <= hora_inicio:
            return False, "La hora de finalización debe ser posterior a la hora de inicio."

        # 10. Actualizar la sesión.
        actualizaciones = []
        parametros = []

        for campo, valor in cambios.items():

            actualizaciones.append(f"{campo} = ?")

            if campo == "Fecha":
                valor = fecha

            elif campo == "HoraInicio":
                valor = hora_inicio

            elif campo == "HoraFin":
                valor = hora_fin

            elif campo == "Estado":
                valor = estado

            parametros.append(valor)

        actualizaciones.append("FechaModificacion = SYSDATETIME()")

        parametros.append(id_sesion)

        consulta = f"""
            UPDATE Sesion
            SET {", ".join(actualizaciones)}
            WHERE IdSesion = ?
        """

        cursor.execute(consulta, parametros)

        conexion.commit()

        return True, "Sesión modificada correctamente."

    except Exception as error:

        if conexion:
            conexion.rollback()

        return False, f"Error al modificar la sesión: {error}"

    finally:

        if cursor:
            cursor.close()

        if conexion:
            conexion.close()



def EliminarSesion(id_sesion, usuario_id):

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

        if rol not in ROLES_GESTIONAR_AGENDA:
            return False, "No tiene permisos para cancelar sesiones."

        # 4. Consultar la sesión.
        cursor.execute("""
            SELECT Estado
            FROM Sesion
            WHERE IdSesion = ?
        """, (id_sesion,))

        sesion = cursor.fetchone()

        if not sesion:
            return False, "La sesión que desea cancelar no existe."

        # 5. Verificar que no esté cancelada.
        if sesion.Estado == ESTADO_CANCELADA:
            return False, "La sesión ya se encuentra cancelada."

        # 6. Cancelar la sesión.
        cursor.execute("""
            UPDATE Sesion
            SET Estado = ?,
                FechaModificacion = SYSDATETIME()
            WHERE IdSesion = ?
        """, (ESTADO_CANCELADA, id_sesion))

        # 7. Confirmar cambios.
        conexion.commit()

        return True, "Sesión cancelada correctamente."

    except Exception as error:

        if conexion:
            conexion.rollback()

        return False, f"Error al cancelar la sesión: {error}"

    finally:

        if cursor:
            cursor.close()

        if conexion:
            conexion.close()
