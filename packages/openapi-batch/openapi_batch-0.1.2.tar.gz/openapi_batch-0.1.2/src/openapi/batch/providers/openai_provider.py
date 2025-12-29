from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Iterable
import json
import tempfile
import os
import time

from .base import ProviderCaps, ProviderError


def _lazy_openai_client(api_key: Optional[str], base_url: Optional[str]):
    try:
        from openai import OpenAI
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "OpenAI provider requires optional dependency: pip install openapi-batch[openai]"
        ) from e

    kwargs: Dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def _to_chat_body(input: Dict[str, Any], *, default_model: str) -> Dict[str, Any]:
    """
    Normalize user input to /v1/chat/completions body.
    Accepts:
      - {"messages":[...], "model":..., "temperature":..., "max_tokens":...}
      - {"prompt":"...", "model":...} -> messages=[{"role":"user","content":prompt}]
    """
    model = input.get("model") or default_model
    if not model:
        raise ProviderError("config", "OpenAI model not provided (input.model or default_model).", False)

    temperature = input.get("temperature", 0)
    max_tokens = input.get("max_tokens", None)

    messages = input.get("messages")
    if messages is None:
        prompt = input.get("prompt")
        if prompt is None:
            raise ProviderError("bad_request", "OpenAI input requires 'messages' or 'prompt'.", False)
        messages = [{"role": "user", "content": str(prompt)}]

    body: Dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature}
    if max_tokens is not None:
        body["max_tokens"] = max_tokens

    # pass-through allowlist for common knobs
    for k in ("top_p", "presence_penalty", "frequency_penalty", "stop", "seed", "logprobs"):
        if k in input:
            body[k] = input[k]

    return body


@dataclass
class OpenAIProvider:
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    base_url: Optional[str] = None
    timeout_s: float = 60.0

    name: str = "openai"

    def caps(self) -> ProviderCaps:
        return ProviderCaps(native_batch=True)

    def _client(self):
        return _lazy_openai_client(self.api_key, self.base_url)

    # ---------------------------
    # Emulated single-call mode
    # ---------------------------
    async def call_one(self, *, input: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        client = self._client()
        model = input.get("model") or self.default_model
        if not model:
            raise ProviderError("config", "OpenAI model not provided (input.model or default_model).", False)

        body = _to_chat_body(input, default_model=model)

        try:
            resp = client.chat.completions.create(**body)
            text = resp.choices[0].message.content if resp.choices else ""
            usage = resp.usage.model_dump() if getattr(resp, "usage", None) else None
            return {"output": text, "model": body["model"], "usage": usage, "raw": resp.model_dump()}
        except Exception as e:
            msg = str(e)
            low = msg.lower()
            retryable = any(s in low for s in ["timeout", "timed out", "temporarily", "rate limit", "429", "503", "502"])
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
    # Native batch mode
    # ---------------------------

    def native_batch_create(
        self,
        *,
        job_id: str,
        endpoint: str,
        completion_window: str,
        requests: Iterable[Dict[str, Any]],
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Build JSONL with OpenAI Batch request lines and submit batch job.

        Each line format:
          {"custom_id": "...", "method": "POST", "url": "/v1/chat/completions", "body": {...}}

        OpenAI docs: upload file with purpose="batch", then create batch with input_file_id. :contentReference[oaicite:3]{index=3}
        """
        client = self._client()

        # Write JSONL to a temp file
        tmp = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".jsonl")
        tmp_path = tmp.name
        try:
            for r in requests:
                tmp.write(json.dumps(r, ensure_ascii=False) + "\n")
            tmp.close()

            # Upload file (purpose=batch)
            with open(tmp_path, "rb") as f:
                batch_file = client.files.create(file=f, purpose="batch")

            # Create batch
            batch = client.batches.create(
                input_file_id=batch_file.id,
                endpoint=endpoint,
                completion_window=completion_window,
                metadata=metadata or {"job_id": job_id},
            )
            return batch.id
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def native_batch_retrieve(self, *, batch_id: str) -> Dict[str, Any]:
        client = self._client()
        b = client.batches.retrieve(batch_id)
        # SDK objects have model_dump; fallback to dict-like
        return b.model_dump() if hasattr(b, "model_dump") else dict(b)

    def native_file_content_text(self, *, file_id: str) -> str:
        client = self._client()
        fr = client.files.content(file_id)
        # docs show .text :contentReference[oaicite:4]{index=4}
        return fr.text if hasattr(fr, "text") else str(fr)

    # ---------------------------
    # Helpers for mapping output/error jsonl to item_id
    # ---------------------------

    @staticmethod
    def parse_output_jsonl(text: str) -> Dict[str, Dict[str, Any]]:
        """
        Return map: item_id(custom_id) -> {"ok": True, "response":..., "body":..., "error":...}
        Output JSONL lines contain:
          {"custom_id": "...", "response": {"status_code":..., "body": {...}}, "error": null}
        Docs emphasize using custom_id for mapping. :contentReference[oaicite:5]{index=5}
        """
        out: Dict[str, Dict[str, Any]] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            cid = obj.get("custom_id")
            if not cid:
                continue
            out[cid] = obj
        return out
