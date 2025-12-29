from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Iterable
import json
import os
import tempfile
import time

from .base import ProviderCaps, ProviderError
from ..logging_utils import log


def _lazy_gemini(api_key: Optional[str]):
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Gemini provider requires optional dependency: pip install openapi-batch[gemini]"
        ) from e

    if not api_key:
        raise RuntimeError("Gemini api_key is required (or set GEMINI_API_KEY).")

    return genai.Client(api_key=api_key), types


def _normalize_job_state(state_obj: Any) -> str:
    """
    Return stable string like 'JOB_STATE_RUNNING', 'JOB_STATE_SUCCEEDED', etc.

    SDK can expose:
      - job.state == 'JOB_STATE_RUNNING' (string)
      - job.state.name == 'JOB_STATE_RUNNING' (enum-like)
      - dict forms depending on model_dump/__dict__
    """
    if state_obj is None:
        return ""

    # If it's already a string
    if isinstance(state_obj, str):
        s = state_obj
    else:
        # enum-like: has .name
        name = getattr(state_obj, "name", None)
        if isinstance(name, str) and name:
            s = name
        else:
            s = str(state_obj)

    # Normalize if string is like "BatchJobState.JOB_STATE_RUNNING"
    if "JOB_STATE_" in s:
        idx = s.find("JOB_STATE_")
        return s[idx:].strip().strip("'\"").split()[0].strip(",)")
    return s.strip().strip("'\"")


def _to_generate_content_request(input: Dict[str, Any], *, default_model: Optional[str]) -> Dict[str, Any]:
    """
    Normalize user input into a Gemini GenerateContentRequest object (dict form).

    Accepts:
      - {"contents":[...], "config":{...}}
      - {"prompt":"..."} -> contents=[{"role":"user","parts":[{"text": "..."}]}]
      - {"text":"..."} -> alias
      - Pass-through:
          - input["config"] (temperature, tools, system_instruction etc.)
          - input["generation_config"], input["tools"], input["safety_settings"], input["system_instruction"]
    """
    if "contents" in input:
        req = {"contents": input["contents"]}
    else:
        prompt = input.get("prompt", input.get("text"))
        if prompt is None:
            raise ProviderError("bad_request", "Gemini input requires 'contents' or 'prompt'/'text'.", False)
        req = {"contents": [{"role": "user", "parts": [{"text": str(prompt)}]}]}

    if "config" in input and isinstance(input["config"], dict):
        req["config"] = input["config"]

    for k in ("generation_config", "system_instruction", "tools", "safety_settings"):
        if k in input and k not in req:
            req[k] = input[k]

    # model is chosen at batch job level; keep item-level model only for convenience upstream
    if "model" in input:
        req["_item_model"] = input["model"]

    return req


