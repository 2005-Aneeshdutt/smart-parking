# Smart Parking System 🅿️

Minimal steps to run the project locally.

## Database

1. Open MySQL and execute these scripts in order:
   - `smart_parking_database_1.sql`
   - `create_stored_procedure.sql`
   - `advanced_database_features.sql`

2. Create `backend/.env` with your MySQL credentials:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=smart_parking_database_1
   ```

## Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

## Frontend

From the project root directory (if you're in `backend`, run `cd ..` first):

```powershell
npm install
npm run dev
```

## Optional

Create an admin user (run inside `backend`):

```powershell
python create_admin.py
```

## Credentials

- Admin: `admin@parking.com` / `admin123`
- Driver: `alice@example.com` / `passAlice1`
- Driver: `bob@example.com` / `passBob1`
- Driver: `charlie@example.com` / `passChar1`

