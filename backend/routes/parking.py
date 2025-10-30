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
    cursor = db.cursor(dictionary=True)

    # Validate lot existence
    cursor.execute("SELECT * FROM parking_lots WHERE lot_id = %s", (data.lot_id,))
    lot = cursor.fetchone()
    if not lot:
        cursor.close()
        db.close()
        raise HTTPException(status_code=404, detail="Parking lot not found")

    # Check availability
    if lot["available_spots"] <= 0:
        cursor.close()
        db.close()
        raise HTTPException(status_code=400, detail="No available spots in this lot")

    # Calculate duration and cost
    start_dt = datetime.strptime(data.start_time, "%Y-%m-%dT%H:%M")  # matches datetime-local format
    end_dt = datetime.strptime(data.end_time, "%Y-%m-%dT%H:%M")
    duration_hours = max((end_dt - start_dt).total_seconds() / 3600, 1)
    cost = round(duration_hours * float(lot["hourly_rate"]), 2)

    # Insert into reservations
    cursor.execute(
        """
        INSERT INTO reservations (user_id, lot_id, start_time, end_time, cost, status)
        VALUES (%s, %s, %s, %s, %s, 'confirmed')
        """,
        (data.user_id, data.lot_id, start_dt, end_dt, cost),
    )

    # Update available spots
    cursor.execute(
        "UPDATE parking_lots SET available_spots = available_spots - 1 WHERE lot_id = %s",
        (data.lot_id,),
    )

    db.commit()
    cursor.close()
    db.close()

    return {
        "message": "Parking booked successfully",
        "booking_summary": {
            "user_id": data.user_id,
            "lot_id": data.lot_id,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "total_cost": cost,
        },
    }