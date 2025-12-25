"""
FastDeDuplicater: CLI tool to find duplicate files using SHA1 (generic files) and
MobileNetV3 embeddings for images/videos (via decord frame sampling) with FAISS
for fast similarity search. Persists indexes/metadata for reruns.
"""
from __future__ import annotations

import argparse
import atexit
import hashlib
import multiprocessing
import os
import sqlite3
import threading
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple
from uuid import uuid4

import faiss
import numpy as np
import torch
from PIL import Image
from decord import VideoReader, cpu
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small
from tqdm import tqdm

# Types
Vector = np.ndarray

SUPPORTED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
SUPPORTED_VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".webm"}

# Default persistent state directory (overridable via env or CLI)
DEFAULT_STATE_DIR = Path(os.environ.get("FASTDEDUP_STATE", Path.home() / ".fastdedup"))

# Cache the model + preprocess per worker process to avoid reloading per file.
_MODEL_CACHE: dict[str, tuple[torch.nn.Module, torch.nn.Module]] = {}


def sha1_file(path: Path, buf_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            b = f.read(buf_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_model(device: torch.device) -> tuple[torch.nn.Module, torch.nn.Module]:
    key = str(device)
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]
    weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1
    model = mobilenet_v3_small(weights=weights)
    model.classifier = torch.nn.Identity()
    model.eval().to(device)
    preprocess = weights.transforms()
    _MODEL_CACHE[key] = (model, preprocess)
    return model, preprocess


def get_image_embedding(model: torch.nn.Module, preprocess, device: torch.device, path: Path) -> Vector:
    img = Image.open(path).convert("RGB")
    # Resize very large images to avoid OOM
    max_dim = 1024
    if max(img.width, img.height) > max_dim:
        scale = max_dim / max(img.width, img.height)
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size)
    with torch.no_grad():
        t = preprocess(img).unsqueeze(0).to(device)
        out = model(t).cpu().numpy()[0]
    return out.astype("float32")


def sample_video_frames(path: Path, num_frames: int) -> List[np.ndarray]:
    vr = VideoReader(str(path), ctx=cpu(0),num_threads=1)
    total = len(vr)
    if total == 0:
        return []
    if num_frames >= total:
        idxs = list(range(total))
    else:
        idxs = np.linspace(0, total - 1, num_frames, dtype=int).tolist()
    batch = vr.get_batch(idxs).asnumpy()
    return [frame for frame in batch]


def get_video_embedding(model: torch.nn.Module, preprocess, device: torch.device, path: Path, num_frames: int) -> Vector:
    frames = sample_video_frames(path, num_frames)
    if not frames:
        return np.zeros(model.classifier.in_features if hasattr(model, "classifier") else 576, dtype="float32")
    with torch.no_grad():
        tensors = [preprocess(Image.fromarray(f)).to(device) for f in frames]
        batch = torch.stack(tensors, dim=0)
        out = model(batch)
        emb = out.mean(dim=0).cpu().numpy()
    return emb.astype("float32")


@dataclass
class FileRecord:
    path: str
    kind: str  # generic|image|video
    sha1: str | None
    embedding: Vector | None


