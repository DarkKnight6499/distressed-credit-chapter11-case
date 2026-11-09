"""Optional network acquisition, isolated from the offline library."""

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Configuration
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data/case_inputs.json"
OUTPUT_DIRECTORY = ROOT / "data/raw"
MANIFEST_PATH = ROOT / "data/fetch_manifest.json"
USER_AGENT = os.environ.get("SEC_USER_AGENT", "")
TIMEOUT_SECONDS = 30
HOST_DELAY_SECONDS = 0.5
ALLOWED_PREFIX = "https://www.sec.gov/Archives/edgar/data/1592058/"


def main():
    if "@" not in USER_AGENT:
        raise SystemExit("Set SEC_USER_AGENT to an identifying name and contact email.")
    case = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    manifest = {"started_utc": datetime.now(timezone.utc).isoformat(), "sources": [],
                "note": "Raw acquisition only. Does not replace the reviewed extracted snapshot."}
    failed = False
    for identifier, source in case["sources"].items():
        url = source["url"]
        if not url.startswith(ALLOWED_PREFIX):
            raise ValueError("Source URL outside the permitted issuer EDGAR directory")
        entry = {"source_id": identifier, "url": url, "document": source["document"],
                 "retrieved_utc": datetime.now(timezone.utc).isoformat()}
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                body = response.read()
                content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower() or len(body) < 500:
                raise ValueError("Unexpected filing response; inspect manually")
            prefix = body[:4000].lower()
            if b"undeclared automated tool" in prefix or b"request rate threshold exceeded" in prefix:
                raise ValueError("SEC block page, not a filing")
            filename = f"{identifier}.html"
            (OUTPUT_DIRECTORY / filename).write_bytes(body)
            entry.update(status="downloaded", path=f"raw/{filename}", sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
        except (HTTPError, URLError, OSError, ValueError) as error:
            entry.update(status="failed", reason=str(error))
            failed = True
        manifest["sources"].append(entry)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if failed:
            break
        time.sleep(HOST_DELAY_SECONDS)
    if failed:
        raise SystemExit("Source fetch stopped after failure. See data/fetch_manifest.json.")


if __name__ == "__main__":
    main()
