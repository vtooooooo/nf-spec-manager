# app.py
import streamlit as st
import yaml, os
from dotenv import load_dotenv
load_dotenv()

from core.auth import login, get_all_users, ROLE_PERMISSIONS, can
from core.deployment import get_specs, read_spec, create_spec, promote_spec, delete_spec
from core.audit import get_logs, init_db
from core.validator import validate_spec_dict
from core.s3_sync import upload_spec, list_s3_specs, sync_all_to_s3

st.set_page_config(page_title="NF Spec Manager", page_icon="🔧", layout="wide")
init_db()

if "user" not in st.session_state:
    st.session_state.user = None

def show_login():
    st.title("🔧 NF Spec Manager")
    st.subheader("Login")
    st.info("Demo users: alice (deployer) | bob (editor) | carol (viewer) | admin (admin)")
    col1, _ = st.columns([1, 2])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

def show_sidebar():
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 👤 {user['username']}")
        st.markdown(f"**Role:** `{user['role']}`")
        perms = ROLE_PERMISSIONS.get(user["role"], [])
        st.markdown("**Permissions:** " + " | ".join(f"`{p}`" for p in perms))
        st.divider()
        page = st.radio("Navigate", [
            "📋 View Specs", "➕ Create Spec", "🚀 Promote Spec",
            "☁️ S3 Sync", "📜 Audit Log", "👥 Users & Roles"
        ])
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()
    return page

def page_view_specs():
    st.header("📋 NF Specifications")
    env = st.selectbox("Environment", ["dev", "staging", "prod"])
    specs = get_specs(env)
    if not specs:
        st.warning(f"No specs found in {env}")
        return
    st.success(f"Found {len(specs)} spec(s) in **{env}**")
    for spec_file in specs:
        with st.expander(f"📄 {spec_file}"):
            data = read_spec(env, spec_file)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Name:** {data.get('name')}")
                st.markdown(f"**Version:** {data.get('version')}")
                st.markdown(f"**Type:** {data.get('nf_type')}")
                st.markdown(f"**Owner:** {data.get('owner')}")
            with col2:
                r = data.get("resources", {})
                st.markdown(f"**CPU:** {r.get('cpu')}")
                st.markdown(f"**Memory:** {r.get('memory')}")
                st.markdown(f"**Replicas:** {r.get('replicas')}")
            if data.get("tags"):
                st.markdown("**Tags:** " + " ".join(f"`{t}`" for t in data["tags"]))

def page_create_spec():
    st.header("➕ Create New NF Spec")
    user = st.session_state.user
    if not can(user, "create"):
        st.error("You don't have permission to create specs.")
        return
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Spec Name (lowercase, hyphens)", placeholder="my-nf-service")
        version = st.text_input("Version", value="1.0.0")
        nf_type = st.selectbox("NF Type", ["VNF", "CNF", "PNF"])
        environment = st.selectbox("Target Environment", ["dev", "staging", "prod"])
        owner = st.text_input("Owner", placeholder="team-name")
        description = st.text_area("Description")
    with col2:
        st.markdown("**Resources**")
        cpu = st.text_input("CPU", value="500m")
        memory = st.text_input("Memory", value="256Mi")
        replicas = st.number_input("Replicas", min_value=1, max_value=20, value=1)
        st.markdown("**Network**")
        port = st.number_input("Port", min_value=1, max_value=65535, value=8080)
        protocol = st.selectbox("Protocol", ["TCP", "UDP", "HTTP", "HTTPS", "GRPC"])
        expose = st.checkbox("Expose externally")
        tags_input = st.text_input("Tags (comma-separated)")
    if st.button("Validate & Create", use_container_width=True):
        spec_data = {
            "name": name, "version": version, "nf_type": nf_type,
            "environment": environment, "owner": owner, "description": description,
            "resources": {"cpu": cpu, "memory": memory, "replicas": int(replicas)},
            "network": {"port": int(port), "protocol": protocol, "expose": expose},
            "tags": [t.strip() for t in tags_input.split(",") if t.strip()]
        }
        is_valid, _, error = validate_spec_dict(spec_data)
        if not is_valid:
            st.error(f"Validation failed: {error}")
        else:
            ok, msg = create_spec(user, environment, name, spec_data)
            st.success(msg) if ok else st.error(msg)

