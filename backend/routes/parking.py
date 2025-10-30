from fastapi import APIRouter, HTTPException
from database import get_db

router = APIRouter(prefix="/parking", tags=["Parking"])

@router.get("/lots")
def get_parking_lots():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT lot_id, lot_name, location, total_spots, available_spots FROM parking_lots")
    lots = cursor.fetchall()
    cursor.close()
    db.close()

    if not lots:
        raise HTTPException(status_code=404, detail="No parking lots found")

    return {"parking_lots": lots}
