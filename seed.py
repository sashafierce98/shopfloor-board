#!/usr/bin/env python3
"""
Seed script to add worker names to the database.
Run: python seed.py
"""

from app import app
from models import db, Worker

def seed_workers():
    """Add sample workers to the database."""
    with app.app_context():
        # Check if workers already exist
        if Worker.query.first():
            print("Workers already exist in database. Skipping seed.")
            return
        
        # List of worker names to add
        workers = [
            "Alice Johnson",
            "Bob Smith",
            "Charlie Brown",
            "Diana Prince",
            "Ethan Hunt",
            "Fiona Green",
            "George Wilson",
            "Hannah Montana",
        ]
        
        try:
            for name in workers:
                worker = Worker(name=name)
                db.session.add(worker)
            
            db.session.commit()
            print(f"✓ Successfully added {len(workers)} workers to database:")
            for name in workers:
                print(f"  - {name}")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error adding workers: {str(e)}")

if __name__ == "__main__":
    seed_workers()
