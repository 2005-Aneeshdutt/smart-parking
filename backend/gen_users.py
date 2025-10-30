# seed_users_vehicles.py
import mysql.connector
import bcrypt

DB = {
    "host": "localhost",
    "user": "root",
    "password": "2005Nag$",
    "database": "smart_parking_database_1"
}

users = [
    ("Alice Johnson", "alice@example.com", "passAlice1"),
    ("Bob Kumar", "bob@example.com", "passBob1"),
    ("Charlie Rao", "charlie@example.com", "passChar1"),
    ("Deepa Singh", "deepa@example.com", "passDeep1"),
    ("Esha Patel", "esha@example.com", "passEsha1"),
    ("Farhan Ali", "farhan@example.com", "passFarh1"),
    ("Gita Menon", "gita@example.com", "passGita1"),
    ("Hemanth R", "hemanth@example.com", "passHem1"),
    ("Isha Verma", "isha@example.com", "passIsha1"),
    ("Jatin Sharma", "jatin@example.com", "passJatin1")
]

vehicles = [
    ("KA01AB1234", "car"),
    ("KA02CD5678", "car"),
    ("KA03EF9012", "bike"),
    ("KA05GH3456", "car"),
    ("KA06IJ7890", "scooter"),
    ("KA07KL2345", "car"),
    ("KA08MN6789", "car"),
    ("KA09OP0123", "bike"),
    ("KA10QR4567", "car"),
    ("KA11ST8901", "car")
]

def main():
    conn = mysql.connector.connect(**DB)
    cursor = conn.cursor()

    # insert users
    for idx, (name, email, plaintext) in enumerate(users):
        pw_hash = bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (name, email, pw_hash, 'driver')
        )
        user_id = cursor.lastrowid

        license_plate, vtype = vehicles[idx]
        cursor.execute(
            "INSERT INTO vehicles (user_id, license_plate, vehicle_type) VALUES (%s, %s, %s)",
            (user_id, license_plate, vtype)
        )

    conn.commit()
    cursor.close()
    conn.close()
    print("Inserted 10 users and vehicles.")

if __name__ == "__main__":
    main()
