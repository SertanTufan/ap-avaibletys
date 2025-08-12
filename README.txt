Run locally (Python 3.10+):

1) Create venv and install deps
   python -m venv .venv
   .venv/bin/pip install -r requirements.txt  (Windows: .venv\Scripts\pip)

2) Start server
   uvicorn app:app --host 0.0.0.0 --port 8000

3) Test endpoints
   http://localhost:8000/hotels
   http://localhost:8000/rooms?hotel_id=1
   http://localhost:8000/availability?check_in_date=2025-08-20&check_out_date=2025-08-24&number_of_adults=2&hotel_id=1
   POST http://localhost:8000/bookings

Swagger UI:
   http://localhost:8000/docs