"""
This module defines a list of holidays and special trading days for 2024 and 2025.

These lists can be used for applications like holiday validation, event scheduling, 
and financial market operations.
"""
from datetime import datetime

holidays = [
    # -------- Existing --------
    datetime(2024, 12, 25).date(),  # Christmas

    datetime(2025, 2, 26).date(),   # Mahashivratri
    datetime(2025, 3, 14).date(),   # Holi
    datetime(2025, 3, 31).date(),   # Id-Ul-Fitr (Ramadan Eid)
    datetime(2025, 4, 10).date(),   # Shri Mahavir Jayanti
    datetime(2025, 4, 14).date(),   # Dr. Baba Saheb Ambedkar Jayanti
    datetime(2025, 4, 18).date(),   # Good Friday
    datetime(2025, 5, 1).date(),    # Maharashtra Day
    datetime(2025, 8, 15).date(),   # Independence Day
    datetime(2025, 8, 27).date(),   # Ganesh Chaturthi
    datetime(2025, 10, 2).date(),   # Mahatma Gandhi Jayanti
    datetime(2025, 10, 21).date(),  # Diwali Laxmi Pujan
    datetime(2025, 10, 22).date(),  # Diwali-Balipratipada
    datetime(2025, 11, 5).date(),   # Prakash Gurpurb Sri Guru Nanak Dev
    datetime(2025, 12, 25).date(),  # Christmas

    # -------- New (2026 – from image) --------
    datetime(2026, 1, 26).date(),   # Republic Day
    datetime(2026, 3, 3).date(),    # Holi
    datetime(2026, 3, 26).date(),   # Shri Ram Navami
    datetime(2026, 3, 31).date(),   # Shri Mahavir Jayanti
    datetime(2026, 4, 3).date(),    # Good Friday
    datetime(2026, 4, 14).date(),   # Dr. Baba Saheb Ambedkar Jayanti
    datetime(2026, 5, 1).date(),    # Maharashtra Day
    datetime(2026, 5, 28).date(),   # Bakri Id
    datetime(2026, 6, 26).date(),   # Muharram
    datetime(2026, 9, 14).date(),   # Ganesh Chaturthi
    datetime(2026, 10, 2).date(),   # Mahatma Gandhi Jayanti
    datetime(2026, 10, 20).date(),  # Dussehra
    datetime(2026, 11, 10).date(),  # Diwali-Balipratipada
    datetime(2026, 11, 24).date(),  # Prakash Gurpurb Sri Guru Nanak Dev
    datetime(2026, 12, 25).date(),  # Christmas
]
special_trading_days = [
    datetime(2025, 2, 1).date(),  # Budget Day
]