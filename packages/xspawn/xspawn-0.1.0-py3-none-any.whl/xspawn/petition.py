import json, os, time, zipfile, hashlib
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def cmd_petition(args):
    out = Path(os.path.expanduser(args.out)).resolve()
    out.mkdir(parents=True, exist_ok=True)

    req_id = args.request_id or f"rook-spawn-{time.strftime('%Y%m%d')}-001"
    petition = {
        "type": "xko.spawn_kit.request",
        "version": "1.0",
        "request_id": req_id,
        "created_utc": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "intended_domain": args.domain or "",
        "domain_claim": "provisional",
        "requested_capabilities": {
            "spawn_newborn_xitadel": True,
            "deliver_inert_zip": True,
            "emit_delivery_receipt": True,
            "emit_genesis_ledger": True,
            "register_xkid_optional": True
        },
        "explicit_exclusions": {
            "motion_control": True,
            "runtime_execution": True,
            "remote_commanding": True,
            "implicit_authority": True
        },
        "governance_model": {
            "prime_xitadel_adoption_required": True,
            "human_in_the_loop": True,
            "revocable_authority": True
        }
    }

    jpath = out / "xko_spawn_kit_request.v1.json"
    jpath.write_text(json.dumps(petition, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    digest = sha256_file(jpath)
    (out / "xko_spawn_kit_request.v1.sha256").write_text(f"{digest}  {jpath.name}\n", encoding="utf-8")

    zpath = out.parent / "rook_xko_spawn_kit_request_v1.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(jpath, arcname=f"petitions/{jpath.name}")
        z.write(out / "xko_spawn_kit_request.v1.sha256", arcname="petitions/xko_spawn_kit_request.v1.sha256")

    print("[OK] wrote:", jpath)
    print("[OK] wrote:", out / "xko_spawn_kit_request.v1.sha256")
    print("[OK] packaged:", zpath)
    return 0
