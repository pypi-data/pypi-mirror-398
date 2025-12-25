# guardianhub_sdk/models/registry/signing.py
from pathlib import Path
from typing import Tuple, Dict, Any
import base64
import json

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256


def generate_rsa_keypair(bits: int = 4096) -> Tuple[bytes, bytes]:
    """
    Generate RSA keypair (private_pem, public_pem).
    In production use: KMS or offline secure key generation.
    """
    key = RSA.generate(bits)
    private_pem = key.export_key(format="PEM")
    public_pem = key.publickey().export_key(format="PEM")
    return private_pem, public_pem


def sign_bytes(private_pem: bytes, payload: bytes) -> str:
    """
    Sign arbitrary bytes with RSA-SHA256, return base64 signature string.
    """
    key = RSA.import_key(private_pem)
    h = SHA256.new(payload)
    signature = pkcs1_15.new(key).sign(h)
    return base64.b64encode(signature).decode("ascii")


def verify_bytes(public_pem: bytes, payload: bytes, signature_b64: str) -> bool:
    """
    Verify a base64 signature over payload bytes using public key.
    """
    key = RSA.import_key(public_pem)
    h = SHA256.new(payload)
    signature = base64.b64decode(signature_b64.encode("ascii"))
    try:
        pkcs1_15.new(key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False


def sign_metadata_dict(private_pem: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach a signature to the metadata dict and return augmented metadata.
    Uses canonical JSON encoding (sorted keys, no whitespace).
    """
    payload = json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = sign_bytes(private_pem, payload)
    metadata_signed = dict(metadata)
    metadata_signed["_signature"] = sig
    return metadata_signed


def verify_metadata_dict(public_pem: bytes, metadata_signed: Dict[str, Any]) -> bool:
    """
    Verify `_signature` in metadata_signed.
    Returns True if valid, False otherwise.
    """
    sig = metadata_signed.get("_signature")
    if not sig:
        return False
    md = dict(metadata_signed)
    md.pop("_signature", None)
    payload = json.dumps(md, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return verify_bytes(public_pem, payload, sig)
