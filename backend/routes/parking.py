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