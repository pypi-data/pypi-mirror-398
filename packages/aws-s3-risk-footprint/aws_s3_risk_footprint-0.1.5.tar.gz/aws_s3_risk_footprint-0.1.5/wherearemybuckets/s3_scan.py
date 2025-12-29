import boto3

def get_buckets_with_regions(profile=None):
    session = boto3.Session(profile_name=profile)
    s3 = session.client("s3")

    response = s3.list_buckets()
    buckets = response.get("Buckets", [])

    results = []

    for bucket in buckets:
        name = bucket["Name"]

        try:
            loc = s3.get_bucket_location(Bucket=name)
            region = loc["LocationConstraint"] or "us-east-1"
        except Exception as e:
            region = f"ERROR: {e}"

        results.append({
            "bucket": name,
            "region": region
        })

    return {
        "total": len(buckets),
        "buckets": results
    }
