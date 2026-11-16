"""
FAQ Retrieval Engine (Section 4.3):
Hybrid semantic search with BM25 keyword matching and TF-IDF vector similarity
over structured camp, supply-point, and schedule tables.
"""

import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import DATA_DIR
from app.translation.engine import detect_language, translator

class FAQEngine:
    def __init__(self):
        self.camps: List[Dict[str, Any]] = []
        self.supplies: List[Dict[str, Any]] = []
        self.schedules: List[Dict[str, Any]] = []
        self.documents: List[Dict[str, Any]] = []
        self.corpus_texts: List[str] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.load_data()

    def load_data(self):
        camps_path = DATA_DIR / "camps.json"
        supplies_path = DATA_DIR / "supplies.json"
        schedules_path = DATA_DIR / "schedules.json"

        if camps_path.exists():
            with open(camps_path, "r", encoding="utf-8") as f:
                self.camps = json.load(f)
        if supplies_path.exists():
            with open(supplies_path, "r", encoding="utf-8") as f:
                self.supplies = json.load(f)
        if schedules_path.exists():
            with open(schedules_path, "r", encoding="utf-8") as f:
                self.schedules = json.load(f)

        self.documents = []
        self.corpus_texts = []

        # Index camps
        for c in self.camps:
            text = f"Camp: {c['name']} ({c['camp_id']}) at {c['location']}. Capacity: {c['capacity']}, Occupancy: {c['current_occupancy']}. Medical: {c['medical_post']}. Water: {c['water_status']}. Contact: {c['contact']}. Notes: {c['notes']}"
            self.documents.append({"type": "camp", "data": c, "text": text})
            self.corpus_texts.append(text)

        # Index supplies
        for s in self.supplies:
            items_str = ", ".join([f"{it['item']} (Stock: {it['stock']}, {it['status']})" for it in s["items"]])
            text = f"Supply Depot: {s['name']} ({s['point_id']}). Available supplies: {items_str}. Hours: {s['distribution_hours']}. Coordinator: {s['coordinator']}. Access: {s['vehicle_access']}"
            self.documents.append({"type": "supply", "data": s, "text": text})
            self.corpus_texts.append(text)

        # Index schedules
        for sch in self.schedules:
            text = f"Schedule: {sch['event']} at {sch['location']} from {sch['start_time']} to {sch['end_time']}. Target: {sch['target_group']}. Team: {sch['assigned_team']}"
            self.documents.append({"type": "schedule", "data": sch, "text": text})
            self.corpus_texts.append(text)

        if self.corpus_texts:
            self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_texts)

    def _bm25_score(self, query: str, doc_text: str) -> float:
        """Lightweight BM25 term frequency-inverse document frequency calculation."""
        words_query = set(re.findall(r'\w+', query.lower()))
        words_doc = re.findall(r'\w+', doc_text.lower())
        doc_len = len(words_doc)
        if doc_len == 0:
            return 0.0

        score = 0.0
        k1 = 1.5
        b = 0.75
        avg_len = sum(len(re.findall(r'\w+', t.lower())) for t in self.corpus_texts) / max(1, len(self.corpus_texts))

        for word in words_query:
            count = words_doc.count(word)
            if count > 0:
                tf = (count * (k1 + 1)) / (count + k1 * (1 - b + b * (doc_len / avg_len)))
                # Approximate IDF
                docs_with_word = sum(1 for t in self.corpus_texts if word in t.lower())
                idf = math.log((len(self.corpus_texts) - docs_with_word + 0.5) / (docs_with_word + 0.5) + 1.0)
                score += tf * max(0.1, idf)
        return score

    def query(self, user_query: str, target_lang: str = "en") -> Dict[str, Any]:
        """
        Retrieves matching logistics information using hybrid TF-IDF + BM25 scoring.
        """
        # If query is in non-English language, translate to English for retrieval
        detected_lang = detect_language(user_query)
        en_query = user_query
        if detected_lang != "en":
            tr = translator.translate(user_query, source_lang=detected_lang, target_lang="en")
            en_query = tr["translated_text"]

        if not self.documents or not self.vectorizer:
            return {
                "matched": False,
                "answer": "No logistics records currently available.",
                "type": "none",
                "score": 0.0
            }

        # Vector cosine similarity
        query_vec = self.vectorizer.transform([en_query])
        cos_sims = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        best_idx = -1
        best_combined = -1.0

        for i, doc in enumerate(self.documents):
            sim = float(cos_sims[i])
            bm25 = self._bm25_score(en_query, doc["text"])
            # Combined score: 60% cosine similarity + 40% normalized BM25
            combined = 0.6 * sim + 0.4 * min(1.0, bm25 / 5.0)

            # Intent type boost
            doc_type = doc["type"]
            q_lower = en_query.lower()
            if doc_type == "camp" and ("camp " in q_lower or "where is" in q_lower):
                combined += 0.25
            elif doc_type == "supply" and ("supply" in q_lower or "supplies" in q_lower or "depot" in q_lower or "stock" in q_lower):
                combined += 0.25
            elif doc_type == "schedule" and ("schedule" in q_lower or "timing" in q_lower or "when is" in q_lower or "event" in q_lower):
                combined += 0.25

            if combined > best_combined:
                best_combined = combined
                best_idx = i

        if best_idx >= 0 and best_combined > 0.15:
            matched_doc = self.documents[best_idx]
            ans_text = matched_doc["text"]

            # Translate answer back to user language if needed
            translated_answer = ans_text
            if target_lang != "en":
                tr_back = translator.translate(ans_text, source_lang="en", target_lang=target_lang)
                translated_answer = tr_back["translated_text"]

            return {
                "matched": True,
                "answer": ans_text,
                "translated_answer": translated_answer,
                "type": matched_doc["type"],
                "data": matched_doc["data"],
                "score": round(best_combined, 4)
            }

        return {
            "matched": False,
            "answer": "I could not find logistics records matching your question. Please specify camp name, supplies, or schedule.",
            "translated_answer": "मुझे आपके प्रश्न से मेल खाने वाले रसद रिकॉर्ड नहीं मिले। कृपया शिविर का नाम, आपूर्ति या समय निर्दिष्ट करें।",
            "type": "none",
            "score": round(best_combined, 4)
        }

faq_engine = FAQEngine()
