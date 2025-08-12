NLPearl Hotel Availability Mock API – Dataset

Files:
- hotels.json
- rooms.json
- availability.json
- bookings.json
- openapi.yaml (mock endpoints for your voice agent to call)

Example availability query (GET):
/availability?check_in_date=2025-08-17&check_out_date=2025-08-22&number_of_adults=2&number_of_children=1&hotel_id=1&max_price=250

Response contract:
- results[]: hotel_id, room_id, date_range, room_type, bed_type, capacities, nightly_price, total_price
- currency: EUR

Notes:
- Prices increase +20% in July/Aug and +10% on weekends (simple logic).
- availability.json includes 90 days from 2025-08-12.