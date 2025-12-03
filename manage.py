#!/usr/bin/env python3
"""
Management script for Telethon FastAPI app.
Supports creating admin users and other operations.

Usage:
  python manage.py create_admin <username> <password> [--no-admin]
  python manage.py list_users
  python manage.py delete_user <username>
"""

import sys
import os
from argparse import ArgumentParser

# Ensure app can be imported
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app import crud


def create_admin(username: str, password: str, is_admin: bool = True):
    """Create a new user."""
    db = SessionLocal()
    try:
        existing = crud.get_user_by_username(db, username)
        if existing:
            print(f"❌ User '{username}' already exists (id={existing.id})")
            return False
        
        user = crud.create_user(db, username, password, is_admin=is_admin)
        role = "admin" if is_admin else "user"
        print(f"✅ Created {role} user:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   ID: {user.id}")
        return True
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False
    finally:
        db.close()


def list_users():
    """List all users in the database."""
    db = SessionLocal()
    try:
        users = db.query(crud.models.User).all()
        if not users:
            print("No users found.")
            return
        
        print("\n📋 Users in database:")
        print(f"{'ID':<5} {'Username':<20} {'Role':<10} {'Created':<20}")
        print("-" * 55)
        for user in users:
            role = "admin" if user.is_admin else "user"
            created = user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else "N/A"
            print(f"{user.id:<5} {user.username:<20} {role:<10} {created:<20}")
    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        db.close()


def delete_user(username: str):
    """Delete a user by username."""
    db = SessionLocal()
    try:
        user = crud.get_user_by_username(db, username)
        if not user:
            print(f"❌ User '{username}' not found.")
            return False
        
        db.delete(user)
        db.commit()
        print(f"✅ Deleted user '{username}' (id={user.id})")
        return True
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        return False
    finally:
        db.close()


def main():
    parser = ArgumentParser(description="Telethon FastAPI management script")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # create_admin command
    create_parser = subparsers.add_parser("create_admin", help="Create a new admin user")
    create_parser.add_argument("username", help="Username")
    create_parser.add_argument("password", help="Password")
    create_parser.add_argument("--no-admin", action="store_true", help="Create as regular user (not admin)")
    
    # list_users command
    subparsers.add_parser("list_users", help="List all users")
    
    # delete_user command
    delete_parser = subparsers.add_parser("delete_user", help="Delete a user")
    delete_parser.add_argument("username", help="Username to delete")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "create_admin":
        is_admin = not args.no_admin
        success = create_admin(args.username, args.password, is_admin=is_admin)
        sys.exit(0 if success else 1)
    
    elif args.command == "list_users":
        list_users()
        sys.exit(0)
    
    elif args.command == "delete_user":
        success = delete_user(args.username)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
