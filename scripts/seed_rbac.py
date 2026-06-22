import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.models.user_role import user_roles
from app.models.role_permission import role_permissions

# Define standard permissions
PERMISSIONS = [
    # User Management
    {"name": "users:read", "resource": "users", "action": "read"},
    {"name": "users:write", "resource": "users", "action": "write"},
    {"name": "users:delete", "resource": "users", "action": "delete"},
    
    # ========== Roles & Permissions Management (NEW) ==========
    {"name": "roles:read", "resource": "roles", "action": "read"},
    {"name": "roles:write", "resource": "roles", "action": "write"},
    {"name": "roles:delete", "resource": "roles", "action": "delete"},
    {"name": "permissions:read", "resource": "permissions", "action": "read"},
    {"name": "permissions:write", "resource": "permissions", "action": "write"},
    {"name": "permissions:delete", "resource": "permissions", "action": "delete"},
    {"name": "dashboard:access", "resource": "dashboard", "action": "access"},
    
    # Bus Management
    {"name": "buses:read", "resource": "buses", "action": "read"},
    {"name": "buses:write", "resource": "buses", "action": "write"},
    {"name": "buses:delete", "resource": "buses", "action": "delete"},
    # Routes & Schedules
    {"name": "routes:read", "resource": "routes", "action": "read"},
    {"name": "routes:write", "resource": "routes", "action": "write"},
    {"name": "schedules:read", "resource": "schedules", "action": "read"},
    {"name": "schedules:write", "resource": "schedules", "action": "write"},
    # Bookings
    {"name": "bookings:read", "resource": "bookings", "action": "read"},
    {"name": "bookings:write", "resource": "bookings", "action": "write"},
    {"name": "bookings:cancel", "resource": "bookings", "action": "cancel"},
    # Payments
    {"name": "payments:read", "resource": "payments", "action": "read"},
    {"name": "payments:write", "resource": "payments", "action": "write"},
    # Reports & Audit
    {"name": "reports:read", "resource": "reports", "action": "read"},
    {"name": "audit:read", "resource": "audit", "action": "read"},
    {"name": "settings:write", "resource": "settings", "action": "write"},
]

# Define roles with their permissions
ROLES = {
    "super_admin": {
        "description": "Super Administrator - Full system access",
        "is_default": False,
        "permissions": [p["name"] for p in PERMISSIONS]
    },
    "manager": {
        "description": "Manager - Dashboard staff with operational management access",
        "is_default": False,
        "permissions": [
            "dashboard:access",
            "users:read",
            "buses:read", "buses:write",
            "routes:read", "routes:write",
            "schedules:read", "schedules:write",
            "bookings:read",
            "payments:read",
            "reports:read"
        ]
    },
    "admin": {
        "description": "Administrator - Can manage users, buses, routes",
        "is_default": False,
        "permissions": [
            "users:read", "users:write",
            "buses:read", "buses:write", "buses:delete",
            "routes:read", "routes:write",
            "schedules:read", "schedules:write",
            "bookings:read",
            "payments:read",
            "reports:read"
        ]
    },
    "bus_operator": {
        "description": "Bus Operator - Manage their own buses and schedules",
        "is_default": False,
        "permissions": [
            "buses:read", "buses:write",
            "schedules:read", "schedules:write",
            "bookings:read",
            "reports:read"
        ]
    },
    "customer": {
        "description": "Customer - Book tickets and view bookings",
        "is_default": True,
        "permissions": [
            "bookings:read", "bookings:write", "bookings:cancel",
            "payments:read"
        ]
    }
}

async def seed_rbac():
    """Seed RBAC data into the database."""
    print("🌱 Seeding RBAC data...")
    
    async with AsyncSessionLocal() as session:
        # 1. Create Permissions (using ORM)
        permission_objects = {}
        for perm_data in PERMISSIONS:
            # Check if exists
            result = await session.execute(
                text("SELECT id FROM permissions WHERE name = :name"),
                {"name": perm_data["name"]}
            )
            row = result.first()
            
            if row:
                # Get existing permission
                perm = await session.get(Permission, row[0])
                permission_objects[perm_data["name"]] = perm
            else:
                # Create new
                perm = Permission(**perm_data)
                session.add(perm)
                await session.flush()
                permission_objects[perm_data["name"]] = perm
        
        await session.commit()
        
        # 2. Create Roles and assign permissions
        for role_name, role_config in ROLES.items():
            # Check if exists
            result = await session.execute(
                text("SELECT id FROM roles WHERE name = :name"),
                {"name": role_name}
            )
            row = result.first()
            
            if row:
                role = await session.get(Role, row[0])
                role.description = role_config["description"]
                role.is_default = role_config["is_default"]
            else:
                role = Role(
                    name=role_name,
                    description=role_config["description"],
                    is_default=role_config["is_default"]
                )
                session.add(role)
            
            await session.flush()
            
            # Clear existing permissions
            await session.execute(
                text("DELETE FROM role_permissions WHERE role_id = :role_id"),
                {"role_id": role.id}
            )
            
            # Add new permissions
            for perm_name in role_config["permissions"]:
                if perm_name in permission_objects:
                    stmt = role_permissions.insert().values(
                        role_id=role.id,
                        permission_id=permission_objects[perm_name].id
                    )
                    await session.execute(stmt)
        
        await session.commit()
        print("✅ RBAC seeding complete!")

async def assign_super_admin(user_email: str):
    """Assign super_admin role to an existing user."""
    async with AsyncSessionLocal() as session:
        # Get user
        result = await session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user_email}
        )
        user_row = result.first()
        if not user_row:
            print(f"❌ User {user_email} not found!")
            return
        
        user_id = user_row[0]

        await session.execute(
            text(
                "UPDATE users "
                "SET account_type = 'staff', is_superuser = true "
                "WHERE id = :user_id"
            ),
            {"user_id": user_id}
        )
        
        # Get super_admin role
        result = await session.execute(
            text("SELECT id FROM roles WHERE name = 'super_admin'")
        )
        role_row = result.first()
        if not role_row:
            print("❌ super_admin role not found! Run seed first.")
            return
        
        role_id = role_row[0]
        
        # Check if already assigned
        result = await session.execute(
            text("SELECT 1 FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
            {"user_id": user_id, "role_id": role_id}
        )
        if result.first():
            await session.commit()
            print(f"✅ {user_email} is already a Super Admin!")
            return
        
        # Assign role
        stmt = user_roles.insert().values(user_id=user_id, role_id=role_id)
        await session.execute(stmt)
        await session.commit()
        print(f"✅ {user_email} is now a Super Admin!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "assign-admin":
        email = sys.argv[2] if len(sys.argv) > 2 else "admin@example.com"
        asyncio.run(assign_super_admin(email))
    else:
        asyncio.run(seed_rbac())
