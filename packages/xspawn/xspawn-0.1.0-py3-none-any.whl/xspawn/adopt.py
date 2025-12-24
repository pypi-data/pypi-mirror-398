import json, os, hashlib, time, zipfile
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def cmd_adopt(args):
    zpath = Path(os.path.expanduser(args.zip)).resolve()
    rpath = Path(os.path.expanduser(args.receipt)).resolve()
    target = Path(os.path.expanduser(args.target)).resolve()

    if not zpath.is_file():
        raise SystemExit(f"[ERR] zip not found: {zpath}")
    if not rpath.is_file():
        raise SystemExit(f"[ERR] receipt not found: {rpath}")

    receipt = json.loads(rpath.read_text(encoding="utf-8"))
    expected = receipt.get("zip", {}).get("sha256") or receipt.get("sha256") or ""
    if not expected or len(expected) != 64:
        raise SystemExit("[ERR] could not parse expected sha256 from receipt")

    actual = sha256_file(zpath)
    print("[INFO] expected sha256:", expected)
    print("[INFO] actual   sha256:", actual)
    if expected != actual:
        raise SystemExit("[ERR] sha256 mismatch; refusing to adopt")

    receipt_domain = receipt.get("domain") or receipt.get("intended_domain") or ""
    override_domain = (args.domain or "").strip()

    if override_domain and receipt_domain and override_domain != receipt_domain and not args.force_domain:
        raise SystemExit(
            "[ERR] domain conflict:\n"
            f"  receipt: {receipt_domain}\n"
            f"  --domain: {override_domain}\n"
            "Refusing. Re-run with --force-domain to override explicitly."
        )

    domain = override_domain or receipt_domain
    if not domain:
        raise SystemExit("[ERR] no domain provided. Supply --domain <name> (no default dominion).")

    # Overwrite guard
    if target.exists():
        if any(target.iterdir()) and not args.force:
            raise SystemExit(f"[ERR] target not empty: {target} (use --force to overwrite)")
    target.mkdir(parents=True, exist_ok=True)

    # Unzip (inert bundle only)
    with zipfile.ZipFile(zpath, "r") as z:
        z.extractall(target)

    # Mark as Prime
    (target / "HEAD").write_text(
        "type: prime_xitadel\n"
        f"domain: {domain}\n"
        "role: governing_root\n"
        "created_by: xko.delivery.zip\n"
        f"adopted_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n",
        encoding="utf-8"
    )

    (target / "receipts").mkdir(exist_ok=True)
    (target / "receipts" / "birth.delivery.zip.v1.json").write_text(
        rpath.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    print("[OK] adopted into:", target)
    print("[OK] HEAD:", target / "HEAD")
    return 0
