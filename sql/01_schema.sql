/* ============================================================================
   SGFDU - Modulo de Gestion de Usuarios y Solicitudes
   Tablas: Rol, EstadoUsuario, Usuario, LineaAccion, EstadoSolicitud,
           Posicion, Solicitudes
   Ejecutar completo en SSMS. Es re-ejecutable.
   ============================================================================ */
IF DB_ID(N'SGFDU') IS NULL
    CREATE DATABASE SGFDU;
GO

USE SGFDU;
GO

/* ---------- Rol ---------- */
IF OBJECT_ID(N'dbo.Rol', N'U') IS NULL
CREATE TABLE dbo.Rol (
    id      INT NOT NULL CONSTRAINT PK_Rol PRIMARY KEY,
    nombre  NVARCHAR(80) NOT NULL CONSTRAINT UQ_Rol_nombre UNIQUE
);
GO

IF NOT EXISTS (SELECT 1 FROM dbo.Rol)
    INSERT INTO dbo.Rol (id, nombre)
    VALUES
    (1, N'Persona solicitante'),
    (2, N'Unidad solicitante'),
    (3, N'Estudiante o persona graduada'),
    (4, N'Profesor que avala'),
    (5, N'Integrante del Comité Técnico'),
    (6, N'Coordinación del Comité'),
    (7, N'Consejo de Escuela'),
    (8, N'Administración del sistema'),
    (9, N'Consulta y auditoría');
GO

/* ---------- EstadoUsuario ---------- */
IF OBJECT_ID(N'dbo.EstadoUsuario', N'U') IS NULL
CREATE TABLE dbo.EstadoUsuario (
    id      INT NOT NULL CONSTRAINT PK_EstadoUsuario PRIMARY KEY,
    nombre  NVARCHAR(20) NOT NULL CONSTRAINT UQ_EstadoUsuario_nombre UNIQUE
);
GO

IF NOT EXISTS (SELECT 1 FROM dbo.EstadoUsuario)
    INSERT INTO dbo.EstadoUsuario (id, nombre)
    VALUES
    (1, N'ACTIVO'),
    (2, N'INACTIVO');
GO

/* ---------- Usuario ---------- */
IF OBJECT_ID(N'dbo.Usuario', N'U') IS NULL
CREATE TABLE dbo.Usuario (
    id                  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Usuario PRIMARY KEY,
    identificacion      NVARCHAR(20)  NOT NULL CONSTRAINT UQ_Usuario_identificacion UNIQUE,
    nombre              NVARCHAR(80)  NOT NULL,
    apellidos           NVARCHAR(100) NOT NULL,
    correo              NVARCHAR(150) NOT NULL CONSTRAINT UQ_Usuario_correo UNIQUE,
    telefono            NVARCHAR(20)  NULL,
    contrasena          NVARCHAR(255) NOT NULL,   -- hash de werkzeug, nunca texto plano
    rol_id              INT           NOT NULL CONSTRAINT FK_Usuario_Rol REFERENCES dbo.Rol(id),
    estado_id           INT           NOT NULL
        CONSTRAINT DF_Usuario_estado DEFAULT 1
        CONSTRAINT FK_Usuario_Estado REFERENCES dbo.EstadoUsuario(id),
    intentos_fallidos   INT           NOT NULL CONSTRAINT DF_Usuario_intentos DEFAULT 0,
    bloqueado_hasta     DATETIME2(3)  NULL,
    fecha_creacion      DATETIME2(3)  NOT NULL CONSTRAINT DF_Usuario_fecha_creacion DEFAULT SYSDATETIME(),
    fecha_modificacion  DATETIME2(3)  NOT NULL CONSTRAINT DF_Usuario_fecha_modificacion DEFAULT SYSDATETIME(),
    fecha_desactivacion DATETIME2(3)  NULL
);
GO

/* ---------- LineaAccion ---------- */
IF OBJECT_ID(N'dbo.LineaAccion', N'U') IS NULL
CREATE TABLE dbo.LineaAccion (
    IdLineaAccion   INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_LineaAccion PRIMARY KEY,
    TextoLinea      NVARCHAR(100) NOT NULL,
    MontoMaximo     DECIMAL(18,2) NOT NULL,
    Porcentaje      DECIMAL(5,2)  NOT NULL
);
GO

