from werkzeug.security import generate_password_hash, check_password_hash
from conexion import ObtenerConexion
import pyodbc

ESTADO_ACTIVO = 1
ESTADO_INACTIVO = 2

# Roles
ROL_ESTUDIANTE = 1
ROL_ESTUDIANTE_GRADUADO = 2
ROL_MIEMBRO_COMITE = 3
ROL_ASISTENTE_CIC = 4
ROL_ADMINISTRATIVO = 5

# Roles permitidos por función
ROLES_ELIMINAR_REACTIVAR = {ROL_MIEMBRO_COMITE, ROL_ADMINISTRATIVO}
ROLES_ACTUALIZAR = {ROL_ESTUDIANTE, ROL_ESTUDIANTE_GRADUADO, ROL_ADMINISTRATIVO}
ROLES_OBTENER = {ROL_MIEMBRO_COMITE, ROL_ASISTENTE_CIC, ROL_ADMINISTRATIVO}


def ObtenerRolSolicitante(correo_solicitante):
    if not correo_solicitante:
        return None

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT rol_id
            FROM Usuario
            WHERE correo = ? AND estado_id = ? AND bloqueado = 0
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

def CrearUsuario(identificacion, nombre, apellido, correo, telefono, contrasena, rol_id):
    # Validaciones antes de abrir la conexión
    if not identificacion or not nombre or not apellido or not correo or not contrasena:
        return False, "Los campos obligatorios deben completarse"

    if "@" not in correo:
        return False, "El correo no es válido"

    if len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not telefono:
        return False, "El teléfono es obligatorio"

    if correo:
        correo = correo.strip()  # Eliminar espacios en blanco al inicio y al final

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            "SELECT id FROM Usuario WHERE identificacion = ? OR correo = ?",
            (identificacion, correo)
        )

        if cursor.fetchone() is not None:
            return False, "Ya existe un usuario con esa identificación o correo"
        
        
        cursor.execute(
            
            """
            INSERT INTO Usuario
            (identificacion, nombre, apellidos, correo, telefono, contrasena, rol_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (identificacion, nombre, apellido, correo, telefono,
             generate_password_hash(contrasena), rol_id)
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
    if not correo:
        return False, "El correo es obligatorio"

    if not TienePermiso(correo_solicitante, ROLES_OBTENER):
        return False, "No tienes permiso para desactivar usuarios"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT id, nombre, apellidos, correo, rol_id, estado_id
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
            "nombre": fila[1],
            "apellido": fila[2],
            "correo": fila[3],
            "rol_id": fila[4],
            "estado_id": fila[5]
        }

        return True, usuario

    except pyodbc.Error as error:
        return False, f"Error al obtener el usuario: {error}"

    finally:
        cursor.close()
        conexion.close()



def VerificarCredenciales(correo, contrasena):
    # Base para GUR005 Iniciar sesión
    if not correo or not contrasena:
        return False, "Correo y contraseña son obligatorios"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            "SELECT id, contrasena, estado_id FROM Usuario WHERE correo = ?",
            (correo,)
        )

        fila = cursor.fetchone()

        if fila is None or not _ContrasenaCoincide(fila[1], contrasena):
            # Mensaje genérico para no revelar si el correo existe
            return False, "Correo o contraseña incorrectos"

        if fila[2] != ESTADO_ACTIVO:
            return False, "El usuario está inactivo"

        return True, fila[0]

    except pyodbc.Error as error:
        return False, f"Error al verificar las credenciales: {error}"

    finally:
        cursor.close()
        conexion.close()


def _ContrasenaCoincide(hash_guardado, contrasena):
    try:
        return check_password_hash(hash_guardado, contrasena)
    except ValueError:
        # El valor guardado no tiene formato de hash (por ejemplo, un registro antiguo en texto plano)
        return False


def ActualizarUsuario(correo, correo_solicitante, nombre=None, apellido=None, contrasena=None):
    if not correo:
        return False, "El correo es obligatorio"

    if not TienePermiso(correo_solicitante, ROLES_ACTUALIZAR):
        return False, "No tienes permiso para desactivar usuarios"

    if correo.strip().lower() != correo_solicitante.strip().lower():
        return False, "Solo puedes modificar tu propio usuario"

    if contrasena is not None and len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    # Solo se actualizan los campos que llegan con valor
    campos = []
    valores = []

    if nombre:
        campos.append("nombre = ?")
        valores.append(nombre)

    if apellido:
        campos.append("apellidos = ?")
        valores.append(apellido)

    if contrasena:
        campos.append("contrasena = ?")
        valores.append(generate_password_hash(contrasena))

    if not campos:
        return False, "No hay campos para actualizar"

    # La fecha de modificación se actualiza siempre que haya un cambio real
    campos.append("fecha_modificacion = SYSDATETIME()")

    valores.append(correo)

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        # Los nombres de columna vienen de la lista fija de arriba, no del usuario
        cursor.execute(
            f"UPDATE Usuario SET {', '.join(campos)} WHERE correo = ?",
            valores
        )

        if cursor.rowcount == 0:
            conexion.rollback()
            return False, "Usuario no encontrado"

        conexion.commit()
        return True, "Usuario actualizado correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al actualizar el usuario: {error}"

    finally:
        cursor.close()
        conexion.close()


def EliminarUsuario(correo, correo_solicitante):
    if not correo:
        return False, "El correo es obligatorio"

    if not TienePermiso(correo_solicitante, ROLES_ELIMINAR_REACTIVAR):
        return False, "No tienes permiso para desactivar usuarios"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        # Baja lógica: el usuario queda INACTIVO y se conserva el historial
        cursor.execute(
            """
            UPDATE Usuario
            SET estado_id = ?,
                fecha_desactivacion = SYSDATETIME(),
                fecha_modificacion = SYSDATETIME(),
                bloqueado = 1
            WHERE correo = ? AND estado_id = ?
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
    if not correo:
        return False, "El correo es obligatorio"

    correo = correo.strip()

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
