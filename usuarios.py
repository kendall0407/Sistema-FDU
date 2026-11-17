
from werkzeug.security import generate_password_hash, check_password_hash
from conexion import ObtenerConexion
import pyodbc


ESTADO_ACTIVO = 1
ESTADO_INACTIVO = 2

# Configuración de seguridad
MAX_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 15

# Roles
ROL_ESTUDIANTE = 1
ROL_ESTUDIANTE_GRADUADO = 2
ROL_MIEMBRO_COMITE = 3
ROL_ASISTENTE_CIC = 4
ROL_ADMINISTRATIVO = 5

ROLES_VALIDOS = {
    ROL_ESTUDIANTE,
    ROL_ESTUDIANTE_GRADUADO,
    ROL_MIEMBRO_COMITE,
    ROL_ASISTENTE_CIC,
    ROL_ADMINISTRATIVO
}

# Roles permitidos por función
ROLES_ELIMINAR_REACTIVAR = {
    ROL_MIEMBRO_COMITE,
    ROL_ADMINISTRATIVO
}

ROLES_ACTUALIZAR = {
    ROL_ESTUDIANTE,
    ROL_ESTUDIANTE_GRADUADO,
    ROL_ADMINISTRATIVO
}

ROLES_OBTENER = {
    ROL_MIEMBRO_COMITE,
    ROL_ASISTENTE_CIC,
    ROL_ADMINISTRATIVO
}

ROLES_DESBLOQUEAR = {
    ROL_MIEMBRO_COMITE,
    ROL_ASISTENTE_CIC,
    ROL_ADMINISTRATIVO
}
def _NormalizarCorreo(correo):
    if not correo:
        return None

    return correo.strip().lower()


def ObtenerRolSolicitante(correo_solicitante):
    correo_solicitante = _NormalizarCorreo(correo_solicitante)

    if not correo_solicitante:
        return None

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT rol_id
            FROM Usuario
            WHERE correo = ?
              AND estado_id = ?
              AND bloqueado = 0
            """,
            (correo_solicitante, ESTADO_ACTIVO)
        )

        fila = cursor.fetchone()
        return fila[0] if fila else None

    except pyodbc.Error:
        return None

    finally:
        cursor.close()
        conexion.close()


def TienePermiso(correo_solicitante, roles_permitidos):
    rol = ObtenerRolSolicitante(correo_solicitante)

    return rol is not None and rol in roles_permitidos


def CrearUsuario(identificacion, nombre, apellido, correo,
                 telefono, contrasena, rol_id):

    if not identificacion or not nombre or not apellido:
        return False, "Los datos personales son obligatorios"

    if not correo or not contrasena or not telefono:
        return False, "Correo, teléfono y contraseña son obligatorios"

    identificacion = identificacion.strip()
    nombre = nombre.strip()
    apellido = apellido.strip()
    correo = _NormalizarCorreo(correo)
    telefono = telefono.strip()

    if "@" not in correo:
        return False, "El correo no es válido"

    if len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    if rol_id not in ROLES_VALIDOS:
        return False, "El rol seleccionado no es válido"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM Usuario
            WHERE identificacion = ? OR correo = ?
            """,
            (identificacion, correo)
        )

        if cursor.fetchone() is not None:
            return False, "Ya existe un usuario con esa identificación o correo"

        cursor.execute(
            """
            INSERT INTO Usuario
            (
                identificacion,
                nombre,
                apellidos,
                correo,
                telefono,
                contrasena,
                rol_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                identificacion,
                nombre,
                apellido,
                correo,
                telefono,
                generate_password_hash(contrasena),
                rol_id
            )
        )

        conexion.commit()
        return True, "Usuario creado correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al crear el usuario: {error}"

    finally:
        cursor.close()
        conexion.close()


def ObtenerUsuario(correo, correo_solicitante):

    correo = _NormalizarCorreo(correo)

    if not correo:
        return False, "El correo es obligatorio"

    if not TienePermiso(correo_solicitante, ROLES_OBTENER):
        return False, "No tienes permiso para consultar usuarios"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT id, identificacion, nombre, apellidos,
                   correo, telefono, rol_id, estado_id, bloqueado
            FROM Usuario
            WHERE correo = ?
            """,
            (correo,)
        )

        fila = cursor.fetchone()

        if fila is None:
            return False, "Usuario no encontrado"

        usuario = {
            "id": fila[0],
            "identificacion": fila[1],
            "nombre": fila[2],
            "apellido": fila[3],
            "correo": fila[4],
            "telefono": fila[5],
            "rol_id": fila[6],
            "estado_id": fila[7],
            "bloqueado": bool(fila[8])
        }

        return True, usuario

    except pyodbc.Error as error:
        return False, f"Error al obtener el usuario: {error}"

    finally:
        cursor.close()
        conexion.close()


