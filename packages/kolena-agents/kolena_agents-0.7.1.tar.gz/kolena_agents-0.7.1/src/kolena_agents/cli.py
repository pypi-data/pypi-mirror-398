import argparse

from kolena_agents._utils.webhook import Proxy


def run() -> None:
    ap = argparse.ArgumentParser()
    subparsers = ap.add_subparsers(required=True, dest="command", help="list help")

    listen_cmd = subparsers.add_parser("listen", help="listen to results of an agent")
    listen_cmd.add_argument("--agent-id", required=True, type=int, help="Agent ID")
    listen_cmd.add_argument("--secret", required=True, help="Webhook secret")
    listen_cmd.add_argument("--forward", help="Forward results to a target URL")
    listen_cmd.add_argument(
        "--tail",
        type=int,
        default=-1,
        help="Number of recent results to fetch. Defaults to -1 to only listen for new results",
    )

    sample_cmd = subparsers.add_parser("sample", help="generate sample results")
    sample_cmd.add_argument("--agent-id", required=True, type=int, help="Agent ID")
    sample_cmd.add_argument("--secret", required=True, help="Webhook secret")
    sample_cmd.add_argument("--forward", help="Forward results to a target URL")

    args = ap.parse_args()
    proxy = Proxy(
        agent_id=args.agent_id,
        secret=args.secret,
        target=args.forward,
    )

    if args.command == "listen":
        proxy.listen(args.tail)
    else:
        proxy.sample()
