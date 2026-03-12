from contextlib import contextmanager
from functools import wraps
from typing import Optional

from fastmcp.server.dependencies import get_access_token

from database import SessionLocal
from users import get_or_create_user
from permissions import has_permission
from models import User, Role, UserRole, Permission, RolePermission
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
            return [{"id": n.id, "content": n.content} for n in notes]
    
    @mcp.tool()
    @require_permission("notes_read")
    def get_note(note_id: int, user_id: Optional[int] = None):
        """
        Retrieve a specific note by ID for the authenticated user.
        
        Args:
            note_id: ID of the note to retrieve
            
        Returns:
            Dictionary containing note details or error if not found/unauthorized
            
        Permission Required: notes_read
        """
        with get_db_session() as db:
            note = db.query(Note).filter(
                Note.id == note_id,
                Note.user_id == user_id
            ).first()
            
            if not note:
                return "Note not found or unauthorized"
            
            return {
                "id": note.id,
                "content": note.content,
                "user_id": note.user_id
            }

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
            return [{"id": t.id, "title": t.title, "completed": t.completed} for t in tasks]
    
    @mcp.tool()
    @require_permission("tasks_read")
    def get_task(task_id: int, user_id: Optional[int] = None):
        """
        Retrieve a specific task by ID for the authenticated user.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Dictionary containing task details or error if not found/unauthorized
            
        Permission Required: tasks_read
        """
        with get_db_session() as db:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == user_id
            ).first()
            
            if not task:
                return "Task not found or unauthorized"
            
            return {
                "id": task.id,
                "title": task.title,
                "completed": task.completed,
                "user_id": task.user_id
            }
    
    @mcp.tool()
    @require_permission("tasks_update")
    def update_task(task_id: int, title: Optional[str] = None, completed: Optional[int] = None, user_id: Optional[int] = None):
        """
        Update an existing task's title or completion status.
        
        Args:
            task_id: ID of the task to update
            title: New title for the task (optional)
            completed: New completion status - 0 for incomplete, 1 for complete (optional)
            
        Returns:
            Success message or error if task not found or unauthorized
            
        Permission Required: tasks_update
        """
        with get_db_session() as db:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == user_id
            ).first()
            
            if not task:
                return "Task not found or unauthorized"
            
            if title is not None:
                task.title = title  # type: ignore
            if completed is not None:
                task.completed = completed  # type: ignore
            
            db.commit()
            return f"Task updated successfully"
    
    @mcp.tool()
    @require_permission("tasks_delete")
    def delete_task(task_id: int, user_id: Optional[int] = None):
        """
        Delete a task.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            Success message or error if task not found or unauthorized
            
        Permission Required: tasks_delete
        """
        with get_db_session() as db:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == user_id
            ).first()
            
            if not task:
                return "Task not found or unauthorized"
            
            db.delete(task)
            db.commit()
            return "Task deleted successfully"
    
    @mcp.tool()
    @require_permission("tasks_update")
    def mark_task_complete(task_id: int, user_id: Optional[int] = None):
        """
        Mark a task as complete.
        
        Args:
            task_id: ID of the task to mark as complete
            
        Returns:
            Success message or error if task not found or unauthorized
            
        Permission Required: tasks_update
        """
        with get_db_session() as db:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == user_id
            ).first()
            
            if not task:
                return "Task not found or unauthorized"
            
            task.completed = 1  # type: ignore
            db.commit()
            return "Task marked as complete"
    
    @mcp.tool()
    @require_permission("tasks_update")
    def mark_task_incomplete(task_id: int, user_id: Optional[int] = None):
        """
        Mark a task as incomplete.
        
        Args:
            task_id: ID of the task to mark as incomplete
            
        Returns:
            Success message or error if task not found or unauthorized
            
        Permission Required: tasks_update
        """
        with get_db_session() as db:
            task = db.query(Task).filter(
                Task.id == task_id,
                Task.user_id == user_id
            ).first()
            
            if not task:
                return "Task not found or unauthorized"
            
            task.completed = 0  # type: ignore
            db.commit()
            return "Task marked as incomplete"
    
    @mcp.tool()
    @require_permission("notes_update")
    def update_note(note_id: int, content: str, user_id: Optional[int] = None):
        """
        Update an existing note's content.
        
        Args:
            note_id: ID of the note to update
            content: New content for the note
            
        Returns:
            Success message or error if note not found or unauthorized
            
        Permission Required: notes_update
        """
        with get_db_session() as db:
            note = db.query(Note).filter(
                Note.id == note_id,
                Note.user_id == user_id
            ).first()
            
            if not note:
                return "Note not found or unauthorized"
            
            note.content = content  # type: ignore
            db.commit()
            return "Note updated successfully"
    
    @mcp.tool()
    @require_permission("notes_delete")
    def delete_note(note_id: int, user_id: Optional[int] = None):
        """
        Delete a note.
        
        Args:
            note_id: ID of the note to delete
            
        Returns:
            Success message or error if note not found or unauthorized
            
        Permission Required: notes_delete
        """
        with get_db_session() as db:
            note = db.query(Note).filter(
                Note.id == note_id,
                Note.user_id == user_id
            ).first()
            
            if not note:
                return "Note not found or unauthorized"
            
            db.delete(note)
            db.commit()
            return "Note deleted successfully"
    
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
    @require_permission("users_view")
    def get_user_details(user_email: str, user_id: Optional[int] = None):
        """
        Get detailed information about a specific user. Admin only.
        
        Args:
            user_email: Email address of the user to get details for
            
        Returns:
            Dictionary containing user details including:
            - id: User's unique identifier
            - email: User's email address
            - scalekit_user_id: User's Scalekit authentication ID
            - roles: List of role names assigned to the user
            - task_count: Total number of tasks created by the user
            - note_count: Total number of notes created by the user
            - completed_tasks: Number of completed tasks
            
        Permission Required: users_view
        """
        with get_db_session() as db:
            user = find_user_by_email(db, user_email)
            if not user:
                return "User not found"
            
            # Get user roles
            user_roles = db.query(Role).join(
                UserRole, Role.id == UserRole.role_id
            ).filter(
                UserRole.user_id == user.id
            ).all()
            
            # Get task statistics
            total_tasks = db.query(Task).filter(Task.user_id == user.id).count()
            completed_tasks = db.query(Task).filter(
                Task.user_id == user.id,
                Task.completed == 1
            ).count()
            
            # Get note count
            total_notes = db.query(Note).filter(Note.user_id == user.id).count()
            
            return {
                "id": user.id,
                "email": user.email,
                "scalekit_user_id": user.scalekit_user_id,
                "roles": [role.name for role in user_roles],
                "task_count": total_tasks,
                "completed_tasks": completed_tasks,
                "note_count": total_notes
            }
    
    @mcp.tool()
    @require_permission("analytics_read")
    def user_statistics(user_email: Optional[str] = None, user_id: Optional[int] = None):
        """
        Get detailed statistics for a specific user or the authenticated user.
        
        Args:
            user_email: Email address of the user to get statistics for (optional, admin only)
                       If not provided, returns statistics for the authenticated user
            
        Returns:
            Dictionary containing:
            - email: User's email address
            - total_tasks: Total number of tasks
            - completed_tasks: Number of completed tasks
            - incomplete_tasks: Number of incomplete tasks
            - completion_rate: Percentage of tasks completed
            - total_notes: Total number of notes
            
        Permission Required: analytics_read
        """
        with get_db_session() as db:
            # If user_email provided, get that user's stats (admin feature)
            if user_email:
                target_user = find_user_by_email(db, user_email)
                if not target_user:
                    return "User not found"
                target_user_id = target_user.id
                target_email = target_user.email
            else:
                # Get stats for authenticated user
                target_user_id = user_id
                user_obj = db.query(User).filter(User.id == user_id).first()
                target_email = user_obj.email if user_obj else "Unknown"
            
            # Get task statistics
            total_tasks = db.query(Task).filter(Task.user_id == target_user_id).count()
            completed_tasks = db.query(Task).filter(
                Task.user_id == target_user_id,
                Task.completed == 1
            ).count()
            incomplete_tasks = total_tasks - completed_tasks
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get note count
            total_notes = db.query(Note).filter(Note.user_id == target_user_id).count()
            
            return {
                "email": target_email,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "incomplete_tasks": incomplete_tasks,
                "completion_rate": round(completion_rate, 2),
                "total_notes": total_notes
            }

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
    
    @mcp.tool()
    @require_permission("users_view")
    def list_role_permissions(role_name: str, user_id: Optional[int] = None):
        """
        List all permissions assigned to a specific role.
        
        Args:
            role_name: Name of the role to get permissions for
            
        Returns:
            Dictionary containing:
            - role: Name of the role
            - permissions: List of permission names assigned to this role
            
        Permission Required: users_view
        """
        with get_db_session() as db:
            role = find_role_by_name(db, role_name)
            if not role:
                return "Role not found"
            
            # Get all permissions for this role
            permissions = db.query(Permission).join(
                RolePermission, Permission.id == RolePermission.permission_id
            ).filter(
                RolePermission.role_id == role.id
            ).all()
            
            return {
                "role": role.name,
                "permissions": [perm.name for perm in permissions]
            }
    
    @mcp.tool()
    @require_permission("roles_manage")
    def create_role(role_name: str, user_id: Optional[int] = None):
        """
        Create a new role in the system. Admin only.
        
        Args:
            role_name: Name of the new role to create
            
        Returns:
            Success message or error if role already exists
            
        Permission Required: roles_manage (admin only)
        """
        with get_db_session() as db:
            # Check if role already exists
            existing_role = find_role_by_name(db, role_name)
            if existing_role:
                return "Role already exists"
            
            # Create new role
            new_role = Role(name=role_name)
            db.add(new_role)
            db.commit()
            
            return f"Role '{role_name}' created successfully"
    
    @mcp.tool()
    @require_permission("roles_manage")
    def assign_permission_to_role(role_name: str, permission_name: str, user_id: Optional[int] = None):
        """
        Assign a permission to a role. Admin only.
        
        Args:
            role_name: Name of the role to assign the permission to
            permission_name: Name of the permission to assign
            
        Returns:
            Success message or error if role/permission not found or already assigned
            
        Permission Required: roles_manage (admin only)
        """
        with get_db_session() as db:
            role = find_role_by_name(db, role_name)
            if not role:
                return "Role not found"
            
            permission = db.query(Permission).filter(Permission.name == permission_name).first()
            if not permission:
                return "Permission not found"
            
            # Check if permission already assigned
            existing = db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id
            ).first()
            
            if existing:
                return "Permission already assigned to this role"
            
            # Assign permission to role
            role_permission = RolePermission(
                role_id=role.id,
                permission_id=permission.id
            )
            db.add(role_permission)
            db.commit()
            
            return f"Permission '{permission_name}' assigned to role '{role_name}'"
    
    @mcp.tool()
    @require_permission("roles_manage")
    def remove_permission_from_role(role_name: str, permission_name: str, user_id: Optional[int] = None):
        """
        Remove a permission from a role. Admin only.
        
        Args:
            role_name: Name of the role to remove the permission from
            permission_name: Name of the permission to remove
            
        Returns:
            Success message or error if role/permission not found or not assigned
            
        Permission Required: roles_manage (admin only)
        """
        with get_db_session() as db:
            role = find_role_by_name(db, role_name)
            if not role:
                return "Role not found"
            
            permission = db.query(Permission).filter(Permission.name == permission_name).first()
            if not permission:
                return "Permission not found"
            
            # Find the role-permission mapping
            mapping = db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id
            ).first()
            
            if not mapping:
                return "Permission not assigned to this role"
            
            # Remove the permission from role
            db.delete(mapping)
            db.commit()
            
            return f"Permission '{permission_name}' removed from role '{role_name}'"
    
    @mcp.tool()
    @require_permission("roles_manage")
    def delete_role(role_name: str, user_id: Optional[int] = None):
        """
        Delete a role from the system. Admin only.
        
        This will also remove all user assignments and permission assignments for this role.
        
        Args:
            role_name: Name of the role to delete
            
        Returns:
            Success message or error if role not found
            
        Permission Required: roles_manage (admin only)
        """
        with get_db_session() as db:
            role = find_role_by_name(db, role_name)
            if not role:
                return "Role not found"
            
            # Delete all user-role assignments
            db.query(UserRole).filter(UserRole.role_id == role.id).delete()
            
            # Delete all role-permission assignments
            db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
            
            # Delete the role itself
            db.delete(role)
            db.commit()
            
            return f"Role '{role_name}' deleted successfully"
    
    @mcp.tool()
    @require_permission("roles_manage")
    def list_permissions(user_id: Optional[int] = None):
        """
        List all available permissions in the system. Admin only.
        
        Returns:
            List of all permission names
            
        Permission Required: roles_manage (admin only)
        """
        with get_db_session() as db:
            permissions = db.query(Permission).all()
            return [perm.name for perm in permissions]
    
    @mcp.tool()
    @require_permission("tasks_read")
    def get_my_data(user_id: Optional[int] = None):
        """
        Get all tasks and notes for the authenticated user in a single call.
        
        This is a convenience tool that combines list_tasks and list_notes
        to fetch all user data at once.
        
        Returns:
            Dictionary containing:
            - tasks: List of tasks with id, title, and completion status
            - notes: List of notes with id and content
            - summary: Quick statistics about tasks and notes
            
        Permission Required: tasks_read (also requires notes_read permission)
        """
        with get_db_session() as db:
            # Get user's tasks
            tasks = db.query(Task).filter(Task.user_id == user_id).all()
            task_list = [{"id": t.id, "title": t.title, "completed": t.completed} for t in tasks]
            
            # Get user's notes
            notes = db.query(Note).filter(Note.user_id == user_id).all()
            note_list = [{"id": n.id, "content": n.content} for n in notes]
            
            # Calculate summary
            total_tasks = len(task_list)
            completed_tasks = sum(1 for t in task_list if t["completed"] == 1)
            
            return {
                "tasks": task_list,
                "notes": note_list,
                "summary": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "incomplete_tasks": total_tasks - completed_tasks,
                    "total_notes": len(note_list)
                }
            }