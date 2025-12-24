import re
from typing import Any, Dict, List, Optional

SECTION_ALIASES = {
    "contact": ["contact", "contacts"],
    "summary": ["summary", "profile", "about"],
    "education": ["education", "academic"],
    "skills": ["skills", "technical skills"],
    "experience": ["experience", "work experience", "employment"],
}

VERBS = {
    "is",
    "are",
    "was",
    "were",
    "be",
    "am",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "make",
    "makes",
    "made",
    "go",
    "goes",
    "went",
    "see",
    "sees",
    "saw",
    "get",
    "gets",
    "got",
    "can",
    "will",
    "shall",
    "should",
    "would",
    "could",
    "may",
    "might",
    "must",
    "want",
    "wants",
}


def is_title_case_or_all_caps(line: str) -> bool:
    return line.istitle() or line.isupper()


def is_short_line(line: str) -> bool:
    return len(line.split()) <= 4


def is_surrounded_by_empty(lines: List[str], idx: int) -> bool:
    before = idx == 0 or not lines[idx - 1].strip()
    after = idx == len(lines) - 1 or not lines[idx + 1].strip()
    return before and after


def not_part_of_sentence(line: str) -> bool:
    return not re.search(r"[.!?]$", line.strip())


def normalize_heading(heading: str) -> Optional[str]:
    heading_lc = heading.lower().strip(":").strip()
    for norm, aliases in SECTION_ALIASES.items():
        if heading_lc in aliases:
            return norm
    return None


def contains_any(text: str, keywords: List[str]) -> bool:
    text = text.lower()
    return any(kw in text for kw in keywords)


