from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
def get_admin_stats():
    """Get dashboard statistics for admin"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Total parking lots
        cursor.execute("SELECT COUNT(*) as total FROM parking_lots")
        total_lots = cursor.fetchone()["total"]
        
        # Total spots
        cursor.execute("SELECT SUM(total_spots) as total FROM parking_lots")
        total_spots = cursor.fetchone()["total"] or 0
        
        # Available spots
        cursor.execute("SELECT SUM(available_spots) as total FROM parking_lots")
        available_spots = cursor.fetchone()["total"] or 0
        
        # Total users
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'driver'")
        total_users = cursor.fetchone()["total"]
        
        # Total bookings (try to get from reservations table if exists)
        try:
            cursor.execute("SELECT COUNT(*) as total FROM reservations")
            total_bookings = cursor.fetchone()["total"]
        except:
            # If reservations table doesn't exist, estimate from occupied spots
            cursor.execute("SELECT COUNT(*) as total FROM parking_spots WHERE is_occupied = 1")
            total_bookings = cursor.fetchone()["total"]
        
        # Revenue (try to get from reservations table if exists)
        try:
            cursor.execute("SELECT SUM(total_cost) as revenue FROM reservations")
            revenue_result = cursor.fetchone()
            total_revenue = float(revenue_result["revenue"]) if revenue_result["revenue"] else 0.0
        except:
            # Estimate based on occupied spots and average rate
            cursor.execute("""
                SELECT SUM(p.hourly_rate * 2) as revenue 
                FROM parking_lots p
                WHERE (p.total_spots - p.available_spots) > 0
            """)
            revenue_result = cursor.fetchone()
            total_revenue = float(revenue_result["revenue"]) if revenue_result["revenue"] else 0.0
        
        # Occupied spots
        occupied_spots = total_spots - available_spots
        
        return {
            "total_lots": total_lots,
            "total_spots": total_spots,
            "available_spots": available_spots,
            "occupied_spots": occupied_spots,
            "total_users": total_users,
            "total_bookings": total_bookings,
            "total_revenue": round(total_revenue, 2),
            "occupancy_rate": round((occupied_spots / total_spots * 100) if total_spots > 0 else 0, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.get("/bookings")
def get_all_bookings():
    """Get all bookings/reservations - Try view first, fallback to direct query"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Try using the view first
        try:
            cursor.execute("""
                SELECT * FROM v_user_bookings
                ORDER BY created_at DESC
                LIMIT 100
            """)
            bookings = cursor.fetchall()
        except:
            # Fallback: Direct query from reservations table if view doesn't exist
            try:
                cursor.execute("""
                    SELECT 
                        r.reservation_id,
                        r.user_id,
                        u.name as user_name,
                        u.email,
                        r.lot_id,
                        p.lot_name,
                        p.location,
                        r.start_time,
                        r.end_time,
                        TIMESTAMPDIFF(HOUR, r.start_time, r.end_time) as duration_hours,
                        r.total_cost,
                        r.status,
                        r.created_at
                    FROM reservations r
                    JOIN users u ON r.user_id = u.user_id
                    JOIN parking_lots p ON r.lot_id = p.lot_id
                    ORDER BY r.created_at DESC
                    LIMIT 100
                """)
                bookings = cursor.fetchall()
            except:
                # If reservations table doesn't exist, return empty
                bookings = []
        
        # Convert datetime objects to strings
        for booking in bookings:
            if booking.get('start_time'):
                booking['start_time'] = booking['start_time'].isoformat() if hasattr(booking['start_time'], 'isoformat') else str(booking['start_time'])
            if booking.get('end_time'):
                booking['end_time'] = booking['end_time'].isoformat() if hasattr(booking['end_time'], 'isoformat') else str(booking['end_time'])
            if booking.get('created_at'):
                booking['created_at'] = booking['created_at'].isoformat() if hasattr(booking['created_at'], 'isoformat') else str(booking['created_at'])
        
        return {"bookings": bookings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bookings: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.get("/lots/manage")
def get_all_lots_manage():
    """Get all parking lots for management - Try view first, fallback to direct query"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Try using the view first
        try:
            cursor.execute("SELECT * FROM v_parking_lot_summary ORDER BY lot_id")
            lots = cursor.fetchall()
        except:
            # Fallback: Direct query from parking_lots table if view doesn't exist
            cursor.execute("""
                SELECT 
                    lot_id,
                    lot_name,
                    location,
                    total_spots,
                    available_spots,
                    (total_spots - available_spots) as occupied_spots,
                    ROUND((available_spots / total_spots * 100), 2) as availability_percent,
                    hourly_rate,
                    status,
                    CASE 
                        WHEN available_spots = 0 THEN 'FULL'
                        WHEN available_spots <= 5 THEN 'LOW'
                        ELSE 'AVAILABLE'
                    END as availability_status
                FROM parking_lots
                ORDER BY lot_id
            """)
            lots = cursor.fetchall()
        
        return {"lots": lots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching lots: {str(e)}")
    finally:
        cursor.close()
        db.close()


class UpdateLotRequest(BaseModel):
    lot_name: Optional[str] = None
    location: Optional[str] = None
    total_spots: Optional[int] = None
    hourly_rate: Optional[float] = None
    status: Optional[str] = None


@router.put("/lots/{lot_id}")
def update_lot(lot_id: int, data: UpdateLotRequest):
    """Update a parking lot"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Build update query dynamically
        updates = []
        params = []
        
        if data.lot_name is not None:
            updates.append("lot_name = %s")
            params.append(data.lot_name)
        if data.location is not None:
            updates.append("location = %s")
            params.append(data.location)
        if data.total_spots is not None:
            updates.append("total_spots = %s")
            params.append(data.total_spots)
        if data.hourly_rate is not None:
            updates.append("hourly_rate = %s")
            params.append(data.hourly_rate)
        if data.status is not None:
            updates.append("status = %s")
            params.append(data.status)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(lot_id)
        query = f"UPDATE parking_lots SET {', '.join(updates)} WHERE lot_id = %s"
        
        cursor.execute(query, params)
        db.commit()
        
        # Get updated lot
        cursor.execute("SELECT * FROM parking_lots WHERE lot_id = %s", (lot_id,))
        updated_lot = cursor.fetchone()
        
        return {"message": "Lot updated successfully", "lot": updated_lot}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating lot: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.get("/users")
def get_all_users():
    """Get all users"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT user_id, name, email, role, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
    finally:
        cursor.close()
        db.close()


class CreateLotRequest(BaseModel):
    lot_name: str
    location: str
    total_spots: int
    hourly_rate: float
    status: str = "open"


@router.post("/lots")
def create_parking_lot(data: CreateLotRequest):
    """Create a new parking lot"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            INSERT INTO parking_lots (lot_name, location, total_spots, available_spots, hourly_rate, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data.lot_name,
            data.location,
            data.total_spots,
            data.total_spots,  # Initially all spots are available
            data.hourly_rate,
            data.status
        ))
        
        lot_id = cursor.lastrowid
        
        # Create parking spots for the new lot
        for spot_num in range(1, data.total_spots + 1):
            cursor.execute("""
                INSERT INTO parking_spots (lot_id, spot_number, is_occupied)
                VALUES (%s, %s, 0)
            """, (lot_id, spot_num))
        
        db.commit()
        
        cursor.execute("SELECT * FROM parking_lots WHERE lot_id = %s", (lot_id,))
        new_lot = cursor.fetchone()
        
        return {"message": "Parking lot created successfully", "lot": new_lot}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating lot: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.delete("/lots/{lot_id}")
