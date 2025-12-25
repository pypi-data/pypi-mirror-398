import argparse
import json
import os
import sys
from .client import CPUMarketsClient


def load_client(args):
    base_url = args.base_url or os.getenv("CPURENT_BASE_URL") or "https://www.cpu.markets"
    api_key = args.api_key or os.getenv("CPURENT_API_KEY")
    api_secret = args.api_secret or os.getenv("CPURENT_API_SECRET")
    if not api_key or not api_secret:
        raise SystemExit("Set CPURENT_API_KEY and CPURENT_API_SECRET (or pass --key/--secret)")
    return CPUMarketsClient(base_url, api_key, api_secret), base_url


def parse_payload(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON payload: {exc}")


def submit_common(args, client, listing_id=None):
    payload = parse_payload(args.payload)
    if listing_id:
        job_id = client.submit_job(
            listing_id=listing_id,
            task_type=args.task,
            payload=payload,
            requested_cores=args.cores,
            requested_seconds=args.seconds,
            priority=args.priority,
        )
    else:
        job_id = client.submit_direct_job(
            task_type=args.task,
            payload=payload,
            requested_cores=args.cores,
            requested_seconds=args.seconds,
            priority=args.priority,
        )
    print(f"Job submitted: {job_id}")
    if args.wait:
        result = client.wait_for_result(job_id, poll_interval=args.poll, timeout=args.timeout)
        print(json.dumps(result, indent=2))


def run_python(args, client):
    if not os.path.isfile(args.file):
        raise SystemExit(f"File not found: {args.file}")
    with open(args.file, "r", encoding="utf-8") as f:
        code = f.read()
    payload = {"code": code, "args": args.arg or []}
    if args.listing:
        job_id = client.submit_job(
            listing_id=args.listing,
            task_type="python",
            payload=payload,
            requested_cores=args.cores,
            requested_seconds=args.seconds,
            priority=args.priority,
        )
    else:
        job_id = client.submit_direct_job(
            task_type="python",
            payload=payload,
            requested_cores=args.cores,
            requested_seconds=args.seconds,
            priority=args.priority,
        )
    print(f"Python job submitted: {job_id}")
    if args.wait:
        result = client.wait_for_result(job_id, poll_interval=args.poll, timeout=args.timeout)
        print(json.dumps(result, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(prog="cpumarkets", description="CPUMarkets CLI for submitting CPU jobs")
    parser.add_argument("--base-url", help="API base URL (default env CPURENT_BASE_URL or https://www.cpu.markets)")
    parser.add_argument("--key", dest="api_key", help="SDK API key (or env CPURENT_API_KEY)")
    parser.add_argument("--secret", dest="api_secret", help="SDK API secret (or env CPURENT_API_SECRET)")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List available listings")
    p_list.set_defaults(handler="list")

    def add_job_args(p, include_listing=False):
        p.add_argument("--task", choices=["hashing", "math", "prime", "python"], required=True)
        p.add_argument("--payload", help="Job payload JSON (ignored for python subcommand)", default="{}")
        p.add_argument("--cores", type=int, default=1, help="Requested cores")
        p.add_argument("--seconds", type=int, default=30, help="Requested seconds")
        p.add_argument("--priority", type=int, default=0, help="Job priority")
        p.add_argument("--wait", action="store_true", help="Wait for completion and print result")
        p.add_argument("--poll", type=int, default=2, help="Polling interval when waiting")
        p.add_argument("--timeout", type=int, default=180, help="Wait timeout seconds")
        if include_listing:
            p.add_argument("--listing", type=int, required=True, help="Listing ID")

    p_submit = sub.add_parser("submit", help="Submit job to a specific listing")
    add_job_args(p_submit, include_listing=True)
    p_submit.set_defaults(handler="submit")

    p_direct = sub.add_parser("direct", help="Submit job to any direct-enabled listing")
    add_job_args(p_direct, include_listing=False)
    p_direct.set_defaults(handler="direct")

    p_py = sub.add_parser("python3", help="Run a Python script on rented CPU")
    p_py.add_argument("file", help="Path to Python file")
    p_py.add_argument("--arg", action="append", help="Argument to pass to the script", default=[])
    p_py.add_argument("--listing", type=int, help="Listing ID (defaults to direct mode)")
    p_py.add_argument("--cores", type=int, default=1)
    p_py.add_argument("--seconds", type=int, default=60)
    p_py.add_argument("--priority", type=int, default=0)
    p_py.add_argument("--wait", action="store_true")
    p_py.add_argument("--poll", type=int, default=2)
    p_py.add_argument("--timeout", type=int, default=300)
    p_py.set_defaults(handler="python3")

    p_result = sub.add_parser("result", help="Fetch job result")
    p_result.add_argument("job_id", type=int)
    p_result.set_defaults(handler="result")

    return parser


def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        client, _ = load_client(args)

        if args.handler == "list":
            listings = client.list_listings()
            print(json.dumps(listings, indent=2))
        elif args.handler == "submit":
            submit_common(args, client, listing_id=args.listing)
        elif args.handler == "direct":
            submit_common(args, client, listing_id=None)
        elif args.handler == "python3":
            run_python(args, client)
        elif args.handler == "result":
            res = client.get_result(args.job_id)
            print(json.dumps(res, indent=2))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
