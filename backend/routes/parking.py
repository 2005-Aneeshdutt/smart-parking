from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from database import get_db
from datetime import datetime


router = APIRouter(prefix="/parking", tags=["Parking"])



@router.get("/lots")
def get_parking_lots():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT lot_id, lot_name, location, total_spots, available_spots, hourly_rate, status FROM parking_lots"
    )
    lots = cursor.fetchall()
    cursor.close()
    db.close()

    if not lots:
        raise HTTPException(status_code=404, detail="No parking lots found")

    return {"parking_lots": lots}



@router.get("/lots/{lot_id}")
def get_parking_lot(lot_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT lot_id, lot_name, location, total_spots, available_spots, hourly_rate, status "
        "FROM parking_lots WHERE lot_id = %s",
        (lot_id,),
    )
    lot = cursor.fetchone()
    cursor.close()
    db.close()

    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")

    return {"parking_lot": lot}



class BookingRequest(BaseModel):
    user_id: int
    lot_id: int
    start_time: str
    end_time: str


@router.post("/book")
def book_parking_spot(data: BookingRequest):
    db = get_db()
    cursor = db.cursor()

    try:
        
        start_dt = datetime.strptime(data.start_time, "%Y-%m-%dT%H:%M")
        end_dt = datetime.strptime(data.end_time, "%Y-%m-%dT%H:%M")

        
        cursor.execute("SET @p_total_cost = 0;")

        
        cursor.callproc("make_reservation1", [data.user_id, data.lot_id, start_dt, end_dt, "@p_total_cost"])

        
        cursor.execute("SELECT @p_total_cost;")
        total_cost = cursor.fetchone()[0]

        db.commit()

        return {
            "message": "Parking booked successfully",
            "booking_summary": {
                "user_id": data.user_id,
                "lot_id": data.lot_id,
                "start_time": data.start_time,
                "end_time": data.end_time,
                "total_cost": float(total_cost),
            },
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cursor.close()
        db.close()


@router.get("/bookings/{user_id}")
def get_user_bookings(user_id: int):
    """Get all bookings for a specific user - Try view first, fallback to direct query"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Try using the view first
        try:
            cursor.execute("""
                SELECT * FROM v_user_bookings
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            bookings = cursor.fetchall()
        except:
            # Fallback: Direct query from reservations table if view doesn't exist
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
                WHERE r.user_id = %s
                ORDER BY r.created_at DESC
            """, (user_id,))
            bookings = cursor.fetchall()
        
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


@router.get("/lots/{lot_id}/calculate-cost")
def calculate_parking_cost(lot_id: int, start_time: str = Query(...), end_time: str = Query(...)):
    """Calculate parking cost using database function"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor()
    
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        end_dt = datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
        
        # Using database function
        cursor.execute("SELECT calculate_parking_cost(%s, %s, %s) as cost", (lot_id, start_dt, end_dt))
        result = cursor.fetchone()
        
        return {
            "lot_id": lot_id,
            "start_time": start_time,
            "end_time": end_time,
            "calculated_cost": float(result[0])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error calculating cost: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.get("/lots/{lot_id}/status")
def get_lot_status(lot_id: int):
    """Get parking lot status using database function"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Using database function
        cursor.execute("SELECT get_lot_status(%s) as status", (lot_id,))
        status_result = cursor.fetchone()
        
        # Also get available spots using function
        cursor.execute("SELECT check_available_spots(%s) as available", (lot_id,))
        available_result = cursor.fetchone()
        
        return {
            "lot_id": lot_id,
            "status": status_result["status"],
            "available_spots": available_result["available"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching status: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.put("/bookings/{reservation_id}/cancel")
def cancel_booking(reservation_id: int):
    """Cancel a booking - updates status to 'cancelled' which triggers database to free up spots"""
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    
    try:
        # Check if booking exists and get its details
        cursor.execute("""
            SELECT reservation_id, user_id, lot_id, status, start_time
            FROM reservations
            WHERE reservation_id = %s
        """, (reservation_id,))
        
        booking = cursor.fetchone()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check if booking is already cancelled or completed
        if booking['status'] == 'cancelled':
            raise HTTPException(status_code=400, detail="Booking is already cancelled")
        
        if booking['status'] == 'completed':
            raise HTTPException(status_code=400, detail="Cannot cancel a completed booking")
        
        # Update booking status to cancelled
        # The trigger will automatically free up the parking spot
        cursor.execute("""
            UPDATE reservations
            SET status = 'cancelled'
            WHERE reservation_id = %s
        """, (reservation_id,))
        
        db.commit()
        
        return {
            "message": "Booking cancelled successfully",
            "reservation_id": reservation_id,
            "status": "cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error cancelling booking: {str(e)}")
    finally:
        cursor.close()
        db.close()