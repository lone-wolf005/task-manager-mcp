from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    scalekit_user_id = Column(String, unique=True)
    email = Column(String)


class Role(Base):

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Permission(Base):

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class UserRole(Base):

    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))


class RolePermission(Base):

    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True)

    role_id = Column(Integer, ForeignKey("roles.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))


class Note(Base):

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)


class Task(Base):

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    completed = Column(Integer, default=0)