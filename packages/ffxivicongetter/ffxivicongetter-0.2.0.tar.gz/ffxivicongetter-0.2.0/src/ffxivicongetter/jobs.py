from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Job:
    index: int
    job_index: int
    name: str
    abbreviation: str
    save_order: int


adventure = Job(
    index=1, job_index=0, name="Adventurer", abbreviation="ADV", save_order=0
)
common = Job(index=-1, job_index=-1, name="Common", abbreviation="", save_order=99)
paladin = Job(index=8, job_index=1, name="Paladin", abbreviation="PLD", save_order=1)
monk = Job(index=9, job_index=2, name="Monk", abbreviation="MNK", save_order=9)
warrior = Job(index=10, job_index=3, name="Warrior", abbreviation="WAR", save_order=2)
dragoon = Job(index=11, job_index=4, name="Dragoon", abbreviation="DRG", save_order=10)
bard = Job(index=12, job_index=5, name="Bard", abbreviation="BRD", save_order=15)
white_mage = Job(
    index=13, job_index=6, name="White Mage", abbreviation="WHM", save_order=5
)
black_mage = Job(
    index=14, job_index=7, name="Black Mage", abbreviation="BLM", save_order=18
)
summoner = Job(
    index=16, job_index=8, name="Summoner", abbreviation="SMN", save_order=19
)
scholar = Job(index=17, job_index=9, name="Scholar", abbreviation="SCH", save_order=6)
ninja = Job(index=19, job_index=10, name="Ninja", abbreviation="NIN", save_order=11)
machinist = Job(
    index=20, job_index=11, name="Machinist", abbreviation="MCH", save_order=16
)
dark_knight = Job(
    index=21, job_index=12, name="Dark Knight", abbreviation="DRK", save_order=3
)
astrologian = Job(
    index=22, job_index=13, name="Astrologian", abbreviation="AST", save_order=7
)
samurai = Job(index=23, job_index=14, name="Samurai", abbreviation="SAM", save_order=12)
red_mage = Job(
    index=24, job_index=15, name="Red Mage", abbreviation="RDM", save_order=20
)
blue_mage = Job(
    index=25, job_index=16, name="Blue Mage", abbreviation="BLU", save_order=21
)
gunbreaker = Job(
    index=26, job_index=17, name="Gunbreaker", abbreviation="GNB", save_order=4
)
dancer = Job(index=27, job_index=18, name="Dancer", abbreviation="DNC", save_order=17)
reaper = Job(index=28, job_index=19, name="Reaper", abbreviation="RPR", save_order=13)
sage = Job(index=29, job_index=20, name="Sage", abbreviation="SGE", save_order=8)
viper = Job(index=30, job_index=21, name="Viper", abbreviation="VPR", save_order=14)
pictomancer = Job(
    index=31, job_index=22, name="Pictomancer", abbreviation="PCT", save_order=22
)


class Jobs(Enum):
    Paladin = paladin
    Warrior = warrior
    DarkKnight = dark_knight
    Gunbreaker = gunbreaker
    WhiteMage = white_mage
    Scholar = scholar
    Astrologian = astrologian
    Sage = sage
    Monk = monk
    Dragoon = dragoon
    Ninja = ninja
    Samurai = samurai
    Reaper = reaper
    Viper = viper
    Bard = bard
    Machinist = machinist
    Dancer = dancer
    BlackMage = black_mage
    Summoner = summoner
    RedMage = red_mage
    BlueMage = blue_mage
    Pictomancer = pictomancer


def abbreviations() -> list[str]:
    return [job.value.abbreviation for job in Jobs]


def abbreviation_to_job(abbreviation: str) -> Job:
    for job in Jobs:
        if job.value.abbreviation == abbreviation:
            return job.value
    msg = f"Invalid abbreviation: {abbreviation}"
    raise ValueError(msg)
