from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
def get_admin_stats():
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT COUNT(*) as total FROM parking_lots")
        total_lots = cursor.fetchone()["total"]
        
        cursor.execute("SELECT SUM(total_spots) as total FROM parking_lots")
        total_spots = cursor.fetchone()["total"] or 0
        
        cursor.execute("SELECT SUM(available_spots) as total FROM parking_lots")
        available_spots = cursor.fetchone()["total"] or 0
        
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'driver'")
        total_users = cursor.fetchone()["total"]
        
        try:
            cursor.execute("SELECT COUNT(*) as total FROM reservations")
            total_bookings = cursor.fetchone()["total"]
        except:
            cursor.execute("SELECT COUNT(*) as total FROM parking_spots WHERE is_occupied = 1")
            total_bookings = cursor.fetchone()["total"]
        
        try:
            cursor.execute("""
                SELECT COALESCE(SUM(total_cost), 0) as revenue 
                FROM reservations 
                WHERE status != 'cancelled'
            """)
            revenue_result = cursor.fetchone()
            total_revenue = float(revenue_result["revenue"]) if revenue_result["revenue"] else 0.0
        except:
            cursor.execute("""
                SELECT COALESCE(SUM(p.hourly_rate * 2), 0) as revenue 
                FROM parking_lots p
                WHERE (p.total_spots - p.available_spots) > 0
            """)
            revenue_result = cursor.fetchone()
            total_revenue = float(revenue_result["revenue"]) if revenue_result["revenue"] else 0.0
        
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
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        try:
            cursor.execute("""
                SELECT * FROM v_user_bookings
                ORDER BY created_at DESC
                LIMIT 100
            """)
            bookings = cursor.fetchall()
        except:
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
                bookings = []
        
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
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        try:
            cursor.execute("SELECT * FROM v_parking_lot_summary ORDER BY lot_id")
            lots = cursor.fetchall()
        except:
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
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
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
            data.total_spots,
            data.hourly_rate,
            data.status
        ))
        
        lot_id = cursor.lastrowid
        
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
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
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
        
        cursor.execute("DELETE FROM parking_spots WHERE lot_id = %s", (lot_id,))
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
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT lot_id, status FROM reservations WHERE reservation_id = %s
        """, (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking["status"] == "active":
            cursor.execute("""
                UPDATE parking_lots 
                SET available_spots = available_spots + 1 
                WHERE lot_id = %s
            """, (booking["lot_id"],))
            
            cursor.execute("""
                UPDATE parking_spots 
                SET is_occupied = 0 
                WHERE lot_id = %s AND is_occupied = 1 
                LIMIT 1
            """, (booking["lot_id"],))
        
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
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        import bcrypt
        
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")
        
        password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        
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
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
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
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = 'reservations'
        """)
        has_reservations = cursor.fetchone()["count"] > 0
        
        revenue_by_day = []
        top_lots = []
        above_avg_lots = []
        booking_stats = {"total": 0, "active": 0, "completed": 0}
        revenue_with_cte = []
        
        if has_reservations:
            try:
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(CASE WHEN status != 'cancelled' THEN 1 END) as bookings_count,
                        COALESCE(SUM(CASE WHEN status != 'cancelled' THEN total_cost ELSE 0 END), 0) as revenue
                    FROM reservations
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                revenue_by_day = cursor.fetchall()
            except:
                revenue_by_day = []
            
            try:
                cursor.execute("""
                    SELECT 
                        lot_id,
                        lot_name,
                        location,
                        total_bookings,
                        total_revenue as revenue,
                        avg_booking_cost,
                        max_booking_cost,
                        min_booking_cost
                    FROM v_lot_revenue_summary
                    ORDER BY total_revenue DESC
                    LIMIT 10
                """)
                top_lots = cursor.fetchall()
                for lot in top_lots:
                    lot['revenue'] = float(lot.get('revenue', 0) or 0)
                    lot['total_bookings'] = int(lot.get('total_bookings', 0) or 0)
            except:
                try:
                    cursor.execute("""
                        SELECT 
                            p.lot_id,
                            p.lot_name,
                            p.location,
                            COUNT(CASE WHEN r.status != 'cancelled' THEN r.reservation_id END) as total_bookings,
                            COALESCE(SUM(CASE WHEN r.status != 'cancelled' THEN r.total_cost ELSE 0 END), 0) as revenue,
                            COALESCE(AVG(CASE WHEN r.status != 'cancelled' THEN r.total_cost END), 0) as avg_booking_cost,
                            COALESCE(MAX(CASE WHEN r.status != 'cancelled' THEN r.total_cost END), 0) as max_booking_cost,
                            COALESCE(MIN(CASE WHEN r.status != 'cancelled' THEN r.total_cost END), 0) as min_booking_cost
                        FROM parking_lots p
                        LEFT JOIN reservations r ON p.lot_id = r.lot_id
                        GROUP BY p.lot_id, p.lot_name, p.location
                        HAVING total_bookings > 0 OR revenue > 0
                        ORDER BY revenue DESC
                        LIMIT 10
                    """)
                    top_lots = cursor.fetchall()
                    for lot in top_lots:
                        lot['revenue'] = float(lot.get('revenue', 0) or 0)
                        lot['total_bookings'] = int(lot.get('total_bookings', 0) or 0)
                except:
                    top_lots = []
            
            try:
                cursor.execute("""
                    SELECT 
                        p.lot_id,
                        p.lot_name,
                        p.location,
                        COALESCE(SUM(CASE WHEN r.status != 'cancelled' THEN r.total_cost ELSE 0 END), 0) as revenue
                    FROM parking_lots p
                    LEFT JOIN reservations r ON p.lot_id = r.lot_id
                    GROUP BY p.lot_id, p.lot_name, p.location
                    HAVING revenue > (
                        SELECT COALESCE(AVG(lot_revenue), 0)
                        FROM (
                            SELECT 
                                COALESCE(SUM(CASE WHEN r2.status != 'cancelled' THEN r2.total_cost ELSE 0 END), 0) as lot_revenue
                            FROM parking_lots p2
                            LEFT JOIN reservations r2 ON p2.lot_id = r2.lot_id
                            GROUP BY p2.lot_id
                        ) as lot_revenues
                    )
                    ORDER BY revenue DESC
                """)
                above_avg_lots = cursor.fetchall()
                for lot in above_avg_lots:
                    lot['revenue'] = float(lot.get('revenue', 0) or 0)
            except Exception as e:
                above_avg_lots = []
                print(f"Error in nested query: {str(e)}")
            
            try:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COALESCE(SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END), 0) as active,
                        COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as completed
                    FROM reservations
                """)
                result = cursor.fetchone()
                booking_stats = {
                    "total": int(result["total"]) if result else 0,
                    "active": int(result["active"]) if result else 0,
                    "completed": int(result["completed"]) if result else 0
                }
            except Exception as e:
                print(f"Error fetching booking stats: {e}")
                booking_stats = {"total": 0, "active": 0, "completed": 0}
        
        return {
            "revenue_by_day": revenue_by_day,
            "top_parking_lots": top_lots,
            "above_avg_lots": above_avg_lots,
            "booking_stats": booking_stats,
            "revenue_trend": revenue_with_cte
        }
    except Exception as e:
        return {
            "revenue_by_day": [],
            "top_parking_lots": [],
            "above_avg_lots": [],
            "booking_stats": {"total": 0, "active": 0, "completed": 0},
            "revenue_trend": []
        }
    finally:
        cursor.close()
        db.close()