IF NOT EXISTS (SELECT 1 FROM dbo.LineaAccion)
    INSERT INTO dbo.LineaAccion (TextoLinea, MontoMaximo, Porcentaje)
    VALUES
    (N'Desarrollo profesional',                          500000.00,  70.00),
    (N'Proyectos de investigación',                     1000000.00, 100.00),
    (N'Propuestas de investigación',                     500000.00, 100.00),
    (N'Internacionalización y proyección',               550000.00, 100.00),
    (N'Inversión e infraestructura',                    1000000.00, 100.00),
    (N'Apoyo operativo',                                 300000.00, 100.00),
    (N'Capital semilla',                                1500000.00, 100.00),
    (N'Actividades especiales (interés institucional)', 3000000.00, 100.00),
    (N'Actividades especiales (interés de la Escuela)', 1500000.00, 100.00),
    (N'Apoyo grupal (por integrante)',                   550000.00, 100.00);
GO

/* ---------- EstadoSolicitud (catálogo) ---------- */
IF OBJECT_ID(N'dbo.EstadoSolicitud', N'U') IS NULL
CREATE TABLE dbo.EstadoSolicitud (
    id      INT NOT NULL CONSTRAINT PK_EstadoSolicitud PRIMARY KEY,
    nombre  NVARCHAR(30) NOT NULL CONSTRAINT UQ_EstadoSolicitud_nombre UNIQUE
);
GO

IF NOT EXISTS (SELECT 1 FROM dbo.EstadoSolicitud)
    INSERT INTO dbo.EstadoSolicitud (id, nombre)
    VALUES
    (1, N'REGISTRADA'),
    (2, N'INFO_ADICIONAL'),
    (3, N'ELIMINADA');
GO

/* ---------- Posicion (catálogo) ---------- */
IF OBJECT_ID(N'dbo.Posicion', N'U') IS NULL
CREATE TABLE dbo.Posicion (
    id      INT NOT NULL CONSTRAINT PK_Posicion PRIMARY KEY,
    nombre  NVARCHAR(30) NOT NULL CONSTRAINT UQ_Posicion_nombre UNIQUE
);
GO

IF NOT EXISTS (SELECT 1 FROM dbo.Posicion)
    INSERT INTO dbo.Posicion (id, nombre)
    VALUES
    (1, N'Docente'),
    (2, N'Estudiante'),
    (3, N'Administrativo');
GO

/* ---------- Solicitudes ---------- */
IF OBJECT_ID(N'dbo.Solicitudes', N'U') IS NULL
CREATE TABLE dbo.Solicitudes (
    IdSolicitud         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Solicitudes PRIMARY KEY,
    usuario_id          INT           NOT NULL CONSTRAINT FK_Solicitudes_Usuario REFERENCES dbo.Usuario(id),
    Identificacion      NVARCHAR(20)  NOT NULL,
    NombreSolicitante   NVARCHAR(100) NOT NULL,
    Carne               NVARCHAR(20)  NOT NULL,
    CorreoElectronico   NVARCHAR(100) NOT NULL,
    NumeroCelular       NVARCHAR(20)  NOT NULL,
    posicion_id         INT           NOT NULL CONSTRAINT FK_Solicitudes_Posicion REFERENCES dbo.Posicion(id),
    MontoSolicitado     DECIMAL(18,2) NOT NULL,
    InformacionBancaria NVARCHAR(200) NOT NULL,
    NombreActividad     NVARCHAR(200) NOT NULL,
    Justificacion       NVARCHAR(MAX) NOT NULL,
    LineaAccion         INT           NOT NULL CONSTRAINT FK_Solicitudes_LineaAccion REFERENCES dbo.LineaAccion(IdLineaAccion),
    estado_id           INT           NOT NULL
        CONSTRAINT DF_Solicitudes_estado DEFAULT 1
        CONSTRAINT FK_Solicitudes_Estado REFERENCES dbo.EstadoSolicitud(id),
    observaciones       NVARCHAR(MAX) NULL,       -- observaciones del Comité (GS005)
    fecha_creacion      DATETIME2(3)  NOT NULL CONSTRAINT DF_Solicitudes_fecha_creacion DEFAULT SYSDATETIME(),
    fecha_modificacion  DATETIME2(3)  NOT NULL CONSTRAINT DF_Solicitudes_fecha_modificacion DEFAULT SYSDATETIME()
);
GO