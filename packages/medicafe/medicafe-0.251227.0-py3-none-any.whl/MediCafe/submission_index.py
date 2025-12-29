"""
submission_index.py - Centralized submission index scaffolding (Phase 3)

Purpose:
- Provide a shared, efficient index of successful claim submissions (and optionally attempts)
- Avoid repeated scanning of historical receipt files across apps (MediLink, MediBot)
- Enable fast deconfliction, window validation, and reporting

Design:
- Backed by a compact JSONL file in receipts_root (one JSON record per line)
- Claim key: (patient_id, payer_id or primary_insurance, date_of_service, service_hash)
- Fields: claim_key, patient_id, payer_id, primary_insurance, dos, endpoint, submitted_at,
          receipt_file, status, checksum, notes, duplicate_override

This is an incremental implementation with JSONL; SQLite can be added later if needed.
"""
import os
import json
import time

META_FILENAME = 'submission_index_meta.json'
INDEX_FILENAME = 'submission_index.jsonl'
LOCK_FILENAME = 'submission_index.lock'

# New: ack field keys for richer timeline entries
ACK_FIELDS = ['ack_type', 'ack_timestamp', 'control_ids', 'source', 'file_name']


def build_initial_index(receipts_root, lookback_days=200):
    """
    Initial index builder for legacy receipts.
    NOTE: Legacy receipts do not include patient_id in the printed table, so we cannot
    reliably backfill claim-level keys from historical receipts. This builder will:
    - Create index/meta files if missing
    - Record meta stats
    - Return 0 (no historical claim entries)
    """
    if not os.path.isdir(receipts_root):
        return 0
    _ensure_files_exist(receipts_root)
    count, max_mtime = _get_receipt_stats(receipts_root)
    meta = _read_meta(receipts_root)
    meta['last_indexed_mtime'] = max_mtime
    meta['last_indexed_count'] = count
    meta['last_full_build_at'] = time.time()
    meta['rebuild_state'] = 'none'
    meta['rebuild_progress'] = 0
    _write_meta(receipts_root, meta)
    return 0


def append_submission_record(receipts_root, record):
    """
    Append a new successful submission record to the index after a claim is submitted.
    """
    try:
        _ensure_files_exist(receipts_root)
        line = json.dumps(record)
        path = _index_path(receipts_root)
        with open(path, 'a') as f:
            f.write(line)
            f.write("\n")
    except Exception:
        pass


def find_by_claim_key(receipts_root, claim_key):
    """
    Look up a claim by its stable key to detect potential duplicates.
    Returns the first matching record or None.
    """
    try:
        path = _index_path(receipts_root)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if isinstance(entry, dict) and entry.get('claim_key') == claim_key:
                        return entry
                except Exception:
                    continue
    except Exception:
        return None
    return None


def reconcile_recent_receipts(receipts_root, since_timestamp, max_seconds):
    """
    Incrementally scan receipts newer than 'since_timestamp' and update meta only.
    JSONL index is built at submission time; this reconcile only updates meta counters.
    Returns number of new files detected.
    """
    start = time.time()
    count = 0
    try:
        for root, dirs, files in os.walk(receipts_root):
            for name in files:
                try:
                    _ = name.encode('ascii')
                except Exception:
                    continue
                try:
                    mtime = os.path.getmtime(os.path.join(root, name))
                    if mtime > since_timestamp:
                        count += 1
                except Exception:
                    continue
                if int(time.time() - start) >= int(max_seconds):
                    return count
    except Exception:
        return count
    return count


def compute_claim_key(patient_id, payer_id, primary_insurance, date_of_service, service_hash):
    """
    Compute a deterministic claim key for deconfliction.
    """
    return "|".join([
        (patient_id or ""),
        (payer_id or primary_insurance or ""),
        (date_of_service or ""),
        (service_hash or "")
    ])


def append_ack_event(receipts_root, claim_key, status_text, ack_type, file_name, control_ids, source, ack_timestamp=None):
    """
    Append a lightweight ack/timeline event to the index. XP/Py3.4/ASCII-safe.
    - claim_key may be empty if unknown. Caller should pass when available.
    - control_ids is a dict with optional ISA/GS/ST/TRN or transactionId.
    """
    try:
        _ensure_files_exist(receipts_root)
        event = {
            'claim_key': claim_key or '',
            'patient_id': '',
            'payer_id': '',
            'primary_insurance': '',
            'dos': '',
            'endpoint': source or 'download_ack',
            'submitted_at': '',
            'receipt_file': file_name or '',
            'status': status_text or '',
            'notes': 'ack event',
        }
        # Attach ack fields with basic validation
        try:
            event['ack_type'] = ack_type or ''
            event['ack_timestamp'] = ack_timestamp or int(time.time())
            event['control_ids'] = control_ids or {}
            event['source'] = source or ''
            event['file_name'] = file_name or ''
        except Exception:
            pass
        path = _index_path(receipts_root)
        line = json.dumps(event)
        f = open(path, 'a')
        try:
            f.write(line)
            f.write("\n")
        finally:
            f.close()
    except Exception:
        pass


