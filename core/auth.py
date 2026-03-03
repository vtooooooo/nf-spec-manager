# core/auth.py
USERS = {
    "alice": {"password": "alice123", "role": "deployer"},
    "bob":   {"password": "bob123",   "role": "editor"},
    "carol": {"password": "carol123", "role": "viewer"},
    "admin": {"password": "admin123", "role": "admin"},
}

ROLE_PERMISSIONS = {
    "viewer":   ["read"],
    "editor":   ["read", "create", "update"],
    "deployer": ["read", "create", "update", "deploy"],
    "admin":    ["read", "create", "update", "deploy", "delete", "manage_users"],
}

def login(username, password):
    user = USERS.get(username)
    if user and user["password"] == password:
        return {"username": username, "role": user["role"]}
    return None

def can(user, action):
    if not user:
        return False
    return action in ROLE_PERMISSIONS.get(user["role"], [])

def require_permission(user, action):
    if not can(user, action):
        raise PermissionError(
            f"User '{user['username']}' with role '{user['role']}' "
            f"cannot perform: '{action}'"
        )

def get_all_users():
    return [{"username": u, "role": d["role"]} for u, d in USERS.items()]