class MetaDB:
    """SQLite-backed metadata + FAISS location store."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
              path TEXT PRIMARY KEY,
              kind TEXT NOT NULL,
              sha1 TEXT,
              embedding BLOB,
              dim INTEGER
            );
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_files_sha1_kind ON files(sha1, kind);")
        self._conn.commit()
        self._lock = threading.Lock()

    def upsert(self, rec: FileRecord):
        with self._lock:
            self._conn.execute(
                "REPLACE INTO files(path, kind, sha1, embedding, dim) VALUES (?,?,?,?,?)",
                (
                    rec.path,
                    rec.kind,
                    rec.sha1,
                    rec.embedding.tobytes() if rec.embedding is not None else None,
                    len(rec.embedding) if rec.embedding is not None else None,
                ),
            )
            self._conn.commit()

    def load_embeddings(self, kind: str) -> Tuple[List[str], np.ndarray]:
        cur = self._conn.execute(
            "SELECT path, embedding, dim FROM files WHERE kind=? AND embedding IS NOT NULL",
            (kind,),
        )
        paths: List[str] = []
        vecs: List[Vector] = []
        for p, blob, dim in cur.fetchall():
            if blob is None or dim is None:
                continue
            if not os.path.exists(p):
                continue  # exclude missing files from consideration
            arr = np.frombuffer(blob, dtype="float32")
            arr = arr.reshape(dim)
            paths.append(p)
            vecs.append(arr)
        if not vecs:
            return [], np.zeros((0, 0), dtype="float32")
        return paths, np.stack(vecs)

    def is_processed(self, path: Path, kind: str) -> bool:
        """Return True if the file already has the expected metadata persisted."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT kind, sha1, embedding FROM files WHERE path=?",
                (str(path),),
            )
            row = cur.fetchone()
        if row is None:
            return False
        existing_kind, sha1, embedding = row
        if kind == "generic":
            return sha1 is not None
        return existing_kind == kind and sha1 is not None and embedding is not None

    def has_sha1(self, kind: str, sha1: str) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "SELECT 1 FROM files WHERE sha1=? AND kind=? LIMIT 1",
                (sha1, kind),
            )
            return cur.fetchone() is not None

    def paths_for_sha1(self, kind: str, sha1: str, allowed_roots: List[Path] | None = None) -> List[str]:
        """Return existing paths of the given kind that share this SHA1, optionally limited to allowed roots."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT path FROM files WHERE sha1=? AND kind=?",
                (sha1, kind),
            )
            paths = [row[0] for row in cur.fetchall() if os.path.exists(row[0])]
        if allowed_roots is None:
            return paths
        return [p for p in paths if _is_under(Path(p), allowed_roots)]

    def sha1_groups(self, kinds: tuple[str, ...]) -> dict[tuple[str, str], List[str]]:
        placeholders = ",".join(["?"] * len(kinds))
        with self._lock:
            cur = self._conn.execute(
                f"SELECT sha1, kind, path FROM files WHERE sha1 IS NOT NULL AND kind IN ({placeholders})",
                kinds,
            )
            rows = cur.fetchall()
        groups: dict[tuple[str, str], List[str]] = {}
        for sha1, kind, path in rows:
            key = (sha1, kind)
            groups.setdefault(key, []).append(path)
        return groups

    def close(self):
        """Flush and close the underlying connection."""
        with self._lock:
            if getattr(self, "_conn", None) is None:
                return
            try:
                self._conn.commit()
            finally:
                self._conn.close()
                self._conn = None

    def get_record(self, path: Path) -> FileRecord | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT path, kind, sha1, embedding, dim FROM files WHERE path=?",
                (str(path),),
            )
            row = cur.fetchone()
        if row is None:
            return None
        p, kind, sha1, blob, dim = row
        emb = None
        if blob is not None and dim is not None:
            arr = np.frombuffer(blob, dtype="float32")
            emb = arr.reshape(dim)
        return FileRecord(p, kind, sha1, emb)

    def delete_path(self, path: Path):
        with self._lock:
            self._conn.execute("DELETE FROM files WHERE path=?", (str(path),))
            self._conn.commit()

    def clone_record(self, source: Path, target: Path):
        rec = self.get_record(source)
        if rec is None:
            return
        self.upsert(FileRecord(str(target), rec.kind, rec.sha1, rec.embedding))


class FaissStore:
    def __init__(self, dim: int):
        self.index = faiss.IndexFlatL2(dim)

    def add(self, vecs: np.ndarray):
        if vecs.size == 0:
            return
        self.index.add(vecs)

    def search(self, vecs: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        return self.index.search(vecs, k)

    def save(self, path: Path):
        faiss.write_index(self.index, str(path))

    @classmethod
    def load(cls, path: Path):
        index = faiss.read_index(str(path))
        obj = cls(index.d)
        obj.index = index
        return obj


def is_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_IMAGE_EXT


def is_video(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_VIDEO_EXT


def decide_kind(path: Path) -> str:
    if is_image(path):
        return "image"
    if is_video(path):
        return "video"
    return "generic"


def process_file(path: Path, num_frames: int, device: torch.device, sha1: str | None = None) -> FileRecord:
    kind = decide_kind(path)
    model = preprocess = None
    if kind in {"image", "video"}:
        model, preprocess = load_model(device)
    if sha1 is None:
        sha1 = sha1_file(path)
    embedding = None
    if kind == "image" and model is not None and preprocess is not None:
        embedding = get_image_embedding(model, preprocess, device, path)
    elif kind == "video" and model is not None and preprocess is not None:
        embedding = get_video_embedding(model, preprocess, device, path, num_frames)
    return FileRecord(str(path), kind, sha1, embedding)


def walk_files(folders: List[Path]) -> Iterable[Path]:
    for folder in folders:
        for root, dirs, files in os.walk(folder, followlinks=False):
            # Skip symlinked directories to avoid traversing external trees
            dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
            for name in files:
                path = Path(root) / name
                if os.path.exists(path) and not path.is_symlink():
                    yield path


def build_indexes(db: MetaDB, allowed_roots: List[Path]) -> Tuple[FaissStore, FaissStore, List[str], List[str]]:
    img_paths, img_vecs = db.load_embeddings("image")
    vid_paths, vid_vecs = db.load_embeddings("video")

    def _filter(paths: List[str], vecs: np.ndarray, base_dim: int) -> Tuple[List[str], np.ndarray]:
        keep_idx = [i for i, p in enumerate(paths) if _is_under(Path(p), allowed_roots)]
        if not keep_idx:
            return [], np.zeros((0, base_dim), dtype="float32")
        return [paths[i] for i in keep_idx], vecs[keep_idx, :]

    img_dim = img_vecs.shape[1] if img_vecs.size else 576
    vid_dim = vid_vecs.shape[1] if vid_vecs.size else 576
    img_paths, img_vecs = _filter(img_paths, img_vecs, img_dim)
    vid_paths, vid_vecs = _filter(vid_paths, vid_vecs, vid_dim)

    img_index = FaissStore(img_dim)
    vid_index = FaissStore(vid_dim)
    img_index.add(img_vecs)
    vid_index.add(vid_vecs)
    return img_index, vid_index, img_paths, vid_paths


def find_duplicates(index: FaissStore, kind: str, paths: List[str], vecs: np.ndarray, k: int, threshold: float) -> List[Tuple[str, str, str, float]]:
    if vecs.size == 0:
        return []

    # Stage 1: cheap top-1 (really top-2 including self) search to find candidates
    k_full = min(k, getattr(index, "index", index).ntotal if hasattr(index, "index") else k)
    if k_full <= 1:
        return []
    initial_k = min(2, k_full)

    print("Performing initial FAISS search for nearest neighbor to filter candidates. This may take a while...")
    D_first, I_first = index.search(vecs, initial_k)

    candidate_idxs: List[int] = []
    for q_idx, (dists, ids) in enumerate(zip(D_first, I_first)):
        # Look at the closest non-self neighbor; only keep if within threshold
        for dist, idx in zip(dists[1:], ids[1:]):
            if idx < 0 or dist > threshold or dist < 1e-10:
                continue
            candidate_idxs.append(q_idx)
            break

    if not candidate_idxs:
        return []

    # Stage 2: full-k search only on the candidates
    print(f"Refining {len(candidate_idxs)} candidate(s) with full k={k_full} search...")
    candidate_vecs = vecs[candidate_idxs]
    D_full, I_full = index.search(candidate_vecs, k_full)

    dupes: List[Tuple[str, str, str, float]] = []
    tbar = tqdm(enumerate(zip(D_full, I_full)), total=len(candidate_idxs), desc=f"Found {len(dupes)} duplicates")
    for local_idx, (dists, ids) in tbar:
        q_idx = candidate_idxs[local_idx]
        src = paths[q_idx]
        for dist, idx in zip(dists[1:], ids[1:]):
            if idx < 0 or dist > threshold or dist < 1e-10:
                continue
            dupes.append((kind, src, paths[idx], float(dist)))
            tbar.set_description(f"Found {len(dupes)} duplicates")
    return dupes


def _render_video_frame(path: Path) -> Image.Image | None:
    try:
        vr = VideoReader(str(path), ctx=cpu(0))
        if len(vr) == 0:
            return None
        frame = vr.get_batch([0]).asnumpy()[0]
        return Image.fromarray(frame)
    except Exception:
        return None


def show_side_by_side(kind: str, path_a: str, path_b: str, num_frames: int = 8):
    def grid_from_frames(frames: List[np.ndarray]) -> Image.Image | None:
        if not frames:
            return None
        target_h = 160
        pil_frames = []
        for f in frames:
            try:
                img = Image.fromarray(f).convert("RGB")
                img = img.resize((img.width * target_h // max(1, img.height), target_h))
                pil_frames.append(img)
            except Exception:
                continue
        if not pil_frames:
            return None
        cols = min(3, len(pil_frames))
        rows = (len(pil_frames) + cols - 1) // cols
        cell_w = max(img.width for img in pil_frames)
        cell_h = max(img.height for img in pil_frames)
        grid = Image.new("RGB", (cell_w * cols, cell_h * rows))
        for idx, img in enumerate(pil_frames):
            r, c = divmod(idx, cols)
            grid.paste(img, (c * cell_w, r * cell_h))
        return grid

    left = right = None
    if kind == "image":
        try:
            left = Image.open(path_a).convert("RGB")
            right = Image.open(path_b).convert("RGB")
        except Exception:
            return
    elif kind == "video":
        try:
            frames_a = sample_video_frames(Path(path_a), num_frames)
            frames_b = sample_video_frames(Path(path_b), num_frames)
            left = grid_from_frames(frames_a)
            right = grid_from_frames(frames_b)
        except Exception:
            return
    if left is None or right is None:
        return
    h = max(left.height, right.height)
    new_left = left.resize((left.width * h // max(1, left.height), h))
    new_right = right.resize((right.width * h // max(1, right.height), h))
    canvas = Image.new("RGB", (new_left.width + new_right.width, h))
    canvas.paste(new_left, (0, 0))
    canvas.paste(new_right, (new_left.width, 0))
    canvas.show(title="Duplicate Preview")


def handle_duplicates(dupes: List[Tuple[str, str, str, float]], mode: str, show: bool, num_frames: int, db: MetaDB):
    potential_saved = 0
    actual_saved = 0
    inactive: set[str] = set()
    group_count = count_duplicate_groups(dupes)

    def sync_duplicate_record(kept: str, dup: str):
        kept_path = Path(kept)
        dup_path = Path(dup)
        source = resolve_canonical(kept_path)
        # Prefer canonical record; fallback to original if missing
        rec = db.get_record(source)
        if rec is None:
            rec = db.get_record(kept_path)
        if rec is None:
            return
        db.upsert(FileRecord(str(dup_path), rec.kind, rec.sha1, rec.embedding))

    with tqdm(total=len(dupes), desc="Handling duplicates", unit="dupe") as pbar:
        for kind, a, b, dist in dupes:
            a_canon = resolve_canonical(Path(a))
            b_path = Path(b)
            b_canon = resolve_canonical(b_path)
            if any(p in inactive for p in {str(a_canon), str(Path(a)), str(b_canon), str(b_path)}):
                pbar.update(1)
                continue

            try:
                size_a = os.path.getsize(a)
            except OSError:
                size_a = 0
            try:
                size_b = os.path.getsize(b)
            except OSError:
                size_b = 0

            # Always keep the larger file to avoid losing quality when linking
            kept_path, kept_canon, kept_size = Path(a), a_canon, size_a
            dup_path, dup_canon, dup_size = b_path, b_canon, size_b
            if size_b > size_a:
                kept_path, kept_canon, kept_size, dup_path, dup_canon, dup_size = (
                    b_path,
                    b_canon,
                    size_b,
                    Path(a),
                    a_canon,
                    size_a,
                )

            potential_saved += dup_size

            success = False
            if mode == "report":
                success = True  # Treat as handled for inactive bookkeeping
                sync_duplicate_record(str(kept_path), str(dup_path))
            elif mode == "delete":
                try:
                    os.remove(dup_path)
                    db.delete_path(dup_path)
                    success = True
                except OSError as e:
                    tqdm.write(f"Failed to delete {dup_path}: {e}")
            elif mode in {"hardlink", "symlink"}:
                target = kept_canon if kept_canon.exists() else kept_path
                try:
                    if dup_path.exists() or dup_path.is_symlink():
                        os.remove(dup_path)
                    if mode == "hardlink":
                        os.link(target, dup_path)
                    else:
                        os.symlink(target, dup_path)
                    # Ensure metadata (sha1/embedding) is cloned to the new link
                    sync_duplicate_record(str(kept_path), str(dup_path))
                    success = True
                except OSError as e:
                    tqdm.write(f"Failed {mode} for {dup_path}: {e}")

            if success:
                inactive.update({str(dup_path), str(dup_canon)})
                actual_saved += dup_size if mode != "report" else 0

            if show and success and kind in {"image", "video"}:
                show_side_by_side(kind, str(kept_path), str(dup_path))

            pbar.set_postfix(saved=fmt_bytes(actual_saved), potential=fmt_bytes(potential_saved))
            pbar.update(1)

    tqdm.write(f"Duplicate groups handled: {group_count}")
    tqdm.write(f"Duplicate pairs checked: {len(dupes)}")
    tqdm.write(f"Potential space to save: {fmt_bytes(potential_saved)}")
    if mode != "report":
        tqdm.write(f"Space saved in mode '{mode}': {fmt_bytes(actual_saved)}")


def fmt_bytes(num: float) -> str:
    """Human-friendly byte formatter for progress reporting."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024 or unit == "TB":
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"