@dataclass
class GeminiProvider:
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    timeout_s: float = 60.0

    name: str = "gemini"

    def caps(self) -> ProviderCaps:
        return ProviderCaps(native_batch=True)

    # ---------------------------
    # Emulated single-call mode
    # ---------------------------
    async def call_one(self, *, input: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        client, _types = _lazy_gemini(self.api_key)

        model = input.get("model") or self.default_model
        if not model:
            raise ProviderError("config", "Gemini model not provided (input.model or default_model).", False)

        contents = input.get("contents")
        if contents is None:
            prompt = input.get("prompt", input.get("text"))
            if prompt is None:
                raise ProviderError("bad_request", "Gemini input requires 'prompt'/'text' or 'contents'.", False)
            contents = str(prompt)

        try:
            resp = client.models.generate_content(model=model, contents=contents)
            text = getattr(resp, "text", None)
            if text is None:
                text = str(resp)
            return {"output": text, "model": model, "raw": resp.__dict__ if hasattr(resp, "__dict__") else str(resp)}
        except Exception as e:
            msg = str(e)
            low = msg.lower()
            retryable = any(s in low for s in ["timeout", "timed out", "temporarily", "rate", "429", "503", "502"])
            if "429" in low or "rate" in low:
                etype = "rate_limit"
            elif "timeout" in low:
                etype = "timeout"
            elif retryable:
                etype = "provider_5xx"
            else:
                etype = "exception"
            raise ProviderError(etype, msg, retryable, raw=None) from e

    # ---------------------------
    # Native batch mode (Gemini Developer API, python-genai)
    # ---------------------------
    def native_batch_supported(self) -> bool:
        return True

    def native_batch_create(
        self,
        *,
        job_id: str,
        endpoint: str,  # unused for Gemini (kept for symmetry)
        completion_window: str,  # unused for Gemini
        requests: Iterable[Dict[str, Any]],
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        client, types = _lazy_gemini(self.api_key)

        model = (metadata or {}).get("model") or self.default_model
        if not model:
            raise ProviderError("config", "Gemini default_model required for native batch.", False)

        if not model.startswith("models/"):
            model = f"models/{model}"

        tmp = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".jsonl")
        tmp_path = tmp.name
        try:
            for line in requests:
                tmp.write(json.dumps(line, ensure_ascii=False) + "\n")
            tmp.close()

            uploaded = None
            try:
                uploaded = client.files.upload(
                    file=tmp_path,
                    config=types.UploadFileConfig(
                        display_name=f"openapi-batch-{job_id}",
                        mime_type="jsonl",
                    ),
                )
            except Exception:
                uploaded = client.files.upload(
                    file=tmp_path,
                    config=types.UploadFileConfig(
                        display_name=f"openapi-batch-{job_id}",
                        mime_type="text/plain",
                    ),
                )

            batch_job = client.batches.create(
                model=model,
                src=uploaded.name,
                config={
                    "display_name": (metadata or {}).get("display_name") or f"openapi-batch-{job_id}",
                },
            )
            return batch_job.name
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def native_batch_retrieve(self, *, batch_id: str) -> Dict[str, Any]:
        """
        BUG FIX: Return a stable dict structure regardless of SDK internal representation.

        We normalize:
          - state -> {'name': 'JOB_STATE_RUNNING'}
          - dest -> {'file_name': '<file-id-or-name>'} if present
          - stats if present
        """
        client, _types = _lazy_gemini(self.api_key)
        job = client.batches.get(name=batch_id)

        state_str = _normalize_job_state(getattr(job, "state", None))
        dest = getattr(job, "dest", None)
        dest_file_name = getattr(dest, "file_name", None) if dest is not None else None

        # Some versions may use camelCase
        if dest_file_name is None and dest is not None:
            dest_file_name = getattr(dest, "fileName", None)

        stats = getattr(job, "batch_stats", None) or getattr(job, "batchStats", None)

        out: Dict[str, Any] = {
            "name": getattr(job, "name", batch_id),
            "state": {"name": state_str},
            "dest": {"file_name": dest_file_name} if dest_file_name else {},
        }

        if stats is not None:
            # best effort dict conversion
            if hasattr(stats, "model_dump"):
                out["batch_stats"] = stats.model_dump()
            elif hasattr(stats, "__dict__"):
                out["batch_stats"] = dict(stats.__dict__)
            else:
                out["batch_stats"] = str(stats)

        # Useful debugging
        out["_raw_repr"] = str(job)

        return out

    def native_file_content_text(self, *, file_id: str) -> str:
        client, _types = _lazy_gemini(self.api_key)
        data = client.files.download(file=file_id)
        if isinstance(data, (bytes, bytearray)):
            return bytes(data).decode("utf-8", errors="replace")
        return str(data)

    # ---------------------------
    # Output parsing helpers
    # ---------------------------
    @staticmethod
    def parse_result_jsonl(text: str) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            key = obj.get("key") or obj.get("metadata", {}).get("key")
            if key:
                out[str(key)] = obj
        return out

    @staticmethod
    def extract_text_from_generate_content_response(resp: Dict[str, Any]) -> str:
        if isinstance(resp, dict):
            if "text" in resp and isinstance(resp["text"], str):
                return resp["text"]

            cands = resp.get("candidates") or []
            if cands:
                c0 = cands[0] or {}
                content = c0.get("content") or {}
                parts = content.get("parts") or []
                texts = []
                for p in parts:
                    t = p.get("text")
                    if isinstance(t, str):
                        texts.append(t)
                if texts:
                    return "".join(texts)

        return ""
