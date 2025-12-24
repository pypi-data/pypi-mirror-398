import argparse
from .petition import cmd_petition
from .adopt import cmd_adopt

def main(argv=None):
    p = argparse.ArgumentParser(prog="xspawn", description="Xaether2 xspawn tools (governance-only).")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_pet = sub.add_parser("petition", help="Create + hash + zip a spawn-kit petition bundle.")
    p_pet.add_argument("--out", required=True, help="Output directory (e.g., ~/rook/petitions)")
    p_pet.add_argument("--domain", default="", help="Intended domain (optional; may be blank)")
    p_pet.add_argument("--request-id", default="", help="Request id override")
    p_pet.set_defaults(fn=cmd_petition)

    p_adopt = sub.add_parser("adopt", help="Adopt a newborn zip into a Prime Xitadel root.")
    p_adopt.add_argument("--zip", required=True, help="Path to newborn.zip")
    p_adopt.add_argument("--receipt", required=True, help="Path to birth.delivery.zip.v1.json")
    p_adopt.add_argument("--target", required=True, help="Target xaether root (e.g., ~/rook/xaether)")
    p_adopt.add_argument("--domain", default="", help="Explicit domain override (human-supplied)")
    p_adopt.add_argument("--force-domain", action="store_true", help="Allow overriding receipt domain if it conflicts")
    p_adopt.add_argument("--force", action="store_true", help="Allow overwrite if target is non-empty")
    p_adopt.set_defaults(fn=cmd_adopt)

    args = p.parse_args(argv)
    return args.fn(args)

if __name__ == "__main__":
    raise SystemExit(main())
