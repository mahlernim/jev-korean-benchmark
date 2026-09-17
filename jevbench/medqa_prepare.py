"""Freeze original-English, four-option MedQA test items without API calls."""
from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

import httpx

from .common import ROOT, SEED, digest, frozen, load_manifest, now, read, write_new

REPO = "GBaker/MedQA-USMLE-4-options"
REVISION = "0fb93dd23a7339b6dcd27e241cb9b5eca62d4d18"
FILENAME = "phrases_no_exclude_test.jsonl"
EXPERIMENT = "medqa-english-v3"
# Conservative screen for unavailable visual inputs, not ordinary descriptions
# of imaging findings. False positive exclusions remain inspectable.
MEDIA = re.compile(
    r"\b(?:figure|fig\.|image|photograph|micrograph|illustration|diagram|table)\s*(?:\d|[A-D]\b)|"
    r"\b(?:shown|depicted|pictured|illustrated)\s+(?:below|above|here|in)|"
    r"\b(?:following|accompanying|provided|attached)\s+(?:image|figure|photograph|micrograph|diagram|table)|"
    r"\b(?:image|figure|photograph|micrograph|diagram|table)\s+(?:below|above|shown|provided)|"
    r"\b(?:shown|photograph|photomicrograph|micrograph|picture|pedigree)\b|"
    r"\bsee\s+(?:the\s+)?(?:image|figure|diagram|table)\b|"
    r"!\[|<img\b", re.IGNORECASE)
MANUAL_EXCLUSIONS = {
    824: "unresolved_source_defect: stem asks a virus property while options name viruses",
    1230: "unresolved_source_defect: inconsistent temperature units",
    102: "unresolved_source_defect: question stem ends as incomplete continuation",
    635: "unresolved_source_defect: references unavailable laboratory reports, ECG and chest radiograph",
}


def validate_row(row):
    if not isinstance(row, dict):
        return "not_an_object"
    if not isinstance(row.get("question"), str) or not row["question"].strip():
        return "missing_question"
    options = row.get("options")
    if not isinstance(options, dict) or list(options) != ["A", "B", "C", "D"]:
        return "invalid_four_option_mapping"
    if any(not isinstance(v, str) or not v.strip() for v in options.values()):
        return "missing_option_text"
    if row.get("answer_idx") not in options or row.get("answer") != options[row["answer_idx"]]:
        return "gold_text_index_disagreement"
    match = MEDIA.search(row["question"] + "\n" + "\n".join(options.values()))
    if match:
        return "possible_unavailable_media:" + match.group(0)
    return None


