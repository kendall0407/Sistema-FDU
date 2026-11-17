
import os
import pyodbc

def ObtenerConexion():
    servidor = os.environ.get(
        "FDU_SQL_SERVER",
        r"localhost\SQLEXPRESS"
    )

    conexion = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={servidor};"
        "DATABASE=SGFDU;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    return conexion
