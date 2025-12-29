import asyncio
from contextlib import suppress
from typing import List, Tuple

import aiohttp
import requests

from .input_processor import process_input
from .split_chunks import chunk_by_words

class PromptShieldPTIT:
    def __init__(self,
            ENDPOINT_MODEL_PREDICT: str = "http://34.66.231.218:8000/predict",
            ENDPOINT_VECTOR_SEARCH: str = "http://35.232.125.227:8001/search",
            USE_CHUNK: bool = False,
            CHUNK_SIZE: int = 50,
            CHUNK_OVERLAP: int = 10,
            MAX_CONCURRENCY: int = 8,
        ) -> None:
        self.ENDPOINT_MODEL_PREDICT = ENDPOINT_MODEL_PREDICT
        self.ENDPOINT_VECTOR_SEARCH = ENDPOINT_VECTOR_SEARCH
        self.use_chunk = USE_CHUNK
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP
        self.max_concurrency = MAX_CONCURRENCY

    def model_fine_tuning_detect_PI(self, prompt: str) -> tuple[str, float]:
        response = requests.post(self.ENDPOINT_MODEL_FINE_TUNING_PREDICT, json={"text": prompt})
        label, score = response.json()["label"], response.json()["score"]
        return label, score

    def model_detect_PI(self, prompt: str) -> tuple[str, float]:
        response = requests.post(self.ENDPOINT_MODEL_PREDICT, json={"text": prompt})
        label, score = response.json()["label"], response.json()["score"]
        return label, score

    def vector_search_detect_PI(self, prompt: str) -> tuple[str, float]:
        response = requests.post(self.ENDPOINT_VECTOR_SEARCH, json={"text": prompt})
        label = response.json()["label"]
        score = response.json()["score"]
        return label, score

    def detect_PI(
        self,
        prompt: str,
        score_weighted_threshold: float = 0.7,
        score_combined_threshold: float = 0.7,
        *,
        use_chunk: bool | None = None,
    ) -> dict:
        # Xử lý prompt trước khi detect: tách sentences và join lại
        processed_prompt = process_input(prompt)
        run_async = self.use_chunk if use_chunk is None else use_chunk

        if run_async:
            return self._detect_with_chunks(
                processed_prompt,
                score_weighted_threshold,
                score_combined_threshold,
            )

        try:
            model_label, model_score = self.model_detect_PI(processed_prompt)
            vector_label, vector_score = self.vector_search_detect_PI(processed_prompt)
            return self._build_detection_dict(
                model_label,
                model_score,
                vector_label,
                vector_score,
                score_weighted_threshold,
                score_combined_threshold,
            )
        except Exception as exc:
            result = self._empty_detection()
            result["error"] = str(exc)
            return result

    def _detect_with_chunks(
        self,
        prompt: str,
        score_weighted_threshold: float,
        score_combined_threshold: float,
    ) -> dict:
        chunks = chunk_by_words(prompt, self.chunk_size, self.chunk_overlap)
        if not chunks:
            result = self._empty_detection()
            result["details"]["chunks_checked"] = 0
            return result

        effective_concurrency = len(chunks) if self.max_concurrency <= 0 else min(self.max_concurrency, len(chunks))

        return asyncio.run(
            self._detect_chunks_async(
                chunks,
                score_weighted_threshold,
                score_combined_threshold,
                effective_concurrency,
                len(chunks),
            )
        )

    def _build_detection_dict(
        self,
        model_label: str,
        model_score: float,
        vector_label: str,
        vector_score: float,
        score_weighted_threshold: float,
        score_combined_threshold: float,
    ) -> dict:
        is_model_malicious = model_label == "injection"
        is_vector_malicious = vector_label == "injection"

        model_weight = 1.5 if model_score >= score_weighted_threshold else 1.0
        vector_weight = 1.5 if vector_score >= score_weighted_threshold else 1.0

        model_score_injection = (
            model_score if is_model_malicious else (1 - model_score)
        )
        vector_score_injection = (
            vector_score if is_vector_malicious else (1 - vector_score)
        )

        model_contribute = model_weight * model_score_injection
        vector_contribute = vector_weight * vector_score_injection

        total_weight = model_weight + vector_weight
        combined_score = (model_contribute + vector_contribute) / total_weight
        
        is_injection = combined_score >= score_combined_threshold

        return {
            "is_injection": is_injection,
            "details": {
                "model_label": model_label,
                "model_score": model_score,
                "vector_label": vector_label,
                "vector_score": vector_score,
                "combined_score": combined_score,
                "score_combined_threshold": score_combined_threshold,
                "score_weighted_threshold": score_weighted_threshold,
                "model_weight": model_weight,
                "vector_weight": vector_weight,
                "total_weight": total_weight,
            },
        }

    def _empty_detection(self) -> dict:
        return {
            "is_injection": False,
            "details": {
                "model_label": None,
                "model_score": 0,
                "vector_label": None,
                "vector_score": 0,
                "combined_score": 0,
                "model_weight": 0,
                "vector_weight": 0,
                "total_weight": 0,
            },
        }

    async def _detect_chunks_async(
        self,
        chunks: List[str],
        score_weighted_threshold: float,
        score_combined_threshold: float,
        max_concurrency: int,
        total_chunks: int,
    ) -> dict:
        semaphore = asyncio.Semaphore(max_concurrency)

        async with aiohttp.ClientSession() as session:
            tasks = [
                asyncio.create_task(
                    self._detect_single_chunk_async(
                        semaphore,
                        session,
                        chunk_text,
                        index,
                        score_weighted_threshold,
                        score_combined_threshold,
                    )
                )
                for index, chunk_text in enumerate(chunks, start=1)
            ]
            best_detection = None
            try:
                for task in asyncio.as_completed(tasks):
                    index, detection = await task
                    if detection.get("is_injection"):
                        detection.setdefault("details", {})["chunk_index"] = index
                        detection["details"]["chunk_text"] = chunks[index - 1]
                        detection["details"]["total_chunks"] = total_chunks
                        for pending in tasks:
                            if pending is not task and not pending.done():
                                pending.cancel()
                        
                        return detection
                    
                    if "details" in detection:
                        if (
                            best_detection is None
                            or detection["details"].get("combined_score", 0)
                            > best_detection["details"].get("combined_score", 0)
                        ):
                            best_detection = detection
                            best_detection.setdefault("details", {})["chunk_index"] = index
                            best_detection["details"]["chunk_text"] = chunks[index - 1]

            finally:
                for task in tasks:
                    if task.cancelled():
                        with suppress(asyncio.CancelledError):
                            await task

        if best_detection:
            best_detection["details"]["chunks_checked"] = total_chunks
            best_detection["details"]["total_chunks"] = total_chunks
            return best_detection

        result = self._empty_detection()
        result["details"]["chunks_checked"] = total_chunks
        result["details"]["total_chunks"] = total_chunks
        return result

    async def _detect_single_chunk_async(
        self,
        semaphore: asyncio.Semaphore,
        session: aiohttp.ClientSession,
        chunk_text: str,
        index: int,
        score_weighted_threshold: float,
        score_combined_threshold: float,
    ) -> Tuple[int, dict]:
        async with semaphore:
            try:
                model_data, vector_data = await asyncio.gather(
                    self._post_json_async(
                        session, self.ENDPOINT_MODEL_PREDICT, {"text": chunk_text}
                    ),
                    self._post_json_async(
                        session, self.ENDPOINT_VECTOR_SEARCH, {"text": chunk_text}
                    ),
                )

                detection = self._build_detection_dict(
                    model_data["label"],
                    model_data["score"],
                    vector_data["label"],
                    vector_data["score"],
                    score_weighted_threshold,
                    score_combined_threshold,
                )

                return index, detection
            except Exception as exc:
                print(f"{type(exc).__name__}: {exc}")

    async def _post_json_async(
        self, session: aiohttp.ClientSession, url: str, payload: dict
    ) -> dict:
        async with session.post(url, json=payload, timeout=30) as response:
            response.raise_for_status()
            return await response.json()
