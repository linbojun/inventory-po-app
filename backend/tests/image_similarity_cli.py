#!/usr/bin/env python3
"""
Utility script to compare two image files using the project's similarity rules.

Example:
    python backend/tests/image_similarity_cli.py path/to/a.png path/to/b.png
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

# Ensure `app.*` imports work when the script is run from the repo root.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import settings
from app.image_similarity import (  # noqa: E402  (import after sys.path tweak)
    compute_phash,
    extract_orb_features,
    feature_similarity,
    hash_similarity,
)


@dataclass
class ImageMetrics:
    """Holds hash and feature data for an image."""

    path_display: str
    phash: Optional[str]
    descriptors: Optional[np.ndarray]


def _load_image_bytes(path_arg: str) -> bytes:
    """
    Load image bytes from a filesystem path or /static/<file> helper path.
    """
    candidate_path = Path(path_arg)
    if candidate_path.exists():
        return candidate_path.read_bytes()

    if path_arg.startswith("/static/"):
        filename = path_arg.replace("/static/", "", 1)
        static_path = Path(settings.image_dir) / filename
        if static_path.exists():
            return static_path.read_bytes()

    raise FileNotFoundError(
        f"Could not locate image '{path_arg}'. "
        "Use an absolute/relative path or /static/<filename>."
    )


def _compute_metrics(path_arg: str) -> ImageMetrics:
    """
    Convert an input path into perceptual hash and ORB descriptors.
    """
    try:
        image_bytes = _load_image_bytes(path_arg)
    except FileNotFoundError as exc:
        print(f"✗ {exc}")
        sys.exit(1)

    phash = compute_phash(image_bytes)
    descriptors = extract_orb_features(image_bytes)
    return ImageMetrics(path_display=path_arg, phash=phash, descriptors=descriptors)


def compare_images(
    first: str,
    second: str,
    *,
    hash_threshold: float,
    feature_ratio: float,
    min_feature_matches: int,
) -> bool:
    """
    Compare two images and print metrics. Returns True if they are considered the same.
    """
    first_metrics = _compute_metrics(first)
    second_metrics = _compute_metrics(second)

    phash_score = hash_similarity(first_metrics.phash, second_metrics.phash)
    feature_score = feature_similarity(
        first_metrics.descriptors,
        second_metrics.descriptors,
        feature_ratio,
    )

    hash_pass = phash_score >= hash_threshold
    orb_pass = feature_score >= float(min_feature_matches)
    is_same = hash_pass or orb_pass

    print("\nImage Similarity Check")
    print("======================")
    print(f"Image A: {first_metrics.path_display}")
    print(f"Image B: {second_metrics.path_display}\n")

    hash_status = "PASS" if hash_pass else "FAIL"
    print(
        f"pHash similarity: {phash_score:.4f} "
        f"(threshold {hash_threshold:.2f}) -> {hash_status}"
    )

    descriptor_a = (
        len(first_metrics.descriptors) if first_metrics.descriptors is not None else 0
    )
    descriptor_b = (
        len(second_metrics.descriptors) if second_metrics.descriptors is not None else 0
    )
    print(f"ORB keypoints (image A / image B): {descriptor_a} / {descriptor_b}")

    orb_status = "PASS" if orb_pass else "FAIL"
    print(
        f"Good matches: {feature_score:.0f} "
        f"(min {min_feature_matches}, ratio {feature_ratio:.2f}) -> {orb_status}"
    )

    print("\nResult: ", end="")
    if is_same:
        print("✓ Images are considered the SAME under current thresholds.")
    else:
        print("✗ Images are considered DIFFERENT under current thresholds.")

    return is_same


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare two images using the project's similarity configuration."
    )
    parser.add_argument("image_a", help="First image path (absolute, relative, or /static/<file>).")
    parser.add_argument("image_b", help="Second image path (absolute, relative, or /static/<file>).")
    parser.add_argument(
        "--hash-threshold",
        type=float,
        default=settings.image_similarity_threshold,
        help=f"Override perceptual hash similarity threshold (default {settings.image_similarity_threshold}).",
    )
    parser.add_argument(
        "--feature-ratio",
        type=float,
        default=settings.feature_match_ratio,
        help=f"Override ORB ratio test (default {settings.feature_match_ratio}).",
    )
    parser.add_argument(
        "--min-feature-matches",
        type=int,
        default=settings.feature_min_matches,
        help=f"Override minimum ORB matches (default {settings.feature_min_matches}).",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    is_same = compare_images(
        args.image_a,
        args.image_b,
        hash_threshold=args.hash_threshold,
        feature_ratio=args.feature_ratio,
        min_feature_matches=args.min_feature_matches,
    )
    sys.exit(0 if is_same else 1)


if __name__ == "__main__":
    main()
