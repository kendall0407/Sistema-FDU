"""Extensión de interfaz FDU para actas, agenda, evaluaciones y líneas de acción.
Registrar en app.py después de crear app: from rutas_extra_fdu import extra_fdu; app.register_blueprint(extra_fdu)
Reutiliza la sesión creada por el login existente y las funciones del backend.
"""
import secrets
from functools import wraps
from flask import Blueprint, request, session, redirect, url_for, render_template, flash, abort, current_app
from conexion import ObtenerConexion
from actas import CrearActa, ConsultarActa, ModificarActa, EliminarActa
from agenda import RegistrarAgendaSesion, ConsultarAgendaSesion, ModificarAgendaSesion, EliminarAgendaSesion
from evaluacion import RegistrarEvaluacion, ConsultarEvaluacion, ModificarEvaluacion, EliminarEvaluacion
from lineaAccion import CrearLineaAccion, ConsultarLineasAccion, ConsultarLineaAccion, ModificarLineaAccion, EliminarLineaAccion

extra_fdu = Blueprint('extra_fdu', __name__)

CONFIG = {
 'actas': {'titulo':'Actas','id':'IdActa','columns':[('IdActa','ID'),('IdSesion','Sesión'),('NombreResponsable','Responsable'),('EstadoSesion','Estado sesión')], 'fields':[('IdSesion','Sesión','session'),('Contenido','Contenido del acta','textarea')]},
 'agenda': {'titulo':'Agenda','id':'IdAgenda','columns':[('IdAgenda','ID'),('IdSesion','Sesión'),('Orden','Orden'),('Tema','Tema'),('NombreActividad','Solicitud'),('EstadoAgenda','Estado')], 'fields':[('IdSesion','Sesión','session'),('IdSolicitud','Solicitud (opcional)','solicitud_opt'),('Tema','Tema (si no hay solicitud)','text'),('Orden','Orden','number'),('Observaciones','Observaciones','textarea')]},
 'evaluaciones': {'titulo':'Evaluaciones','id':'IdEvaluacion','columns':[('IdEvaluacion','ID'),('IdSesion','Sesión'),('IdSolicitud','Solicitud'),('Decision','Decisión'),('MontoAprobado','Monto aprobado'),('NombreActividad','Actividad')], 'fields':[('IdSesion','Sesión','session'),('IdSolicitud','Solicitud','solicitud'),('Decision','Decisión','decision'),('MontoAprobado','Monto aprobado (solo si se aprueba)','decimal_opt'),('Observaciones','Observaciones','textarea')]},
 'lineas': {'titulo':'Líneas de acción','id':'IdLineaAccion','columns':[('IdLineaAccion','ID'),('TextoLinea','Nombre'),('MontoMaximo','Monto máximo'),('Porcentaje','Porcentaje'),('Estado','Estado')], 'fields':[('TextoLinea','Nombre de línea','text'),('MontoMaximo','Monto máximo','decimal'),('Porcentaje','Porcentaje (%)','decimal')]},
}


