"""
sprint3_milestone56.py
======================
Milestone 5 — Concurrency & High Performance
Milestone 6 — Research Innovation: Active Learning Integration

Authors  : Group 8 members
Dataset : fake_job_postings.csv  (Kaggle)
"""

# ─────────────────────────────────────────────
#  Standard Library
# ─────────────────────────────────────────────
import os
import re
import json
import time
import logging
import pickle
import asyncio
import threading
from typing import List, Callable, Iterable, Dict, Any, Generator, Tuple

# ─────────────────────────────────────────────
#  Concurrency
# ─────────────────────────────────────────────
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing

# ─────────────────────────────────────────────
#  Data / ML
# ─────────────────────────────────────────────
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# ═══════════════════════════════════════════════════════════════════
#  MILESTONE 4 (inherited) — Custom Exceptions
# ═══════════════════════════════════════════════════════════════════

class NLPError(Exception):
    """Base exception for the NLP system."""


class DataLoadError(NLPError):
    """Raised when data cannot be loaded or is incorrectly formatted."""


class ModelStateError(NLPError):
    """Raised when prediction is attempted on an untrained model."""


# ═══════════════════════════════════════════════════════════════════
#  MILESTONE 3 (inherited) — Core Data Structures
# ═══════════════════════════════════════════════════════════════════

class Document:
    """Immutable value-object for a single job posting."""

    __slots__ = ("text", "label", "doc_id")

    def __init__(self, text: str, label: int, doc_id: str = None):
        self.text   = text
        self.label  = label
        self.doc_id = doc_id


# ═══════════════════════════════════════════════════════════════════
#  MILESTONE 5 — Concurrent TextPreprocessor
# ═══════════════════════════════════════════════════════════════════

