import argparse

from ffxivicongetter.core import actions_by_job, fetch_icons, fetch_user_skills


def cli():
    parser = argparse.ArgumentParser(description="FFXIV Icon Getter")
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory for icons (default: ./data)",
        default="./data",
    )
    args = parser.parse_args()
    skills = fetch_user_skills()
    actions = actions_by_job(skills)
    fetch_icons(actions, args.output)
