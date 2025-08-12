from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import json, os

app = FastAPI(title="NLPearl Hotel Availability Mock API", version="1.0.0")

DATA_DIR = os.path.dirname(__file__)

def load_json(name: str):
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

hotels = load_json("hotels.json")
rooms = load_json("rooms.json")
availability = load_json("availability.json")
bookings = load_json("bookings.json")

# Fast lookups
rooms_by_id = {r["room_id"]: r for r in rooms}
availability_map = {}
for a in availability:
    availability_map.setdefault(a["room_id"], {})[a["date"]] = a["is_available"]

class BookingIn(BaseModel):
    room_id: int
    check_in_date: str
    check_out_date: str
    guest_name: str

@app.get("/hotels")
def list_hotels():
    return hotels

@app.get("/rooms")
def list_rooms(hotel_id: Optional[int] = None,
               room_type: Optional[str] = None,
               bed_type: Optional[str] = None):
    results = rooms
    if hotel_id is not None:
        results = [r for r in results if r["hotel_id"] == hotel_id]
    if room_type:
        results = [r for r in results if r["room_type"].lower() == room_type.lower()]
    if bed_type:
        results = [r for r in results if r["bed_type"].lower() == bed_type.lower()]
    return results

def parse_date(d: str) -> date:
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

def date_range(ci: date, co: date):
    d = ci
    while d < co:
        yield d
        d += timedelta(days=1)

def nightly_price(base_price: float, d: date) -> float:
    price = float(base_price)
    # Simple seasonal & weekend adjustments
    if d.month in (7, 8):
        price *= 1.2  # +20% Jul/Aug
    if d.weekday() >= 5:
        price *= 1.1  # +10% weekend
    return round(price, 2)

@app.get("/availability")
def check_availability(check_in_date: str = Query(...),
                       check_out_date: str = Query(...),
                       number_of_adults: Optional[int] = Query(None, ge=1),
                       number_of_children: Optional[int] = Query(0, ge=0),
                       hotel_id: Optional[int] = None,
                       room_type: Optional[str] = None,
                       bed_type: Optional[str] = None,
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None):
    ci = parse_date(check_in_date)
    co = parse_date(check_out_date)
    if ci >= co:
        raise HTTPException(status_code=422, detail="check_out_date must be after check_in_date.")
    nights = (co - ci).days

    # filter candidate rooms
    candidates = rooms
    if hotel_id is not None:
        candidates = [r for r in candidates if r["hotel_id"] == hotel_id]
    if room_type:
        candidates = [r for r in candidates if r["room_type"].lower() == room_type.lower()]
    if bed_type:
        candidates = [r for r in candidates if r["bed_type"].lower() == bed_type.lower()]
    if number_of_adults is not None:
        candidates = [r for r in candidates if r["capacity_adults"] >= number_of_adults]
    if number_of_children is not None:
        candidates = [r for r in candidates if r["capacity_children"] >= number_of_children]

    results = []
    for r in candidates:
        avail = availability_map.get(r["room_id"], {})
        # Check full block availability
        all_ok = True
        total = 0.0
        nightly = None
        for d in date_range(ci, co):
            dstr = d.isoformat()
            if not avail.get(dstr, False):
                all_ok = False
                break
            p = nightly_price(r["base_price"], d)
            total += p
            nightly = p  # last assigned is fine; we also return total
        if not all_ok:
            continue
        # price filter
        if min_price is not None and nightly is not None and nightly < min_price:
            continue
        if max_price is not None and nightly is not None and nightly > max_price:
            continue
        results.append({
            "hotel_id": r["hotel_id"],
            "room_id": r["room_id"],
            "date_range": {"check_in_date": ci.isoformat(), "check_out_date": co.isoformat()},
            "room_type": r["room_type"],
            "bed_type": r["bed_type"],
            "capacity_adults": r["capacity_adults"],
            "capacity_children": r["capacity_children"],
            "nightly_price": round(total / nights, 2),
            "total_price": round(total, 2)
        })

    return {"results": results, "currency": "EUR"}

@app.post("/bookings", status_code=201)
def create_booking(payload: BookingIn):
    # Basic validation
    if payload.room_id not in rooms_by_id:
        raise HTTPException(status_code=404, detail="Room not found.")
    ci = parse_date(payload.check_in_date)
    co = parse_date(payload.check_out_date)
    if ci >= co:
        raise HTTPException(status_code=422, detail="check_out_date must be after check_in_date.")
    # In a real system we'd re-check availability and then reserve; here we simulate success.
    new_id = max([b["booking_id"] for b in load_json("bookings.json")] + [100]) + 1
    room = rooms_by_id[payload.room_id]
    # Compute total
    nights = (co - ci).days
    total = 0.0
    d = ci
    while d < co:
        total += nightly_price(room["base_price"], d)
        d += timedelta(days=1)
    booking = {
        "booking_id": new_id,
        "room_id": payload.room_id,
        "guest_name": payload.guest_name,
        "check_in_date": ci.isoformat(),
        "check_out_date": co.isoformat(),
        "total_price": round(total, 2),
        "status": "confirmed"
    }
    # We don't persist on disk to keep this stateless in demo.
    return booking