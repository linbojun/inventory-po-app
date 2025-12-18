from __future__ import annotations

from io import BytesIO
from typing import Dict, Optional, Tuple

import cv2
import imagehash
import numpy as np
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from app.database import settings
from app.models import Product
from app.storage import get_image_bytes

_orb_cache: Dict[str, Optional[np.ndarray]] = {}


def compute_phash(image_bytes: bytes) -> Optional[str]:
    """Compute perceptual hash for image bytes."""
    if not image_bytes:
        return None

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            normalized = ImageOps.exif_transpose(image)
            phash = imagehash.phash(normalized)
            return str(phash)
    except Exception:
        return None


def extract_orb_features(image_bytes: bytes) -> Optional[np.ndarray]:
    """Return ORB descriptors for feature comparison."""
    if not image_bytes:
        return None

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            normalized = ImageOps.exif_transpose(image)
            gray = np.array(normalized.convert("L"))
    except Exception:
        return None

    if gray.size == 0 or gray.shape[0] < 32 or gray.shape[1] < 32:
        return None

    orb = cv2.ORB_create(nfeatures=500)
    keypoints, descriptors = orb.detectAndCompute(gray, None)
    if descriptors is None or len(descriptors) == 0:
        return None
    return descriptors.astype(np.uint8, copy=False)


def hash_similarity(hash_a: Optional[str], hash_b: Optional[str]) -> float:
    """Return similarity ratio (0-1) between two perceptual hashes."""
    if not hash_a or not hash_b:
        return 0.0

    try:
        hash_obj_a = imagehash.hex_to_hash(hash_a)
        hash_obj_b = imagehash.hex_to_hash(hash_b)
    except Exception:
        return 0.0

    if hash_obj_a.hash.size == 0 or hash_obj_a.hash.size != hash_obj_b.hash.size:
        return 0.0

    distance = hash_obj_a - hash_obj_b
    max_distance = hash_obj_a.hash.size
    similarity = 1.0 - (distance / max_distance)
    return max(0.0, min(1.0, similarity))


def feature_similarity(
    candidate_desc: Optional[np.ndarray],
    existing_desc: Optional[np.ndarray],
    ratio: float,
) -> float:
    """Compute feature-based similarity using Lowe's ratio test."""
    if candidate_desc is None or existing_desc is None:
        return 0.0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    try:
        matches = bf.knnMatch(candidate_desc, existing_desc, k=2)
    except cv2.error:
        return 0.0

    if not matches:
        return 0.0

    good = 0
    for pair in matches:
        if len(pair) < 2:
            continue
        m1, m2 = pair
        if m1.distance < ratio * m2.distance:
            good += 1
    return float(good)


def get_or_store_product_hash(db: Session, product: Product) -> Optional[str]:
    """Ensure a product has an image hash cached."""
    if not product.image_url:
        return None

    if product.image_hash:
        return product.image_hash

    image_bytes = get_image_bytes(product.image_url)
    if not image_bytes:
        return None

    phash = compute_phash(image_bytes)
    if phash:
        product.image_hash = phash
    return product.image_hash


def get_orb_descriptors(image_url: str) -> Optional[np.ndarray]:
    cache_key = str(image_url)
    if cache_key in _orb_cache:
        return _orb_cache[cache_key]

    image_bytes = get_image_bytes(image_url)
    if not image_bytes:
        _orb_cache[cache_key] = None
        return _orb_cache[cache_key]

    descriptors = extract_orb_features(image_bytes)
    _orb_cache[cache_key] = descriptors
    return descriptors


def find_best_image_match(
    db: Session,
    candidate_hash: Optional[str],
    candidate_descriptors: Optional[np.ndarray],
    exclude_product_id: Optional[int] = None,
) -> Tuple[Optional[Product], str, float]:
    """Find best matching product image using pHash or ORB features."""
    query = db.query(Product).filter(Product.image_url.isnot(None))
    if exclude_product_id is not None:
        query = query.filter(Product.id != exclude_product_id)

    candidate_desc = candidate_descriptors
    best_product: Optional[Product] = None
    best_score = 0.0
    best_method = "none"

    for product in query.all():
        # First check pHash similarity
        existing_hash = get_or_store_product_hash(db, product)
        hash_score = hash_similarity(candidate_hash, existing_hash)
        if hash_score >= settings.image_similarity_threshold and hash_score > best_score:
            best_score = hash_score
            best_product = product
            best_method = "hash"
            continue

        # Fallback to ORB-based matching
        existing_desc = get_orb_descriptors(product.image_url)
        if existing_desc is None:
            continue

        feature_score = feature_similarity(
            candidate_desc,
            existing_desc,
            settings.feature_match_ratio,
        )

        if feature_score >= settings.feature_min_matches and feature_score > best_score:
            best_score = feature_score
            best_product = product
            best_method = "orb"

    return best_product, best_method, best_score


def invalidate_orb_cache(image_url: Optional[str]):
    if not image_url:
        return
    _orb_cache.pop(str(image_url), None)
