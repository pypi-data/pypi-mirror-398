import bcrypt


def hash_password(password: str) -> str:
    """Return hashed password using `bcrypt`."""
    hashed_password = bcrypt.hashpw(
        password=password.encode("utf-8"), salt=bcrypt.gensalt()
    )
    return hashed_password.decode("utf-8")


def validate_password(password: str, hashed_password: str) -> bool:
    """Verify password against hashed password using `bcrypt`."""
    return bcrypt.checkpw(
        password=password.encode("utf-8"),
        hashed_password=hashed_password.encode("utf-8"),
    )
