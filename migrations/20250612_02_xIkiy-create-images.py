"""
Create images
"""

from yoyo import step

__depends__ = {'20250612_01_fCGB4-create-users'}

steps = [
    step(
            "CREATE TABLE images (id UUID PRIMARY KEY, uid VARCHAR(32) NOT NULL UNIQUE, deletion_key VARCHAR(64) NOT NULL UNIQUE, original_name VARCHAR NOT NULL, extension VARCHAR NOT NULL, content_type VARCHAR NOT NULL, size INTEGER NOT NULL, sha256 VARCHAR NOT NULL, user_id UUID NOT NULL REFERENCES users(id), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
            "DROP TABLE images"
    )
]
