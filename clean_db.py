import sqlite3

conn = sqlite3.connect('mintkit.db')
cur = conn.cursor()
cur.execute("DELETE FROM deployments WHERE mint_address = '8vNNsZVcWheSdGJvMm8Me3kznfkeGRccb3CK8d5VUfW1'")
conn.commit()
conn.close()
print("Duplicate removed!")
