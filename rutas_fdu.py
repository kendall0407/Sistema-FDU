# Rutas Flask para la interfaz. No modifica el backend existente.
from functools import wraps
from secrets import token_urlsafe
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, current_app
from conexion import ObtenerConexion
from usuarios import CrearUsuario, ActualizarUsuario, EliminarUsuario, ReactivarUsuario
from solicitudes import CrearSolicitud, ModificarSolicitud, EliminarSolicitud

fdu = Blueprint('fdu', __name__)
from sesion import RegistrarSesion, ModificarSesion, EliminarSesion
STAFF = {3, 4, 5}


def requiere_acceso(roles=None):
    def envolver(fn):
        @wraps(fn)
        def ejecuta(*args, **kwargs):
            if not session.get('usuario_id') or not isinstance(session.get('usuario_id'), int):
                return redirect(url_for('login'))
            conexion = ObtenerConexion()
            try:
                cur = conexion.cursor()
                cur.execute('SELECT rol_id FROM dbo.Usuario WHERE id=? AND estado_id=1 AND bloqueado=0', session['usuario_id'])
                fila = cur.fetchone()
                cur.close()
            finally:
                conexion.close()
            if not fila:
                session.clear()
                return redirect(url_for('login'))
            if roles is not None and fila[0] not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return ejecuta
    return envolver


def rol_actual():
    data = consultar('SELECT rol_id FROM dbo.Usuario WHERE id=?', (session['usuario_id'],))
    return data[0]['rol_id'] if data else None


def csrf_token():
    if '_fdu_csrf' not in session:
        session['_fdu_csrf'] = token_urlsafe(32)
    return session['_fdu_csrf']

@fdu.app_context_processor
def inyectar_token():
    return {'fdu_csrf': csrf_token}


def valida_formulario():
    from hmac import compare_digest
    if not compare_digest(request.form.get('_csrf', ''), session.get('_fdu_csrf', '')):
        abort(400, 'Formulario caducado. Recargá la página.')


def consultar(sql, parametros=()):
    conexion = ObtenerConexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)
        nombres = [c[0] for c in cursor.description]
        resultado = [dict(zip(nombres, fila)) for fila in cursor.fetchall()]
        cursor.close()
        return resultado
    finally:
        conexion.close()


@fdu.route('/usuarios', methods=['GET'])
@requiere_acceso(STAFF)
def usuarios():
    datos = consultar('''SELECT u.id, u.nombre, u.apellidos, u.correo, u.telefono,
        r.nombre AS rol, e.nombre AS estado FROM dbo.Usuario u
        JOIN dbo.Rol r ON u.rol_id=r.id JOIN dbo.EstadoUsuario e ON u.estado_id=e.id
        ORDER BY u.nombre, u.apellidos''')
    return render_template('usuarios.html', usuarios=datos, rol_actual=rol_actual(), correo_actual=session.get('correo'))


@fdu.route('/usuarios/nuevo', methods=['GET', 'POST'])
@requiere_acceso({5})
def nuevo_usuario():
    if request.method == 'POST':
        valida_formulario()
        try:
            rol = int(request.form.get('rol_id',''))
            if rol not in {1,2,3,4,5}:
                raise ValueError()
        except ValueError:
            flash('Elegí un rol válido.', 'danger')
            return redirect(url_for('fdu.nuevo_usuario'))
        try:
            ok, mensaje = CrearUsuario(
                request.form.get('identificacion','').strip(),
                request.form.get('nombre','').strip(),
                request.form.get('apellidos','').strip(),
                request.form.get('correo','').strip(),
                request.form.get('telefono','').strip(),
                request.form.get('contrasena',''), rol)
        except Exception:
            current_app.logger.exception('No se pudo crear usuario')
            ok, mensaje = False, 'No se pudo completar el registro.'
        flash(str(mensaje), 'success' if ok else 'danger')
        return redirect(url_for('fdu.usuarios' if ok else 'fdu.nuevo_usuario'))
    roles = consultar('SELECT id, nombre FROM dbo.Rol ORDER BY id')
    return render_template('nuevo_usuario.html', roles=roles)


@fdu.route('/solicitudes')
@requiere_acceso()
def solicitudes():
    usuario_id = session['usuario_id']
    datos = consultar('''SELECT s.IdSolicitud AS id, s.NombreSolicitante AS solicitante,
       s.NombreActividad AS actividad, s.MontoSolicitado AS monto,
       e.nombre AS estado, s.fecha_creacion AS fecha
       FROM dbo.Solicitudes s JOIN dbo.EstadoSolicitud e ON e.id=s.estado_id
       WHERE s.usuario_id=? OR EXISTS (
           SELECT 1 FROM dbo.Usuario u WHERE u.id=? AND u.rol_id IN (3,4,5)
              AND u.estado_id=1 AND u.bloqueado=0)
       ORDER BY s.fecha_creacion DESC''', (usuario_id, usuario_id))
    return render_template('solicitudes.html', solicitudes=datos, rol_actual=rol_actual())