class StructuredExtractor:
    def __init__(self, text: str):
        self.text = text
        self.lines = [line.rstrip() for line in text.splitlines()]
        self.sections: Dict[str, Any] = {}
        self.entities = {
            "emails": [],
            "phones": [],
            "dates": [],
        }
        self.classification = None

    def extract(self) -> Dict[str, Any]:
        section_spans = self._find_headings()
        self._extract_sections(section_spans)
        self._extract_entities()
        self._classify()

        return {
            "classification": self.classification,
            "sections": self.sections,
            "entities": self.entities,
        }

    def _find_headings(self) -> List[Dict[str, Any]]:
        headings = []

        for idx, line in enumerate(self.lines):
            if not line.strip():
                continue

            score = 0
            if is_short_line(line):
                score += 1
            if is_surrounded_by_empty(self.lines, idx):
                score += 1
            if is_title_case_or_all_caps(line):
                score += 1
            if not_part_of_sentence(line):
                score += 1

            if score >= 2:
                norm = normalize_heading(line)
                if norm:
                    headings.append(
                        {
                            "idx": idx,
                            "norm": norm,
                            "raw": line,
                        }
                    )

        return headings

    def _extract_sections(self, headings: List[Dict[str, Any]]) -> None:
        spans = []

        for i, h in enumerate(headings):
            start = h["idx"] + 1
            end = (
                headings[i + 1]["idx"]
                if i + 1 < len(headings)
                else len(self.lines)
            )
            spans.append((h["norm"], start, end))

        for norm, start, end in spans:
            content = self.lines[start:end]

            if norm == "contact":
                self.sections[norm] = self._parse_contact(content)
            elif norm == "summary":
                self.sections[norm] = " ".join(
                    line for line in content if line.strip()
                )
            elif norm == "education":
                self.sections[norm] = self._parse_education(content)
            elif norm == "skills":
                self.sections[norm] = self._parse_skills(content)
            elif norm == "experience":
                self.sections[norm] = self._parse_experience(content)

    def _parse_contact(self, lines: List[str]) -> Dict[str, str]:
        contact: Dict[str, str] = {}

        for line in lines:
            line_lc = line.lower()

            email = re.search(r"([\w\.-]+@[\w\.-]+)", line)
            if email:
                contact["email"] = email.group(1)

            phone = re.search(r"(\+?\d{7,15})", line)
            if phone and contains_any(
                line_lc,
                ["phone", "mobile", "tel"],
            ):
                contact["phone"] = phone.group(1)

            if contains_any(line_lc, ["location", "address", "city"]):
                contact["location"] = (
                    line.split(":", 1)[-1].strip()
                    if ":" in line
                    else line.strip()
                )

        return contact

    def _parse_education(self, lines: List[str]) -> List[Dict[str, str]]:
        edus = []

        for line in lines:
            match = re.match(
                r"(.+?)\s*\|\s*(.+?)\s*\|\s*([\d\-–]+)",
                line,
            )
            if match:
                edus.append(
                    {
                        "degree": match.group(1).strip(),
                        "institution": match.group(2).strip(),
                        "period": match.group(3).strip(),
                    }
                )

        return edus

    def _parse_skills(self, lines: List[str]) -> Dict[str, List[str]]:
        skills: Dict[str, List[str]] = {}

        for line in lines:
            match = re.match(r"@\s*([\w\s]+):\s*(.+)", line)
            if match:
                key = match.group(1).strip().lower()
                values = [
                    v.strip()
                    for v in re.split(r",|;", match.group(2))
                    if v.strip()
                ]
                skills[key] = values

        return skills

    def _parse_experience(self, lines: List[str]) -> List[Dict[str, Any]]:
        exps = []
        current = None

        for line in lines:
            match = re.match(
                r"(.+?)\s*\|\s*([\d\w\s\-–]+)",
                line,
            )
            if match:
                if current:
                    exps.append(current)

                current = {
                    "title": match.group(1).strip(),
                    "period": match.group(2).strip(),
                    "details": [],
                }
            elif current and line.strip():
                current["details"].append(line.strip())

        if current:
            exps.append(current)

        return exps

    def _extract_entities(self) -> None:
        for line in self.lines:
            for m in re.finditer(r"[\w\.-]+@[\w\.-]+", line):
                self.entities["emails"].append(m.group(0))

        for line in self.lines:
            if contains_any(line, ["phone", "mobile", "tel"]):
                phone = re.search(r"(\+?\d{7,15})", line)
                if phone:
                    self.entities["phones"].append(phone.group(1))

        for line in self.lines:
            for m in re.finditer(r"\b(\d{4})\b", line):
                self.entities["dates"].append(m.group(1))

    def _classify(self) -> None:
        # Add more document types as needed
        types = [
            "resume",
            "letter",
            "letterhead",
            "invoice",
            "report",
            "receipt",
            "form",
            "contract",
            "statement",
            "certificate",
            "application",
            "order",
            "manual",
            "guide",
            "plan",
            "proposal",
            "schedule",
            "summary",
            "transcript",
            "other",
        ]

        score = {k: 0 for k in types}

        # Resume detection
        # Requires skills/experience/education + contact info
        has_core_sections = (
            "skills" in self.sections
            or "experience" in self.sections
            or "education" in self.sections
        )
        has_contact = (
            self.entities["emails"]
            or self.entities["phones"]
        )
        if has_core_sections and has_contact:
            score["resume"] += 3
        if "skills" in self.sections:
            score["resume"] += 1
        if "experience" in self.sections:
            score["resume"] += 1
        if "education" in self.sections:
            score["resume"] += 1

        # Letter: look for common phrases
        letter_phrases = [
            "sincerely",
            "dear",
            "regards",
            "to:",
            "from:",
            "subject:",
            "head of",
            "letterhead",
        ]
        for line in self.lines:
            if any(
                phrase in line.lower()
                for phrase in letter_phrases
            ):
                score["letter"] += 1
        # Letterhead detection
        # Looks for company name, address, contact info
        has_company = (
            len(self.lines) > 0
            and (
                "co." in self.lines[0].lower()
                or "company" in self.lines[0].lower()
            )
        )
        if has_company:
            score["letterhead"] += 1
        if any("@" in line for line in self.lines[:5]):
            score["letterhead"] += 1
        address_pattern = re.compile(
            r"\d{3,}.*("
            r"street|"
            r"st\.|"
            r"ave|"
            r"road|"
            r"rd\.|"
            r"city|"
            r"zip|"
            r"code"
            r")"
        )
        if any(
            address_pattern.search(line.lower())
            for line in self.lines[:10]
        ):
            score["letterhead"] += 1

        # Invoice detection
        # Keywords: invoice, total, due, bill to
        invoice_phrases = [
            "invoice",
            "total",
            "due",
            "bill to",
            "amount",
            "balance",
            "item",
            "qty",
            "unit price",
        ]

        for line in self.lines:
            if any(
                phrase in line.lower()
                for phrase in invoice_phrases
            ):
                score["invoice"] += 1

        # Report detection
        # Keywords: report, summary, findings
        report_phrases = [
            "report",
            "summary",
            "findings",
            "analysis",
            "conclusion",
        ]

        for line in self.lines:
            if any(
                phrase in line.lower()
                for phrase in report_phrases
            ):
                score["report"] += 1

        # Receipt detection
        # Keywords: receipt, paid, cashier
        receipt_phrases = [
            "receipt",
            "paid",
            "change",
            "cashier",
            "transaction",
        ]
        for line in self.lines:
            if any(
                phrase in line.lower()
                for phrase in receipt_phrases
            ):
                score["receipt"] += 1

        # Contract detection
        # Keywords: contract, agreement, terms
        contract_phrases = [
            "contract",
            "agreement",
            "party",
            "parties",
            "terms",
            "conditions",
        ]
        for line in self.lines:
            if any(
                phrase in line.lower()
                for phrase in contract_phrases
            ):
                score["contract"] += 1

        # If all scores are zero, fallback to 'other'
        if all(v == 0 for v in score.values()):
            score["other"] = 1

        best = max(score, key=score.get)

        base_conf = {
            "resume": 0.9,
            "letter": 0.85,
            "letterhead": 0.8,
            "invoice": 0.85,
            "report": 0.8,
            "receipt": 0.85,
            "form": 0.8,
            "contract": 0.85,
            "statement": 0.85,
            "certificate": 0.85,
            "application": 0.8,
            "order": 0.85,
            "manual": 0.8,
            "guide": 0.8,
            "plan": 0.8,
            "proposal": 0.8,
            "schedule": 0.8,
            "summary": 0.8,
            "transcript": 0.85,
            "other": 0.5,
        }

        self.classification = {
            "type": best,
            "confidence": round(
                base_conf.get(best, 0.5)
                + 0.01 * min(score[best], 10),
                2,
            ),
        }
