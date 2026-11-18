
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "solo-desarrollo-local")

from rutas_fdu import fdu
app.register_blueprint(fdu)
from rutas_extra_fdu import extra_fdu
app.register_blueprint(extra_fdu)

def login_requerido(funcion):
    @wraps(funcion)
    def decorador(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return funcion(*args, **kwargs)
    return decorador


@app.route("/")
def inicio():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip()
        contrasena = request.form.get("contrasena", "")

        try:
            from usuarios import VerificarCredenciales
            correcto, resultado = VerificarCredenciales(correo, contrasena)
        except Exception:
            app.logger.exception("Error en el inicio de sesión")
            flash("No fue posible conectar con el sistema.", "danger")
            return render_template("login.html")

        if correcto:
            session.clear()
            session["usuario_id"] = resultado
            session["correo"] = correo
            return redirect(url_for("dashboard"))

        flash(str(resultado), "danger")

    return render_template("login.html")


@app.route("/dashboard")
@login_requerido
def dashboard(): 
    return render_template("dashboard.html")


@app.route("/logout", methods=["POST"])
@login_requerido
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/usuarios")
@login_requerido
def listar_usuarios():
    from conexion import ObtenerConexion
    from usuarios import ObtenerRolSolicitante, ROLES_OBTENER

    correo_actual = session.get("correo")

    # Comprobamos los permisos en el servidor.
    if ObtenerRolSolicitante(correo_actual) not in ROLES_OBTENER:
        return "No tenés permisos para consultar usuarios", 403

    conexion = None
    cursor = None

    try:
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                u.id,
                u.nombre,
                u.apellidos,
                u.correo,
                r.nombre AS rol,
                e.nombre AS estado
            FROM dbo.Usuario AS u
            INNER JOIN dbo.Rol AS r
                ON u.rol_id = r.id
            INNER JOIN dbo.EstadoUsuario AS e
                ON u.estado_id = e.id
            ORDER BY u.nombre, u.apellidos
        """)

        columnas = [col[0] for col in cursor.description]

        usuarios = [
            dict(zip(columnas, fila))
            for fila in cursor.fetchall()
        ]

        return render_template(
            "usuarios.html",
            usuarios=usuarios
        )

    except Exception:
        app.logger.exception("Error consultando usuarios")
        return "No se pudo consultar la lista de usuarios", 500

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()
from flask import session, current_app
from conexion import ObtenerConexion

PERMISOS_MENU = {
    1: {'solicitudes'},                        # Estudiante
    2: {'solicitudes'},                        # Graduado
    3: {'usuarios', 'solicitudes', 'sesiones', 'agenda', 'evaluaciones'},
    4: {'usuarios', 'solicitudes', 'sesiones', 'actas', 'agenda', 'evaluaciones', 'lineas'},
    5: {'usuarios', 'solicitudes', 'sesiones', 'actas', 'agenda', 'evaluaciones', 'lineas'},
}

@app.context_processor
def permisos_para_plantillas():
    rol = None
    conexion = None
    try:
        usuario_id = session.get('usuario_id')
        if isinstance(usuario_id, int) and not session.get('modo_demo'):
            conexion = ObtenerConexion()
            cursor = conexion.cursor()
            cursor.execute("SELECT rol_id FROM dbo.Usuario WHERE id = ? AND estado_id = 1 AND bloqueado = 0",
                           (usuario_id,))
            fila = cursor.fetchone()
            if fila:
                rol = fila[0]
    except Exception:
        current_app.logger.exception('No se pudieron consultar permisos del menú')
    finally:
        if conexion is not None:
            conexion.close()

    permitidos = PERMISOS_MENU.get(rol, set())
    return {'puede_ver': lambda modulo: modulo in permitidos}

if __name__ == "__main__":
    app.run(debug=True)
