import os
import logging
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

VALID_TRIGGERS = {
    "Urgency_Bias",
    "Authority_Bias",
    "Scarcity_Bias",
    "Social_Proof_Bias",
    "None",
}

_PROJECT_ROOT           = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LABELS_PATH            = os.path.join(_PROJECT_ROOT, "data", "processed", "nlp_cognitive_labels.csv")
_GEMINI_API_KEY         = os.getenv("GEMINI_API_KEY", "")
_GEMINI_URL             = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
_GEMINI_TIMEOUT         = 10
_OLLAMA_URL             = "http://localhost:11434/api/generate"
_USE_OLLAMA             = os.getenv("USE_OLLAMA", "false").lower() == "true"
_EXAMPLES_PER_CLASS     = 2
_MAX_KEYWORDS_PER_CLASS = 5

_KEYWORD_MAP: dict[str, list[str]] = {
    "Urgency_Bias": [
        "urgent", "immediately", "expires", "expiring", "expired",
        "within 24 hours", "action required", "act now", "deadline",
        "suspended", "suspension", "locked", "time-sensitive",
        "last chance", "today only", "critical", "warning",
    ],
    "Authority_Bias": [
        "it department", "it support", "it team", "helpdesk",
        "hr department", "human resources", "management", "compliance",
        "microsoft", "google", "paypal", "amazon", "apple",
        "your bank", "federal", "government", "official notice",
        "administrator", "system administrator", "ceo", "cfo",
    ],
    "Scarcity_Bias": [
        "limited", "only a few", "running out", "last available",
        "seats remaining", "slots left", "closing soon", "fill up",
        "nearly full", "quota", "allocation", "reassigned",
        "no longer available", "claim yours",
    ],
    "Social_Proof_Bias": [
        "your colleagues", "your team", "everyone has", "already completed",
        "most employees", "others have", "join your team",
        "you are the only", "your peers", "your department has",
        "94%", "all members", "entire team",
    ],
}


class CognitiveModelError(Exception):
    pass