# ------------------------- ASCII-safe meta/lock helpers -----------------------

def _meta_path(root_dir):
    return os.path.join(root_dir, META_FILENAME)


def _index_path(root_dir):
    return os.path.join(root_dir, INDEX_FILENAME)


def _lock_path(root_dir):
    return os.path.join(root_dir, LOCK_FILENAME)


def _ensure_files_exist(root_dir):
    try:
        meta_path = _meta_path(root_dir)
        if not os.path.exists(meta_path):
            _write_meta(root_dir, {
                'last_indexed_mtime': 0.0,
                'last_indexed_count': 0,
                'last_full_build_at': 0.0,
                'rebuild_state': 'none',
                'rebuild_progress': 0
            })
        index_path = _index_path(root_dir)
        if not os.path.exists(index_path):
            with open(index_path, 'w') as f:
                f.write("")
    except Exception:
        pass


def _read_meta(root_dir):
    path = _meta_path(root_dir)
    if not os.path.exists(path):
        return {
            'last_indexed_mtime': 0.0,
            'last_indexed_count': 0,
            'last_full_build_at': 0.0,
            'rebuild_state': 'none',  # 'none' | 'pending' | 'in_progress'
            'rebuild_progress': 0
        }
    try:
        with open(path, 'r') as f:
            data = f.read()
            try:
                meta = json.loads(data)
            except Exception:
                return {
                    'last_indexed_mtime': 0.0,
                    'last_indexed_count': 0,
                    'last_full_build_at': 0.0,
                    'rebuild_state': 'none',
                    'rebuild_progress': 0
                }
            return meta if isinstance(meta, dict) else {}
    except Exception:
        return {
            'last_indexed_mtime': 0.0,
            'last_indexed_count': 0,
            'last_full_build_at': 0.0,
            'rebuild_state': 'none',
            'rebuild_progress': 0
        }


def _write_meta(root_dir, meta):
    try:
        with open(_meta_path(root_dir), 'w') as f:
            f.write(json.dumps(meta))
    except Exception:
        pass


def _try_acquire_lock(root_dir):
    lock = _lock_path(root_dir)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return True
    except Exception:
        return False


def _release_lock(root_dir):
    try:
        os.remove(_lock_path(root_dir))
    except Exception:
        pass


def _get_receipt_stats(receipts_root):
    count = 0
    max_mtime = 0.0
    try:
        for root, dirs, files in os.walk(receipts_root):
            for name in files:
                try:
                    _ = name.encode('ascii')
                except Exception:
                    continue
                count += 1
                try:
                    mtime = os.path.getmtime(os.path.join(root, name))
                    if mtime > max_mtime:
                        max_mtime = mtime
                except Exception:
                    continue
    except Exception:
        pass
    return count, max_mtime


# ------------------------- Public entry point --------------------------------

def ensure_submission_index(receipts_root, lookback_days=200, large_growth_threshold=0.1, max_inline_seconds=2):
    """
    XP/ASCII-safe, inline-only upkeep for the submission index.
    - No background tasks
    - Bounded work per call
    - Chunked rebuild across boots
    """
    if not receipts_root or not os.path.isdir(receipts_root):
        return

    # Ensure files exist early
    _ensure_files_exist(receipts_root)

    if not _try_acquire_lock(receipts_root):
        return

    try:
        meta = _read_meta(receipts_root)
        current_count, current_max_mtime = _get_receipt_stats(receipts_root)

        if meta.get('last_indexed_mtime', 0.0) == 0.0 and meta.get('last_indexed_count', 0) == 0:
            # First-time or corrupt meta: do bounded initial build
            build_initial_index(receipts_root, lookback_days)
            return

        # Incremental reconcile if new files detected by mtime
        if current_max_mtime > meta.get('last_indexed_mtime', 0.0):
            added = reconcile_recent_receipts(receipts_root, meta.get('last_indexed_mtime', 0.0), max_inline_seconds)
            meta['last_indexed_mtime'] = current_max_mtime
            meta['last_indexed_count'] = meta.get('last_indexed_count', 0) + int(added)
            _write_meta(receipts_root, meta)
            return

        # Large growth heuristic -> schedule chunked rebuild (across boots)
        last_count = meta.get('last_indexed_count', 0)
        delta = current_count - last_count
        if delta > 0 and delta >= max(100, int(large_growth_threshold * (last_count or 1))):
            if meta.get('rebuild_state') == 'none':
                meta['rebuild_state'] = 'pending'
                meta['rebuild_progress'] = 0
                _write_meta(receipts_root, meta)
            return

        # If rebuild pending, we would process a chunk here in a future implementation
        return
    finally:
        _release_lock(receipts_root)