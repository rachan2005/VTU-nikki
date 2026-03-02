"""Excel/CSV processor for bulk diary entries"""
from typing import List, Dict, Any
from pathlib import Path
import pandas as pd
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExcelProcessor:
    """Processes Excel/CSV files with diary data"""

    # Column name variations to detect
    DATE_COLUMNS = ["date", "day", "when", "fecha", "datum"]
    HOURS_COLUMNS = ["hours", "duration", "time", "horas", "heures", "task duration"]
    ACTIVITY_COLUMNS = ["activity", "activities", "work", "task", "tasks", "keywords", "description", "notes"]
    SKILLS_COLUMNS = ["skills", "skill", "competencias", "compétences"]

    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """Process Excel/CSV file into list of diary entries"""
        file_path = Path(file_path)
        logger.info(f"Processing Excel/CSV: {file_path.name}")

        # Read file (try multiple encodings for CSV)
        if file_path.suffix.lower() == ".csv":
            for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1", "iso-8859-1"):
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"CSV decoded with encoding: {encoding}")
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            else:
                df = pd.read_csv(file_path, encoding="utf-8", encoding_errors="replace")
                logger.warning("CSV decoded with replacement characters")
        else:
            df = pd.read_excel(file_path)

        # Auto-detect header row: if columns have "Unnamed" in them,
        # scan first 10 rows for the real header
        df = self._fix_header(df)

        logger.info(f"Loaded {len(df)} rows, columns: {df.columns.tolist()}")

        # Auto-detect columns
        date_col = self._detect_column(df, self.DATE_COLUMNS)
        hours_col = self._detect_column(df, self.HOURS_COLUMNS)
        activity_col = self._detect_column(df, self.ACTIVITY_COLUMNS)
        skills_col = self._detect_column(df, self.SKILLS_COLUMNS)

        if not activity_col:
            # No recognized activity column — dump entire spreadsheet as raw text
            # so the LLM can figure it out
            logger.warning(
                f"No activity column detected in {df.columns.tolist()}. "
                "Falling back to full-row dump mode."
            )
            return self._dump_all_rows(df, date_col, hours_col, skills_col)

        logger.info(f"Detected columns - Date: {date_col}, Hours: {hours_col}, Activity: {activity_col}")

        # Process each row
        entries = []
        for idx, row in df.iterrows():
            try:
                entry = self._process_row(
                    row,
                    date_col=date_col,
                    hours_col=hours_col,
                    activity_col=activity_col,
                    skills_col=skills_col,
                    row_number=idx + 1
                )

                if entry:  # Skip empty rows
                    entries.append(entry)

            except Exception as e:
                logger.warning(f"Skipping row {idx + 1}: {e}")
                continue

        logger.info(f"Processed {len(entries)} valid entries from Excel")
        return entries

    def _fix_header(self, df: pd.DataFrame) -> pd.DataFrame:
        """Auto-detect the real header row in any CSV/Excel.

        Works for ANY file — no hardcoded column names.
        Heuristic: the header row is the first row with the most
        non-null, short, non-numeric, unique string cells.
        """
        unnamed_count = sum(1 for c in df.columns if "unnamed" in str(c).lower())
        if unnamed_count < len(df.columns) // 2:
            return df  # Current header looks fine already

        best_row = -1
        best_score = 0
        scan = min(10, len(df))

        for i in range(scan):
            row = df.iloc[i]
            non_null = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
            if len(non_null) < 2:
                continue

            # Header cells are typically: short, non-numeric, unique strings
            score = 0
            for val in non_null:
                is_short = len(val) < 40
                is_not_number = not val.replace('.', '').replace('-', '').isdigit()
                is_not_weekday = val.lower() not in ("sat", "sun", "mon", "tue", "wed", "thu", "fri")
                if is_short and is_not_number and is_not_weekday:
                    score += 1

            # Bonus: more filled cells = more likely a header
            fill_ratio = len(non_null) / len(row)
            score *= (1 + fill_ratio)

            if score > best_score:
                best_score = score
                best_row = i

        if best_row >= 0 and best_score >= 3:
            new_header = [str(v).strip() if pd.notna(v) else f"col_{j}" for j, v in enumerate(df.iloc[best_row])]
            df = df.iloc[best_row + 1:].reset_index(drop=True)
            df.columns = new_header
            logger.info(f"Auto-detected header at row {best_row + 1}: {new_header}")
            return df

        return df

    def _detect_column(self, df: pd.DataFrame, keywords: List[str]) -> str:
        """Detect column by matching keywords"""
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if any(kw in col_lower for kw in keywords):
                return col
        return None

    def _process_row(
        self,
        row: pd.Series,
        date_col: str,
        hours_col: str,
        activity_col: str,
        skills_col: str,
        row_number: int
    ) -> Dict[str, Any]:
        """Process single row into entry data"""

        # Extract activity text
        activity_text = str(row[activity_col]).strip() if activity_col else ""

        # Skip empty rows
        if not activity_text or activity_text.lower() in ["nan", "none", ""]:
            return None

        # Extract date
        date_value = None
        if date_col and pd.notna(row[date_col]):
            try:
                # Try parsing as date
                date_value = pd.to_datetime(row[date_col]).date().isoformat()
            except:
                # If it's a string, keep as is for later inference
                date_value = str(row[date_col]).strip()

        # Extract hours
        hours_value = None
        if hours_col and pd.notna(row[hours_col]):
            try:
                hours_value = float(row[hours_col])
            except:
                pass

        # Extract skills if present
        skills_value = None
        if skills_col and pd.notna(row[skills_col]):
            skills_str = str(row[skills_col]).strip()
            # Split by comma or semicolon
            skills_value = [s.strip() for s in skills_str.replace(";", ",").split(",")]

        return {
            "raw_text": activity_text,
            "metadata": {
                "source": "excel",
                "row_number": row_number,
                "date": date_value,
                "hours": hours_value,
                "skills": skills_value,
                "original_row": row.to_dict()
            }
        }

    def _dump_all_rows(
        self,
        df: pd.DataFrame,
        date_col: str,
        hours_col: str,
        skills_col: str,
    ) -> List[Dict[str, Any]]:
        """
        Fallback: serialize every row as raw text for the LLM to interpret.
        Works with any schema — the AI figures out what's relevant.
        """
        entries = []
        for idx, row in df.iterrows():
            # Build a human-readable dump of all non-null columns
            parts = []
            for col in df.columns:
                val = row[col]
                if pd.notna(val):
                    val_str = str(val).strip()
                    if val_str and val_str.lower() not in ("nan", "none", ""):
                        parts.append(f"{col}: {val_str}")

            raw_text = "\n".join(parts)
            if not raw_text.strip():
                continue

            # Still extract date/hours if we found those columns
            date_value = None
            if date_col and pd.notna(row.get(date_col)):
                try:
                    date_value = pd.to_datetime(row[date_col]).date().isoformat()
                except Exception:
                    date_value = str(row[date_col]).strip()

            hours_value = None
            if hours_col and pd.notna(row.get(hours_col)):
                try:
                    hours_value = float(row[hours_col])
                except Exception:
                    pass

            entries.append({
                "raw_text": raw_text,
                "metadata": {
                    "source": "excel",
                    "row_number": idx + 1,
                    "date": date_value,
                    "hours": hours_value,
                    "skills": None,
                    "dump_mode": True,
                }
            })

        logger.info(f"Dump mode: extracted {len(entries)} rows as raw text")
        return entries