# Module-level function required by multiprocessing (must be picklable).
def _clean_text(text: str) -> str:
    """
    Pure function — no class state required.
    Runs in a separate OS process to bypass the GIL.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return " ".join(text.split())


class TextPreprocessor:
    """
    Strategy Pattern: encapsulates cleaning logic.

    Milestone 5 upgrade
    -------------------
    parallel_clean()  — fans out to N worker processes via ProcessPoolExecutor,
                        then fans back in, preserving document order.
    """

    def clean(self, text: str) -> str:
        """Single-document synchronous clean (kept for backwards compatibility)."""
        return _clean_text(text)

    def parallel_clean(
        self,
        texts: List[str],
        n_workers: int = None,
        chunk_size: int = 500,
    ) -> List[str]:
        """
        Parallel batch cleaning.

        Parameters
        ----------
        texts      : raw text strings to clean
        n_workers  : number of OS processes (defaults to CPU count - 1)
        chunk_size : documents submitted per task to reduce IPC overhead

        Why ProcessPoolExecutor and not ThreadPoolExecutor?
        ---------------------------------------------------
        Python's GIL serialises CPU-bound regex work inside threads.
        Spawning OS processes side-steps the GIL entirely, giving true
        parallelism for CPU-intensive regex workloads.
        """
        n_workers = n_workers or max(1, multiprocessing.cpu_count() - 1)

        # Partition into chunks to reduce inter-process communication (IPC) overhead
        chunks = [texts[i : i + chunk_size] for i in range(0, len(texts), chunk_size)]

        results: List[str] = [""] * len(texts)

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            # Submit chunks; track original slice so we can reassemble in order
            future_to_slice = {
                executor.submit(_clean_chunk, chunk): (i * chunk_size, (i + 1) * chunk_size)
                for i, chunk in enumerate(chunks)
            }
            for future in as_completed(future_to_slice):
                start, end = future_to_slice[future]
                results[start:end] = future.result()

        return results


def _clean_chunk(texts: List[str]) -> List[str]:
    """Helper: clean a list of texts. Must be module-level for pickling."""
    return [_clean_text(t) for t in texts]


# ═══════════════════════════════════════════════════════════════════
#  MILESTONE 5 — Thread-Safe NLPSystem
# ═══════════════════════════════════════════════════════════════════

class NLPSystem:
    """
    Milestone 5 upgrades
    --------------------
    1. Multiprocessing  — parallel_clean via ProcessPoolExecutor
    2. Async I/O        — load_data_async / save_system_state_async
    3. Thread safety    — RLock guards _is_trained and model state
    4. Benchmarking     — benchmark() class method
    """

    def __init__(self, C: float = 1.0, csv_path: str = None):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        )
        self.logger = logging.getLogger("NLPSystem")

        # ── Production-ready path resolution ──────────────────────
        # Priority: argument > env-var > current directory fallback
        self.csv_path = (
            csv_path
            or os.environ.get("NLP_DATASET_PATH")
            or os.path.join(os.getcwd(), "fake_job_postings.csv")
        )

        self.preprocessor = TextPreprocessor()
        self.vectorizer   = TfidfVectorizer(max_features=1000)
        self.model        = LogisticRegression(max_iter=1000, C=C)

        # ── Thread Safety ─────────────────────────────────────────
        # RLock (re-entrant) allows the same thread to acquire the lock
        # multiple times without deadlocking (useful when train() calls
        # internal helpers that also need the lock in future extensions).
        self._lock      = threading.RLock()
        self._is_trained = False

    # ── Functional generator pipeline (Milestone 3, preserved) ────

    def data_pipeline(
        self,
        docs: Iterable[Document],
        transform: Callable[[str], str],
    ) -> Generator[str, None, None]:
        """Lazy sequential pipeline — O(1) memory footprint."""
        for doc in docs:
            yield transform(doc.text)

    # ── Synchronous load (kept for benchmarking comparison) ───────

    def load_data(self, csv_path: str = None) -> List[Document]:
        """Synchronous CSV load with robust error handling."""
        path = csv_path or self.csv_path
        try:
            self.logger.info(f"[SYNC] Loading data from: {path}")
            df = pd.read_csv(path)
            df["text_content"] = df["title"].fillna("") + " " + df["description"].fillna("")
            return [
                Document(row["text_content"], row["fraudulent"], str(row["job_id"]))
                for _, row in df.iterrows()
            ]
        except FileNotFoundError:
            raise DataLoadError(f"File not found: '{path}'")
        except KeyError as e:
            raise DataLoadError(f"Missing expected column in CSV: {e}")
        except Exception as e:
            raise DataLoadError(f"Unexpected I/O error: {e}")

    # ── Async I/O ─────────────────────────────────────────────────

    async def load_data_async(self, csv_path: str = None) -> List[Document]:
        """
        Milestone 5 — Async I/O

        Offloads the blocking pandas read to a thread pool so the event
        loop remains free for other coroutines (e.g., serving HTTP
        prediction requests while loading a new dataset batch).

        In a real production system this would be replaced by an async
        database driver (e.g., asyncpg) or an async HTTP call to a data
        lake API.
        """
        path = csv_path or self.csv_path
        loop = asyncio.get_event_loop()

        self.logger.info(f"[ASYNC] Scheduling non-blocking load from: {path}")
        # run_in_executor prevents blocking the event loop with sync I/O
        documents = await loop.run_in_executor(None, self.load_data, path)
        self.logger.info(f"[ASYNC] Load complete — {len(documents)} documents.")
        return documents

    async def save_system_state_async(
        self, model_path: str, config_path: str
    ) -> None:
        """
        Milestone 5 — Async serialisation.

        Pickle writes to disk can take hundreds of milliseconds for large
        models. Offloading to a thread pool allows the server to keep
        accepting inference requests during a checkpoint save.
        """
        with self._lock:
            if not self._is_trained:
                raise ModelStateError("Cannot save an untrained system.")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._sync_save,
            model_path,
            config_path,
        )

    def _sync_save(self, model_path: str, config_path: str) -> None:
        """Internal blocking save — called from async wrapper."""
        with self._lock:
            with open(model_path, "wb") as f:
                pickle.dump((self.vectorizer, self.model), f)

            config = {
                "model_type": type(self.model).__name__,
                "C_parameter": self.model.C,
                "trained": self._is_trained,
                "vocab_size": len(self.vectorizer.vocabulary_),
            }
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)

        self.logger.info(f"[SAVE] Persisted → {model_path}, {config_path}")

    # Synchronous save (Milestone 4, kept for compatibility)
    def save_system_state(self, model_path: str, config_path: str) -> None:
        self._sync_save(model_path, config_path)

    # ── Training ──────────────────────────────────────────────────

    def train(self, train_docs: List[Document], parallel: bool = True) -> None:
        """
        Train with optional parallel preprocessing.

        Parameters
        ----------
        train_docs : documents to fit on
        parallel   : if True, uses ProcessPoolExecutor for cleaning phase
        """
        try:
            raw_texts = [doc.text for doc in train_docs]

            if parallel:
                self.logger.info("[TRAIN] Using parallel preprocessing.")
                processed_texts = self.preprocessor.parallel_clean(raw_texts)
            else:
                self.logger.info("[TRAIN] Using sequential preprocessing.")
                processed_texts = [self.preprocessor.clean(t) for t in raw_texts]

            labels = [doc.label for doc in train_docs]
            X = self.vectorizer.fit_transform(processed_texts)

            with self._lock:          # ← thread-safe state transition
                self.model.fit(X, labels)
                self._is_trained = True

            self.logger.info("[TRAIN] Completed successfully.")
        except Exception as e:
            self.logger.error(f"[TRAIN] Failed: {e}")
            raise

    # ── Inference ─────────────────────────────────────────────────

    def predict(self, docs: List[Document], parallel: bool = True) -> List[int]:
        """
        Thread-safe inference.

        The RLock ensures that if two threads call predict() simultaneously,
        neither reads a partially-updated _is_trained / model state.
        """
        with self._lock:
            if not self._is_trained:
                raise ModelStateError("Model must be trained before prediction.")
            # Snapshot references under the lock — safe to use outside it
            vectorizer = self.vectorizer
            model      = self.model

        raw_texts = [doc.text for doc in docs]
        processed = (
            self.preprocessor.parallel_clean(raw_texts)
            if parallel
            else [self.preprocessor.clean(t) for t in raw_texts]
        )
        X = vectorizer.transform(processed)
        return list(model.predict(X))

    def predict_proba(self, docs: List[Document]) -> np.ndarray:
        """Return class probabilities — required by Active Learning."""
        with self._lock:
            if not self._is_trained:
                raise ModelStateError("Model must be trained before prediction.")
            vectorizer = self.vectorizer
            model      = self.model

        processed = self.preprocessor.parallel_clean([d.text for d in docs])
        X = vectorizer.transform(processed)
        return model.predict_proba(X)

    # ── Benchmarking ──────────────────────────────────────────────

    @staticmethod
    def benchmark(
        documents: List[Document],
        n_runs: int = 3,
    ) -> Dict[str, float]:
        """
        Compare sequential vs parallel preprocessing wall-clock time.

        Returns a dict with mean times and speedup ratio.
        """
        preprocessor = TextPreprocessor()
        texts = [d.text for d in documents]

        # ── Sequential ────────────────────────────────────────────
        seq_times = []
        for _ in range(n_runs):
            t0 = time.perf_counter()
            _ = [preprocessor.clean(t) for t in texts]
            seq_times.append(time.perf_counter() - t0)

        # ── Parallel ──────────────────────────────────────────────
        par_times = []
        for _ in range(n_runs):
            t0 = time.perf_counter()
            _ = preprocessor.parallel_clean(texts)
            par_times.append(time.perf_counter() - t0)

        seq_mean = sum(seq_times) / n_runs
        par_mean = sum(par_times) / n_runs

        results = {
            "n_documents"      : len(documents),
            "n_runs"           : n_runs,
            "sequential_mean_s": round(seq_mean, 4),
            "parallel_mean_s"  : round(par_mean, 4),
            "speedup_ratio"    : round(seq_mean / par_mean, 2),
        }
        return results


# ═══════════════════════════════════════════════════════════════════
#  MILESTONE 6 — Active Learning Integration
# ═══════════════════════════════════════════════════════════════════

class ActiveLearner:
    """
    Uncertainty Sampling — Least Confidence Strategy.

    How it works
    ------------
    After each prediction batch the classifier outputs P(y=1|x) for
    every document.  Documents whose max class probability is CLOSEST
    to 0.5 are the ones the model is *least* confident about — i.e.,
    exactly on the decision boundary.  A human annotator reviewing
    those N documents provides the highest information gain per
    annotation dollar spent.

    The selected documents are appended to a review queue.  After
    human labelling, the system retrains on the augmented corpus,
    shifting the decision boundary in the right direction.

    Research motivation
    -------------------
    Settles (2009) "Active Learning Literature Survey" shows that
    active learning can achieve the same accuracy as passive learning
    with as few as 30 % of the labelled examples.  For rare-class
    detection (fraud is ≈5 % of postings) this is especially valuable
    because random sampling underrepresents the positive class.
    """

    def __init__(self, nlp_system: "NLPSystem", uncertainty_threshold: float = 0.35):
        """
        Parameters
        ----------
        nlp_system            : trained NLPSystem instance
        uncertainty_threshold : documents with max_prob < threshold are flagged
                                (default 0.35 → flagged when model is <65% confident)
        """
        self.system    = nlp_system
        self.threshold = uncertainty_threshold
        self.review_queue: List[Document] = []
        self.logger = logging.getLogger("ActiveLearner")

    def flag_uncertain(self, docs: List[Document]) -> Tuple[List[Document], List[Document]]:
        """
        Split docs into (confident, uncertain) buckets.

        Returns
        -------
        confident  : model prediction is reliable → can auto-label
        uncertain  : sent to human review queue
        """
        proba = self.system.predict_proba(docs)          # shape (N, 2)
        max_proba = proba.max(axis=1)                    # confidence per sample

        uncertain = [d for d, p in zip(docs, max_proba) if p < self.threshold]
        confident = [d for d, p in zip(docs, max_proba) if p >= self.threshold]

        self.review_queue.extend(uncertain)
        self.logger.info(
            f"[AL] Flagged {len(uncertain)}/{len(docs)} documents for review "
            f"(threshold={self.threshold})."
        )
        return confident, uncertain

    def retrain_with_feedback(
        self,
        human_labels: Dict[str, int],
        original_train: List[Document],
    ) -> None:
        """
        Incorporate human annotations and retrain.

        Parameters
        ----------
        human_labels  : mapping doc_id → corrected label
        original_train: the original training set to augment
        """
        newly_labelled = [
            Document(doc.text, human_labels[doc.doc_id], doc.doc_id)
            for doc in self.review_queue
            if doc.doc_id in human_labels
        ]

        augmented_corpus = original_train + newly_labelled
        self.logger.info(
            f"[AL] Retraining on {len(augmented_corpus)} docs "
            f"({len(newly_labelled)} newly labelled)."
        )
        self.system.train(augmented_corpus)
        self.review_queue.clear()      # reset queue after retrain

    def uncertainty_report(self) -> Dict[str, Any]:
        """Summary statistics on the current review queue."""
        return {
            "queued_for_review": len(self.review_queue),
            "doc_ids": [d.doc_id for d in self.review_queue[:10]],  # first 10
        }


# ═══════════════════════════════════════════════════════════════════
#  EXECUTION BLOCK
# ═══════════════════════════════════════════════════════════════════

async def main():
    print("=" * 60)
    print("  NLP Fraud Detection — Milestone 5 & 6")
    print("=" * 60)

    # ── Instantiate (path via env-var or argument) ─────────────────
    system = NLPSystem(C=1.0)   # reads NLP_DATASET_PATH env-var if set

    try:
        # ── 1. Async data load ─────────────────────────────────────
        print("\n[1/5] Loading data asynchronously …")
        documents = await system.load_data_async()
        print(f"      Loaded {len(documents)} documents.")

        train_data, test_data = train_test_split(
            documents, test_size=0.2, random_state=42
        )

        # ── 2. Parallel training ───────────────────────────────────
        print("\n[2/5] Training with parallel preprocessing …")
        system.train(train_data, parallel=True)

        # ── 3. Evaluation ──────────────────────────────────────────
        print("\n[3/5] Evaluating …")
        predictions = system.predict(test_data, parallel=True)
        true_labels = [d.label for d in test_data]
        print(classification_report(true_labels, predictions, target_names=["Legit", "Fraud"]))

        # ── 4. Active Learning demo ────────────────────────────────
        print("\n[4/5] Active Learning — flagging uncertain predictions …")
        learner = ActiveLearner(system, uncertainty_threshold=0.35)
        confident_docs, uncertain_docs = learner.flag_uncertain(test_data[:500])
        print(f"      Confident: {len(confident_docs)}  |  Uncertain (queued): {len(uncertain_docs)}")
        print("      Report:", json.dumps(learner.uncertainty_report(), indent=6))

        # ── 5. Async save ─────────────────────────────────────────
        print("\n[5/5] Saving system state asynchronously …")
        await system.save_system_state_async("nlp_model.pkl", "config.json")

        # ── 6. Benchmarking ───────────────────────────────────────
        print("\n[BENCHMARK] Comparing sequential vs parallel preprocessing …")
        bench = NLPSystem.benchmark(documents[:2000], n_runs=3)
        for k, v in bench.items():
            print(f"  {k:<25} {v}")

    except NLPError as e:
        print(f"\n[SYSTEM FAILURE] {e}")


if __name__ == "__main__":
    # Guard required for multiprocessing on Windows / macOS (spawn context)
    multiprocessing.freeze_support()
    asyncio.run(main())