def show_welcome(db: MetaDB, folders: List[Path], state_dir: Path):
    """Print a large welcome/overview before scanning.

    Shows folders that will be scanned, quick on-disk counts by kind, database
    statistics (entries, per-kind counts, sha1/embedding availability), the
    number of SHA1 duplicate groups already known, and sizes of any existing
    FAISS index files.
    """
    print("\n" + "=" * 80)
    print("FastDeDuplicater".center(80))
    print("A tool to find and handle duplicate files using SHA1 and embeddings".center(80))
    print("=" * 80)

    # Folders
    print("Folders to scan:")
    for f in folders:
        status = "(exists)" if f.exists() else "(missing)"
        try:
            # Quick stat for readability
            cnt_preview = sum(1 for _ in f.rglob("*") if _.is_file()) if f.exists() else 0
        except Exception:
            cnt_preview = 0
        print(f"  - {f} {status} — ~{cnt_preview} files (preview)")

    print("\nCounting files on disk by kind (this may take a moment for large folders)...")
    disk_counts = {"image": 0, "video": 0, "generic": 0}
    disk_total = 0
    try:
        for p in walk_files(folders):
            disk_total += 1
            k = decide_kind(p)
            disk_counts[k] += 1
    except Exception as e:
        print(f"  Failed walking folders: {e}")

    print(f"  Total files found: {disk_total}")
    print(f"    Images: {disk_counts['image']}")
    print(f"    Videos: {disk_counts['video']}")
    print(f"    Generic: {disk_counts['generic']}")

    # Database stats
    print("\nDatabase (dedup.sqlite) summary:")
    try:
        cur = db._conn.execute("SELECT COUNT(*) FROM files")
        total_db = cur.fetchone()[0]
    except Exception:
        total_db = 0
    print(f"  Total DB entries: {total_db}")

    for kind in ("image", "video", "generic"):
        try:
            cur = db._conn.execute("SELECT COUNT(*) FROM files WHERE kind=?", (kind,))
            n = cur.fetchone()[0]
        except Exception:
            n = 0
        print(f"    {kind.capitalize()}: {n}")

    # Embedding counts
    for kind in ("image", "video"):
        try:
            paths, vecs = db.load_embeddings(kind)
            emb_count = len(paths)
        except Exception:
            emb_count = 0
        print(f"    {kind.capitalize()} embeddings persisted: {emb_count}")

    # SHA1 duplicate groups
    try:
        groups = db.sha1_groups(("image", "video", "generic"))
        dup_groups = sum(1 for v in groups.values() if len(v) > 1)
    except Exception:
        dup_groups = 0
    print(f"  SHA1 duplicate groups known: {dup_groups}")

    # FAISS index files
    print("\nFAISS index files:")
    for fname in (state_dir / "faiss_images.index", state_dir / "faiss_videos.index"):
        if fname.exists():
            try:
                size = os.path.getsize(fname)
                print(f"  {fname.name}: present in {state_dir} ({fmt_bytes(size)})")
            except Exception:
                print(f"  {fname.name}: present in {state_dir} (size unknown)")
        else:
            print(f"  {fname.name}: not present (expected in {state_dir})")

    print("\nMode and behavior")
    print("  - Default duplicate handling mode: report (use --mode to change)")
    print("  - Images and videos will have embeddings extracted (if supported by system)")
    print("  - Generic files use SHA1 for exact dedup detection")
    print("  - Images/videos check BOTH SHA1 (exact) and embeddings (similarity)")
    print("  - Symlinked files/directories are skipped to avoid external targets")
    print("  - Ctrl+C/SIGTERM will stop workers and flush the DB before exit")

    print("=" * 80 + "\n")


