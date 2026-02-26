"""
api_resilience.py — Enterprise AI API Resilience Layer
=======================================================
Provides a production-grade call wrapper for all AI model interactions.

Architecture:
    call_ai_with_schema(...)
        ├── [1] Retry with exponential backoff + jitter (Groq)
        ├── [2] Timeout enforcement (concurrent.futures)
        ├── [3] Strict JSON validation with one-shot repair pass
        ├── [4] Fallback: Gemini (if Groq fails all retries)
        └── [5] Fallback: deterministic_fn (if Gemini fails)

Token Management:
    trim_input(data, max_chars) — trims string fields in a dict so the
    total prompt stays within context window.

Usage:
    from api_resilience import call_ai_with_schema, trim_input

    result = call_ai_with_schema(
        system_prompt=SYSTEM,
        user_prompt=USER,
        schema_keys=["credibility_assessment", "evidence_breakdown", ...],
        groq_client=groq_client,
        gemini_client=gemini_client,           # optional
        deterministic_fn=my_fallback_fn,       # optional callable → dict
        timeout_sec=25,
        max_retries=3,
        temperature=0.05,
        max_tokens=2000,
    )
"""

import json
import time
import logging
import threading
import concurrent.futures
import re

log = logging.getLogger("HonestRecruiter.Resilience")

# ── Module-level lock for Groq (rate limit protection) ────────────────────────
_groq_lock = threading.Lock()


# ══════════════════════════════════════════════════════════════════════════════
# 1. TOKEN TRIMMER
# ══════════════════════════════════════════════════════════════════════════════

def trim_input(data: dict, max_chars: int = 4000) -> dict:
    """
    Recursively trims string values within a dict so the total serialized size
    stays under `max_chars`. Longer strings are trimmed first.
    Only sends structured data — never the full raw resume text in API payloads.
    """
    out = {}
    for k, v in data.items():
        if isinstance(v, str) and len(v) > max_chars:
            out[k] = v[:max_chars] + "…[trimmed]"
        elif isinstance(v, dict):
            out[k] = trim_input(v, max_chars)
        elif isinstance(v, list):
            # Trim each string in list, cap list length at 20
            out[k] = [
                (item[:300] + "…" if isinstance(item, str) and len(item) > 300 else item)
                for item in v[:20]
            ]
        else:
            out[k] = v
    return out


