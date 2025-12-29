from __future__ import annotations

import os
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from pathlib import Path
from typing import TypedDict

from hishel import SyncSqliteStorage
from hishel.httpx import SyncCacheClient
from tqdm.auto import tqdm

from .jobs import Job, Jobs, abbreviation_to_job, adventure, common

BASE_URL = "https://v2.xivapi.com/api"
XIV_ROLE_MAP = {
    "Paladin": 1,
    "Monk": 2,
    "Warrior": 3,
    "Dragoon": 4,
    "Bard": 5,
    "White Mage": 6,
    "Black Mage": 7,
    "Summoner": 8,
    "Scholar": 9,
    "Ninja": 10,
    "Machinist": 11,
    "Dark Knight": 12,
    "Astrologian": 13,
    "Samurai": 14,
    "Red Mage": 15,
    "Blue Mage": 16,
    "Gunbreaker": 17,
    "Dancer": 18,
    "Reaper": 19,
    "Sage": 20,
    "Viper": 21,
    "Pictomancer": 22,
}
XIV_ROLE_MAP_REVERSE = {v: k for k, v in XIV_ROLE_MAP.items()}

ROLE_MAP = {
    "Paladin": 1,
    "Warrior": 2,
    "Dark Knight": 3,
    "Gunbreaker": 4,
    "White Mage": 5,
    "Scholar": 6,
    "Astrologian": 7,
    "Sage": 8,
    "Monk": 9,
    "Dragoon": 10,
    "Ninja": 11,
    "Samurai": 12,
    "Reaper": 13,
    "Viper": 14,
    "Bard": 15,
    "Machinist": 16,
    "Dancer": 17,
    "Black Mage": 18,
    "Summoner": 19,
    "Red Mage": 20,
    "Blue Mage": 21,
    "Pictomancer": 22,
}
ROLE_MAP_REVERSE = {v: k for k, v in ROLE_MAP.items()}


class ActionCategory(Enum):
    "https://v2.xivapi.com/api/sheet/ActionCategory"

    AutoAttack = 1
    Spell = 2
    Weaponskill = 3
    Ability = 4
    Item = 5
    DoLAbility = 6
    DoHAbility = 7
    Event = 8
    LimitBreak = 9
    System = 10
    System2 = 11
    Mount = 12
    Special = 13
    ItemManipulation = 14
    LimitBreak2 = 15  # pvp limit break
    Artillery = 17


class IconType(TypedDict):
    id: int
    path: str
    path_hr1: str


class Field(TypedDict):
    Icon: IconType
    Name: str


class ActionRow(TypedDict):
    score: float
    sheet: str
    row_id: int
    fields: Field


def init_client() -> SyncCacheClient:
    return SyncCacheClient(
        base_url=BASE_URL,
        headers={
            "User-Agent": "FFXIVIconGetter/0.1.0",
            "Accept-Encoding": "zstd, gzip, deflate, br",
        },
        http2=True,
        timeout=20,
        follow_redirects=True,
        storage=SyncSqliteStorage(default_ttl=60 * 60 * 24),
    )


def has_icon(data: dict) -> bool:
    try:
        icon_id: int = data["fields"]["Icon"]["id"]
    except KeyError:
        return False
    return icon_id not in (0, 405)


def is_that_category(data: dict) -> bool:
    try:
        category_value: int = data["fields"]["ActionCategory"]["value"]
    except KeyError:
        return False
    return category_value in [
        ActionCategory.Ability.value,
        ActionCategory.Weaponskill.value,
        ActionCategory.Spell.value,
        ActionCategory.LimitBreak.value,
        ActionCategory.LimitBreak2.value,
    ]


def is_class_skill(data: dict) -> bool:
    try:
        class_job: int = data["fields"]["ClassJob"]["value"]
    except KeyError:
        return False
    return class_job > 0


