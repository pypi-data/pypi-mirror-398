# xspawn

Governance-only spawn and adoption tooling for Xaether2.

`xspawn` allows humans to:
- generate XKO spawn-kit petitions
- hash and bundle requests
- adopt newborn xitadels into a Prime Xitadel root

This tool performs **no motion, execution, or runtime control**.
All outputs are inert, auditable artifacts.

## Usage

```bash
xspawn petition --out ~/rook/petitions --domain rook
xspawn adopt --zip newborn.zip --receipt birth.delivery.zip.v1.json --target ~/rook/xaether
license MIT
