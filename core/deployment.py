# core/deployment.py
import shutil, os, yaml
from core.validator import validate_spec, validate_spec_dict
from core.audit import log_action
from core.auth import require_permission

PROMOTION_PATH = {"dev": "staging", "staging": "prod"}

def get_specs(environment):
    folder = os.path.join("specs", environment)
    os.makedirs(folder, exist_ok=True)
    return [f for f in os.listdir(folder) if f.endswith((".yaml", ".yml"))]

def read_spec(environment, spec_file):
    path = os.path.join("specs", environment, spec_file)
    with open(path, "r") as f:
        return yaml.safe_load(f)

def create_spec(user, environment, spec_name, spec_data):
    try:
        require_permission(user, "create")
        spec_data["environment"] = environment
        is_valid, _, error = validate_spec_dict(spec_data)
        if not is_valid:
            log_action(user, "create", spec_name, to_env=environment,
                       status="FAILED", message=error)
            return False, f"Validation failed: {error}"
        folder = os.path.join("specs", environment)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, f"{spec_name}.yaml"), "w") as f:
            yaml.dump(spec_data, f, default_flow_style=False)
        log_action(user, "create", spec_name, to_env=environment,
                   status="SUCCESS", message="Created")
        return True, f"Spec '{spec_name}' created in {environment}"
    except PermissionError as e:
        return False, str(e)

def promote_spec(user, spec_file, from_env):
    try:
        require_permission(user, "deploy")
        if from_env not in PROMOTION_PATH:
            return False, f"Cannot promote from '{from_env}'"
        to_env = PROMOTION_PATH[from_env]
        src_path = os.path.join("specs", from_env, spec_file)
        dst_folder = os.path.join("specs", to_env)
        os.makedirs(dst_folder, exist_ok=True)
        is_valid, _, error = validate_spec(src_path)
        if not is_valid:
            log_action(user, "promote", spec_file, from_env=from_env,
                       to_env=to_env, status="FAILED", message=error)
            return False, f"Validation failed: {error}"
        shutil.copy2(src_path, os.path.join(dst_folder, spec_file))
        log_action(user, "promote", spec_file, from_env=from_env,
                   to_env=to_env, status="SUCCESS",
                   message=f"Promoted to {to_env}")
        return True, f"'{spec_file}' promoted from {from_env} to {to_env}"
    except PermissionError as e:
        log_action(user, "promote", spec_file, from_env=from_env,
                   to_env=PROMOTION_PATH.get(from_env, "unknown"),
                   status="DENIED", message=str(e))
        return False, str(e)

def delete_spec(user, environment, spec_file):
    try:
        require_permission(user, "delete")
        path = os.path.join("specs", environment, spec_file)
        if not os.path.exists(path):
            return False, "Spec not found"
        os.remove(path)
        log_action(user, "delete", spec_file, from_env=environment,
                   status="SUCCESS")
        return True, f"'{spec_file}' deleted from {environment}"
    except PermissionError as e:
        return False, str(e)