"""
Create users
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
            "CREATE TABLE users (id UUID PRIMARY KEY, username VARCHAR NOT NULL UNIQUE, sub VARCHAR NOT NULL UNIQUE, email VARCHAR NOT NULL UNIQUE, api_key VARCHAR(64), admin BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
            "DROP TABLE users"
    )
]