def page_promote_spec():
    st.header("🚀 Promote Spec")
    user = st.session_state.user
    if not can(user, "deploy"):
        st.error("You don't have permission to promote specs.")
        return
    col1, col2 = st.columns(2)
    with col1:
        from_env = st.selectbox("Promote FROM", ["dev", "staging"])
    with col2:
        to_env = "staging" if from_env == "dev" else "prod"
        st.info(f"Will promote to: **{to_env}**")
    specs = get_specs(from_env)
    if not specs:
        st.warning(f"No specs in {from_env}")
        return
    spec_file = st.selectbox("Select Spec", specs)
    if spec_file:
        st.json(read_spec(from_env, spec_file))
    if st.button(f"Promote {spec_file} to {to_env}", use_container_width=True):
        ok, msg = promote_spec(user, spec_file, from_env)
        if ok:
            st.success(msg)
            s3_ok, s3_msg = upload_spec(to_env, spec_file)
            st.info(f"S3: {s3_msg}") if s3_ok else st.warning(f"S3 skipped: {s3_msg}")
        else:
            st.error(msg)

def page_s3_sync():
    st.header("☁️ AWS S3 Sync")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Upload to S3")
        env = st.selectbox("Environment", ["dev", "staging", "prod"])
        specs = get_specs(env)
        if specs:
            spec_file = st.selectbox("Select Spec", specs)
            if st.button("Upload to S3"):
                ok, msg = upload_spec(env, spec_file)
                st.success(msg) if ok else st.error(msg)
        else:
            st.warning("No specs found locally")
        if st.button("Sync ALL to S3", use_container_width=True):
            uploaded, errors = sync_all_to_s3()
            if uploaded:
                st.success(f"Uploaded: {', '.join(uploaded)}")
            if errors:
                st.error(f"Errors: {'; '.join(errors)}")
    with col2:
        st.subheader("S3 Contents")
        s3_env = st.selectbox("Filter", ["all", "dev", "staging", "prod"])
        if st.button("List S3 Files"):
            keys = list_s3_specs(None if s3_env == "all" else s3_env)
            for k in keys:
                st.code(k)
            if not keys:
                st.info("No files found in S3")

def page_audit_log():
    st.header("📜 Audit Log")
    logs = get_logs(limit=200)
    if not logs:
        st.info("No audit entries yet.")
        return
    import pandas as pd
    df = pd.DataFrame(logs)
    st.dataframe(df, use_container_width=True, height=500)
    st.download_button("Download CSV", data=df.to_csv(index=False),
                       file_name="audit_log.csv", mime="text/csv")

def page_users():
    st.header("👥 Users & Roles")
    import pandas as pd
    st.subheader("Current Users")
    st.dataframe(pd.DataFrame(get_all_users()), use_container_width=True)
    st.subheader("Role Permissions Matrix")
    all_actions = ["read", "create", "update", "deploy", "delete", "manage_users"]
    rows = []
    for role, perms in ROLE_PERMISSIONS.items():
        row = {"role": role}
        for a in all_actions:
            row[a] = "YES" if a in perms else "-"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows).set_index("role"), use_container_width=True)

def main():
    if st.session_state.user is None:
        show_login()
        return
    page = show_sidebar()
    if page == "📋 View Specs":      page_view_specs()
    elif page == "➕ Create Spec":   page_create_spec()
    elif page == "🚀 Promote Spec":  page_promote_spec()
    elif page == "☁️ S3 Sync":       page_s3_sync()
    elif page == "📜 Audit Log":     page_audit_log()
    elif page == "👥 Users & Roles": page_users()

if __name__ == "__main__":
    main()