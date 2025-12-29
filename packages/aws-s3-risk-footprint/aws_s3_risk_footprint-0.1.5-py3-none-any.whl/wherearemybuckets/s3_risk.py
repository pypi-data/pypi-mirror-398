import boto3

def is_bucket_public(bucket, session):
    s3 = session.client("s3")
    try:
        pab = s3.get_public_access_block(Bucket=bucket)
        config = pab["PublicAccessBlockConfiguration"]
        return not all(config.values())
    except:
        return True  # No block config = potentially public


def is_bucket_encrypted(bucket, session):
    s3 = session.client("s3")
    try:
        s3.get_bucket_encryption(Bucket=bucket)
        return True
    except:
        return False


def get_object_count(bucket, session):
    s3 = session.client("s3")
    paginator = s3.get_paginator("list_objects_v2")

    count = 0
    for page in paginator.paginate(Bucket=bucket):
        count += page.get("KeyCount", 0)

    return count


def analyze_bucket(bucket, session, include_objects=False):
    public = is_bucket_public(bucket, session)
    encrypted = is_bucket_encrypted(bucket, session)

    objects = None
    if include_objects:
        objects = get_object_count(bucket, session)

    if public:
        risk = "HIGH"
    elif not encrypted:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "bucket": bucket,
        "public": public,
        "encrypted": encrypted,
        "risk": risk,
        "objects": objects
    }