def require_login(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get('usuario_id') or session.get('modo_demo'):
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapped


def current_user():
    try:
        return int(session['usuario_id'])
    except (ValueError, TypeError, KeyError):
        abort(403)


def csrf_token():
    if '_extra_csrf' not in session:
        session['_extra_csrf'] = secrets.token_hex(24)
    return session['_extra_csrf']

@extra_fdu.app_context_processor
def token_context():
    return {'fdu_csrf_token':csrf_token}


def check_csrf():
    if not secrets.compare_digest(str(session.get('_extra_csrf','')), request.form.get('_csrf','')):
        abort(400, 'Formulario expirado: recargá la página e intentá de nuevo.')


def lookup_options():
    connection = ObtenerConexion()
    try:
        cursor=connection.cursor()
        cursor.execute('SELECT IdSesion, Fecha FROM dbo.Sesion ORDER BY IdSesion DESC')
        sesiones=[{'id':r[0],'label':f'Sesión {r[0]} · {r[1]}'} for r in cursor.fetchall()]
        cursor.execute('SELECT IdSolicitud, NombreActividad FROM dbo.Solicitudes ORDER BY IdSolicitud DESC')
        solicitudes=[{'id':r[0],'label':f'#{r[0]} · {r[1]}'} for r in cursor.fetchall()]
        return sesiones, solicitudes
    finally:
        connection.close()


def list_rows(modulo, uid, id_sesion=None):
    if modulo == 'actas': return ConsultarActa(usuario_id=uid)
    if modulo == 'evaluaciones': return ConsultarEvaluacion(usuario_id=uid)
    if modulo == 'lineas': return ConsultarLineasAccion(uid, incluir_inactivas=True)
    if modulo == 'agenda':
        if not id_sesion:
            return True, []
        return ConsultarAgendaSesion(id_sesion, uid)
    abort(404)


def detail(modulo, record_id, uid, id_sesion=None):
    if modulo == 'actas': return ConsultarActa(id_acta=record_id, usuario_id=uid)
    if modulo == 'evaluaciones':
        ok, data = ConsultarEvaluacion(usuario_id=uid, id_evaluacion=record_id)
        return ok, data[0] if ok and data else data
    if modulo == 'lineas': return ConsultarLineaAccion(record_id, uid)
    if modulo == 'agenda':
        if not id_sesion: return False, 'Indicá la sesión del punto de agenda.'
        ok, data=ConsultarAgendaSesion(id_sesion, uid)
        if not ok: return ok, data
        record=next((x for x in data if x['IdAgenda']==record_id),None)
        return (True,record) if record else (False,'Punto de agenda no encontrado.')
    abort(404)


def value(field):
    return request.form.get(field,'').strip()


def numeric(field, optional=False):
    raw=value(field)
    if not raw and optional: return None
    return int(raw)


def changes(modulo):
    if modulo=='actas': return {'Contenido':value('Contenido')}
    if modulo=='lineas': return {k:value(k) for k in ('TextoLinea','MontoMaximo','Porcentaje')}
    if modulo=='evaluaciones':
        return {'Decision':value('Decision'), 'MontoAprobado':value('MontoAprobado') or None, 'Observaciones':value('Observaciones') or None}
    if modulo=='agenda':
        solicitud=numeric('IdSolicitud', optional=True)
        return {'IdSolicitud':solicitud, 'Tema':None if solicitud else value('Tema'), 'Orden':numeric('Orden'), 'Observaciones':value('Observaciones') or None}


def create(modulo,uid):
    if modulo=='actas': return CrearActa(numeric('IdSesion'),value('Contenido'),uid)
    if modulo=='agenda':
        solicitud=numeric('IdSolicitud', optional=True)
        return RegistrarAgendaSesion(numeric('IdSesion'),solicitud,numeric('Orden'),uid,observaciones=value('Observaciones') or None,tema=None if solicitud else value('Tema'))
    if modulo=='evaluaciones': return RegistrarEvaluacion(numeric('IdSesion'),numeric('IdSolicitud'),value('Decision'),uid,monto_aprobado=value('MontoAprobado') or None,observaciones=value('Observaciones') or None)
    if modulo=='lineas': return CrearLineaAccion(value('TextoLinea'),value('MontoMaximo'),value('Porcentaje'),uid)
    abort(404)


def update(modulo,record_id,uid):
    data=changes(modulo)
    if modulo=='actas': return ModificarActa(record_id,data['Contenido'],uid)
    if modulo=='agenda': return ModificarAgendaSesion(record_id,data,uid)
    if modulo=='evaluaciones': return ModificarEvaluacion(record_id,data,uid)
    if modulo=='lineas': return ModificarLineaAccion(record_id,data,uid)
    abort(404)


def remove(modulo,record_id,uid):
    if modulo=='actas': return EliminarActa(record_id,uid)
    if modulo=='agenda': return EliminarAgendaSesion(record_id,uid)
    if modulo=='evaluaciones': return EliminarEvaluacion(record_id,uid)
    if modulo=='lineas': return EliminarLineaAccion(record_id,uid)
    abort(404)


@extra_fdu.route('/modulos/<modulo>')
@require_login
def listado(modulo):
    cfg=CONFIG.get(modulo)
    if cfg is None: abort(404)
    uid=current_user()
    sesiones=[]
    try:
        sesion_id=request.args.get('sesion',type=int)
        if modulo=='agenda': sesiones,_=lookup_options()
        ok, rows=list_rows(modulo,uid,sesion_id)
    except Exception:
        current_app.logger.exception('Error al listar %s',modulo)
        ok,rows=False,'No se pudo conectar con los datos de este módulo.'
    if not ok:
        flash(str(rows),'warning')
        rows=[]
    return render_template('fdu_extra_lista.html',modulo=modulo,cfg=cfg,filas=rows,sesiones=sesiones,sesion_id=sesion_id if modulo=='agenda' else None)


@extra_fdu.route('/modulos/<modulo>/nuevo', methods=['GET','POST'])
@require_login
def nuevo(modulo):
    cfg=CONFIG.get(modulo)
    if cfg is None: abort(404)
    if request.method=='POST':
        check_csrf()
        try:
            ok,msg=create(modulo,current_user())
        except (ValueError,TypeError):
            ok,msg=False,'Revisá los identificadores numéricos.'
        except Exception:
            current_app.logger.exception('Error creando %s',modulo)
            ok,msg=False,'Ocurrió un error al guardar.'
        flash(str(msg),'success' if ok else 'danger')
        if ok: return redirect(url_for('extra_fdu.listado',modulo=modulo))
    try: sesiones,solicitudes=lookup_options() if modulo!='lineas' else ([],[])
    except Exception:
        sesiones,solicitudes=[],[]
        flash('No se pudieron cargar las opciones de sesión o solicitud.','warning')
    return render_template('fdu_extra_form.html',modulo=modulo,cfg=cfg,registro={},sesiones=sesiones,solicitudes=solicitudes,editando=False)


@extra_fdu.route('/modulos/<modulo>/<int:record_id>/editar',methods=['GET','POST'])
@require_login
def editar(modulo,record_id):
    cfg=CONFIG.get(modulo)
    if cfg is None: abort(404)
    session_id=request.args.get('sesion',type=int) or request.form.get('sesion_original',type=int)
    uid=current_user()
    if request.method=='POST':
        check_csrf()
        try:
            ok,msg=update(modulo,record_id,uid)
        except (ValueError,TypeError):
            ok,msg=False,'Revisá los datos numéricos.'
        except Exception:
            current_app.logger.exception('Error editando %s',modulo)
            ok,msg=False,'Ocurrió un error al actualizar.'
        flash(str(msg),'success' if ok else 'danger')
        if ok: return redirect(url_for('extra_fdu.listado',modulo=modulo,**({'sesion':session_id} if session_id else {})))
    try:
        ok, registro=detail(modulo,record_id,uid,session_id)
    except Exception:
        current_app.logger.exception('Error consultando detalle %s',modulo)
        ok,registro=False,'No se pudo consultar el registro.'
    if not ok:
        flash(str(registro),'danger')
        return redirect(url_for('extra_fdu.listado',modulo=modulo))
    try: sesiones,solicitudes=lookup_options() if modulo!='lineas' else ([],[])
    except Exception: sesiones,solicitudes=[],[]
    return render_template('fdu_extra_form.html',modulo=modulo,cfg=cfg,registro=registro,sesiones=sesiones,solicitudes=solicitudes,editando=True,record_id=record_id,session_id=session_id)


@extra_fdu.route('/modulos/<modulo>/<int:record_id>/eliminar',methods=['POST'])
@require_login
def eliminar(modulo,record_id):
    if modulo not in CONFIG: abort(404)
    check_csrf()
    try: ok,msg=remove(modulo,record_id,current_user())
    except Exception:
        current_app.logger.exception('Error eliminando %s',modulo)
        ok,msg=False,'Ocurrió un error al cancelar o desactivar.'
    flash(str(msg),'success' if ok else 'danger')
    sesion_id=request.form.get('sesion_original',type=int)
    return redirect(url_for('extra_fdu.listado',modulo=modulo,**({'sesion':sesion_id} if sesion_id else {})))