def build_compact_prompt(input_data: dict, resume_text: str = "", max_resume_chars: int = 3500) -> str:
    """
    Builds a compact, structured JSON prompt string from input_data.
    Includes only a trimmed resume excerpt (not the full text).
    """
    compact = trim_input(input_data, max_chars=500)
    if resume_text:
        # Only send the most signal-rich first N chars of resume
        compact["resume_excerpt"] = resume_text[:max_resume_chars]
    return json.dumps(compact, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# 2. JSON VALIDATOR + REPAIR
# ══════════════════════════════════════════════════════════════════════════════

def validate_json_response(raw: str, required_keys: list) -> dict | None:
    """
    Attempts to parse raw string as JSON and validates required_keys exist.
    Returns the parsed dict on success, None on failure.
    """
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        missing = [k for k in required_keys if k not in data]
        if missing:
            log.warning("JSON response missing keys: %s", missing)
            return None
        return data
    except json.JSONDecodeError as e:
        log.warning("JSON decode error: %s | raw[:200]: %s", e, raw[:200])
        return None


def repair_json(raw: str, groq_client, required_keys: list,
                timeout_sec: float = 12.0) -> dict | None:
    """
    One-shot JSON repair pass: asks the model to reformat the malformed output.
    Only called when the primary call returns unparseable JSON.
    """
    if not groq_client or not raw:
        return None

    repair_prompt = (
        f"The following text was supposed to be valid JSON but is malformed. "
        f"Return ONLY the fixed JSON with these exact top-level keys: {required_keys}. "
        f"No explanation, no markdown, pure JSON only.\n\n"
        f"Malformed text:\n{raw[:3000]}"
    )

    try:
        def _call():
            with _groq_lock:
                return groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",   # Fast, cheap repair model
                    messages=[{"role": "user", "content": repair_prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=1500,
                )

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_call)
            result = future.result(timeout=timeout_sec)

        repaired_raw = result.choices[0].message.content
        return validate_json_response(repaired_raw, required_keys)

    except Exception as e:
        log.warning("JSON repair pass failed: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 3. CORE: GROQ CALL WITH EXPONENTIAL BACKOFF + TIMEOUT
# ══════════════════════════════════════════════════════════════════════════════

def _groq_call_once(groq_client, model: str, messages: list,
                    temperature: float, max_tokens: int,
                    timeout_sec: float) -> str | None:
    """
    Single Groq call, enforced with a hard timeout via ThreadPoolExecutor.
    Returns raw content string or None.
    """
    def _call():
        with _groq_lock:
            time.sleep(0.2)   # minimal inter-request pacing
            return groq_client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temperature,
                max_tokens=max_tokens,
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_call)
        try:
            result = future.result(timeout=timeout_sec)
            return result.choices[0].message.content
        except concurrent.futures.TimeoutError:
            log.warning("Groq call timed out after %.0fs", timeout_sec)
            return None


def _groq_with_backoff(groq_client, model: str, messages: list,
                       required_keys: list, temperature: float,
                       max_tokens: int, timeout_sec: float,
                       max_retries: int = 3,
                       attempt_repair: bool = True) -> dict | None:
    """
    Groq call with:
      - Exponential backoff + jitter  (2^attempt + random 0–1s)
      - Hard timeout per attempt
      - Strict JSON validation
      - One-shot JSON repair on last valid attempt
    """
    last_raw = None

    for attempt in range(max_retries):
        try:
            raw = _groq_call_once(groq_client, model, messages,
                                  temperature, max_tokens, timeout_sec)
            if raw is None:
                raise RuntimeError("Timeout or empty response")

            last_raw = raw
            parsed = validate_json_response(raw, required_keys)
            if parsed:
                log.info("Groq OK on attempt %d", attempt + 1)
                return parsed

            # JSON valid but missing keys — try repair immediately on last attempt
            if attempt == max_retries - 1 and attempt_repair:
                log.warning("Groq: valid JSON but missing keys on last attempt — running repair.")
                repaired = repair_json(raw, groq_client, required_keys, timeout_sec)
                if repaired:
                    return repaired

            log.warning("Groq attempt %d: JSON invalid/incomplete. Retrying.", attempt + 1)

        except Exception as e:
            err = str(e).lower()
            is_rate_limit = any(x in err for x in ["rate_limit", "429", "overloaded", "quota"])
            if is_rate_limit:
                delay = (2 ** attempt) + (time.time() % 1.0)  # exp backoff + jitter
                log.warning("Groq 429/rate-limit. Backoff %.1fs (attempt %d/%d)",
                            delay, attempt + 1, max_retries)
                time.sleep(delay)
            else:
                log.error("Groq error (attempt %d): %s", attempt + 1, e)
                # For non-rate-limit errors, shorter fixed wait
                time.sleep(1.0)

    # Last resort: try JSON repair on whatever we have
    if last_raw and attempt_repair:
        log.warning("Groq exhausted retries — attempting repair on last response.")
        return repair_json(last_raw, groq_client, required_keys, timeout_sec)

    log.error("Groq exhausted all %d retries.", max_retries)
    return None


# ══════════════════════════════════════════════════════════════════════════════
# 4. GEMINI FALLBACK
# ══════════════════════════════════════════════════════════════════════════════

def _gemini_call(gemini_client, system_prompt: str, user_prompt: str,
                 required_keys: list, timeout_sec: float,
                 max_tokens: int = 2000) -> dict | None:
    """
    Gemini fallback call via google-genai SDK.
    Uses gemini-1.5-flash (fast, cost-efficient).
    """
    if not gemini_client:
        return None

    full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nReturn ONLY valid JSON."

    def _call():
        try:
            # Try google.genai SDK (newer)
            response = gemini_client.models.generate_content(
                model="gemini-1.5-flash",
                contents=full_prompt,
            )
            return response.text
        except AttributeError:
            # Fall back to older google-generativeai SDK
            response = gemini_client.generate_content(full_prompt)
            return response.text

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_call)
            raw = future.result(timeout=timeout_sec)

        # Strip markdown fences if model wraps output
        raw = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
        raw = re.sub(r'```\s*$', '', raw.strip(), flags=re.MULTILINE)

        parsed = validate_json_response(raw, required_keys)
        if parsed:
            log.info("Gemini fallback: OK")
            return parsed

        log.warning("Gemini response failed schema validation — attempting local repair.")
        # Simple structured extraction fallback for Gemini
        return _extract_partial_json(raw, required_keys)

    except concurrent.futures.TimeoutError:
        log.warning("Gemini call timed out after %.0fs", timeout_sec)
    except Exception as e:
        log.error("Gemini fallback error: %s", e)
    return None


