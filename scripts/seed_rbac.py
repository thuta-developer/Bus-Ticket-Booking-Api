import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, text
from app.core.database import AsyncSessionLocal
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.models.user_role import user_roles
from app.models.role_permission import role_permissions

# Permission names are generated as "{resource}:{action}".
# Add a resource here instead of writing every permission dict manually.
CRUD_ACTIONS = ["read", "write", "delete"]
CRUD_RESOURCES = [
    "users",
    "roles",
    "permissions",
    # "buses",
]

# CUSTOM_RESOURCE_ACTIONS = {
#     "dashboard": ["access"],
#     "routes": ["read", "write"],
#     "schedules": ["read", "write"],
#     "bookings": ["read", "write", "cancel"],
#     "payments": ["read", "write"],
#     "reports": ["read"],
#     "audit": ["read"],
#     "settings": ["write"],
# }


def build_permissions():
    permissions = [
        {"name": f"{resource}:{action}", "resource": resource, "action": action}
        for resource in CRUD_RESOURCES
        for action in CRUD_ACTIONS
    ]

    # permissions.extend(
    #     {"name": f"{resource}:{action}", "resource": resource, "action": action}
    #     for resource, actions in CUSTOM_RESOURCE_ACTIONS.items()
    #     for action in actions
    # )

    return permissions


PERMISSIONS = build_permissions()

# Define roles with their permissions
ROLES = {
    "super_admin": {
        "description": "Super Administrator - Full system access",
        "is_default": False,
        "permissions": [p["name"] for p in PERMISSIONS]
    }
}

async def seed_rbac(sync_stale_roles: bool = False):
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

        if sync_stale_roles:
            active_role_names = list(ROLES.keys())
            stale_roles_result = await session.execute(
                select(Role.id, Role.name).where(Role.name.not_in(active_role_names))
            )
            stale_roles = stale_roles_result.all()

            if stale_roles:
                stale_role_ids = [role_id for role_id, _ in stale_roles]
                stale_role_names = [role_name for _, role_name in stale_roles]

                await session.execute(
                    delete(user_roles).where(user_roles.c.role_id.in_(stale_role_ids))
                )
                await session.execute(
                    delete(role_permissions).where(role_permissions.c.role_id.in_(stale_role_ids))
                )
                await session.execute(
                    delete(Role).where(Role.id.in_(stale_role_ids))
                )
                await session.commit()
                print(f"🧹 Deleted stale roles: {', '.join(stale_role_names)}")
        
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
        asyncio.run(seed_rbac(sync_stale_roles="--sync" in sys.argv))