@fdu.route('/solicitudes/nueva', methods=['GET', 'POST'])
@requiere_acceso({1,2,5})
def nueva_solicitud():
    if request.method == 'POST':
        valida_formulario()
        try:
            monto = request.form.get('monto','').strip()
            linea = int(request.form.get('linea_accion',''))
            ok, mensaje = CrearSolicitud(session['usuario_id'], monto,
                request.form.get('informacion_bancaria','').strip(),
                request.form.get('actividad','').strip(),
                request.form.get('justificacion','').strip(), linea)
        except (ValueError, TypeError):
            ok, mensaje = False, 'Completá los datos correctamente.'
        except Exception:
            current_app.logger.exception('No se pudo crear solicitud')
            ok, mensaje = False, 'No se pudo guardar la solicitud.'
        flash(('Solicitud #' + str(mensaje) + ' creada correctamente.') if ok else str(mensaje),
              'success' if ok else 'danger')
        return redirect(url_for('fdu.solicitudes' if ok else 'fdu.nueva_solicitud'))
    lineas = consultar('SELECT IdLineaAccion AS id, TextoLinea AS nombre, MontoMaximo AS maximo FROM dbo.LineaAccion ORDER BY IdLineaAccion')
    return render_template('nueva_solicitud.html', lineas=lineas)


@fdu.route('/sesiones')
@requiere_acceso(STAFF)
def sesiones():
    datos = consultar('''SELECT s.IdSesion AS id, s.Fecha AS fecha,
        s.HoraInicio AS inicio, s.HoraFin AS fin, s.Estado AS estado,
        u.nombre + ' ' + u.apellidos AS creador
        FROM dbo.Sesion s JOIN dbo.Usuario u ON u.id=s.UsuarioCreador
        ORDER BY s.Fecha DESC, s.HoraInicio DESC''')
    return render_template('sesiones.html', sesiones=datos, rol_actual=rol_actual())


# === CRUD USUARIOS: consulta, edición del propio perfil y baja/reactivación lógica ===
@fdu.route('/usuarios/<int:id_usuario>/editar', methods=['GET', 'POST'])
@requiere_acceso()
def editar_usuario(id_usuario):
    filas = consultar('SELECT id, nombre, apellidos, correo, rol_id FROM dbo.Usuario WHERE id=?', (id_usuario,))
    if not filas: abort(404)
    usuario = filas[0]
    # El backend existente solo permite que cada persona edite su propia cuenta.
    if session['correo'].strip().lower() != usuario['correo'].strip().lower(): abort(403)
    if request.method == 'POST':
        valida_formulario()
        try:
            ok, mensaje = ActualizarUsuario(usuario['correo'], session['correo'],
                nombre=request.form.get('nombre', '').strip() or None,
                apellido=request.form.get('apellidos', '').strip() or None,
                contrasena=request.form.get('contrasena') or None)
        except Exception:
            current_app.logger.exception('Error modificando usuario')
            ok, mensaje = False, 'No se pudo actualizar el usuario.'
        flash(str(mensaje), 'success' if ok else 'danger')
        return redirect(url_for('fdu.usuarios' if rol_actual() in STAFF else 'fdu.editar_usuario', id_usuario=id_usuario))
    return render_template('editar_usuario.html', usuario=usuario)


@fdu.route('/usuarios/<int:id_usuario>/estado', methods=['POST'])
@requiere_acceso({3,5})
def estado_usuario(id_usuario):
    valida_formulario()
    filas = consultar('SELECT correo, estado_id FROM dbo.Usuario WHERE id=?', (id_usuario,))
    if not filas: abort(404)
    if id_usuario == session['usuario_id']:
        flash('No podés desactivar tu propia cuenta desde aquí.', 'danger')
    else:
        u = filas[0]
        operacion = ReactivarUsuario if u['estado_id'] != 1 else EliminarUsuario
        ok, mensaje = operacion(u['correo'], session['correo'])
        flash(str(mensaje), 'success' if ok else 'danger')
    return redirect(url_for('fdu.usuarios'))


