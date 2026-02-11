"""Agentic diary generation system -- single-call optimized with date mapping."""
import json
from typing import List, Dict, Any, Optional, Union
from datetime import date
from pydantic import BaseModel, Field

from .llm_client import get_llm_client
from .vtu_skills import get_skills_list, format_skills_for_prompt
from src.date_management import DateManager
from config import (
    BATCH_SIZE_DAYS,
    DEFAULT_HOURS_PER_DAY,
    MIN_ENTRY_WORDS,
    MAX_ENTRY_WORDS,
    CONFIDENCE_THRESHOLD,
    SYSTEM_PROMPTS_DIR
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DiaryEntry(BaseModel):
    """Single diary entry"""
    date: str = Field(description="Date in YYYY-MM-DD format")
    hours: float = Field(description="Hours worked (8-9)", ge=8.0, le=9.0)
    activities: str = Field(description="Detailed description (120-180 words)")
    learnings: str = Field(description="Learning summary")
    blockers: str = Field(description="Blockers or challenges", default="None")
    links: str = Field(description="Related links", default="")
    skills: List[str] = Field(description="VTU skill names", min_items=1, max_items=5)
    confidence: float = Field(description="Confidence score 0-1", ge=0.0, le=1.0)


class MultiDayOutput(BaseModel):
    """Output for multiple diary entries"""
    entries: List[DiaryEntry]
    warnings: List[str] = Field(default_factory=list)
    total_generated: int = 0


class DiaryGenerationAgent:
    """Single-call diary generation with date-mapped input."""

    def __init__(self, llm_client=None):
        self.llm = llm_client or get_llm_client()
        self.date_manager = DateManager()
        self.skills_list = get_skills_list()
        self.system_prompt = self._load_prompt("god_mode_system.txt") or self._load_prompt("multi_day_system.txt")
        logger.info("Diary Generation Agent initialized")

    def _load_prompt(self, filename: str) -> str:
        prompt_path = SYSTEM_PROMPTS_DIR / filename
        if prompt_path.exists():
            return prompt_path.read_text()
        return ""

    def generate_single(self, raw_text: str, target_date: Optional[date] = None, hours: Optional[float] = None) -> DiaryEntry:
        if target_date is None:
            target_date = date.today()

        skills_formatted = format_skills_for_prompt()
        prompt = f"""Generate 1 entry for {target_date.isoformat()}.
Input: {raw_text}
Hours: {hours or DEFAULT_HOURS_PER_DAY}
Skills: {skills_formatted}
Return JSON {{"entries":[{{...}}]}}"""

        response = self.llm.generate(prompt=prompt, system=self.system_prompt, json_mode=True)
        if isinstance(response, dict) and "entries" in response:
            entry_data = response["entries"][0]
        elif isinstance(response, list) and len(response) > 0:
            entry_data = response[0]
        else:
            entry_data = response
        return DiaryEntry(**entry_data)

    def generate_bulk(
        self,
        input_data: Union[str, List[Dict[str, Any]]],
        target_dates: List[date],
        distribute_content: bool = True
    ) -> MultiDayOutput:
        """Generate entries -- maps input rows to dates when possible."""
        logger.info(f"Generating bulk entries for {len(target_dates)} dates")

        # Build date-mapped prompt
        prompt_input = self._build_date_mapped_input(input_data, target_dates)
        logger.info(f"Built prompt input: {len(prompt_input)} chars")

        return self._generate_all(prompt_input, target_dates)

    def _build_date_mapped_input(
        self,
        input_data: Union[str, List[Dict[str, Any]]],
        target_dates: List[date],
    ) -> str:
        """Build input that maps each row to its date.

        If input rows have dates in metadata, associate them:
            2026-01-05: Onboarding and system setup
            2026-01-06: Evaluate private cloud features...
            2026-01-14: (no specific input -- infer from context)

        This prevents the LLM from mixing Jan 30 tasks into Jan 14.
        """
        if isinstance(input_data, str):
            return input_data

        if not isinstance(input_data, list):
            return str(input_data)

        # Try to map rows to dates using metadata.date
        date_to_tasks: Dict[str, List[str]] = {}
        unmapped_tasks: List[str] = []

        for row in input_data:
            raw = row.get("raw_text", "").strip()
            if not raw or raw.lower() in ("nan", "none", "null"):
                continue

            meta_date = row.get("metadata", {}).get("date")
            if meta_date:
                date_to_tasks.setdefault(str(meta_date), []).append(raw)
            else:
                unmapped_tasks.append(raw)

        # If no rows had dates, just join raw text
        if not date_to_tasks:
            logger.info("No date-mapped rows, joining raw text")
            return "\n".join(r.get("raw_text", "") for r in input_data if r.get("raw_text", "").strip())

        # Build structured input: one line per date with its tasks
        lines = []
        target_strs = {d.isoformat() for d in target_dates}

        for d in sorted(date_to_tasks.keys()):
            tasks = "; ".join(date_to_tasks[d])
            lines.append(f"{d}: {tasks}")

        # For target dates without input, mark them explicitly
        mapped_dates = set(date_to_tasks.keys())
        for td in target_dates:
            td_str = td.isoformat()
            if td_str not in mapped_dates:
                lines.append(f"{td_str}: (no specific input -- infer from project context)")

        # Add unmapped context at the end
        if unmapped_tasks:
            context = "\n".join(unmapped_tasks)
            lines.append(f"\nAdditional context: {context}")

        result = "\n".join(sorted(lines))
        logger.info(f"Date-mapped input: {len(date_to_tasks)} mapped, "
                     f"{len(target_dates) - len(date_to_tasks)} to infer")
        return result

    def _generate_all(self, prompt_input: str, target_dates: List[date]) -> MultiDayOutput:
        """ALL entries in ONE call with date-specific input."""
        date_strs = [d.isoformat() for d in target_dates]
        n = len(date_strs)
        skills_formatted = format_skills_for_prompt()

        prompt = f"""Generate {n} diary entries for these dates: {', '.join(date_strs)}

IMPORTANT: Each date has its OWN specific input below. Use ONLY that date's input for its entry.
Do NOT mix activities from different dates.

DATE-MAPPED INPUT:
{prompt_input}

SKILLS (pick 1-3 per entry): {skills_formatted}

Return {{"entries":[...]}} with exactly {n} entries. Each entry MUST only describe work from its own date."""

        logger.info(f"Single-call: {n} dates, ~{len(prompt)} prompt chars")

        try:
            response = self.llm.generate(
                prompt=prompt,
                system=self.system_prompt,
                json_mode=True,
                max_tokens=min(8192, n * 350 + 500),
            )

            if isinstance(response, dict) and "entries" in response:
                entries_data = response["entries"]
            elif isinstance(response, list):
                entries_data = response
            else:
                raise ValueError(f"Unexpected format: {type(response)}")

            entries = []
            for entry_data in entries_data:
                try:
                    if "hours" in entry_data:
                        entry_data["hours"] = max(8.0, min(9.0, float(entry_data["hours"])))
                    if "confidence" in entry_data:
                        entry_data["confidence"] = max(0.0, min(1.0, float(entry_data["confidence"])))
                    entries.append(DiaryEntry(**entry_data))
                except Exception as e:
                    logger.warning(f"Failed to parse entry: {e}")

            logger.info(f"Single call produced {len(entries)}/{n} entries")

            warnings = []
            if len(entries) < n:
                warnings.append(f"LLM produced {len(entries)}/{n} entries.")

            return MultiDayOutput(entries=entries, warnings=warnings, total_generated=len(entries))

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return MultiDayOutput(entries=[], warnings=[str(e)], total_generated=0)

    def filter_by_confidence(self, output: MultiDayOutput, threshold: float = CONFIDENCE_THRESHOLD) -> Dict[str, List[DiaryEntry]]:
        high = [e for e in output.entries if e.confidence >= threshold]
        low = [e for e in output.entries if e.confidence < threshold]
        logger.info(f"Confidence filter: {len(high)} high, {len(low)} need review")
        return {"auto_submit": high, "manual_review": low}
