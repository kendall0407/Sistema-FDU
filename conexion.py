import pyodbc

def ObtenerConexion():
    global conexion
    conexion = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=DESKTOP-EANBJGP\\SQLEXPRESS;"
        "DATABASE=SGFDU;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    return conexion