def prepare(path=None):
    path = Path(path) if path else ROOT / "data" / EXPERIMENT
    if not (path / "manifest.json").exists() and (ROOT / "results" / EXPERIMENT / "source-manifest-index.json").exists():
        return restore_from_public(path)
    path.mkdir(parents=True, exist_ok=True)
    lock_path = path / "source-lock.json"
    raw_path = path / FILENAME
    if lock_path.exists():
        source = read(lock_path)
        url = source["download_url"]
    else:
        url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{FILENAME}"
        source = None
    if not raw_path.exists():
        previous_raw = ROOT / "data" / "medqa-english-v1" / FILENAME
        if previous_raw.exists():
            raw_path.write_bytes(previous_raw.read_bytes())
        else:
            response = httpx.get(url, follow_redirects=True, timeout=120)
            response.raise_for_status()
            raw_path.write_bytes(response.content)
    raw = raw_path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if source is None:
        source = dict(repository=REPO, revision=REVISION, filename=FILENAME,
            download_url=url, sha256=checksum, rows=len(rows), language="original English",
            split="test", variant="USMLE four options", retrieved_at=now(),
            primary_source="https://github.com/jind11/MedQA",
            paper="https://arxiv.org/abs/2009.13081",
            mirror_card=f"https://huggingface.co/datasets/{REPO}/blob/{REVISION}/README.md",
            provenance="Mirror card attributes Jin et al. Primary repository documents official random train/dev/test splits and a four-option US version. Mirror test file has 1,273 rows. Byte identity with the primary Google Drive archive has not been independently verified.",
            license="Mirror card declares CC-BY-4.0; primary code repository uses MIT. These declarations do not independently establish rights to all underlying examination text. Public artifacts therefore omit question and option text.")
        write_new(lock_path, source)
    if source["sha256"] != checksum or source["rows"] != len(rows):
        raise ValueError("Frozen MedQA source checksum or row count changed")
    manifest_path = path / "manifest.json"
    if manifest_path.exists():
        return load_manifest(manifest_path)
    eligible, exclusions, seen = [], [], set()
    for index, row in enumerate(rows):
        identifier = f"medqa-us-test-{index:04d}"
        reason = MANUAL_EXCLUSIONS.get(index) or validate_row(row)
        identity = digest({"question": row.get("question"), "options": row.get("options")})
        if identity in seen:
            reason = reason or "duplicate_question_options"
        seen.add(identity)
        if reason:
            exclusions.append(dict(case_id=identifier, row_index=index, reason=reason))
        else:
            eligible.append((index, row))
    previous_v2 = load_manifest(ROOT / "data" / "medqa-english-v2" / "manifest.json")
    previous_v1 = load_manifest(ROOT / "data" / "medqa-english-v1" / "manifest.json")
    prior_indices = {e["source_row_index"] for m in (previous_v1, previous_v2) for e in m["evaluations"]}
    replacement_pool = [(i, r) for i, r in eligible if i not in prior_indices]
    replacements = random.Random(SEED).sample(replacement_pool, 2)
    replacement_by_removed = dict(zip((102, 635), replacements))
    selected = [replacement_by_removed.get(e["source_row_index"], (e["source_row_index"], rows[e["source_row_index"]]))
                for e in previous_v2["evaluations"]]
    sampling = "Retain v2 item order and all 98 rows except source indices 102 and 635. Form replacement pool from v2 eligible rows in original source order, excluding all v1/v2 selected indices and all recorded blocking defects. random.Random(20260917).sample(pool,2) assigns draws in order to removed indices 102,635 in their original slots."
    evaluations, audit = [], []
    for index, row in selected:
        identifier = f"medqa-us-test-{index:04d}"
        request = dict(model="jev-latest", state={"question": row["question"]},
            questions={"answer": dict(type="choice", instructions="Select the single best answer to this medical examination question.", criteria=row["options"])})
        evaluations.append(dict(eval_id=identifier+"__en_en", case_id=identifier,
            stage=0, task="medqa", condition="en_en", kind="choice", gold=row["answer_idx"],
            review_status="public_gold", source_row_index=index, source_row_hash=digest(row),
            request=request, request_hash=digest(request)))
        audit.append(dict(case_id=identifier, source_row_index=index,
            question=row["question"], options=row["options"],
            purpose="Gold-blinded input-completeness review before inference"))
    previous_review_path = ROOT / "data" / "medqa-english-v1" / "input-review.json"
    previous_review = read(previous_review_path)
    v2_review_path = ROOT / "data" / "medqa-english-v2" / "input-review.json"
    v2_review = read(v2_review_path)
    manifest = dict(schema_version=1, experiment=EXPERIMENT, created_at=now(), seed=SEED,
        model="jev-latest", price_per_million_input_usd=0.042, budget_usd=0.25,
        concurrency_per_provider=4, sources={"medqa": source}, exclusions=exclusions,
        audit=dict(source_rows=len(rows), eligible_rows=len(eligible), excluded_rows=len(exclusions),
            selected_rows=100, sampling=sampling,
            media_screen=MEDIA.pattern, independent_input_review="pending",
            comparison_scope="Original English MedQA benchmark. Not matched to Korean licensing questions, so differences between datasets cannot isolate a language effect."),
        deviations=dict(rejected_experiment="medqa-english-v1", rejected_manifest_hash=previous_review["manifest_hash"],
            reason="Independent pre-inference review found missing-media references missed by the initial screen and two unresolved source defects. No scored API calls occurred for v1. The v1 files are preserved.",
            revised_screen="Expanded screening applied to all 1,273 source rows before resampling, plus two explicit source-defect exclusions. Conservative false positives can exclude text-complete items and cause selection bias.",
            prior_review_sha256=hashlib.sha256(previous_review_path.read_bytes()).hexdigest(),
            prior_review_flags=previous_review["flags"], manual_exclusions=MANUAL_EXCLUSIONS,
            v2_rejected_manifest_hash=previous_v2["sha256"],
            v2_review_sha256=hashlib.sha256(v2_review_path.read_bytes()).hexdigest(),
            v2_review_flags=v2_review["flags"],
            v3_reason="Gold-blinded input review found two unresolved defects in v2. Preserve 98 items and replace only these two before any scored API calls. Nonblocking original unit wording remains unchanged and is disclosed in review flags. This is AI-assisted completeness review, not clinician gold-label review.",
            replacement_rule=sampling, replacement_pool_size=len(replacement_pool),
            replacements=[dict(removed_row_index=i, replacement_row_index=r[0], replacement_case_id=f"medqa-us-test-{r[0]:04d}") for i,r in replacement_by_removed.items()]),
        evaluations=evaluations)
    manifest["sha256"] = digest(manifest)
    frozen(path / "exclusions.json", exclusions)
    frozen(path / "selected-input-audit.json", audit)
    frozen(path / "replacement-input-audit.json", [r for r in audit if r["source_row_index"] in {i for i,_ in replacements}])
    frozen(path / "selected-source-rows.json", [dict(row_index=i, source=row) for i,row in selected])
    write_new(manifest_path, manifest)
    return load_manifest(manifest_path)