# === CRUD SOLICITUDES: edición y eliminación lógica utilizando el backend ===
@fdu.route('/solicitudes/<int:id_solicitud>/editar', methods=['GET','POST'])
@requiere_acceso()
def editar_solicitud(id_solicitud):
    filas = consultar('''SELECT IdSolicitud AS id, usuario_id, estado_id,
        NombreActividad, MontoSolicitado, InformacionBancaria, Justificacion, LineaAccion
        FROM dbo.Solicitudes WHERE IdSolicitud=?''', (id_solicitud,))
    if not filas: abort(404)
    solicitud = filas[0]
    rol = rol_actual()
    if rol not in STAFF and solicitud['usuario_id'] != session['usuario_id']: abort(403)
    if solicitud['estado_id'] not in (1,2): abort(403)
    if request.method == 'POST':
        valida_formulario()
        try:
            cambios = {
                'NombreActividad': request.form.get('actividad','').strip(),
                'MontoSolicitado': request.form.get('monto','').strip(),
                'InformacionBancaria': request.form.get('informacion_bancaria','').strip(),
                'Justificacion': request.form.get('justificacion','').strip(),
                'LineaAccion': int(request.form.get('linea_accion',''))
            }
            ok, mensaje = ModificarSolicitud(id_solicitud, session['usuario_id'], cambios, session['correo'])
        except (ValueError, TypeError):
            ok, mensaje = False, 'Completá los datos correctamente.'
        except Exception:
            current_app.logger.exception('Error modificando solicitud')
            ok, mensaje = False, 'No se pudo actualizar la solicitud.'
        flash(str(mensaje), 'success' if ok else 'danger')
        return redirect(url_for('fdu.solicitudes' if ok else 'fdu.editar_solicitud', id_solicitud=id_solicitud))
    lineas = consultar('SELECT IdLineaAccion AS id, TextoLinea AS nombre FROM dbo.LineaAccion ORDER BY IdLineaAccion')
    return render_template('editar_solicitud.html', solicitud=solicitud, lineas=lineas)


@fdu.route('/solicitudes/<int:id_solicitud>/eliminar', methods=['POST'])
@requiere_acceso()
def eliminar_solicitud(id_solicitud):
    valida_formulario()
    ok, mensaje = EliminarSolicitud(id_solicitud, session['usuario_id'], session['correo'])
    flash(str(mensaje), 'success' if ok else 'danger')
    return redirect(url_for('fdu.solicitudes'))


# === CRUD SESIONES: permisos delegados en sesion.py ===
@fdu.route('/sesiones/nueva', methods=['GET', 'POST'])
@requiere_acceso({4})
def nueva_sesion():
    if request.method == 'POST':
        valida_formulario()
        participantes = request.form.getlist('participantes')
        try:
            ok, mensaje = RegistrarSesion(session['usuario_id'],
                request.form.get('fecha'), request.form.get('inicio'), participantes,
                request.form.get('fin') or None)
        except Exception:
            current_app.logger.exception('Error registrando sesión')
            ok, mensaje = False, 'No se pudo crear la sesión.'
        flash(str(mensaje), 'success' if ok else 'danger')
        return redirect(url_for('fdu.sesiones' if ok else 'fdu.nueva_sesion'))
    miembros = consultar('SELECT id, nombre, apellidos FROM dbo.Usuario WHERE rol_id=3 AND estado_id=1 AND bloqueado=0')
    return render_template('nueva_sesion.html', miembros=miembros)


@fdu.route('/sesiones/<int:id_sesion>/editar', methods=['GET','POST'])
@requiere_acceso({4})
def editar_sesion(id_sesion):
    filas = consultar('SELECT IdSesion AS id, Fecha AS fecha, HoraInicio AS inicio, HoraFin AS fin, Estado AS estado FROM dbo.Sesion WHERE IdSesion=?', (id_sesion,))
    if not filas: abort(404)
    if request.method == 'POST':
        valida_formulario()
        cambios = {'Fecha': request.form.get('fecha'), 'HoraInicio': request.form.get('inicio'),
                   'HoraFin': request.form.get('fin') or None, 'Estado': request.form.get('estado')}
        try:
            ok, mensaje = ModificarSesion(id_sesion, cambios, session['usuario_id'])
        except Exception:
            current_app.logger.exception('Error modificando sesión')
            ok, mensaje = False, 'No se pudo modificar la sesión.'
        flash(str(mensaje), 'success' if ok else 'danger')
        return redirect(url_for('fdu.sesiones' if ok else 'fdu.editar_sesion', id_sesion=id_sesion))
    return render_template('editar_sesion.html', sesion=filas[0])


@fdu.route('/sesiones/<int:id_sesion>/eliminar', methods=['POST'])
@requiere_acceso({4})
def eliminar_sesion(id_sesion):
    valida_formulario()
    try:
        ok, mensaje = EliminarSesion(id_sesion, session['usuario_id'])
    except Exception:
        current_app.logger.exception('Error cancelando sesión')
        ok, mensaje = False, 'No se pudo cancelar la sesión.'
    flash(str(mensaje), 'success' if ok else 'danger')
    return redirect(url_for('fdu.sesiones'))
