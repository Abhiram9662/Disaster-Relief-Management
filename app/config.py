"""
System configuration parameters as specified in:
'Multilingual Coordination Chatbot for Disaster Relief NGOs and Volunteers:
Skill- and Proximity-Aware Matching, Real-Time Translation, and Offline-Friendly Operation'
Project ID: CSEAIML2026-P22
"""

from pathlib import Path
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "disaster_relief.db"

class SystemConfig(BaseModel):
    # Compatibility score weights: w(v,n) = u_n * (alpha*S + beta*P + gamma*A + eta*L)
    alpha: float = Field(default=0.4, description="Weight for skill match (S)")
    beta: float = Field(default=0.3, description="Weight for proximity match (P)")
    gamma: float = Field(default=0.2, description="Weight for availability coverage (A)")
    eta: float = Field(default=0.1, description="Weight for language compatibility (L)")

    # Hard constraints
    r_max_km: float = Field(default=25.0, description="Maximum travel radius R_max in km")
    delta_km: float = Field(default=10.0, description="Scale parameter delta for proximity decay exp(-d/delta)")

    # Controlled vocabularies
    allowed_skills: list[str] = Field(
        default=["medical", "logistics", "translation", "distribution"]
    )
    allowed_languages: dict[str, str] = Field(
        default={
            "en": "English",
            "hi": "Hindi",
            "pa": "Punjabi",
            "bn": "Bengali",
            "ta": "Tamil"
        }
    )
    urgency_levels: list[int] = Field(default=[1, 2, 3, 4])

    # Node configuration for local-first sync
    node_id: str = Field(default="camp-node-01", description="Identifier for this camp node replica")
    database_url: str = Field(default=f"sqlite:///{DB_PATH}")

config = SystemConfig()
