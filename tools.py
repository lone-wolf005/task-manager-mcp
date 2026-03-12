from contextlib import contextmanager
from functools import wraps
from typing import Optional

from fastmcp.server.dependencies import get_access_token

from database import SessionLocal
from users import get_or_create_user
from permissions import has_permission
from models import User, Role, UserRole
from models import Note, Task


@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_permission(permission_name: str):
    """Decorator to handle authentication and authorization."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = get_access_token()
            user_id = get_or_create_user(token)
            
            if not has_permission(user_id, permission_name):
                return "Access denied"
            
            # Remove user_id from kwargs if it exists to avoid duplicate argument error
            kwargs.pop('user_id', None)
            
            return func(user_id=user_id, *args, **kwargs)
        return wrapper
    return decorator


def find_user_by_email(db, email: str):
    """Find user by email or return None."""
    return db.query(User).filter(User.email == email).first()


def find_role_by_name(db, name: str):
    """Find role by name or return None."""
    return db.query(Role).filter(Role.name == name).first()



def register_tools(mcp):

    @mcp.tool()
    @require_permission("notes_create")
    def create_note(content: str, user_id: Optional[int] = None):
        """
        Create a new note for the authenticated user.
        
        Args:
            content: The text content of the note
            
        Returns:
            Success message confirming note creation
            
        Permission Required: notes_create
        """
        with get_db_session() as db:
            note = Note(user_id=user_id, content=content)
            db.add(note)
            db.commit()
            return "Note created"

    @mcp.tool()
    @require_permission("notes_read")
    def list_notes(user_id: Optional[int] = None):
        """
        Retrieve all notes created by the authenticated user.
        
        Returns:
            List of note contents
            
        Permission Required: notes_read
        """
        with get_db_session() as db:
            notes = db.query(Note).filter(Note.user_id == user_id).all()
            return [n.content for n in notes]

    @mcp.tool()
    @require_permission("tasks_create")
    def create_task(title: str, user_id: Optional[int] = None):
        """
        Create a new task for the authenticated user.
        
        Args:
            title: The title/description of the task
            
        Returns:
            Success message confirming task creation
            
        Permission Required: tasks_create
        """
        with get_db_session() as db:
            task = Task(user_id=user_id, title=title)
            db.add(task)
            db.commit()
            return "Task created"

    @mcp.tool()
    @require_permission("tasks_read")
    def list_tasks(user_id: Optional[int] = None):
        """
        Retrieve all tasks for the authenticated user.
        
        Returns:
            List of tasks with title and completion status
            
        Permission Required: tasks_read
        """
        with get_db_session() as db:
            tasks = db.query(Task).filter(Task.user_id == user_id).all()
            return [{"title": t.title, "completed": t.completed} for t in tasks]
    
    @mcp.tool()
    @require_permission("users_view")
    def list_users(user_id: Optional[int] = None):
        """
        List all users in the system.
        
        Returns:
            List of users with their ID and email
            
        Permission Required: users_view
        """
        with get_db_session() as db:
            users = db.query(User).all()
            return [{"id": u.id, "email": u.email} for u in users]
    
    @mcp.tool()
    @require_permission("users_view")
    def list_roles(user_id: Optional[int] = None):
        """
        List all available roles in the system.
        
        Returns:
            List of role names
            
        Permission Required: users_view
        """
        with get_db_session() as db:
            roles = db.query(Role).all()
            return [r.name for r in roles]

    @mcp.tool()
    @require_permission("users_manage")
    def assign_role(user_email: str, role_name: str, user_id: Optional[int] = None):
        """
        Assign a role to a user. Admin only.
        
        Args:
            user_email: Email address of the user to assign the role to
            role_name: Name of the role to assign
            
        Returns:
            Success message or error if user/role not found or already assigned
            
        Permission Required: users_manage (admin only)
        """
        with get_db_session() as db:
            target_user = find_user_by_email(db, user_email)
            if not target_user:
                return "User not found"

            role = find_role_by_name(db, role_name)
            if not role:
                return "Role not found"

            existing = db.query(UserRole).filter(
                UserRole.user_id == target_user.id,
                UserRole.role_id == role.id
            ).first()

            if existing:
                return "User already has this role"

            new_role = UserRole(
                user_id=target_user.id,
                role_id=role.id
            )

            db.add(new_role)
            db.commit()

            return f"{user_email} promoted to {role_name}"
    
    @mcp.tool()
    @require_permission("users_manage")
    def remove_role(user_email: str, role_name: str, user_id: Optional[int] = None):
        """
        Remove a role from a user. Admin only.
        
        Args:
            user_email: Email address of the user to remove the role from
            role_name: Name of the role to remove
            
        Returns:
            Success message or error if user/role not found or not assigned
            
        Permission Required: users_manage (admin only)
        """
        with get_db_session() as db:
            user = find_user_by_email(db, user_email)
            if not user:
                return "User not found"

            role = find_role_by_name(db, role_name)
            if not role:
                return "Role not found"

            mapping = db.query(UserRole).filter(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id
            ).first()

            if not mapping:
                return "Role not assigned"

            db.delete(mapping)
            db.commit()

            return f"{role_name} removed from {user_email}"
    
    @mcp.tool()
    @require_permission("users_manage")
    def list_users_with_roles(user_id: Optional[int] = None):
        """
        Fetch all users with their assigned roles. Admin only.
        
        This tool provides a comprehensive view of all users in the system
        along with their role assignments, useful for user management and auditing.
        
        Returns:
            List of dictionaries, each containing:
            - id: User's unique identifier
            - email: User's email address
            - scalekit_user_id: User's Scalekit authentication ID
            - roles: List of role names assigned to the user
            
        Permission Required: users_manage (admin only)
        
        Example output:
        [
            {
                "id": 1,
                "email": "admin@example.com",
                "scalekit_user_id": "sk_user_123",
                "roles": ["admin", "user"]
            },
            {
                "id": 2,
                "email": "user@example.com",
                "scalekit_user_id": "sk_user_456",
                "roles": ["user"]
            }
        ]
        """
        with get_db_session() as db:
            users = db.query(User).all()
            
            result = []
            for user in users:
                # Query all roles for this user
                user_roles = db.query(Role).join(
                    UserRole, Role.id == UserRole.role_id
                ).filter(
                    UserRole.user_id == user.id
                ).all()
                
                result.append({
                    "id": user.id,
                    "email": user.email,
                    "scalekit_user_id": user.scalekit_user_id,
                    "roles": [role.name for role in user_roles]
                })
            
            return result

    @mcp.tool()
    @require_permission("analytics_read")
    def analytics(user_id: Optional[int] = None):
        """
        Get system-wide analytics and statistics.
        
        Returns:
            Dictionary containing:
            - total_users: Total number of users in the system
            - total_tasks: Total number of tasks across all users
            
        Permission Required: analytics_read
        """
        with get_db_session() as db:
            users = db.query(User).count()
            tasks = db.query(Task).count()

            return {
                "total_users": users,
                "total_tasks": tasks
            }