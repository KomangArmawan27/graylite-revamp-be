import pyodbc

conn_str = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=graylite1.database.windows.net;DATABASE=DB_OFA;UID=userjvi;PWD=Theking$123;Encrypt=yes;TrustServerCertificate=yes"

try:
    conn = pyodbc.connect(conn_str, timeout=10)
    print("SUCCESS!")
    conn.close()
except Exception as e:
    print("FAILED:", e)