def _RegistrarIntentoFallido(cursor, usuario_id):

    cursor.execute(
        """
        UPDATE Usuario
        SET intentos_fallidos = intentos_fallidos + 1,

            bloqueado = CASE
                WHEN intentos_fallidos + 1 >= ?
                THEN 1
                ELSE bloqueado
            END,

            bloqueo_hasta = CASE
                WHEN intentos_fallidos + 1 >= ?
                THEN DATEADD(MINUTE, ?, SYSDATETIME())
                ELSE bloqueo_hasta
            END

        WHERE id = ?
          AND estado_id = ?
          AND bloqueado = 0
        """,
        (
            MAX_INTENTOS_FALLIDOS,
            MAX_INTENTOS_FALLIDOS,
            MINUTOS_BLOQUEO,
            usuario_id,
            ESTADO_ACTIVO
        )
    )


def VerificarCredenciales(correo, contrasena):

    correo = _NormalizarCorreo(correo)

    if not correo or not contrasena:
        return False, "Correo y contraseña son obligatorios"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT id, contrasena, estado_id,
                   bloqueado, intentos_fallidos, bloqueo_hasta
            FROM Usuario
            WHERE correo = ?
            """,
            (correo,)
        )

        fila = cursor.fetchone()

        if fila is None:
            return False, "Correo o contraseña incorrectos"

        usuario_id = fila[0]
        hash_guardado = fila[1]
        estado_id = fila[2]
        bloqueado = bool(fila[3])
        bloqueo_hasta = fila[5]

        if estado_id != ESTADO_ACTIVO:
            return False, "Correo o contraseña incorrectos"

        # Comprobar si existe un bloqueo vigente.
        if bloqueado:

            # Si no tiene vencimiento, se considera un bloqueo administrativo.
            if bloqueo_hasta is None:
                return False, "La cuenta está bloqueada. Contacte al administrador"

            cursor.execute(
                """
                SELECT CASE
                    WHEN bloqueo_hasta > SYSDATETIME() THEN 1
                    ELSE 0
                END
                FROM Usuario
                WHERE id = ?
                """,
                (usuario_id,)
            )

            bloqueo_vigente = cursor.fetchone()[0]

            if bloqueo_vigente:
                return False, "Cuenta bloqueada temporalmente. Intente más tarde"

            # El bloqueo temporal venció: restablecer la cuenta.
            cursor.execute(
                """
                UPDATE Usuario
                SET bloqueado = 0,
                    intentos_fallidos = 0,
                    bloqueo_hasta = NULL,
                    fecha_modificacion = SYSDATETIME()
                WHERE id = ?
                """,
                (usuario_id,)
            )

            conexion.commit()

        # Comprobar contraseña.
        if not _ContrasenaCoincide(hash_guardado, contrasena):

            _RegistrarIntentoFallido(cursor, usuario_id)

            cursor.execute(
                """
                SELECT bloqueado
                FROM Usuario
                WHERE id = ?
                """,
                (usuario_id,)
            )

            cuenta_bloqueada = bool(cursor.fetchone()[0])

            conexion.commit()

            if cuenta_bloqueada:
                return False, "Cuenta bloqueada por demasiados intentos. Intente en 15 minutos"

            return False, "Correo o contraseña incorrectos"

        # Credenciales correctas: reiniciar contador.
        cursor.execute(
            """
            UPDATE Usuario
            SET intentos_fallidos = 0,
                bloqueo_hasta = NULL,
                fecha_modificacion = SYSDATETIME()
            WHERE id = ?
            """,
            (usuario_id,)
        )

        conexion.commit()

        return True, usuario_id

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al verificar las credenciales: {error}"

    finally:
        cursor.close()
        conexion.close()


def _ContrasenaCoincide(hash_guardado, contrasena):

    try:
        return check_password_hash(hash_guardado, contrasena)

    except (ValueError, TypeError):
        return False



def ActualizarUsuario(correo, correo_solicitante,
                      nombre=None, apellido=None, contrasena=None,
                      desbloquear=False):

    correo = _NormalizarCorreo(correo)
    correo_solicitante = _NormalizarCorreo(correo_solicitante)

    if not correo:
        return False, "El correo es obligatorio"

    if not correo_solicitante:
        return False, "No se pudo identificar al usuario solicitante"

    rol_solicitante = ObtenerRolSolicitante(correo_solicitante)

    if rol_solicitante is None:
        return False, "Usuario solicitante no válido o inactivo"

    # Si solicita desbloquear, debe tener un rol autorizado.
    if desbloquear:
        if rol_solicitante not in ROLES_DESBLOQUEAR:
            return False, "No tienes permiso para desbloquear usuarios"

    else:
        if rol_solicitante not in ROLES_ACTUALIZAR:
            return False, "No tienes permiso para actualizar usuarios"

        if correo != correo_solicitante:
            return False, "Solo puedes modificar tu propio usuario"

    if contrasena is not None and len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    campos = []
    valores = []

    if nombre is not None:
        nombre = nombre.strip()

        if not nombre:
            return False, "El nombre no puede estar vacío"

        campos.append("nombre = ?")
        valores.append(nombre)

    if apellido is not None:
        apellido = apellido.strip()

        if not apellido:
            return False, "Los apellidos no pueden estar vacíos"

        campos.append("apellidos = ?")
        valores.append(apellido)

    if contrasena:
        campos.append("contrasena = ?")
        valores.append(generate_password_hash(contrasena))

    if desbloquear:
        campos.extend([
            "bloqueado = 0",
            "intentos_fallidos = 0",
            "bloqueo_hasta = NULL"
        ])

    if not campos:
        return False, "No hay campos para actualizar"

    campos.append("fecha_modificacion = SYSDATETIME()")
    valores.append(correo)

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            f"""
            UPDATE Usuario
            SET {', '.join(campos)}
            WHERE correo = ?
              AND estado_id = ?
            """,
            valores + [ESTADO_ACTIVO]
        )

        if cursor.rowcount == 0:
            conexion.rollback()
            return False, "Usuario no encontrado o inactivo"

        conexion.commit()
        return True, "Usuario actualizado correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al actualizar el usuario: {error}"

    finally:
        cursor.close()
        conexion.close()



def EliminarUsuario(correo, correo_solicitante):

    correo = _NormalizarCorreo(correo)

    if not correo:
        return False, "El correo es obligatorio"

    if not TienePermiso(correo_solicitante, ROLES_ELIMINAR_REACTIVAR):
        return False, "No tienes permiso para desactivar usuarios"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            UPDATE Usuario
            SET estado_id = ?,
                fecha_desactivacion = SYSDATETIME(),
                fecha_modificacion = SYSDATETIME(),
                bloqueado = 1,
                bloqueo_hasta = NULL
            WHERE correo = ?
              AND estado_id = ?
            """,
            (ESTADO_INACTIVO, correo, ESTADO_ACTIVO)
        )

        if cursor.rowcount == 0:
            conexion.rollback()
            return False, "Usuario no encontrado o ya estaba inactivo"

        conexion.commit()
        return True, "Usuario desactivado correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al desactivar el usuario: {error}"

    finally:
        cursor.close()
        conexion.close()


def ReactivarUsuario(correo, correo_solicitante):

    correo = _NormalizarCorreo(correo)

    if not correo:
        return False, "El correo es obligatorio"

    if not TienePermiso(correo_solicitante, ROLES_ELIMINAR_REACTIVAR):
        return False, "No tienes permiso para reactivar usuarios"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            UPDATE Usuario
            SET estado_id = ?,
                bloqueado = 0,
                intentos_fallidos = 0,
                bloqueo_hasta = NULL,
                fecha_desactivacion = NULL,
                fecha_modificacion = SYSDATETIME()
            WHERE correo = ?
              AND estado_id = ?
              AND fecha_desactivacion IS NOT NULL
            """,
            (ESTADO_ACTIVO, correo, ESTADO_INACTIVO)
        )

        if cursor.rowcount == 0:
            conexion.rollback()
            return False, "Usuario no encontrado o ya estaba activo"

        conexion.commit()
        return True, "Usuario reactivado correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al reactivar el usuario: {error}"

    finally:
        cursor.close()
        conexion.close()
