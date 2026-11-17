
from usuarios import (
    CrearUsuario,
    ObtenerUsuario,
    ActualizarUsuario,
    EliminarUsuario,
    ReactivarUsuario
)


# =====================================================
# USUARIOS DE PRUEBA
# =====================================================

USUARIOS = [
    ("111111111", "Estudiante", "Uno",
     "test_estudiante@gmail.com", 1),

    ("222222222", "Graduado", "Dos",
     "test_graduado@gmail.com", 2),

    ("333333333", "Comite", "Tres",
     "test_comite@gmail.com", 3),

    ("444444444", "Asistente", "Cuatro",
     "test_asistente@gmail.com", 4),

    ("555555555", "Administrativo", "Cinco",
     "test_administrativo@gmail.com", 5)
]


# =====================================================
# CREAR USUARIOS PARA LAS PRUEBAS
# =====================================================

def crear_usuarios_prueba():

    print("\n========== CREACIÓN DE USUARIOS ==========")

    for identificacion, nombre, apellido, correo, rol in USUARIOS:

        print(f"\nCreando usuario: {correo}")

        print(CrearUsuario(
            identificacion,
            nombre,
            apellido,
            correo,
            "88888888",
            "Password123",
            rol
        ))


# =====================================================
# TEST: CONSULTAR USUARIOS
# =====================================================

def probar_permisos_consulta():

    print("\n========== PERMISOS DE CONSULTA ==========")

    correo_objetivo = "test_estudiante@gmail.com"

    for usuario in USUARIOS:

        correo_solicitante = usuario[3]

        print(f"\nSolicitante: {correo_solicitante}")

        print(ObtenerUsuario(
            correo_objetivo,
            correo_solicitante
        ))


# =====================================================
# TEST: ACTUALIZAR USUARIOS
# =====================================================

def probar_permisos_actualizacion():

    print("\n========== PERMISOS DE ACTUALIZACIÓN ==========")

    for usuario in USUARIOS:

        correo = usuario[3]

        print(f"\nSolicitante: {correo}")

        print(ActualizarUsuario(
            correo,
            correo,
            nombre="NombreModificado"
        ))


# =====================================================
# TEST: DESBLOQUEAR USUARIOS
# =====================================================

def probar_permisos_desbloqueo():

    print("\n========== PERMISOS DE DESBLOQUEO ==========")

    correo_objetivo = "test_estudiante@gmail.com"

    for usuario in USUARIOS:

        correo_solicitante = usuario[3]

        print(f"\nSolicitante: {correo_solicitante}")

        print(ActualizarUsuario(
            correo_objetivo,
            correo_solicitante,
            desbloquear=True
        ))


# =====================================================
# TEST: DESACTIVAR USUARIOS
# =====================================================

def probar_permisos_desactivacion():

    print("\n========== PERMISOS DE DESACTIVACIÓN ==========")

    correo_objetivo = "test_estudiante@gmail.com"

    for usuario in USUARIOS:

        correo_solicitante = usuario[3]

        print(f"\nSolicitante: {correo_solicitante}")

        print(EliminarUsuario(
            correo_objetivo,
            correo_solicitante
        ))


# =====================================================
# TEST: REACTIVAR USUARIOS
# =====================================================

def probar_permisos_reactivacion():

    print("\n========== PERMISOS DE REACTIVACIÓN ==========")

    correo_objetivo = "test_estudiante@gmail.com"

    for usuario in USUARIOS:

        correo_solicitante = usuario[3]

        print(f"\nSolicitante: {correo_solicitante}")

        print(ReactivarUsuario(
            correo_objetivo,
            correo_solicitante
        ))


# =====================================================
# EJECUTAR PRUEBAS
# =====================================================

if __name__ == "__main__":

    crear_usuarios_prueba()

    probar_permisos_consulta()
    probar_permisos_actualizacion()
    probar_permisos_desbloqueo()
    probar_permisos_desactivacion()
    probar_permisos_reactivacion()
