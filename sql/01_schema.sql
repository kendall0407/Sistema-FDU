SELECT *
FROM Rol
SELECT *
FROM Usuario
SELECT *
FROM Solicitudes
SELECT *
FROM EstadoUsuario

SELECT *
FROM EstadoSolicitud
SELECT *
FROM LineaAccion


/* ============================================================================
   SGFDU - Modulo de Gestion de Usuarios y Solicitudes
   Tablas: Rol, EstadoUsuario, Usuario, LineaAccion, EstadoSolicitud,
           Posicion, Solicitudes, Sesion, Actas, ParticipanteSesion, AgendaSesion
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
    (1, N'Estudiante'),
    (2, N'Estudiante Graduado'),
    (3, N'Miembro del Comite'),
    (4, N'Asistente del CIC'),
    (5, N'Administrativo');
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
    telefono            NVARCHAR(20)  NOT NULL,
    contrasena          NVARCHAR(255) NOT NULL,   -- hash de werkzeug, nunca texto plano
    rol_id              INT           NOT NULL CONSTRAINT FK_Usuario_Rol REFERENCES dbo.Rol(id),
    estado_id           INT           NOT NULL
        CONSTRAINT DF_Usuario_estado DEFAULT 1
        CONSTRAINT FK_Usuario_Estado REFERENCES dbo.EstadoUsuario(id),
    intentos_fallidos   INT           NOT NULL CONSTRAINT DF_Usuario_intentos DEFAULT 0,
    bloqueado           bit           NOT NULL,CONSTRAINT DF_Usuario_bloqueado DEFAULT 0,
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


/* ---------- Solicitudes ---------- */
IF OBJECT_ID(N'dbo.Solicitudes', N'U') IS NULL
CREATE TABLE dbo.Solicitudes (
    IdSolicitud         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Solicitudes PRIMARY KEY,
    usuario_id          INT           NOT NULL CONSTRAINT FK_Solicitudes_Usuario REFERENCES dbo.Usuario(id),
    NombreSolicitante   NVARCHAR(100) NOT NULL,
    Carne               NVARCHAR(20)  NOT NULL,
    CorreoElectronico   NVARCHAR(100) NOT NULL,
    NumeroCelular       NVARCHAR(20)  NOT NULL,
    rol_id INT NOT NULL
        CONSTRAINT FK_Solicitudes_Rol REFERENCES dbo.Rol(id),
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
GO



--Sesiones
-- ==========================================
-- 1. TABLA SESION
-- ==========================================

IF OBJECT_ID('dbo.Sesion', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sesion (
        IdSesion INT IDENTITY(1,1) PRIMARY KEY,
        Fecha DATE NOT NULL,
        HoraInicio TIME(0) NOT NULL,
        HoraFin TIME(0) NULL,
        Estado NVARCHAR(20) NOT NULL DEFAULT 'PROGRAMADA',

        UsuarioCreador INT NOT NULL,

        FechaCreacion DATETIME2(3) NOT NULL
            DEFAULT SYSDATETIME(),

        CONSTRAINT FK_Sesion_Usuario
            FOREIGN KEY (UsuarioCreador)
            REFERENCES dbo.Usuario(id),

        CONSTRAINT CK_Sesion_Estado
            CHECK (Estado IN ('PROGRAMADA', 'REALIZADA', 'CANCELADA')),

        CONSTRAINT CK_Sesion_Horario
            CHECK (HoraFin IS NULL OR HoraFin > HoraInicio)
    );
END;
GO


-- ==========================================
-- 2. TABLA AGENDASESION
-- ==========================================

IF OBJECT_ID('dbo.AgendaSesion', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.AgendaSesion (
        IdAgenda INT IDENTITY(1,1) PRIMARY KEY,
        IdSesion INT NULL, --en caso de que se deseen tratar otros temas 
        IdSolicitud INT NOT NULL,
        Orden INT NOT NULL,
        Observaciones NVARCHAR(MAX) NULL,

        CONSTRAINT FK_AgendaSesion_Sesion
            FOREIGN KEY (IdSesion)
            REFERENCES dbo.Sesion(IdSesion),

        CONSTRAINT FK_AgendaSesion_Solicitudes
            FOREIGN KEY (IdSolicitud)
            REFERENCES dbo.Solicitudes(IdSolicitud),

        CONSTRAINT UQ_AgendaSesion_Solicitud
            UNIQUE (IdSesion, IdSolicitud),

        CONSTRAINT UQ_AgendaSesion_Orden
            UNIQUE (IdSesion, Orden),

        CONSTRAINT CK_AgendaSesion_Orden
            CHECK (Orden > 0)
    );
END;
GO


-- ==========================================
-- 3. TABLA PARTICIPANTESESION
-- ==========================================

IF OBJECT_ID('dbo.ParticipanteSesion', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ParticipanteSesion (
        IdParticipanteSesion INT IDENTITY(1,1) PRIMARY KEY,
        IdSesion INT NOT NULL,
        IdUsuario INT NOT NULL,
        Asistencia NVARCHAR(15) NOT NULL DEFAULT 'PENDIENTE',

        CONSTRAINT FK_ParticipanteSesion_Sesion
            FOREIGN KEY (IdSesion)
            REFERENCES dbo.Sesion(IdSesion),

        CONSTRAINT FK_ParticipanteSesion_Usuario
            FOREIGN KEY (IdUsuario)
            REFERENCES dbo.Usuario(id),

        CONSTRAINT UQ_ParticipanteSesion
            UNIQUE (IdSesion, IdUsuario),

        CONSTRAINT CK_ParticipanteSesion_Asistencia
            CHECK (Asistencia IN ('PENDIENTE', 'ASISTIO', 'AUSENTE'))
    );
END;
GO


-- ==========================================
-- 4. TABLA ACTA
-- ==========================================

IF OBJECT_ID('dbo.Acta', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Acta (
        IdActa INT IDENTITY(1,1) PRIMARY KEY,
        IdSesion INT NOT NULL,
        Contenido NVARCHAR(MAX) NULL,

        FechaCreacion DATETIME2(3) NOT NULL
            DEFAULT SYSDATETIME(),

        FechaModificacion DATETIME2(3) NULL,

        UsuarioResponsable INT NOT NULL,

        CONSTRAINT FK_Acta_Sesion
            FOREIGN KEY (IdSesion)
            REFERENCES dbo.Sesion(IdSesion),

        CONSTRAINT FK_Acta_Usuario
            FOREIGN KEY (UsuarioResponsable)
            REFERENCES dbo.Usuario(id),

        CONSTRAINT UQ_Acta_Sesion
            UNIQUE (IdSesion)
    );
END;
GO

-- alter

-- Permitir puntos de agenda que no sean solicitudes
ALTER TABLE dbo.AgendaSesion
ALTER COLUMN IdSolicitud INT NULL;
GO

-- Agregar campo para describir temas generales
ALTER TABLE dbo.AgendaSesion
ADD Tema NVARCHAR(200) NULL;
GO

-- Eliminar restricción UNIQUE anterior
ALTER TABLE dbo.AgendaSesion
DROP CONSTRAINT UQ_AgendaSesion_Solicitud;
GO

-- Una solicitud no puede repetirse en la misma sesión
CREATE UNIQUE INDEX IX_AgendaSesion_Solicitud_Unica
ON dbo.AgendaSesion (IdSesion, IdSolicitud)
WHERE IdSolicitud IS NOT NULL;
GO

-- Cada punto debe ser una solicitud o un tema, nunca ambos
ALTER TABLE dbo.AgendaSesion
ADD CONSTRAINT CK_AgendaSesion_TipoPunto
CHECK (
    (IdSolicitud IS NOT NULL AND Tema IS NULL)
    OR
    (IdSolicitud IS NULL AND Tema IS NOT NULL
     AND LEN(LTRIM(RTRIM(Tema))) > 0)
);
GO

--
ALTER TABLE Sesion
ADD FechaModificacion DATETIME2(3) NULL;