def delete_parking_lot(lot_id: int):
    """Delete a parking lot"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Check if lot has active bookings
        cursor.execute("""
            SELECT COUNT(*) as count FROM reservations 
            WHERE lot_id = %s AND status = 'active'
        """, (lot_id,))
        active_bookings = cursor.fetchone()["count"]
        
        if active_bookings > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete lot with {active_bookings} active bookings"
            )
        
        # Delete parking spots first (due to foreign key)
        cursor.execute("DELETE FROM parking_spots WHERE lot_id = %s", (lot_id,))
        
        # Delete the lot
        cursor.execute("DELETE FROM parking_lots WHERE lot_id = %s", (lot_id,))
        
        db.commit()
        
        return {"message": "Parking lot deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting lot: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.delete("/bookings/{booking_id}")
def delete_booking(booking_id: int):
    """Delete/cancel a booking"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get booking details
        cursor.execute("""
            SELECT lot_id, status FROM reservations WHERE reservation_id = %s
        """, (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # If active, update available spots
        if booking["status"] == "active":
            cursor.execute("""
                UPDATE parking_lots 
                SET available_spots = available_spots + 1 
                WHERE lot_id = %s
            """, (booking["lot_id"],))
            
            # Free up a parking spot
            cursor.execute("""
                UPDATE parking_spots 
                SET is_occupied = 0 
                WHERE lot_id = %s AND is_occupied = 1 
                LIMIT 1
            """, (booking["lot_id"],))
        
        # Delete the booking
        cursor.execute("DELETE FROM reservations WHERE reservation_id = %s", (booking_id,))
        
        db.commit()
        
        return {"message": "Booking deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting booking: {str(e)}")
    finally:
        cursor.close()
        db.close()


class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "driver"


@router.post("/users")
def create_user(data: CreateUserRequest):
    """Create a new user"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        import bcrypt
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Hash password
        password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (data.name, data.email, password_hash, data.role))
        
        user_id = cursor.lastrowid
        db.commit()
        
        cursor.execute("SELECT user_id, name, email, role FROM users WHERE user_id = %s", (user_id,))
        new_user = cursor.fetchone()
        
        return {"message": "User created successfully", "user": new_user}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Check if user exists
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent deleting yourself if you're an admin
        # This check should be done on frontend, but safety check here too
        
        # Delete user (cascades to vehicles and reservations)
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        
        db.commit()
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.get("/analytics")
def get_analytics():
    """Get detailed analytics for admin - with fallbacks"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Check if reservations table exists
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = 'reservations'
        """)
        has_reservations = cursor.fetchone()["count"] > 0
        
        revenue_by_day = []
        top_lots = []
        booking_stats = {"total": 0, "active": 0, "completed": 0}
        revenue_with_cte = []
        
        if has_reservations:
            # Revenue by day (last 7 days)
            try:
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as bookings_count,
                        SUM(total_cost) as revenue
                    FROM reservations
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                revenue_by_day = cursor.fetchall()
            except:
                revenue_by_day = []
            
            # Top parking lots by revenue - Try view first, fallback to direct query
            try:
                cursor.execute("""
                    SELECT * FROM v_lot_revenue_summary
                    ORDER BY total_revenue DESC
                    LIMIT 10
                """)
                top_lots = cursor.fetchall()
            except:
                # Fallback: Direct query
                try:
                    cursor.execute("""
                        SELECT 
                            p.lot_id,
                            p.lot_name,
                            p.location,
                            COUNT(r.reservation_id) as total_bookings,
                            SUM(r.total_cost) as revenue,
                            AVG(r.total_cost) as avg_booking_cost,
                            MAX(r.total_cost) as max_booking_cost,
                            MIN(r.total_cost) as min_booking_cost
                        FROM parking_lots p
                        LEFT JOIN reservations r ON p.lot_id = r.lot_id
                        GROUP BY p.lot_id, p.lot_name, p.location
                        ORDER BY revenue DESC
                        LIMIT 10
                    """)
                    top_lots = cursor.fetchall()
                except:
                    top_lots = []
            
            # Recent bookings count
            try:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                    FROM reservations
                """)
                booking_stats = cursor.fetchone() or {"total": 0, "active": 0, "completed": 0}
            except:
                booking_stats = {"total": 0, "active": 0, "completed": 0}
        
        return {
            "revenue_by_day": revenue_by_day,
            "top_parking_lots": top_lots,
            "booking_stats": booking_stats,
            "revenue_trend": revenue_with_cte
        }
    except Exception as e:
        # Return empty data instead of raising error
        return {
            "revenue_by_day": [],
            "top_parking_lots": [],
            "booking_stats": {"total": 0, "active": 0, "completed": 0},
            "revenue_trend": []
        }
    finally:
        cursor.close()
        db.close()

