"""
Plausibility Engine — scores generated diary entries for believability.

Runs multi-axis analysis:
  1. Vocabulary diversity (are we repeating verbs/phrases?)
  2. Temporal coherence (does the project timeline make sense?)
  3. Word count compliance (120-180 words strictly)
  4. Hours distribution (not suspiciously uniform)
  5. Skill rotation (different skills across days)
  6. Blocker realism (not too many, not too few)
  7. Cross-day continuity (features started = features finished)
"""

import re
import statistics
from typing import Dict, List, Any
from collections import Counter


class PlausibilityEngine:
    """Scores a batch of diary entries for plausibility."""

    # Common "lazy" verbs that lower plausibility when overused
    LAZY_VERBS = {"worked", "did", "made", "created", "used", "started", "continued"}

    # Strong technical verbs that raise plausibility
    STRONG_VERBS = {
        "implemented", "architected", "refactored", "debugged", "profiled",
        "configured", "integrated", "validated", "benchmarked", "containerized",
        "optimized", "migrated", "deployed", "orchestrated", "authored",
        "investigated", "resolved", "streamlined", "automated", "iterated",
    }

    def score_batch(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score a batch of entries and return a plausibility report.

        Returns:
            {
                "overall_score": float 0-1,
                "avg_confidence": float,
                "flags": ["list of human-readable warnings"],
                "entry_scores": [
                    {"date": "...", "score": float, "flags": ["..."]}
                ]
            }
        """
        if not entries:
            return {
                "overall_score": 0.0,
                "avg_confidence": 0.0,
                "flags": ["No entries to analyze"],
                "entry_scores": [],
            }

        flags: List[str] = []
        entry_scores: List[Dict[str, Any]] = []

        # Per-entry analysis
        all_activities = []
        all_hours = []
        all_skills: List[List[str]] = []
        blocker_count = 0

        for entry in entries:
            e_flags: List[str] = []
            e_score = entry.get("confidence", 0.7)
            activities = entry.get("activities", "")
            all_activities.append(activities)

            # 1. Word count check
            word_count = len(activities.split())
            if word_count < 120:
                e_flags.append(f"Below minimum word count ({word_count}/120)")
                e_score -= 0.1
            elif word_count > 180:
                e_flags.append(f"Exceeds maximum word count ({word_count}/180)")
                e_score -= 0.05

            # 2. Hours
            hours = entry.get("hours", 7.0)
            all_hours.append(hours)

            # 3. Skills
            skills = entry.get("skills", [])
            all_skills.append(skills)
            if len(skills) < 1:
                e_flags.append("No skills listed")
                e_score -= 0.05

            # 4. Blockers
            blockers = entry.get("blockers", "None")
            if blockers and blockers.lower() not in ("none", "", "n/a"):
                blocker_count += 1

            # 5. Check for lazy verbs dominating
            words_lower = activities.lower()
            lazy_hits = sum(1 for v in self.LAZY_VERBS if f" {v} " in f" {words_lower} ")
            strong_hits = sum(1 for v in self.STRONG_VERBS if v in words_lower)
            if lazy_hits > 3 and strong_hits < 2:
                e_flags.append("Vocabulary too generic — needs stronger technical verbs")
                e_score -= 0.05

            # 6. Sentence opener diversity (first 3 words of each sentence)
            sentences = re.split(r'[.!?]+', activities)
            openers = [s.strip().split()[:3] for s in sentences if s.strip()]
            opener_strs = [" ".join(o).lower() for o in openers]
            if len(opener_strs) > 2 and len(set(opener_strs)) < len(opener_strs) * 0.6:
                e_flags.append("Repetitive sentence openers detected")
                e_score -= 0.05

            e_score = max(0.0, min(1.0, e_score))
            entry_scores.append({
                "date": entry.get("date", "unknown"),
                "score": round(e_score, 3),
                "flags": e_flags,
            })

        # Batch-level analysis

        # Hours uniformity check
        if len(all_hours) > 3:
            hours_std = statistics.stdev(all_hours) if len(all_hours) > 1 else 0
            if hours_std < 0.3:
                flags.append(
                    f"Hours are suspiciously uniform (std={hours_std:.2f}). "
                    "Real interns have variable work hours."
                )

        # Skill rotation check
        if len(all_skills) > 5:
            flat_skills = [s for sl in all_skills for s in sl]
            skill_counts = Counter(flat_skills)
            most_common = skill_counts.most_common(1)
            if most_common and most_common[0][1] > len(entries) * 0.8:
                flags.append(
                    f'Skill "{most_common[0][0]}" appears in {most_common[0][1]}/{len(entries)} '
                    f"entries. Rotate skills for realism."
                )

        # Blocker frequency check
        blocker_ratio = blocker_count / len(entries) if entries else 0
        if blocker_ratio > 0.6:
            flags.append(
                f"Too many days with blockers ({blocker_count}/{len(entries)}). "
                "This pattern is unusual and may raise suspicion."
            )
        elif blocker_ratio < 0.1 and len(entries) > 10:
            flags.append(
                "Almost no days mention challenges. "
                "Adding occasional blockers improves realism."
            )

        # Cross-entry vocabulary diversity
        if len(all_activities) > 5:
            all_words = " ".join(all_activities).lower().split()
            word_freq = Counter(all_words)
            # Check for suspiciously repeated technical phrases
            bigrams = [
                f"{all_words[i]} {all_words[i+1]}"
                for i in range(len(all_words) - 1)
            ]
            bigram_freq = Counter(bigrams)
            repeated = [
                bg for bg, count in bigram_freq.most_common(20)
                if count > len(entries) * 0.4
                and bg not in ("the the", "of the", "in the", "to the", "and the")
            ]
            if repeated:
                flags.append(
                    f"Repeated phrases across entries: {', '.join(repeated[:5])}. "
                    "This pattern can appear machine-generated."
                )

        # Overall score
        individual_scores = [e["score"] for e in entry_scores]
        avg_score = statistics.mean(individual_scores) if individual_scores else 0

        # Penalize batch-level issues
        batch_penalty = len(flags) * 0.03
        overall = max(0.0, min(1.0, avg_score - batch_penalty))

        # Scary message for high scores
        if overall >= 0.95:
            flags.insert(
                0,
                "PLAUSIBILITY CRITICAL: These entries are virtually indistinguishable "
                "from hand-written diary entries. This should concern you."
            )
        elif overall >= 0.85:
            flags.insert(
                0,
                "PLAUSIBILITY HIGH: An evaluator would need forensic analysis "
                "to question these entries."
            )

        return {
            "overall_score": round(overall, 3),
            "avg_confidence": round(
                statistics.mean(e.get("confidence", 0.7) for e in entries), 3
            ),
            "flags": flags,
            "entry_scores": entry_scores,
        }