class CognitiveModel:

    def __init__(self) -> None:
        self._few_shot_examples = self._load_few_shot_examples()
        self._gemini_available  = bool(_GEMINI_API_KEY)

        if not self._gemini_available:
            logger.warning(
                "GEMINI_API_KEY not set — CognitiveModel will use keyword fallback. "
                "Set GEMINI_API_KEY in .env for full Gemini-powered classification."
            )
        else:
            logger.info(
                "CognitiveModel initialized | few-shot examples: %d | mode: gemini",
                sum(len(v) for v in self._few_shot_examples.values()),
            )

    def tag_trigger(self, page_context: str) -> dict[str, Any]:
        """
        Classify the dominant cognitive trigger and return both the label
        and a bias_score (0.0-1.0) representing trigger intensity.

        Returns:
            {
                "cognitive_trigger": "Urgency_Bias",
                "bias_score": 0.72
            }
        """
        if not page_context or not page_context.strip():
            return {"cognitive_trigger": "None", "bias_score": 0.0}

        if self._gemini_available:
            try:
                raw = self._classify_with_gemini(page_context.strip())
                label, bias_score = self._parse_label_and_score(raw)
                logger.info(
                    "CognitiveModel | gemini | trigger=%s | bias_score=%s | context_len=%d",
                    label, bias_score, len(page_context)
                )
                return {"cognitive_trigger": label, "bias_score": bias_score}
            except Exception as exc:
                logger.warning("Gemini API error: %s — falling back to Ollama.", exc)

        if _USE_OLLAMA:
            try:
                raw = self._classify_with_ollama(page_context.strip())
                label, bias_score = self._parse_label_and_score(raw)
                logger.info(
                    "CognitiveModel | ollama | trigger=%s | bias_score=%s | context_len=%d",
                    label, bias_score, len(page_context)
                )
                return {"cognitive_trigger": label, "bias_score": bias_score}
            except Exception as exc:
                logger.warning("Ollama failed: %s — falling back to keyword classifier.", exc)

        label, bias_score = self._classify_with_keywords(page_context.strip())
        logger.info(
            "CognitiveModel | keyword_fallback | trigger=%s | bias_score=%s | context_len=%d",
            label, bias_score, len(page_context)
        )
        return {"cognitive_trigger": label, "bias_score": bias_score}

    def _classify_with_gemini(self, text: str) -> str:
        """Call Gemini API and return raw response text for parsing by caller."""
        import urllib.request
        import urllib.error
        import json

        prompt  = self._build_prompt(text)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 20},
        }

        url  = f"{_GEMINI_URL}?key={_GEMINI_API_KEY}"
        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=_GEMINI_TIMEOUT) as resp:
                body     = json.loads(resp.read().decode("utf-8"))
                raw_text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            raise CognitiveModelError(f"Gemini HTTP {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise CognitiveModelError(f"Gemini connection error: {e.reason}") from e
        except (KeyError, IndexError) as e:
            raise CognitiveModelError(f"Unexpected Gemini response format: {e}") from e

        return raw_text

    def _classify_with_ollama(self, text: str) -> str:
        """Call local Ollama instance and return raw response text for parsing."""
        import urllib.request
        import json

        prompt  = self._build_prompt(text)
        payload = {"model": "llama3.2:3b", "prompt": prompt, "stream": False}
        data    = json.dumps(payload).encode()
        req     = urllib.request.Request(
            _OLLAMA_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
            return body["response"].strip()

    def _build_prompt(self, text: str) -> str:
        lines = [
            "You are a cognitive bias classifier for a cybersecurity training platform.",
            "",
            "Classify the dominant psychological manipulation tactic in the email text.",
            "Return EXACTLY one label and one integer score (0-10) on a single line separated by a pipe.",
            "Format: LABEL|SCORE",
            "",
            "Labels:",
            "  Urgency_Bias       — time pressure, deadlines, account expiry warnings",
            "  Authority_Bias     — impersonates IT, HR, management, software vendors",
            "  Scarcity_Bias      — limited availability, seats/slots running out",
            "  Social_Proof_Bias  — colleagues already did this, peer pressure",
            "  None               — no clear dominant manipulation tactic",
            "",
            "Score: 0 = very weak signal, 10 = extremely strong signal.",
            "",
            "Rules:",
            "- Return ONLY: LABEL|SCORE. No explanation. Nothing else.",
            "- If two tactics apply, return the stronger one.",
            "- If unsure, return None|0.",
            "",
            "Examples:",
        ]

        for trigger_label, examples in self._few_shot_examples.items():
            for example_text in examples:
                lines.append(f'Text: "{example_text}"')
                lines.append(f"Response: {trigger_label}|8")
                lines.append("")

        lines.append(f'Text: "{text}"')
        lines.append("Response:")

        return "\n".join(lines)

    def _parse_label_and_score(self, raw_text: str) -> tuple[str, float]:
        """
        Parse 'Urgency_Bias|8' format into (label, bias_score).
        bias_score is normalized from 0-10 to 0.0-1.0.
        """
        cleaned = raw_text.strip().strip("`").strip("*").strip()

        if "|" in cleaned:
            parts      = cleaned.split("|", 1)
            label_raw  = parts[0].strip()
            score_raw  = parts[1].strip()
            label      = self._normalize_label(label_raw)
            try:
                raw_score  = float(score_raw)
                bias_score = round(min(1.0, max(0.0, raw_score / 10.0)), 2)
            except ValueError:
                bias_score = 0.5
            return label, bias_score

        label = self._normalize_label(cleaned)
        return label, (0.5 if label != "None" else 0.0)

    def _normalize_label(self, raw: str) -> str:
        if raw in VALID_TRIGGERS:
            return raw

        lower = raw.lower().replace(" ", "_")
        normalization = {
            "urgency_bias":      "Urgency_Bias",
            "authority_bias":    "Authority_Bias",
            "scarcity_bias":     "Scarcity_Bias",
            "social_proof_bias": "Social_Proof_Bias",
            "socialproof_bias":  "Social_Proof_Bias",
            "none":              "None",
        }
        if lower in normalization:
            return normalization[lower]

        partial = {
            "urgency":   "Urgency_Bias",
            "authority": "Authority_Bias",
            "scarcity":  "Scarcity_Bias",
            "social":    "Social_Proof_Bias",
        }
        for key, label in partial.items():
            if key in lower:
                return label

        logger.warning("Unrecognized label '%s' — defaulting to None.", raw)
        return "None"

    def _classify_with_keywords(self, text: str) -> tuple[str, float]:
        """Keyword fallback. Returns (label, bias_score)."""
        text_lower = text.lower()
        scores: dict[str, int] = {}

        for trigger, keywords in _KEYWORD_MAP.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[trigger] = score

        if not scores:
            return "None", 0.0

        winner     = max(scores, key=lambda k: scores[k])
        raw_score  = scores[winner]
        bias_score = round(min(1.0, raw_score / _MAX_KEYWORDS_PER_CLASS), 2)
        return winner, bias_score

    def _load_few_shot_examples(self) -> dict[str, list[str]]:
        try:
            import pandas as pd

            if not os.path.exists(_LABELS_PATH):
                raise FileNotFoundError(_LABELS_PATH)

            df = pd.read_csv(_LABELS_PATH)
            df["cognitive_trigger"] = df["cognitive_trigger"].fillna("None")

            label_map = {
                "Urgency":      "Urgency_Bias",
                "Authority":    "Authority_Bias",
                "Scarcity":     "Scarcity_Bias",
                "Social_Proof": "Social_Proof_Bias",
            }

            examples: dict[str, list[str]] = {}
            for dataset_label, output_label in label_map.items():
                subset = df[df["cognitive_trigger"] == dataset_label]["body"].dropna()
                subset = subset[subset.str.len() > 30]
                if len(subset) == 0:
                    continue
                sampled = subset.sample(
                    min(_EXAMPLES_PER_CLASS, len(subset)), random_state=42
                ).tolist()
                examples[output_label] = [s[:300] for s in sampled]

            logger.info("Few-shot examples loaded from dataset | classes: %s", list(examples.keys()))
            return examples

        except FileNotFoundError:
            logger.warning("nlp_cognitive_labels.csv not found at %s — using hardcoded examples.", _LABELS_PATH)
            return self._hardcoded_examples()
        except Exception as exc:
            logger.warning("Failed to load few-shot examples from CSV: %s — using hardcoded fallback.", exc)
            return self._hardcoded_examples()

    def _hardcoded_examples(self) -> dict[str, list[str]]:
        return {
            "Urgency_Bias": [
                "Your password expires in 24 hours. Click here to reset it immediately or you will be locked out.",
                "URGENT: Suspicious activity detected on your account. Verify your identity within 30 minutes.",
            ],
            "Authority_Bias": [
                "From the IT Security Team: All employees must complete mandatory credential verification by end of week.",
                "HR Department: Please acknowledge the updated Employee Code of Conduct by Friday or it will be noted in your file.",
            ],
            "Scarcity_Bias": [
                "Only 3 VPN license seats remain in your department. Claim yours before they are reassigned.",
                "Your storage allocation is being reduced. You have been selected for early access — slots are filling up.",
            ],
            "Social_Proof_Bias": [
                "Your entire team has already completed the security verification. You are the only member who has not confirmed.",
                "94% of employees in your department have enrolled in the new benefits portal. Complete your enrollment now.",
            ],
        }