def _is_some_action(data: dict, limit: int) -> bool:
    try:
        class_job_category: dict = data["fields"]["ClassJobCategory"]["fields"]
    except KeyError:
        return False
    count = 0
    for k, v in class_job_category.items():
        if k == "Name":
            continue
        if v:
            count += 1
    return count >= limit


def is_adv_action(data: dict) -> bool:
    limit = len(list(Jobs))
    return _is_some_action(data, limit)


def is_common_action(data: dict) -> bool:
    limit = 3
    return _is_some_action(data, limit)


def fetch_user_skills() -> list[ActionRow]:
    client = init_client()
    results = []
    query = "ClassJobCategory>0"

    resp = client.get("/search", params={"query": query, "sheets": "Action"})
    resp.raise_for_status()

    result = resp.json()
    results.extend(result["results"])

    next_token = result.get("next")
    while next_token:
        resp = client.get("/search", params={"cursor": next_token})
        resp.raise_for_status()

        result = resp.json()
        results.extend(result["results"])
        next_token = result.get("next")

    return results


def row_id_to_jobs(row_id: int) -> list[Job]:
    client = init_client()
    resp = client.get(f"/sheet/Action/{row_id}")
    resp.raise_for_status()

    data = resp.json()
    if "fields" not in data:
        return []

    try:
        class_job_category = data["fields"]["ClassJobCategory"]["fields"]
    except KeyError:
        return []

    has_icon_ = has_icon(data)
    is_that_category_ = is_that_category(data)

    if not has_icon_ or not is_that_category_:
        return []
    if is_adv_action(data):
        return [adventure]
    if is_common_action(data):
        return [common]

    jobs = []
    for abb, value in class_job_category.items():
        abb: str
        value: bool

        if abb == "Name" or not value:
            continue
        try:
            job = abbreviation_to_job(abb)
        except ValueError:
            continue
        jobs.append(job)

    return jobs


def actions_by_job(rows: list[ActionRow]) -> defaultdict[Job, list[ActionRow]]:
    results = defaultdict(list)
    pbar = tqdm(total=len(rows))

    tasks: list[Future[list[Job]]] = []
    with ThreadPoolExecutor() as executor:
        for row in rows:
            row_id = row["row_id"]
            task = executor.submit(row_id_to_jobs, row_id)
            task.add_done_callback(lambda _: pbar.update())
            tasks.append(task)

    for row, task in zip(rows, tasks, strict=True):
        jobs = task.result()
        for job in jobs:
            results[job].append(row)

    return results


def fetch_one_icon(path: str) -> bytes:
    client = init_client()
    params = {"path": path, "format": "png"}
    resp = client.get("/asset", params=params)
    resp.raise_for_status()
    return resp.content


def fetch_icons(
    actions_by_job: defaultdict[Job, list[ActionRow]],
    output_dir: str | os.PathLike[str] = "./data",
) -> None:
    icon_urls: set[str] = set()
    for rows in actions_by_job.values():
        for row in rows:
            icon = row["fields"]["Icon"]
            icon_urls.add(icon["path"])

    url_to_image: dict[str, bytes] = {}

    tasks: list[Future[bytes]] = []
    pbar = tqdm(total=len(icon_urls))
    with ThreadPoolExecutor() as executor:
        for path in icon_urls:
            task = executor.submit(fetch_one_icon, path)
            task.add_done_callback(lambda _: pbar.update())
            tasks.append(task)

    for path, task in zip(icon_urls, tasks, strict=True):
        image = task.result()
        url_to_image[path] = image

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    for job, rows in actions_by_job.items():
        save_dir_name = f"{job.save_order:02d}_{job.name}"
        save_dir = output.joinpath(save_dir_name)
        save_dir.mkdir(parents=True, exist_ok=True)

        for row in rows:
            icon = row["fields"]["Icon"]
            path = icon["path"]
            image = url_to_image[path]
            if len(image) == 0:
                continue
            name = row["fields"]["Name"]
            row_id = row["row_id"]

            filename = f"{row_id:04d}_{name}.png"
            output_path = save_dir.joinpath(filename)
            output_path.write_bytes(image)
