SELECT *
FROM Solicitudes

/* ============================================================================
   SGFDU - Modulo de Gestion de Usuarios y Solicitudes
   Ejecutar completo en SSMS. Es re-ejecutable.
   Si una tabla ya existe, no se modifica: los cambios solo aplican en una BD nueva.
   ============================================================================ */
IF DB_ID(N'SGFDU') IS NULL
    CREATE DATABASE SGFDU;
GO

USE SGFDU;
GO

/* ---------- Rol ---------- */
IF OBJECT_ID(N'dbo.Rol', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Rol (
        id      INT NOT NULL CONSTRAINT PK_Rol PRIMARY KEY,
        nombre  NVARCHAR(80) NOT NULL CONSTRAINT UQ_Rol_nombre UNIQUE
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.Rol)
    INSERT INTO dbo.Rol (id, nombre)
    VALUES
    (1, N'Estudiante'),
    (2, N'Estudiante Graduado'),
    (3, N'Miembro del Comite'),
    (4, N'Asistente del CIC'),
    (5, N'Administrativo');
GO

/* ---------- EstadoUsuario ---------- */
IF OBJECT_ID(N'dbo.EstadoUsuario', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.EstadoUsuario (
        id      INT NOT NULL CONSTRAINT PK_EstadoUsuario PRIMARY KEY,
        nombre  NVARCHAR(20) NOT NULL CONSTRAINT UQ_EstadoUsuario_nombre UNIQUE
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.EstadoUsuario)
    INSERT INTO dbo.EstadoUsuario (id, nombre)
    VALUES
    (1, N'ACTIVO'),
    (2, N'INACTIVO');
GO

/* ---------- Usuario ---------- */
IF OBJECT_ID(N'dbo.Usuario', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Usuario (
        id                  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Usuario PRIMARY KEY,
        identificacion      NVARCHAR(20)  NOT NULL CONSTRAINT UQ_Usuario_identificacion UNIQUE,
        nombre              NVARCHAR(80)  NOT NULL,
        apellidos           NVARCHAR(100) NOT NULL,
        correo              NVARCHAR(150) NOT NULL CONSTRAINT UQ_Usuario_correo UNIQUE,
        telefono            NVARCHAR(20)  NOT NULL,
        contrasena          NVARCHAR(255) NOT NULL,   -- hash de werkzeug, nunca texto plano
        rol_id              INT           NOT NULL CONSTRAINT FK_Usuario_Rol REFERENCES dbo.Rol(id),
        estado_id           INT           NOT NULL
            CONSTRAINT DF_Usuario_estado DEFAULT 1
            CONSTRAINT FK_Usuario_Estado REFERENCES dbo.EstadoUsuario(id),
        intentos_fallidos INT NOT NULL DEFAULT 0,
        bloqueado BIT NOT NULL DEFAULT 0,
        bloqueo_hasta DATETIME2(3) NULL,
        fecha_creacion DATETIME2(3) NOT NULL DEFAULT SYSDATETIME(),
        fecha_modificacion DATETIME2(3) NOT NULL DEFAULT SYSDATETIME(),
        fecha_desactivacion DATETIME2(3) NULL
    );
END;
GO

/* ---------- LineaAccion ---------- */
IF OBJECT_ID(N'dbo.LineaAccion', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.LineaAccion (
        IdLineaAccion       INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_LineaAccion PRIMARY KEY,
        TextoLinea          NVARCHAR(100) NOT NULL,
        MontoMaximo         DECIMAL(18,2) NOT NULL,
        Porcentaje          DECIMAL(5,2)  NOT NULL,
        Estado              NVARCHAR(15)  NOT NULL CONSTRAINT DF_LineaAccion_Estado DEFAULT 'ACTIVA',
        FechaModificacion   DATETIME2(3)  NULL,

        CONSTRAINT CK_LineaAccion_Estado
            CHECK (Estado IN ('ACTIVA', 'INACTIVA'))
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.LineaAccion)
    INSERT INTO dbo.LineaAccion (TextoLinea, MontoMaximo, Porcentaje)
    VALUES
    (N'Desarrollo profesional',                          500000.00,  10.00),
    (N'Proyectos de investigación',                     1000000.00,  10.00),
    (N'Propuestas de investigación',                     500000.00,  10.00),
    (N'Internacionalización y proyección',               550000.00,  20.00),
    (N'Inversión e infraestructura',                    1000000.00,  10.00),
    (N'Apoyo operativo',                                 300000.00,  10.00),
    (N'Capital semilla',                                1500000.00,  10.00),
    (N'Actividades especiales (interés institucional)', 3000000.00,  10.00),
    (N'Actividades especiales (interés de la Escuela)', 1500000.00,  10.00),
    (N'Apoyo grupal (por integrante)',                   550000.00,  10.00);
GO

/* ---------- HistorialLineaAccion ---------- */
IF OBJECT_ID(N'dbo.HistorialLineaAccion', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.HistorialLineaAccion (
        IdHistorial         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_HistorialLineaAccion PRIMARY KEY,
        IdLineaAccion       INT           NOT NULL,
        UsuarioModificador  INT           NOT NULL,
        TipoCambio          NVARCHAR(20)  NOT NULL,
        ValoresAnteriores   NVARCHAR(MAX) NULL,
        ValoresNuevos       NVARCHAR(MAX) NULL,
        FechaCambio         DATETIME2(3)  NOT NULL CONSTRAINT DF_HistorialLineaAccion_FechaCambio DEFAULT SYSDATETIME(),

        CONSTRAINT FK_HistorialLineaAccion_LineaAccion
            FOREIGN KEY (IdLineaAccion) REFERENCES dbo.LineaAccion(IdLineaAccion),
        CONSTRAINT FK_HistorialLineaAccion_Usuario
            FOREIGN KEY (UsuarioModificador) REFERENCES dbo.Usuario(id),
        CONSTRAINT CK_HistorialLineaAccion_Tipo
            CHECK (TipoCambio IN ('CREACION', 'MODIFICACION', 'ELIMINACION'))
    );
END;
GO

/* ---------- EstadoSolicitud (catálogo) ---------- */
IF OBJECT_ID(N'dbo.EstadoSolicitud', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.EstadoSolicitud (
        id      INT NOT NULL CONSTRAINT PK_EstadoSolicitud PRIMARY KEY,
        nombre  NVARCHAR(30) NOT NULL CONSTRAINT UQ_EstadoSolicitud_nombre UNIQUE
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.EstadoSolicitud)
    INSERT INTO dbo.EstadoSolicitud (id, nombre)
    VALUES
    (1, N'REGISTRADA'),
    (2, N'INFO_ADICIONAL'),
    (3, N'ELIMINADA');
GO

/* ---------- Solicitudes ---------- */
IF OBJECT_ID(N'dbo.Solicitudes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Solicitudes (
        IdSolicitud         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Solicitudes PRIMARY KEY,
        usuario_id          INT           NOT NULL CONSTRAINT FK_Solicitudes_Usuario REFERENCES dbo.Usuario(id),
        NombreSolicitante   NVARCHAR(100) NOT NULL,
        Carne               NVARCHAR(20)  NOT NULL,
        CorreoElectronico   NVARCHAR(100) NOT NULL,
        NumeroCelular       NVARCHAR(20)  NOT NULL,
        rol_id              INT           NOT NULL CONSTRAINT FK_Solicitudes_Rol REFERENCES dbo.Rol(id),
        MontoSolicitado     DECIMAL(18,2) NOT NULL,
        InformacionBancaria NVARCHAR(200) NOT NULL,
        NombreActividad     NVARCHAR(200) NOT NULL,
        Justificacion       NVARCHAR(400) NOT NULL,
        LineaAccion         INT           NOT NULL CONSTRAINT FK_Solicitudes_LineaAccion REFERENCES dbo.LineaAccion(IdLineaAccion),
        estado_id           INT           NOT NULL
            CONSTRAINT DF_Solicitudes_estado DEFAULT 1
            CONSTRAINT FK_Solicitudes_Estado REFERENCES dbo.EstadoSolicitud(id),
        observaciones       NVARCHAR(400) NULL,       -- observaciones del Comité (GS005)
        fecha_creacion      DATETIME2(3)  NOT NULL CONSTRAINT DF_Solicitudes_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_modificacion  DATETIME2(3)  NOT NULL CONSTRAINT DF_Solicitudes_fecha_modificacion DEFAULT SYSDATETIME()
    );
END;
GO

/* ---------- Sesion ---------- */
IF OBJECT_ID(N'dbo.Sesion', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sesion (
        IdSesion            INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Sesion PRIMARY KEY,
        Fecha               DATE          NOT NULL,
        HoraInicio          TIME(0)       NOT NULL,
        HoraFin             TIME(0)       NULL,
        Estado              NVARCHAR(20)  NOT NULL CONSTRAINT DF_Sesion_Estado DEFAULT 'PROGRAMADA',
        UsuarioCreador      INT           NOT NULL,
        FechaCreacion       DATETIME2(3)  NOT NULL CONSTRAINT DF_Sesion_FechaCreacion DEFAULT SYSDATETIME(),
        FechaModificacion   DATETIME2(3)  NULL,

        CONSTRAINT FK_Sesion_Usuario
            FOREIGN KEY (UsuarioCreador) REFERENCES dbo.Usuario(id),
        CONSTRAINT CK_Sesion_Estado
            CHECK (Estado IN ('PROGRAMADA', 'REALIZADA', 'CANCELADA')),
        CONSTRAINT CK_Sesion_Horario
            CHECK (HoraFin IS NULL OR HoraFin > HoraInicio)
    );
END;
GO

/* ---------- AgendaSesion ---------- */
IF OBJECT_ID(N'dbo.AgendaSesion', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.AgendaSesion (
        IdAgenda            INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_AgendaSesion PRIMARY KEY,
        IdSesion            INT           NULL,       -- NULL si el punto no pertenece a una sesión
        IdSolicitud         INT           NULL,       -- NULL si el punto es un tema general
        Tema                NVARCHAR(200) NULL,       -- temas generales (no solicitudes)
        Orden               INT           NOT NULL,
        Observaciones       NVARCHAR(MAX) NULL,
        Estado              NVARCHAR(15)  NOT NULL CONSTRAINT DF_AgendaSesion_Estado DEFAULT 'PROGRAMADO',
        FechaModificacion   DATETIME2(3)  NULL,

        CONSTRAINT FK_AgendaSesion_Sesion
            FOREIGN KEY (IdSesion) REFERENCES dbo.Sesion(IdSesion),
        CONSTRAINT FK_AgendaSesion_Solicitudes
            FOREIGN KEY (IdSolicitud) REFERENCES dbo.Solicitudes(IdSolicitud),
        CONSTRAINT UQ_AgendaSesion_Orden
            UNIQUE (IdSesion, Orden),
        CONSTRAINT CK_AgendaSesion_Orden
            CHECK (Orden > 0),
        CONSTRAINT CK_AgendaSesion_Estado
            CHECK (Estado IN ('PROGRAMADO', 'CANCELADO')),
        CONSTRAINT CK_AgendaSesion_TipoPunto
            CHECK (
                (IdSolicitud IS NOT NULL AND Tema IS NULL)
                OR
                (IdSolicitud IS NULL AND Tema IS NOT NULL AND LEN(LTRIM(RTRIM(Tema))) > 0)
            )
    );

    -- Una solicitud no puede repetirse en la misma sesión
    CREATE UNIQUE INDEX IX_AgendaSesion_Solicitud_Unica
        ON dbo.AgendaSesion (IdSesion, IdSolicitud)
        WHERE IdSolicitud IS NOT NULL;
END;
GO

/* ---------- ParticipanteSesion ---------- */
IF OBJECT_ID(N'dbo.ParticipanteSesion', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ParticipanteSesion (
        IdParticipanteSesion INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_ParticipanteSesion PRIMARY KEY,
        IdSesion             INT          NOT NULL,
        IdUsuario            INT          NOT NULL,
        Asistencia           NVARCHAR(15) NOT NULL CONSTRAINT DF_ParticipanteSesion_Asistencia DEFAULT 'PENDIENTE',

        CONSTRAINT FK_ParticipanteSesion_Sesion
            FOREIGN KEY (IdSesion) REFERENCES dbo.Sesion(IdSesion),
        CONSTRAINT FK_ParticipanteSesion_Usuario
            FOREIGN KEY (IdUsuario) REFERENCES dbo.Usuario(id),
        CONSTRAINT UQ_ParticipanteSesion
            UNIQUE (IdSesion, IdUsuario),
        CONSTRAINT CK_ParticipanteSesion_Asistencia
            CHECK (Asistencia IN ('PENDIENTE', 'ASISTIO', 'AUSENTE'))
    );
END;
GO

/* ---------- Acta ---------- */
IF OBJECT_ID(N'dbo.Acta', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Acta (
        IdActa              INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Acta PRIMARY KEY,
        IdSesion            INT           NOT NULL,
        Contenido           NVARCHAR(MAX) NULL,
        FechaCreacion       DATETIME2(3)  NOT NULL CONSTRAINT DF_Acta_FechaCreacion DEFAULT SYSDATETIME(),
        FechaModificacion   DATETIME2(3)  NULL,
        UsuarioResponsable  INT           NOT NULL,
        Estado              NVARCHAR(15)  NOT NULL CONSTRAINT DF_Acta_Estado DEFAULT 'ACTIVA',

        CONSTRAINT FK_Acta_Sesion
            FOREIGN KEY (IdSesion) REFERENCES dbo.Sesion(IdSesion),
        CONSTRAINT FK_Acta_Usuario
            FOREIGN KEY (UsuarioResponsable) REFERENCES dbo.Usuario(id),
        CONSTRAINT UQ_Acta_Sesion
            UNIQUE (IdSesion),
        CONSTRAINT CK_Acta_Estado
            CHECK (Estado IN ('ACTIVA', 'CANCELADA'))
    );
END;
GO

/* ---------- Evaluacion ---------- */
IF OBJECT_ID(N'dbo.Evaluacion', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Evaluacion (
        IdEvaluacion        INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Evaluacion PRIMARY KEY,
        IdSesion            INT           NOT NULL,
        IdSolicitud         INT           NOT NULL,
        Decision            NVARCHAR(30)  NOT NULL,
        MontoAprobado       DECIMAL(18,2) NULL,
        Observaciones       NVARCHAR(MAX) NULL,
        FechaEvaluacion     DATETIME2(3)  NOT NULL CONSTRAINT DF_Evaluacion_FechaEvaluacion DEFAULT SYSDATETIME(),
        FechaModificacion   DATETIME2(3)  NULL,
        EstadoEvaluacion    NVARCHAR(15)  NOT NULL CONSTRAINT DF_Evaluacion_Estado DEFAULT 'ACTIVA',

        CONSTRAINT FK_Evaluacion_Sesion
            FOREIGN KEY (IdSesion) REFERENCES dbo.Sesion(IdSesion),
        CONSTRAINT FK_Evaluacion_Solicitud
            FOREIGN KEY (IdSolicitud) REFERENCES dbo.Solicitudes(IdSolicitud),
        CONSTRAINT CK_Evaluacion_Decision
            CHECK (Decision IN ('APROBADA', 'RECHAZADA', 'INFORMACION_ADICIONAL')),
        CONSTRAINT CK_Evaluacion_MontoAprobado
            CHECK (MontoAprobado IS NULL OR MontoAprobado >= 0),
        CONSTRAINT CK_Evaluacion_Estado
            CHECK (EstadoEvaluacion IN ('ACTIVA', 'CANCELADA'))
    );
END;
GO
