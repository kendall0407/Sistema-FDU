
from werkzeug.security import generate_password_hash
from conexion import ObtenerConexion

usuarios = [
    ("100000001", "Administrador", "Sistema",
     "admin@sgfdu.com", "88880001", "AdminFDU2026!", 5),

    ("100000002", "Asistente", "CIC",
     "asistente@sgfdu.com", "88880002", "AsistenteFDU2026!", 4),

    ("100000003", "Estudiante", "Prueba",
     "estudiante@sgfdu.com", "88880003", "EstudianteFDU2026!", 1),

    ("100000004", "Graduado", "Prueba",
     "graduado@sgfdu.com", "88880004", "GraduadoFDU2026!", 2),

    ("100000005", "Miembro", "Comite",
     "comite@sgfdu.com", "88880005", "ComiteFDU2026!", 3)
]

conexion = ObtenerConexion()
cursor = conexion.cursor()

try:
    for identificacion, nombre, apellido, correo, telefono, contrasena, rol_id in usuarios:

        cursor.execute(
            """
            INSERT INTO Usuario
            (identificacion, nombre, apellidos, correo,
             telefono, contrasena, rol_id, estado_id, bloqueado)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0)
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
    print("Los cinco usuarios fueron creados correctamente.")

except Exception as error:
    conexion.rollback()
    print(f"Error al crear usuarios: {error}")

finally:
    cursor.close()
    conexion.close()
