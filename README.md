# Smart Parking System 🅿️

A full-stack web application for managing parking lot reservations with real-time availability tracking, booking management, and admin dashboard.


1. **Open MySQL Workbench** and connect to your MySQL server

2. **Run SQL File 1: `smart_parking_database_1.sql`**
   - **File → Open SQL Script** → Select `smart_parking_database_1.sql`
   - Click **Execute** (⚡ button)
   - **Creates:**
     - Database `smart_parking_database_1`
     - Tables: `parking_lots`, `parking_spots`, `users`, `vehicles`
     - Sample data: 30 parking lots and 10 test users

3. **Run SQL File 2: `create_stored_procedure.sql`**
   - **File → Open SQL Script** → Select `create_stored_procedure.sql`
   - Click **Execute**
   - **Creates:**
     - `reservations` table (for storing bookings)
     - `make_reservation1` stored procedure (for booking logic)

4. **Run SQL File 3: `advanced_database_features.sql`**
   - **File → Open SQL Script** → Select `advanced_database_features.sql`
   - Click **Execute**
   - **Creates:**
     - 3 Functions: `calculate_parking_cost`, `check_available_spots`, `get_lot_status`
     - 4 Triggers: Auto-update spots on booking create/delete/update
     - 3 Views: `v_parking_lot_summary`, `v_user_bookings`, `v_lot_revenue_summary`
     - Audit table for tracking changes

5. **Verify Database:**
   ```sql
   USE smart_parking_database_1;
   SHOW TABLES;  -- Should show: parking_lots, parking_spots, users, vehicles, reservations
   SHOW FULL TABLES WHERE Table_type = 'VIEW';  -- Should show 3 views
   ```

---

### Step 3: Backend Setup

1. **Open Terminal/PowerShell** and navigate to project folder:
   ```powershell
   cd "path\to\Smart_parking2"
   cd backend
   ```

2. **Activate Virtual Environment:**
   ```powershell
   # If venv folder exists:
   .\venv\Scripts\Activate.ps1
   
   # OR create new venv:
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Python Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Create `.env` File:**
   - Create a new file named `.env` in the `backend` folder (no extension)
   - Add the following content:
     ```
     DB_HOST=localhost
     DB_USER=root
     DB_PASSWORD=your_mysql_password_here
     DB_NAME=smart_parking_database_1
     ```
   - **Replace `your_mysql_password_here`** with your actual MySQL root password
   - **If MySQL has no password**, use: `DB_PASSWORD=`

5. **(Optional) Generate Test Users:**
   ```powershell
   python gen_users.py
   ```
   - Note: You may need to update database credentials in `gen_users.py` if different from `.env`

6. **Start Backend Server:**
   ```powershell
   uvicorn main:app --reload
   ```
   - Backend will run on `http://localhost:8000`
   - **Keep this terminal window open!**
   - You should see: `INFO: Application startup complete`

---

### Step 4: Frontend Setup

1. **Open a NEW Terminal/PowerShell window**

2. **Navigate to Project Root:**
   ```powershell
   cd "path\to\Smart_parking2"
   ```

3. **Install Dependencies:**
   ```powershell
   npm install
   ```

4. **Start Frontend Development Server:**
   ```powershell
   npm run dev
   ```
   - Frontend will run on `http://localhost:5173` (or another port if 5173 is busy)
   - **Keep this terminal window open!**
   - You should see: `Local: http://localhost:5173/`

---

### Step 5: Access Application

1. **Open your web browser**
2. **Navigate to:** `http://localhost:5173`
3. **Login with test accounts:**
   - Email: `alice@example.com` | Password: `passAlice1`
   - Email: `bob@example.com` | Password: `passBob1`
   - Email: `charlie@example.com` | Password: `passChar1`
   - (See `backend/gen_users.py` for all test accounts)

---

