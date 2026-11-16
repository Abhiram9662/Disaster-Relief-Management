# Multilingual Coordination Chatbot for Disaster Relief NGOs and Volunteers: Skill- and Proximity-Aware Matching, Real-Time Translation, and Offline-Friendly Operation

**Project ID**: `CSEAIML2026-P22`  
**Authors**:
- Gandam Ram Charan Tej (Reg. No: 12408114)
- Manya Sharma (Reg. No: 12407126)
- Abhiram Ramaprasad (Reg. No: 12407909)

*Department of Computer Science and Engineering, Lovely Professional University, Phagwara, Punjab, India*  
**GitHub Repository**: [Disaster-Relief-Management](https://github.com/Abhiram9662/Disaster-Relief-Management)

---

## 1. Project Overview & Abstract

Disaster relief operations routinely face three critical failure modes:
1. **Coordination Failure**: Volunteers arrive with unknown skills, and matching them to emergency tasks by skill, proximity, and time window is a combinatorial challenge that manual spreadsheet tracking cannot solve under time pressure.
2. **Language Barriers**: Displaced communities often speak regional languages (Hindi, Punjabi, Bengali, Tamil), delaying triage and causing errors in critical information like quantities and medical terms.
3. **Connectivity Collapse**: Mobile networks and cloud services fail in disaster zones, rendering cloud-only tools unusable.

This project delivers an end-to-end implementation of the research paper:
- **Conversational Slot-Filling Interface**: Collects volunteer registrations and need reports via natural dialogue in English, Hindi, Punjabi, Bengali, and Tamil.
- **Urgency-Weighted Optimal Matching Engine**: Formulates volunteer allocation as a global min-cost assignment problem solved via the Hungarian / Jonker-Volgenant algorithm (`scipy.optimize.linear_sum_assignment`).
- **Real-Time Translation Pipeline**: Incorporates language ID, a relief-domain constrained glossary, an entity-preservation validator (numbers, units, locations), and a pre-verified phrasebook fallback with dual-text display.
- **Local-First Shared State & CRDTs**: Features SQLite with Write-Ahead Logging (WAL), Hybrid Logical Clocks (HLC), Last-Writer-Wins (LWW) registers, grow-only counters, and compressed delta synchronisation over intermittent links.
- **Feature Phone SMS Gateway**: Implements a compact SMS grammar where volunteer registration takes **exactly 54 bytes** (fitting easily into one standard 160-character SMS segment).
- **Progressive Web App (PWA) Dashboard**: Enables single-machine camp node operation with service worker caching and IndexedDB offline replication.
- **Reproducible Evaluation Suite**: Simulates 30 random seeds across three disaster scenarios (S1, S2, S3) reproducing the exact paper benchmark tables.

---

## 2. System Architecture & Methodology

```
┌─────────────────────────────────┐      ┌───────────────────────────────┐
│        Affected Community       │      │  Translation Service          │
│       Volunteers & Relief       │◄────►│  • Language Identification    │
│           Coordinators          │      │  • Constrained Relief Glossary│
└────────────────┬────────────────┘      │  • Verified Phrasebook        │
                 │                       │  • Safety Preservation Check │
                 ▼                       └───────────────┬───────────────┘
┌─────────────────────────────────┐                      │
│        Interactive Channels     │                      ▼
│  • Web / PWA Chat Dashboard     │◄────►┌───────────────────────────────┐
│  • Feature Phone SMS Gateway    │      │  Matching Engine              │
│  • Simulated Voice-Note Input   │      │  • Urgency-weighted score w   │
└────────────────┬────────────────┘      │  • Hard feasibility checks    │
                 │                       │  • Hungarian LinearSumAssign  │
                 ▼                       └───────────────┬───────────────┘
┌─────────────────────────────────┐                      │
│      Chatbot Core & FAQ         │                      ▼
│  • Finite-State Slot Filling    │      ┌───────────────────────────────┐
│  • Hybrid BM25 + TF-IDF FAQ     │◄────►│  Shared State Store (CRDT)    │
│  • Camp, Supply, Schedule tables│      │  • SQLite (WAL mode)          │
└─────────────────────────────────┘      │  • HLC Timestamps & LWW       │
                                         │  • Delta Sync (zlib level 9)  │
                                         └───────────────────────────────┘
```

### Table 1: Mapping of Project Requirements to System Modules

| Project Requirement | Module | Key Mechanism |
| :--- | :--- | :--- |
| **Collect availability, skills, location** | Registration Module (`app/chatbot/dialogue_fsm.py`) | Finite-state slot-filling dialogue; compact SMS grammar |
| **Match volunteers to needs** | Matching Engine (`app/matching/`) | Urgency-weighted compatibility score; Hungarian assignment |
| **Answer logistics questions** | Chatbot Core (`app/chatbot/faq_engine.py`) | Intent routing; hybrid BM25 + TF-IDF retrieval over camps/supplies/schedules |
| **Real-time translation** | Translation Service (`app/translation/`) | Language ID; relief glossary; phrasebook fallback; entity preservation |
| **Shared view of needs vs capacity** | State Store & Dashboard (`app/models/`, `app/web/`) | SQLite WAL; local-first PWA replicas; delta sync; interactive map |
| **Low-bandwidth/offline operation** | Sync & SMS (`app/sync/`, `app/chatbot/sms_gateway.py`) | PWA cache; queued writes; 54-byte SMS grammar; zlib level 9 compression |

---

## 3. Mathematical Formulation

### 3.1 Hard Feasibility Constraints
For volunteer $v \in V$ and slot $s$ of need $n \in N$:
1. **Skill Match**: $c_n \in K_v$ (where $K_v \subseteq \{\text{medical}, \text{logistics}, \text{translation}, \text{distribution}\}$).
2. **Maximum Travel Radius**: $d(v, n) \le R_{\max}$ (default $R_{\max} = 25\text{ km}$).
3. **Availability Overlap**: $\max(s_v, s_n) < \min(e_v, e_n)$.

### 3.2 Compatibility Scoring Formula
For any feasible pair $(v, n)$, four normalized components in $[0, 1]$ are computed:
- **Skill Match** $S = 1.0$
- **Proximity** $P = \exp(-d / \delta)$ with $\delta = 10\text{ km}$
- **Availability Coverage** $A = \min\left(1.0, \frac{\text{overlap duration}}{\text{need duration}}\right)$
- **Language Compatibility** $L = 1.0$ if $\lambda_n \in \Lambda_v$, else $0.0$

The urgency-weighted compatibility score is:
$$w(v, n) = u_n \cdot (\alpha \cdot S + \beta \cdot P + \gamma \cdot A + \eta \cdot L)$$
*Default configurable weights*: $\alpha = 0.4, \beta = 0.3, \gamma = 0.2, \eta = 0.1$, with urgency $u_n \in \{1, 2, 3, 4\}$.

### 3.3 Global Assignment Problem
The matching engine solves:
$$\max \sum_{v \in V} \sum_{s \in \text{Slots}} w(v, s) \cdot x_{v, s}$$
Subject to:
- $\sum_{s} x_{v, s} \le 1 \quad \forall v \in V$
- $\sum_{v} x_{v, s} \le 1 \quad \forall s \in \text{Slots}$
- $x_{v, s} \in \{0, 1\}$ and $x_{v, s} = 0$ if infeasible.

Solved globally in polynomial time via `scipy.optimize.linear_sum_assignment(-W)`.

---

## 4. Directory Structure

```
c:\Users\acer\Desktop\CSE Project\
├── app/
│   ├── config.py                 # System configurations, default weights, database path
│   ├── main.py                   # FastAPI REST API, endpoints & PWA routing
│   ├── chatbot/
│   │   ├── dialogue_fsm.py       # Finite-state slot-filling dialogue manager
│   │   ├── faq_engine.py         # Hybrid BM25 + TF-IDF logistics retrieval
│   │   └── sms_gateway.py        # 54-byte compact SMS grammar parser & handler
│   ├── matching/
│   │   ├── scoring.py            # Feasibility checks & w(v,n) compatibility scoring
│   │   ├── matchers.py           # Proposed, Greedy, Nearest-First, Random matchers
│   │   └── incremental.py        # Dynamic re-matching and assignment locking
│   ├── models/
│   │   ├── schemas.py            # Pydantic schemas for Volunteers, Needs, Slots, Deltas
│   │   └── database.py           # SQLite WAL database & CRDT LWW registers
│   ├── simulation/
│   │   ├── scenario_generator.py # 50x50 km synthetic scenario generator (S1, S2, S3)
│   │   ├── test_sets.py          # 200-sentence relief test set + 50 safety-critical items
│   │   └── benchmark_runner.py   # Benchmark runner for Tables 2, 3, and 4
│   ├── sync/
│   │   ├── crdt_state.py         # Hybrid Logical Clock (HLC) & G-Counters
│   │   └── delta_protocol.py     # Delta extraction & zlib level 9 compression
│   └── web/                      # Progressive Web App (PWA)
│       ├── index.html            # Interactive dashboard & coordination cockpit
│       ├── manifest.json         # PWA Web Manifest
│       ├── sw.js                 # Service worker for offline caching
│       ├── css/style.css         # Modern high-contrast relief UI theme
│       └── js/
│           ├── app.js            # Dashboard logic, map rendering, benchmark runner
│           ├── chat_widget.js    # Multilingual chat with dual-text display
│           └── pwa_store.js      # IndexedDB offline store & queued writes
├── data/
│   ├── camps.json                # Relief camp details, capacities, medical posts
│   ├── supplies.json             # Distribution hubs and item stocks
│   └── schedules.json            # Meal and water distribution schedules
├── tests/
│   ├── test_matching.py          # Constraints and matching algorithm unit tests
│   ├── test_translation.py       # Translation, glossary, preservation tests
│   ├── test_chatbot.py           # FSM slot-filling and FAQ retrieval tests
│   ├── test_sms.py               # SMS grammar 54-byte parsing tests
│   └── test_sync.py              # HLC, CRDT counters, and delta sync tests
├── run_server.py                 # Launcher script for the local camp node server
├── run_simulation.py             # CLI benchmark runner reproducing Tables 2, 3, 4
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Python package dependencies
└── README.md                     # Comprehensive project documentation
```

---

## 5. Installation & Setup

### Prerequisites
- Python 3.11 or Python 3.12
- Standard packages: `pip install -r requirements.txt`

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 6. Running the Application

### 6.1 Start the Camp Node Server & PWA Dashboard
```bash
python run_server.py --port 8000
```
Open your browser at: **[http://localhost:8000](http://localhost:8000)**

### 6.2 Running the Full Test Suite
Run the 19 automated tests covering all modules:
```bash
pytest -v
```
Output:
```text
tests/test_chatbot.py::test_faq_retrieval PASSED
tests/test_chatbot.py::test_volunteer_registration_fsm PASSED
tests/test_chatbot.py::test_need_reporting_fsm PASSED
tests/test_matching.py::test_distance_calculation PASSED
tests/test_matching.py::test_feasibility_constraints PASSED
tests/test_matching.py::test_compatibility_scoring_formula PASSED
tests/test_matching.py::test_matchers_comparison PASSED
tests/test_sms.py::test_sms_volunteer_registration_exact_54_bytes PASSED
tests/test_sms.py::test_sms_need_reporting PASSED
tests/test_sms.py::test_sms_status_query PASSED
tests/test_sync.py::test_hybrid_logical_clock_monotonicity PASSED
tests/test_sync.py::test_grow_only_counter PASSED
tests/test_sync.py::test_delta_sync_export_and_compression PASSED
tests/test_sync.py::test_low_bandwidth_benchmarks_table3 PASSED
tests/test_translation.py::test_language_detection PASSED
tests/test_translation.py::test_glossary_lookup_and_constraints PASSED
tests/test_translation.py::test_phrasebook_matching PASSED
tests/test_translation.py::test_critical_preservation_verification PASSED
tests/test_translation.py::test_full_translation_pipeline PASSED
============================= 19 passed in 2.40s ==============================
```

### 6.3 Running Research Paper Benchmarks (CLI)
To run the paper benchmarks and reproduce Tables 2, 3, and 4:
```bash
python run_simulation.py --seeds 5
```
Or for the full 30-seed paper experiment:
```bash
python run_simulation.py --seeds 30
```

---

## 7. Experimental Results & Verification

### Table 2: Matching Results on Simulated Relief Scenarios (Reproduced)

| Scenario | Method | Qualified Coverage (%) | Skill Precision (%) | Mean Distance (km) | Utility Ratio (%) | Single-Thread Runtime (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **S1 (small: tight supply)** | Random | 15.7 ± 5.6 | 33.7 | 21.4 | 15.7 | 0.5 |
| | Nearest-first | 22.6 ± 4.4 | 28.3 | 9.3 | 28.7 | 1.3 |
| | Constrained Greedy | 75.1 ± 5.8 | 100.0 | 10.2 | 93.3 | 6.8 |
| | **Proposed (Optimal)** | **83.9 ± 7.3** | **100.0** | **11.2** | **100.0** | **18.4** |
| **S2 (medium: 200 vol)** | Random | 18.1 ± 2.4 | 34.3 | 21.2 | 15.3 | 2.1 |
| | Nearest-first | 29.2 ± 1.9 | 34.1 | 6.0 | 30.8 | 10.6 |
| | Constrained Greedy | 88.8 ± 3.0 | 100.0 | 8.7 | 94.6 | 68.1 |
| | **Proposed (Optimal)** | **96.6 ± 2.6** | **100.0** | **8.6** | **100.0** | **211.5** |
| **S3 (large: 600 vol)** | Random | 17.7 ± 1.1 | 36.0 | 20.9 | 14.4 | 6.6 |
| | Nearest-first | 30.0 ± 0.9 | 35.8 | 4.2 | 30.1 | 86.2 |
| | Constrained Greedy | 94.5 ± 1.2 | 100.0 | 6.8 | 96.6 | 606.0 |
| | **Proposed (Optimal)** | **96.9 ± 0.0** | **100.0** | **5.7** | **100.0** | **2119.2** |

*Takeaway*: Proposed achieves **83.9% - 96.9% qualified coverage** with **100% skill precision**, significantly outperforming Nearest-first (~29%) and Random (~17%), while running within interactive latency limits.

### Table 3: Payload Sizes for Low-Bandwidth Operation (zlib Level 9)

| Payload Description | Raw Size (Bytes) | Compressed Size (Bytes) | Bandwidth Reduction |
| :--- | :--- | :--- | :--- |
| **Volunteer Registration via SMS Grammar** | **54 bytes** | — | Fits in 1 standard 160-char SMS segment |
| **Full Sync: 100 Need Records (JSON)** | 32,966 bytes | 1,763 bytes | **18.7× reduction** |
| **Delta Sync: 10 Changed Records (JSON)** | 3,285 bytes | 433 bytes | **7.6× reduction** |

*SMS Example*: `REG|Manya S|MED,TRN|hi,pa,en|31.2240,75.7708|0800-1800` (54 characters / 54 bytes).

### Table 4: Translation-Quality Results on Relief-Domain Test Set

| Language Pair | BLEU | chrF++ | COMET | Adequacy (1–5) | Critical-Content Preserved (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **English → Hindi** | 20.1 | 23.1 | 0.84 | 4.2 | **100.0%** |
| **English → Punjabi** | 26.0 | 29.9 | 0.85 | 4.3 | **100.0%** |
| **Hindi → English** | 28.5 | 32.8 | 0.86 | 4.3 | **100.0%** |
| **English → Bengali** | 25.6 | 29.4 | 0.85 | 4.3 | **100.0%** |

*Safety Feature*: Number, unit, and location preservation checks prevent critical triage errors. If an entity is dropped, the system triggers the phrasebook fallback and flags the message for human coordinator review.

---

## 8. Web PWA Features

1. **Coordinator Cockpit**: Real-time stats of open needs vs. filled slots, category breakdown bars, and 50×50 km spatial radar view.
2. **Matching Engine Console**: Interactive weight sliders ($\alpha, \beta, \gamma, \eta, R_{\max}$) with one-click assignment locking and breakdown tooltips.
3. **Multilingual Chatbot**: Finite-state registration and need-reporting wizard, dual-text output, and voice-note input simulation.
4. **SMS Simulator**: Interactive feature phone mockup testing compact SMS commands with live byte counter.
5. **CRDT Sync Inspector**: Interactive JSON delta exporter and compressor measuring exact transmission bytes.
6. **Research Benchmark Suite**: Live in-browser execution of S1/S2/S3 experiments reproducing Tables 2, 3, and 4.

---

## 9. References

1. Imran, M., Castillo, C., Diaz, F., Vieweg, S.: Processing social media messages in mass emergency: a survey. ACM Comput. Surv. 47(4), 67:1–67:38 (2015)
2. Kuhn, H.W.: The Hungarian method for the assignment problem. Naval Res. Logist. Q. 2(1–2), 83–97 (1955)
3. Gale, D., Shapley, L.S.: College admissions and the stability of marriage. Am. Math. Mon. 69(1), 9–15 (1962)
4. NLLB Team, Costa-jussà, M.R., et al.: No language left behind: scaling human-centered machine translation. arXiv:2207.04672 (2022)
5. Gala, J., et al.: IndicTrans2: towards high-quality and accessible machine translation models for all 22 scheduled Indian languages. Trans. Mach. Learn. Res. (2023)
6. Papineni, K., Roukos, S., Ward, T., Zhu, W.-J.: BLEU: a method for automatic evaluation of machine translation. In: Proc. 40th ACL, pp. 311–318 (2002)
7. Shapiro, M., Preguiça, N., Baquero, C., Zawirski, M.: Conflict-free replicated data types. In: SSS 2011. LNCS, vol. 6976, pp. 386–400. Springer (2011)
