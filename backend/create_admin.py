# Create admin user
from database import get_db
import bcrypt

def create_admin():
    db = get_db()
    if not db:
        print("Database connection failed!")
        return
    
    cursor = db.cursor()
    
    # Check if admin already exists
    cursor.execute("SELECT * FROM users WHERE email = %s", ("admin@parking.com",))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing user to admin
        cursor.execute("UPDATE users SET role = 'admin' WHERE email = %s", ("admin@parking.com",))
        print("Updated existing user to admin role")
    else:
        # Create new admin user
        password = "admin123"
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            ("Admin User", "admin@parking.com", pw_hash, "admin")
        )
        print("Admin user created!")
    
    db.commit()
    cursor.close()
    db.close()
    
    print("\nAdmin Login Credentials:")
    print("Email: admin@parking.com")
    print("Password: admin123")

if __name__ == "__main__":
    create_admin()

