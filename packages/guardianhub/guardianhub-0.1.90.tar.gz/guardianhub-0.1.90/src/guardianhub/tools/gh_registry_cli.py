# guardianhub_sdk/tools/gh_registry_cli.py
import argparse
import json
import os
import sys
import tempfile
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

import httpx

from ..models.registry.signing import generate_rsa_keypair, sign_metadata_dict
from guardianhub import get_logger

logger = get_logger(__name__)

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def pack_directory_to_zip(src: Path, dest: Path) -> None:
    """
    Create a zip artifact containing the src directory contents.
    This is a lightweight 'wheel-like' artifact (not a proper wheel) but suitable
    for the registry loader that accepts zipped source.
    """
    import zipfile
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        base = src.resolve()
        for p in sorted(src.rglob("*")):
            arcname = p.relative_to(base)
            zf.write(p, arcname)


def pack_module_to_archive(source_path: Path, artifact_path: Path) -> None:
    """
    If source_path is a .py file -> zip it; if directory -> zip contents; if tar/wheel requested, you can extend.
    """
    if source_path.is_file() and source_path.suffix == ".py":
        # create zip with single file at top-level
        import zipfile
        with zipfile.ZipFile(artifact_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(source_path, source_path.name)
    elif source_path.is_dir():
        pack_directory_to_zip(source_path, artifact_path)
    else:
        raise ValueError("Unsupported source path for packing: %s" % source_path)


def create_metadata(name: str, version: str, artifact_filename: str, sha256: str, module: Optional[str] = None, class_name: Optional[str] = None) -> Dict[str, Any]:
    meta = {
        "name": name,
        "version": version,
        "artifact_filename": artifact_filename,
        "sha256": sha256,
    }
    if module:
        meta["module"] = module
    if class_name:
        meta["class"] = class_name
    return meta


def upload_artifact(registry_base: str, artifact_path: Path, metadata_signed: Dict[str, Any], api_key: Optional[str] = None) -> httpx.Response:
    """
    POST artifact and metadata to registry. Assumes registry has an endpoint:
       POST {registry_base}/models/{name}/{version}/upload
    which accepts multipart/form-data:
       - file -> artifact
       - metadata -> metadata json
    """
    name = metadata_signed["name"]
    version = metadata_signed["version"]
    url = registry_base.rstrip("/") + f"/models/{name}/{version}/upload"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    with open(artifact_path, "rb") as af:
        files = {
            "file": (artifact_path.name, af, "application/octet-stream"),
            "metadata": (None, json.dumps(metadata_signed), "application/json"),
        }
        resp = httpx.post(url, files=files, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp


def cli_pack_sign_publish(args):
    src = Path(args.source).resolve()
    if not src.exists():
        logger.error("Source path does not exist: %s", src)
        sys.exit(2)

    tmpdir = Path(tempfile.mkdtemp(prefix="gh_pack_"))
    try:
        artifact_name = f"{args.name}-{args.version}.zip"
        artifact_path = tmpdir / artifact_name
        pack_module_to_archive(src, artifact_path)
        sha256 = compute_sha256(artifact_path)
        logger.info("Packed artifact at %s (sha256=%s)", artifact_path, sha256)

        # load/generate signing key
        if args.private_key:
            private_key_path = Path(args.private_key)
            private_pem = private_key_path.read_bytes()
        else:
            # generate ephemeral keys (not recommended for production)
            private_pem, public_pem = generate_rsa_keypair()
            logger.warning("Generated ephemeral RSA keypair (use persistent KMS key in prod)")
        metadata = create_metadata(args.name, args.version, artifact_name, sha256, module=args.module, class_name=args.class_name)
        metadata_signed = sign_metadata_dict(private_pem, metadata)

        if args.registry:
            resp = upload_artifact(args.registry, artifact_path, metadata_signed, api_key=args.api_key)
            logger.info("Upload response: %s", resp.text)
        else:
            # local output: write artifact + metadata
            out_dir = Path(args.out_dir or ".").resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            final_artifact = out_dir / artifact_name
            shutil.copy(str(artifact_path), str(final_artifact))
            meta_file = out_dir / f"{args.name}-{args.version}.metadata.json"
            meta_file.write_text(json.dumps(metadata_signed, indent=2))
            logger.info("Wrote artifact %s and metadata %s", final_artifact, meta_file)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gh-registry-cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pack = sub.add_parser("publish", help="Pack, sign and publish artifact")
    pack.add_argument("--source", required=True, help="Path to module file (.py) or package directory")
    pack.add_argument("--name", required=True, help="Model logical name")
    pack.add_argument("--version", required=True, help="Model version (semver recommended)")
    pack.add_argument("--module", required=False, help="Module path inside artifact (optional)")
    pack.add_argument("--class-name", dest="class_name", required=False, help="Class name exported (optional)")
    pack.add_argument("--private-key", required=False, help="Path to private PEM to sign metadata (optional). If absent, ephemeral key is generated (unsafe).")
    pack.add_argument("--registry", required=False, help="Registry base url to upload to. If omitted, write to --out-dir")
    pack.add_argument("--api-key", required=False, help="Registry API key")
    pack.add_argument("--out-dir", required=False, help="Local output directory when --registry omitted")

    genkey = sub.add_parser("gen-keys", help="Generate RSA keypair for signing")
    genkey.add_argument("--out-private", required=True)
    genkey.add_argument("--out-public", required=True)
    genkey.add_argument("--bits", type=int, default=4096)

    args = parser.parse_args(argv)

    if args.cmd == "publish":
        cli_pack_sign_publish(args)
    elif args.cmd == "gen-keys":
        priv, pub = generate_rsa_keypair(bits=args.bits)
        Path(args.out_private).write_bytes(priv)
        Path(args.out_public).write_bytes(pub)
        logger.info("Wrote keypair to %s / %s", args.out_private, args.out_public)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