def resolve_canonical(path: Path) -> Path:
    """Resolve symlinks to the ultimate target; fallback to absolute path."""
    try:
        return path.resolve(strict=True)
    except Exception:
        try:
            return path.resolve()
        except Exception:
            return path.absolute()


def count_duplicate_groups(dupes: List[Tuple[str, str, str, float]]) -> int:
    """Count connected components of duplicate relationships (duplicate groups)."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for _, a, b, _ in dupes:
        union(a, b)

    # Only count sets that have at least two members
    groups: dict[str, set[str]] = {}
    for node in parent:
        root = find(node)
        groups.setdefault(root, set()).add(node)
    return sum(1 for members in groups.values() if len(members) >= 2)


def _is_under(path: Path, roots: List[Path]) -> bool:
    for root in roots:
        try:
            if path.resolve().is_relative_to(root.resolve()):
                return True
        except Exception:
            try:
                if path.is_relative_to(root):
                    return True
            except Exception:
                continue
    return False


def default_state_dir() -> Path:
    return DEFAULT_STATE_DIR


def main():
    parser = argparse.ArgumentParser(description="FastDeDuplicater")
    parser.add_argument("folders", nargs="+", help="Folders to scan")
    parser.add_argument("--state-dir", type=Path, default=default_state_dir(), help="Persistent state directory for DB and indexes (default: ~/.fastdedup or FASTDEDUP_STATE)")
    parser.add_argument("--db", type=Path, default=None, help="Path to SQLite DB (overrides --state-dir default)")
    parser.add_argument("--frames", type=int, default=8, help="Frames per video")
    parser.add_argument("--k", type=int, default=10, help="Neighbors to search")
    parser.add_argument("--threshold", type=float, default=5.0, help="L2 threshold for duplicates")
    parser.add_argument("--mode", choices=["report", "delete", "hardlink", "symlink"], default="report")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--show", action="store_true", help="Display side-by-side preview for found duplicates")
    args = parser.parse_args()

    state_dir = args.state_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = args.db if args.db is not None else state_dir / "dedup.sqlite"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # CUDA with multiprocessing requires the spawn start method.
    if torch.cuda.is_available():
        multiprocessing.set_start_method("spawn", force=True)

    sha1_dupes: list[tuple[str, str, str, float]] = []
    db = MetaDB(db_path)
    atexit.register(db.close)

    stop_event = threading.Event()
    pool: ProcessPoolExecutor | None = None

    # def handle_sig(sig, frame):
    #     stop_event.set()
    #     tqdm.write("Stopping... flushing DB")
    #     if pool is not None:
    #         pool.shutdown(wait=False, cancel_futures=True)

    #signal.signal(signal.SIGINT, handle_sig)
    #signal.signal(signal.SIGTERM, handle_sig)

    folders = [Path(f) for f in args.folders]

    # Show the welcome / overview prior to scanning
    try:
        show_welcome(db, folders, state_dir)
    except Exception as e:
        print(f"Warning: failed to generate welcome overview: {e}")

    futures = {}
    pending_sha1: dict[str, List[Path]] = {}
    future_sha1: dict[object, str] = {}
    try:
        pool = ProcessPoolExecutor(max_workers=args.workers)
        for p in tqdm(walk_files(folders), desc="Scanning files and generating SHA1 hashes. This can take a while"):
            if stop_event.is_set():
                break
            kind = decide_kind(p)
            if db.is_processed(p, kind):
                continue
            sha1 = sha1_file(p)
            # Track exact duplicates by SHA1 regardless of kind
            existing_paths = db.paths_for_sha1(kind, sha1, folders)
            for other in existing_paths:
                if other == str(p):
                    continue
                sha1_dupes.append((kind, str(p), other, 0.0))

            if kind == "generic":
                # Generic files are SHA1-only
                db.upsert(FileRecord(str(p), kind, sha1, None))
                continue

            # Persist SHA1 immediately even if embedding computation is interrupted later
            #db.upsert(FileRecord(str(p), kind, sha1, None))

            # If we already have an embedding for this SHA1, reuse it instead of recomputing
            needs_embedding = True
            for other in existing_paths:
                if other == str(p):
                    continue
                rec = db.get_record(Path(other))
                if rec and rec.embedding is not None:
                    db.clone_record(Path(other), p)
                    needs_embedding = False
                    break

            # Only skip embedding if we successfully reused a non-empty embedding from another file
            if not needs_embedding:
                continue

            # If another file with the same SHA1 is already queued, defer and clone later
            if sha1 in pending_sha1:
                pending_sha1[sha1].append(p)
                continue

            # Images/videos always get embeddings, even if SHA1 already exists
            fut = pool.submit(process_file, p, args.frames, device, sha1)
            futures[fut] = p
            future_sha1[fut] = sha1
            pending_sha1.setdefault(sha1, [])

        pending = set(futures.keys())
        with tqdm(total=len(futures), desc="Processing files into DB") as pbar:
            while pending and not stop_event.is_set():
                done, pending = wait(pending, timeout=0.5, return_when=FIRST_COMPLETED)
                for fut in done:
                    try:
                        rec = fut.result()
                    except Exception as e:
                        print(f"Failed processing {futures[fut]}: {e}")
                        pbar.update(1)
                        continue
                    db.upsert(rec)
                    sha1 = future_sha1.get(fut)
                    if sha1:
                        # Clone embedding to any waiting paths for this SHA1
                        for wait_path in pending_sha1.get(sha1, []):
                            db.clone_record(Path(rec.path), wait_path)
                        pending_sha1.pop(sha1, None)
                        future_sha1.pop(fut, None)
                    pbar.update(1)
    except KeyboardInterrupt:
        stop_event.set()
        tqdm.write("Interrupted. Cancelling workers and flushing DB...")
    finally:
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)
        for fut in futures:
            fut.cancel()

    if stop_event.is_set():
        db.close()
        return

    img_index, vid_index, img_paths, vid_paths = build_indexes(db, folders)

    # Re-load embeddings for search
    _, img_vecs = db.load_embeddings("image")
    _, vid_vecs = db.load_embeddings("video")

    print("Searching for duplicates...")
    img_dupes = find_duplicates(img_index, "image", img_paths, img_vecs, args.k, args.threshold)
    vid_dupes = find_duplicates(vid_index, "video", vid_paths, vid_vecs, args.k, args.threshold)

    if stop_event.is_set():
        db.close()
        return

    print("Handling duplicates...")
    # Merge SHA1 and embedding-based duplicates, de-duplicating pairs
    merged = []
    seen_pairs: set[tuple[str, str]] = set()
    for kind, a, b, dist in sha1_dupes + img_dupes + vid_dupes:
        key = tuple(sorted((a, b)))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        merged.append((kind, a, b, dist))

    handle_duplicates(merged, args.mode, args.show, args.frames, db)

    # Save FAISS indexes
    img_index.save(state_dir / "faiss_images.index")
    vid_index.save(state_dir / "faiss_videos.index")

    # Ensure DB is flushed and closed at the very end
    db.close()


if __name__ == "__main__":
    main()
