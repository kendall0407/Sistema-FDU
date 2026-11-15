from werkzeug.security import generate_password_hash, check_password_hash
from conexion import ObtenerConexion
import pyodbc

ESTADO_ACTIVO = 1
ESTADO_INACTIVO = 2


def CrearUsuario(identificacion, nombre, apellido, correo, telefono, contrasena, rol_id):
    # Validaciones antes de abrir la conexión
    if not identificacion or not nombre or not apellido or not correo or not contrasena:
        return False, "Los campos obligatorios deben completarse"

    if "@" not in correo:
        return False, "El correo no es válido"

    if len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

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


def ObtenerUsuario(correo):
    if not correo:
        return False, "El correo es obligatorio"

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


def ActualizarUsuario(correo, nombre=None, apellido=None, contrasena=None):
    if not correo:
        return False, "El correo es obligatorio"

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


def EliminarUsuario(correo):
    if not correo:
        return False, "El correo es obligatorio"

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        # Baja lógica: el usuario queda INACTIVO y se conserva el historial
        cursor.execute(
            """
            UPDATE Usuario
            SET estado_id = ?,
                fecha_desactivacion = SYSDATETIME(),
                fecha_modificacion = SYSDATETIME()
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