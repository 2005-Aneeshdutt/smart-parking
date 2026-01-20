# Smart Parking System 🅿️

A modern, full-stack parking management system that allows users to browse available parking lots, make reservations, and manage their bookings. Built with React and FastAPI, featuring a comprehensive admin dashboard for parking lot management.

## ✨ Features

### For Drivers
- 🔐 **User Authentication** - Secure login and registration system
- 🔍 **Browse Parking Lots** - View all available parking lots with real-time availability
- 📅 **Book Parking Spots** - Reserve parking spots with date and time selection
- 📋 **View Bookings** - Track all your current and past reservations
- 💰 **Transparent Pricing** - See hourly rates for each parking lot

### For Administrators
- 🎛️ **Admin Dashboard** - Comprehensive management interface
- 🏢 **Parking Lot Management** - Add, edit, and manage parking lots
- 👥 **User Management** - View and manage all registered users
- 📊 **Reservation Overview** - Monitor all bookings and reservations
- ⚙️ **System Configuration** - Control parking lot status and availability

### Technical Features
- 🗄️ **Advanced Database** - MySQL with stored procedures, triggers, functions, and views
- 🔄 **Real-time Updates** - Automatic spot availability updates
- 🛡️ **Role-based Access Control** - Separate interfaces for admins and drivers
- 🎨 **Modern UI** - Responsive design with Bootstrap
- 🚀 **RESTful API** - FastAPI backend with comprehensive endpoints

## 🛠️ Tech Stack

### Frontend
- **React 19** - Modern UI library
- **Vite** - Fast build tool and dev server
- **React Router** - Client-side routing
- **Bootstrap 5** - Responsive CSS framework
- **React Bootstrap** - Bootstrap components for React
- **Axios** - HTTP client for API calls
- **React DatePicker** - Date and time selection

### Backend
- **FastAPI** - Modern Python web framework
- **Python 3** - Programming language
- **MySQL** - Relational database
- **Uvicorn** - ASGI server
- **Bcrypt** - Password hashing
- **Pydantic** - Data validation

### Database
- **MySQL 8.0** - Database management system
- **Stored Procedures** - Business logic in database
- **Triggers** - Automatic data updates
- **User-defined Functions** - Custom calculations
- **Views** - Optimized data access

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **MySQL** (v8.0 or higher)
- **Git**

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/2005-Aneeshdutt/smart-parking.git
cd smart-parking
```

### 2. Database Setup

1. Open MySQL Workbench or your MySQL client
2. Execute the SQL scripts in order:
   ```sql
   -- Run these scripts in MySQL
   smart_parking_database_1.sql
   create_stored_procedure.sql
   advanced_database_features.sql
   ```

3. Create `backend/.env` file with your MySQL credentials:
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=smart_parking_database_1
   ```

### 3. Backend Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # On Windows
# source venv/bin/activate    # On Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend API will be available at `http://localhost:8000`

### 4. Frontend Setup

From the project root directory (if you're in `backend`, run `cd ..` first):

```powershell
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port shown in terminal)

### 5. Create Admin User (Optional)

To create an admin user, run this command from the `backend` directory:

```powershell
python create_admin.py
```

## 🔑 Default Credentials

For testing purposes, the following accounts are available:

- **Admin**: `admin@parking.com` / `admin123`
- **Driver**: `alice@example.com` / `passAlice1`
- **Driver**: `bob@example.com` / `passBob1`
- **Driver**: `charlie@example.com` / `passChar1`

## 📁 Project Structure

```
smart-parking/
├── backend/
│   ├── routes/
│   │   ├── admin.py      # Admin management endpoints
│   │   ├── auth.py       # Authentication endpoints
│   │   └── parking.py    # Parking lot and booking endpoints
│   ├── database.py       # Database connection
│   ├── main.py           # FastAPI application
│   ├── create_admin.py    # Admin user creation script
│   └── requirements.txt  # Python dependencies
├── src/
│   ├── components/
│   │   ├── AdminDashboard.jsx  # Admin interface
│   │   ├── BookPage.jsx        # Booking page
│   │   ├── Dashboard.jsx       # User dashboard
│   │   └── Login.jsx            # Login page
│   ├── context/
│   │   └── AuthContext1.jsx    # Authentication context
│   └── App.jsx                 # Main application component
├── smart_parking_database_1.sql        # Main database schema
├── create_stored_procedure.sql         # Stored procedures
├── advanced_database_features.sql      # Triggers, functions, views
└── README.md                           # This file
```

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Parking
- `GET /parking/lots` - Get all parking lots
- `GET /parking/lots/{lot_id}` - Get specific parking lot
- `POST /parking/book` - Book a parking spot
- `GET /parking/bookings/{user_id}` - Get user bookings

### Admin
- `GET /admin/users` - Get all users
- `GET /admin/reservations` - Get all reservations
- `POST /admin/lots` - Create parking lot
- `PUT /admin/lots/{lot_id}` - Update parking lot
- `DELETE /admin/lots/{lot_id}` - Delete parking lot

Visit `http://localhost:8000/docs` for interactive API documentation.

## 🎯 Usage

1. **Login** - Use the provided credentials or create a new account
2. **Browse Lots** - View all available parking lots on the dashboard
3. **Book a Spot** - Click on a parking lot to view details and make a reservation
4. **Manage Bookings** - View and manage your reservations from the dashboard
5. **Admin Access** - Admins can access the admin dashboard to manage the system

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Aneesh Dutt**

- GitHub: [@2005-Aneeshdutt](https://github.com/2005-Aneeshdutt)

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI components from [React Bootstrap](https://react-bootstrap.github.io/)
- Icons and emojis for better visual appeal

---

⭐ If you find this project helpful, please consider giving it a star!