def _extract_partial_json(raw: str, required_keys: list) -> dict | None:
    """
    Last-resort regex-based JSON block extraction for malformed responses.
    Tries to find a JSON object in the text and parse it.
    """
    # Try to find the first complete JSON block
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            missing = [k for k in required_keys if k not in data]
            if len(missing) <= 1:   # Allow 1 missing key — better than nothing
                return data
        except Exception:
            pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# 5. PUBLIC API: call_ai_with_schema
# ══════════════════════════════════════════════════════════════════════════════

def call_ai_with_schema(
    system_prompt: str,
    user_prompt: str,
    schema_keys: list,
    groq_client=None,
    groq_model: str = "llama-3.3-70b-versatile",
    gemini_client=None,
    deterministic_fn=None,          # callable() → dict, final fallback
    timeout_sec: float = 25.0,
    max_retries: int = 3,
    temperature: float = 0.05,
    max_tokens: int = 2000,
) -> dict:
    """
    Enterprise-grade AI call.
    Tries: Groq → Gemini → deterministic_fn (never returns None).

    Parameters
    ----------
    schema_keys : list
        Required top-level JSON keys. Call is retried/repaired until all present.
    deterministic_fn : callable
        Must return a valid dict matching schema_keys. Called if all AI fails.
    timeout_sec : float
        Per-attempt hard timeout (enforced via ThreadPoolExecutor).

    Returns
    -------
    dict with an extra key `ai_status`:
        "groq_primary"        — Groq succeeded
        "gemini_fallback"     — Groq failed, Gemini succeeded
        "deterministic_fallback" — All AI failed, deterministic used
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

    # ── Attempt 1: Groq ───────────────────────────────────────────────────────
    if groq_client:
        result = _groq_with_backoff(
            groq_client=groq_client,
            model=groq_model,
            messages=messages,
            required_keys=schema_keys,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_sec=timeout_sec,
            max_retries=max_retries,
        )
        if result:
            result["ai_status"] = "groq_primary"
            return result
        log.warning("Groq primary path failed. Falling back to Gemini.")

    # ── Attempt 2: Gemini ─────────────────────────────────────────────────────
    if gemini_client:
        result = _gemini_call(
            gemini_client=gemini_client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            required_keys=schema_keys,
            timeout_sec=timeout_sec,
            max_tokens=max_tokens,
        )
        if result:
            result["ai_status"] = "gemini_fallback"
            log.info("Gemini fallback succeeded.")
            return result
        log.warning("Gemini fallback failed. Using deterministic report.")

    # ── Attempt 3: Deterministic ──────────────────────────────────────────────
    if deterministic_fn:
        try:
            result = deterministic_fn()
            if isinstance(result, dict):
                result["ai_status"] = "deterministic_fallback"
                log.info("Deterministic fallback used.")
                return result
        except Exception as e:
            log.error("Deterministic fallback raised: %s", e)

    # Should never reach here if deterministic_fn is provided
    log.error("All AI paths exhausted — returning empty schema shell.")
    return {k: [] if "flags" in k or "signals" in k or "observations" in k else {} for k in schema_keys}


# ══════════════════════════════════════════════════════════════════════════════
# 6. LEGACY WRAPPER — Drop-in replacement for old safe_groq_call
# ══════════════════════════════════════════════════════════════════════════════

def safe_groq_call(func, *args, **kwargs):
    """
    Drop-in replacement for the old `safe_groq_call` in ai_consensus_engine.py.
    Adds exponential backoff with jitter. Passes through all args/kwargs.
    """
    max_retries = int(kwargs.pop("_max_retries", 3))
    timeout_sec = float(kwargs.pop("_timeout", 25.0))

    for attempt in range(max_retries):
        try:
            # Honour timeout via ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(func, *args, **kwargs)
                return future.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError:
            log.warning("safe_groq_call timed out (attempt %d/%d)", attempt + 1, max_retries)
        except Exception as e:
            err = str(e).lower()
            is_rate_limit = any(x in err for x in ["rate_limit", "429", "overloaded", "quota"])
            delay = (2 ** attempt) + (time.time() % 1.0)
            if is_rate_limit:
                log.warning("Groq 429. Backoff %.1fs (attempt %d/%d)", delay, attempt + 1, max_retries)
                time.sleep(delay)
            else:
                log.error("Groq API error (attempt %d): %s", attempt + 1, e)
                time.sleep(min(delay, 3.0))

    log.error("safe_groq_call exhausted %d retries.", max_retries)
    return None
