from database import SessionLocal
from models import Permission, RolePermission, UserRole, Role


def has_permission(user_id, permission):

    db = SessionLocal()
    try:
        result = db.query(Permission).join(
            RolePermission, Permission.id == RolePermission.permission_id
        ).join(
            Role, RolePermission.role_id == Role.id
        ).join(
            UserRole, Role.id == UserRole.role_id
        ).filter(
            UserRole.user_id == user_id,
            Permission.name == permission
        ).first()

        return result is not None
    finally:
        db.close()