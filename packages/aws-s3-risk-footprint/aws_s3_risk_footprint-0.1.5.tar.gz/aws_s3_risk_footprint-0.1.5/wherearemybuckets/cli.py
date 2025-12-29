import argparse
import boto3
from collections import defaultdict
from wherearemybuckets.s3_scan import get_buckets_with_regions
from wherearemybuckets.s3_risk import analyze_bucket

def group_by_region(buckets):
    regions = defaultdict(list)
    for b in buckets:
        regions[b["region"]].append(b["bucket"])
    return regions


def render_map(regions):
    print("\nAWS S3 REGIONAL DISTRIBUTION")
    print("-" * 30)

    MAX_BAR_WIDTH = 20
    max_count = max(len(b) for b in regions.values())

    for region in sorted(regions.keys()):
        count = len(regions[region])
        bar_length = int((count / max_count) * MAX_BAR_WIDTH)
        bar = "█" * bar_length
        print(f"{region:<15} {bar:<20} {count}")

    def section(title, region_keys):
        print(f"\n{title}")
        print("-" * len(title))
        for r in region_keys:
            if r in regions:
                count = len(regions[r])
                MAX_BAR_WIDTH = 20
                max_count = max(len(b) for b in regions.values())
                bar_length = int((count / max_count) * MAX_BAR_WIDTH)
                bar = "█" * bar_length
                print(f"{r:<15} [{bar}] {count}")

    section("WEST (Americas)", ["us-west-1", "us-west-2"])
    section("EAST (Americas)", ["us-east-1", "us-east-2"])
    section("EUROPE", ["eu-central-1", "eu-west-1"])
    section("APAC", ["ap-south-1", "ap-northeast-1"])


def render_expand(regions, region=None):
    print("\n🌎 AWS S3 BUCKET FOOTPRINT")
    print("=" * 50)

    for r, buckets in regions.items():
        if region and r != region:
            continue

        print(f"\n{r} ({len(buckets)})")
        print("-" * (len(r) + 5))
        for b in buckets:
            print(f"• {b}")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize AWS S3 buckets by region"
    )

    parser.add_argument(
        "--profile",
        help="AWS profile to use",
        default=None
    )

    subparsers = parser.add_subparsers(dest="command")

    # MAP
    subparsers.add_parser("map", help="Show regional distribution view")

    # EXPAND
    expand_cmd = subparsers.add_parser("expand", help="Show full bucket list")
    expand_cmd.add_argument(
        "--region",
        help="Show buckets for a specific region"
    )

    # RISK
    risk_cmd = subparsers.add_parser(
        "risk",
        help="Analyze S3 bucket security risk"
    )
    risk_cmd.add_argument(
        "--objects",
        action="store_true",
        help="Include object counts (may be slow / incur API calls)"
    )

    # WHOAMI
    subparsers.add_parser("whoami", help="Show AWS identity context")

    args = parser.parse_args()

    # WHOAMI does NOT need S3 calls
    if args.command == "whoami":
        session = boto3.Session(profile_name=args.profile)
        sts = session.client("sts")
        identity = sts.get_caller_identity()

        print("\nAWS Identity")
        print("=" * 30)
        print(f"Account ID : {identity['Account']}")
        print(f"ARN        : {identity['Arn']}")
        return

    # All other commands require S3 inventory
    data = get_buckets_with_regions(profile=args.profile)
    total_buckets = data["total"]
    buckets = data["buckets"]
    regions = group_by_region(buckets)

    if args.command == "map":
        print(f"\nTotal S3 Buckets: {total_buckets}")
        render_map(regions)

    elif args.command == "expand":
        print(f"\nTotal S3 Buckets: {total_buckets}")
        render_expand(regions, args.region)

    elif args.command == "risk":
        print(f"\nTotal S3 Buckets: {total_buckets}")
        session = boto3.Session(profile_name=args.profile)
        results = []

        for region, buckets_in_region in regions.items():
            for bucket in buckets_in_region:
                result = analyze_bucket(
                    bucket=bucket,
                    session=session,
                    include_objects=args.objects
                )
                result["region"] = region
                results.append(result)

        high = [r for r in results if r["risk"] == "HIGH"]
        med  = [r for r in results if r["risk"] == "MEDIUM"]
        low  = [r for r in results if r["risk"] == "LOW"]

        print("\nAWS S3 RISK SUMMARY")
        print("=" * 40)
        print(f"HIGH RISK   : {len(high)} buckets")
        print(f"MEDIUM RISK : {len(med)} buckets")
        print(f"LOW RISK    : {len(low)} buckets")

        if high:
            print("\nHigh-Risk Buckets")
            print("-" * 40)
            for b in high:
                line = f"• {b['bucket']} ({b['region']})"
                if b["objects"] is not None:
                    line += f" — {b['objects']} objects"
                print(line)

    else:
        parser.print_help()




if __name__ == "__main__":
    main()