def restore_from_public(path=None, public_path=None):
    """Rebuild exact frozen requests from metadata and a pinned public source."""
    path = Path(path) if path else ROOT / "data" / EXPERIMENT
    public_path = Path(public_path) if public_path else ROOT / "results" / EXPERIMENT
    index = read(public_path / "source-manifest-index.json")
    source = index["sources"]["medqa"]
    if index["experiment"] != EXPERIMENT:
        raise ValueError("Unexpected public experiment")
    path.mkdir(parents=True, exist_ok=True)
    # Never derive local paths from an unvalidated downloaded filename.
    if source["filename"] != FILENAME:
        raise ValueError("Unexpected MedQA source filename")
    raw_path = path / FILENAME
    if not raw_path.exists():
        cache = ROOT / "data" / EXPERIMENT / FILENAME
        if cache.exists() and cache.resolve() != raw_path.resolve():
            raw = cache.read_bytes()
        else:
            response = httpx.get(source["download_url"], follow_redirects=True, timeout=120)
            response.raise_for_status()
            raw = response.content
        if hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError("Public source checksum mismatch")
        with raw_path.open("xb") as stream:
            stream.write(raw)
    raw = raw_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != source["sha256"]:
        raise ValueError("Cached public source checksum mismatch")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if len(rows) != source["rows"]:
        raise ValueError("Public source row count mismatch")
    evaluations = []
    for entry in index["evaluations"]:
        row = rows[entry["source_row_index"]]
        if digest(row) != entry["source_row_hash"]:
            raise ValueError("Public source row hash mismatch")
        if row["answer_idx"] != entry["gold"] or row["options"].get(entry["gold"]) != row["answer"]:
            raise ValueError("Public gold mapping mismatch")
        request = dict(model=index["model"], state={"question": row["question"]},
            questions={"answer": dict(type="choice", instructions="Select the single best answer to this medical examination question.", criteria=row["options"])})
        if digest(request) != entry["request_hash"]:
            raise ValueError("Public request reconstruction mismatch")
        restored = {}
        for key, value in entry.items():
            if key == "request_hash":
                restored["request"] = request
            restored[key] = value
        evaluations.append(restored)
    manifest = {key: evaluations if key == "evaluations" else value for key, value in index.items()}
    expected = manifest["sha256"]
    if digest({k: v for k, v in manifest.items() if k != "sha256"}) != expected:
        raise ValueError("Reconstructed public manifest hash mismatch")
    frozen(path / "source-lock.json", source)
    frozen(path / "manifest.json", manifest)
    review_path = public_path / "input-review.json"
    if review_path.exists():
        review = read(review_path)
        if review.get("manifest_hash") != expected:
            raise ValueError("Public review manifest mismatch")
        frozen(path / "input-review.json", review)
    return load_manifest(path / "manifest.json")


if __name__ == "__main__":
    result = prepare()
    print(json.dumps({"experiment": result["experiment"], "sha256": result["sha256"],
        "audit": result["audit"]}, indent=2))
