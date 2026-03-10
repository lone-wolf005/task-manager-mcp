import requests

from database import SessionLocal
from models import User
from config import USERINFO_ENDPOINT


def get_or_create_user(token):

    db = SessionLocal()

    scalekit_id = token.claims["sub"]

    user = db.query(User).filter(
        User.scalekit_user_id == scalekit_id
    ).first()

    if user:
        # Get the user id before closing the session
        user_id = user.id
        db.close()
        return user_id

    response = requests.get(
        USERINFO_ENDPOINT,
        headers={"Authorization": f"Bearer {token.token}"}
    )

    userinfo = response.json()

    email = userinfo.get("email")

    user = User(
        scalekit_user_id=scalekit_id,
        email=email
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    db.close()

    return user_id