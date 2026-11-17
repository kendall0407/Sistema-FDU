
from usuarios import CrearUsuario, VerificarCredenciales


# =====================================================
# CONFIGURACIÓN
# =====================================================

CORREO = "test_autenticacion@gmail.com"
CONTRASENA = "Password123"


# =====================================================
# TEST: AUTENTICACIÓN
# =====================================================

def probar_autenticacion():

    print("\n========== PRUEBAS DE AUTENTICACIÓN ==========")

    print("\nTEST 1 - Crear usuario de prueba")

    print(CrearUsuario(
        "888888881",
        "Usuario",
        "Autenticacion",
        CORREO,
        "88888888",
        CONTRASENA,
        1
    ))

    print("\nTEST 2 - Iniciar sesión con credenciales correctas")

    print(VerificarCredenciales(
        CORREO,
        CONTRASENA
    ))

    print("\nTEST 3 - Iniciar sesión con contraseña incorrecta")

    print(VerificarCredenciales(
        CORREO,
        "ClaveIncorrecta"
    ))

    print("\nTEST 4 - Realizar cinco intentos fallidos")

    for intento in range(1, 6):

        print(f"\nIntento fallido {intento}")

        print(VerificarCredenciales(
            CORREO,
            "ClaveIncorrecta"
        ))

    print("\nTEST 5 - Intentar ingresar con la contraseña correcta después del bloqueo")

    print(VerificarCredenciales(
        CORREO,
        CONTRASENA
    ))


if __name__ == "__main__":
    probar_autenticacion()
