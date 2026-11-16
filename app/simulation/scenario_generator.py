"""
Synthetic Scenario Generator (Section 5.1):
Generates realistic disaster relief scenarios over a 50x50 km area
with three need clusters representing affected zones.
Scenarios:
- S1 (small): 60 volunteers, 25 needs, ~61 slots (supply is tight)
- S2 (medium): 200 volunteers, 80 needs, ~200 slots
- S3 (large): 600 volunteers, 250 needs, ~619 slots
"""

import random
import numpy as np
from typing import List, Tuple
from app.models.schemas import Volunteer, Need

CLUSTERS = [
    (12.5, 12.5),  # Cluster 1: West zone
    (37.5, 15.0),  # Cluster 2: East zone
    (25.0, 37.5),  # Cluster 3: North zone
]

SKILLS = ["medical", "logistics", "translation", "distribution"]
LANGUAGES = ["en", "hi", "pa", "bn", "ta"]

FIRST_NAMES = ["Aarav", "Manya", "Abhiram", "Charan", "Priya", "Rahul", "Ananya", "Rohan", "Simran", "Deepak", "Neha", "Vikram", "Sunita", "Harpreet", "Gurpreet", "Amit", "Kavita", "Siddharth", "Meera", "Arjun"]
LAST_NAMES = ["Sharma", "Tej", "Ramaprasad", "Singh", "Kumar", "Kaur", "Patel", "Verma", "Gupta", "Das", "Reddy", "Banerjee", "Gill", "Chopra", "Joshi"]

def sample_clustered_point(rng: random.Random, sigma: float = 4.5) -> Tuple[float, float]:
    """Generates coordinate clustered around one of the three affected zones within 50x50 km."""
    cx, cy = rng.choice(CLUSTERS)
    x = rng.gauss(cx, sigma)
    y = rng.gauss(cy, sigma)
    # Clip to [0.0, 50.0]
    return max(0.5, min(49.5, x)), max(0.5, min(49.5, y))

def generate_volunteers(num_volunteers: int, rng: random.Random) -> List[Volunteer]:
    volunteers = []
    for i in range(num_volunteers):
        # 1 or 2 skills
        num_skills = rng.choices([1, 2], weights=[0.6, 0.4])[0]
        chosen_skills = rng.sample(SKILLS, num_skills)

        # 1 or 2 languages
        num_langs = rng.choices([1, 2], weights=[0.5, 0.5])[0]
        chosen_langs = rng.sample(LANGUAGES, num_langs)
        if "hi" not in chosen_langs and rng.random() < 0.6:
            chosen_langs.append("hi")

        x, y = sample_clustered_point(rng, sigma=6.0)

        # 4-12 hour availability window
        duration = rng.uniform(4.0, 12.0)
        start_time = rng.uniform(6.0, 16.0)
        end_time = min(24.0, start_time + duration)

        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"

        volunteers.append(Volunteer(
            id=f"vol-{i+1:03d}",
            name=name,
            skills=chosen_skills,
            languages=chosen_langs,
            latitude=round(x, 4),
            longitude=round(y, 4),
            start_time=round(start_time, 2),
            end_time=round(end_time, 2),
            status="available",
            hlc_timestamp=1700000000000 + i,
            node_id="camp-node-01"
        ))
    return volunteers

def generate_needs(num_needs: int, target_slots: int, rng: random.Random) -> List[Need]:
    needs = []
    # Distribute slots across needs to match target_slots closely
    slots_per_need = []
    rem_slots = target_slots
    for i in range(num_needs):
        slots_left_for_rest = (num_needs - 1 - i)
        # Choose 1 to 4
        min_possible = max(1, rem_slots - slots_left_for_rest * 4)
        max_possible = min(4, rem_slots - slots_left_for_rest * 1)
        if min_possible > max_possible:
            min_possible = max_possible
        cnt = rng.randint(min_possible, max_possible)
        slots_per_need.append(cnt)
        rem_slots -= cnt

    rng.shuffle(slots_per_need)

    for i in range(num_needs):
        category = rng.choice(SKILLS)
        x, y = sample_clustered_point(rng, sigma=4.0)

        # 3-8 hour need window
        duration = rng.uniform(3.0, 8.0)
        start_time = rng.uniform(7.0, 15.0)
        end_time = min(24.0, start_time + duration)

        urgency = rng.choices([1, 2, 3, 4], weights=[0.15, 0.35, 0.35, 0.15])[0]
        req_lang = rng.choices(["hi", "pa", "en", "bn", "ta"], weights=[0.4, 0.25, 0.15, 0.1, 0.1])[0]

        head_count = slots_per_need[i]

        title = f"{category.capitalize()} Relief Operation #{i+1} in Zone {rng.randint(1,3)}"

        needs.append(Need(
            id=f"need-{i+1:03d}",
            title=title,
            category=category,
            latitude=round(x, 4),
            longitude=round(y, 4),
            required_language=req_lang,
            start_time=round(start_time, 2),
            end_time=round(end_time, 2),
            required_head_count=head_count,
            urgency=urgency,
            status="open",
            filled_slots=0,
            hlc_timestamp=1700000000000 + i,
            node_id="camp-node-01"
        ))
    return needs

def generate_scenario(scenario_name: str, seed: int = 42) -> Tuple[List[Volunteer], List[Need]]:
    rng = random.Random(seed)
    if scenario_name == "S1":
        # S1 (small): 60 volunteers, 25 needs, ~61 slots (supply is tight)
        vols = generate_volunteers(60, rng)
        needs = generate_needs(25, 61, rng)
    elif scenario_name == "S2":
        # S2 (medium): 200 volunteers, 80 needs, ~200 slots
        vols = generate_volunteers(200, rng)
        needs = generate_needs(80, 200, rng)
    elif scenario_name == "S3":
        # S3 (large): 600 volunteers, 250 needs, ~619 slots
        vols = generate_volunteers(600, rng)
        needs = generate_needs(250, 619, rng)
    else:
        vols = generate_volunteers(60, rng)
        needs = generate_needs(25, 61, rng)
    return vols, needs
