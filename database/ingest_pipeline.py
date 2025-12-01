# database/ingest_pipeline.py

import json
import sqlite3

DB_PATH = "database/bbk.db"

def insert_rotor(conn, rotor: dict):
    fields = ",".join(rotor.keys())
    placeholders = ",".join(["?"] * len(rotor))
    sql = f"INSERT INTO rotors ({fields}) VALUES ({placeholders})"
    conn.execute(sql, list(rotor.values()))

def insert_pad(conn, pad: dict):
    fields = ",".join(pad.keys())
    placeholders = ",".join(["?"] * len(pad))
    sql = f"INSERT INTO pads ({fields}) VALUES ({placeholders})"
    conn.execute(sql, list(pad.values()))

def insert_vehicle(conn, vh: dict):
    fields = ",".join(vh.keys())
    placeholders = ",".join(["?"] * len(vh))
    sql = f"INSERT INTO vehicles ({fields}) VALUES ({placeholders})"
    conn.execute(sql, list(vh.values()))

def ingest_jsonl(path: str, table: str):
    conn = sqlite3.connect(DB_PATH)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            if table == "rotors":
                insert_rotor(conn, obj)
            elif table == "pads":
                insert_pad(conn, obj)
            elif table == "vehicles":
                insert_vehicle(conn, obj)
    conn.commit()
    conn.close()
