# core/s3_sync.py
import boto3, os
from botocore.exceptions import ClientError

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )

def get_bucket():
    return os.getenv("S3_BUCKET", "nf-spec-manager")

def upload_spec(environment, spec_file):
    try:
        s3 = get_s3_client()
        local_path = os.path.join("specs", environment, spec_file)
        s3_key = f"specs/{environment}/{spec_file}"
        s3.upload_file(local_path, get_bucket(), s3_key)
        return True, f"Uploaded to s3://{get_bucket()}/{s3_key}"
    except Exception as e:
        return False, f"S3 error: {e}"

def list_s3_specs(environment=None):
    try:
        s3 = get_s3_client()
        prefix = f"specs/{environment}/" if environment else "specs/"
        response = s3.list_objects_v2(Bucket=get_bucket(), Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]
    except Exception:
        return []

def sync_all_to_s3():
    uploaded, errors = [], []
    for env in ["dev", "staging", "prod"]:
        folder = os.path.join("specs", env)
        if not os.path.exists(folder):
            continue
        for f in os.listdir(folder):
            if f.endswith((".yaml", ".yml")):
                ok, msg = upload_spec(env, f)
                if ok:
                    uploaded.append(f"{env}/{f}")
                else:
                    errors.append(msg)
    return uploaded, errors