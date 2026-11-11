/* ============================================================================
   SGFDU - Modulo de Gestion de Usuarios y Roles (GUR)
   Tablas: Rol, Usuario, Sesion, Bitacora
   Ejecutar completo en SSMS. Es re-ejecutable.
   ============================================================================ */
IF DB_ID(N'SGFDU') IS NULL
    CREATE DATABASE SGFDU;
GO

USE SGFDU;
GO
SELECT *
FROM USUARIO
/* ---------- Rol ---------- */
IF OBJECT_ID(N'dbo.Rol', N'U') IS NULL
CREATE TABLE dbo.Rol (
    id INT NOT NULL PRIMARY KEY,
    nombre NVARCHAR(80) NOT NULL UNIQUE
);
GO

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

/* ---------- Usuario ---------- */
IF OBJECT_ID(N'dbo.Usuario', N'U') IS NULL
CREATE TABLE dbo.Usuario (
    id                  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Usuario PRIMARY KEY,
    identificacion      NVARCHAR(20)  NOT NULL CONSTRAINT UQ_Usuario_identificacion UNIQUE,
    nombre              NVARCHAR(80)  NOT NULL,
    apellidos           NVARCHAR(100) NOT NULL,
    correo              NVARCHAR(150) NOT NULL CONSTRAINT UQ_Usuario_correo UNIQUE,
    telefono            NVARCHAR(20)  NULL,
    contrasena          NVARCHAR(255) NOT NULL,
    rol_id              INT           NOT NULL CONSTRAINT FK_Usuario_Rol REFERENCES dbo.Rol(id),
    estado_id INT NOT NULL
        CONSTRAINT DF_Usuario_estado DEFAULT 1
        CONSTRAINT FK_Usuario_Estado
        REFERENCES dbo.EstadoUsuario(id),
    intentos_fallidos   INT           NOT NULL CONSTRAINT DF_Usuario_intentos DEFAULT 0,
    bloqueado_hasta     DATETIME2(3)  NULL,
    fecha_creacion      DATETIME2(3)  NOT NULL
                                      CONSTRAINT DF_Usuario_fecha_creacion DEFAULT SYSUTCDATETIME(),
    fecha_desactivacion DATETIME2(3)  NULL
);
GO

IF OBJECT_ID(N'dbo.EstadoUsuario', N'U') IS NULL
CREATE TABLE dbo.EstadoUsuario (
    id     INT NOT NULL PRIMARY KEY,
    nombre NVARCHAR(20) NOT NULL UNIQUE
);
GO

INSERT INTO dbo.EstadoUsuario (id, nombre)
VALUES
(1, N'ACTIVO'),
(2, N'INACTIVO');
GO  

/* ---------- Sesion (permite cerrar sesion de verdad: GUR006) ---------- */
IF OBJECT_ID(N'dbo.Sesion', N'U') IS NULL
CREATE TABLE dbo.Sesion (
    id              INT IDENTITY(1,1) NOT NULL
                    CONSTRAINT PK_Sesion PRIMARY KEY,

    usuario_id      INT NOT NULL
                    CONSTRAINT FK_Sesion_Usuario
                    REFERENCES dbo.Usuario(id),

    fecha_creacion  DATETIME2(3) NOT NULL
                    CONSTRAINT DF_Sesion_fecha_creacion
                    DEFAULT SYSUTCDATETIME(),

    fecha_cierre    DATETIME2(3) NULL
);
GO


--Solicitudes
CREATE TABLE LineaAccion (
    IdLineaAccion INT IDENTITY(1,1) PRIMARY KEY,
    TextoLinea NVARCHAR(100) NOT NULL,
    MontoMaximo DECIMAL(18,2) NOT NULL,
    Porcentaje DECIMAL(5,2) NOT NULL
);

CREATE TABLE Solicitudes (
    IdSolicitud INT IDENTITY(1,1) PRIMARY KEY,
    NombreSolicitante NVARCHAR(100) NOT NULL,
    Carne NVARCHAR(20) NOT NULL,
    CorreoElectronico NVARCHAR(100) NOT NULL,
    NumeroCelular NVARCHAR(20) NOT NULL,
    MontoSolicitado DECIMAL(18,2) NOT NULL,
    InformacionBancaria NVARCHAR(200) NOT NULL,
    NombreActividad NVARCHAR(200) NOT NULL,
    LineaAccion INT not null
        CONSTRAINT FK_Solicitudes_Linea_Accion
        REFERENCES LineaAccion(idlineaAccion)
);

