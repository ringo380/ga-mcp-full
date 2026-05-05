#!/usr/bin/env bash
#
# record-oauth-demo.sh — captures the OAuth + scope-in-use demo video
# required by Google's OAuth consent-screen verification form.
#
# Google's video requirement for the analytics.edit scope:
#   "Provide a YouTube video demonstrating how you'll use the data from
#    these scopes in your app. Your video must include all OAuth
#    clients that you assigned to this project."
#
# This script stages a clean terminal with scripted narration, triggers
# the OAuth browser flow (user clicks Continue in the consent screen),
# then demonstrates a GA4 admin call that uses the scope. QuikGif
# records the whole thing; ffmpeg converts the GIF to MP4. Upload the
# MP4 to YouTube (unlisted is fine) and paste the URL into the
# Google Console Data Access form.
#
# Usage:
#   ./scripts/record-oauth-demo.sh
#
# Requires on $PATH:
#   ga-mcp-full, quikgif, ffmpeg, python3 (with the ga-mcp-full package)

set -euo pipefail

for tool in ga-mcp-full quikgif ffmpeg python3; do
  command -v "$tool" >/dev/null 2>&1 || { echo "error: $tool not on PATH" >&2; exit 1; }
done

if [ -z "${GA_DEMO_PROPERTY_ID:-}" ]; then
  cat >&2 <<'ERR'
error: GA_DEMO_PROPERTY_ID is not set.

The verification demo creates and immediately archives a throwaway
custom dimension to prove the analytics.edit scope is needed for write
operations (otherwise reviewers may insist on the readonly scope).

Set GA_DEMO_PROPERTY_ID to a GA4 property ID you own and can safely
write to, e.g.:

  export GA_DEMO_PROPERTY_ID=123456789
  ./scripts/record-oauth-demo.sh
ERR
  exit 1
fi

OUTPUT_DIR="${HOME}/Desktop"
STAMP=$(date +%Y%m%d-%H%M%S)
GIF_PATH="${OUTPUT_DIR}/ga-mcp-full-oauth-demo-${STAMP}.gif"
MP4_PATH="${OUTPUT_DIR}/ga-mcp-full-oauth-demo-${STAMP}.mp4"

cat <<'INTRO'

╭───────────────────────────────────────────────────────────────────╮
│  ga-mcp-full OAuth verification demo recorder                     │
╰───────────────────────────────────────────────────────────────────╯

This script will:
  1. Clear any cached ga-mcp-full OAuth credentials
  2. Start a QuikGif screen recording (full display, up to 60s)
  3. Run `ga-mcp-full auth login` — your browser will open
  4. PAUSE for you to click through Google's consent screen
  5. Show auth status and a read-only tool call that uses analytics.edit
  6. Stop recording, convert GIF → MP4

What Google wants to see in the finished video:
  • The "ga-mcp-full" OAuth client name in the consent screen
  • The analytics.edit scope being granted
  • The scope actually being used for a WRITE operation (this script
    creates + archives a throwaway custom dimension to prove the scope
    is minimal — analytics.readonly cannot do this)

Required env var:
  GA_DEMO_PROPERTY_ID — a GA4 property ID you own and can safely
                       create+archive a test custom dimension on.
                       Example:  export GA_DEMO_PROPERTY_ID=123456789

After the recording, upload the MP4 to YouTube (Unlisted is fine),
then paste the URL into the "YouTube link" field at:
  https://console.cloud.google.com/auth/scopes?project=ga-mcp-full-260416

Press Enter to begin (or Ctrl-C to cancel).
INTRO
read -r

# Step 1: clear creds so the OAuth browser flow triggers
if [ -f "${HOME}/.config/ga-mcp/credentials.json" ]; then
  echo ""
  echo "[prep] clearing cached credentials..."
  ga-mcp-full auth logout >/dev/null 2>&1 || true
fi

echo ""
echo "[prep] starting QuikGif recording (30s budget, full screen)..."
echo "[prep] recording will save to: ${GIF_PATH}"
echo ""

# Step 2: start QuikGif recording in background.
# --duration 60 gives headroom for the OAuth browser flow + a write
# operation (create + archive a custom dimension) so reviewers see the
# analytics.edit scope actually being used for writes, not just reads.
# --region is required — without it, quikgif
# hangs silently waiting for an interactive window picker.
# Detect screen size in logical points (macOS) for full-screen capture.
SCREEN_DIMS=$(osascript -e 'tell application "Finder" to get bounds of window of desktop' 2>/dev/null | awk -F', ' '{print $3 "," $4}')
SCREEN_W="${SCREEN_DIMS%,*}"
SCREEN_H="${SCREEN_DIMS#*,}"
: "${SCREEN_W:=1512}"
: "${SCREEN_H:=982}"
QG_LOG="${OUTPUT_DIR}/quikgif-${STAMP}.log"

quikgif record \
  --region "0,0,${SCREEN_W},${SCREEN_H}" \
  --duration 60 \
  --fps 24 \
  --output "${GIF_PATH}" \
  --show-cursor \
  >"${QG_LOG}" 2>&1 &
QUIKGIF_PID=$!

# Give QuikGif 2 seconds to initialize before the narration starts
sleep 2

# Step 3: the narrated demo
clear
cat <<'DEMO'
╭──────────────────────────────────────────────────────────╮
│  ga-mcp-full · OAuth + analytics.edit scope demo         │
╰──────────────────────────────────────────────────────────╯

DEMO
sleep 1

echo "$ ga-mcp-full auth login"
sleep 1

# This blocks until the user completes the OAuth browser flow.
# Google's consent screen will be visible on-screen during this pause.
ga-mcp-full auth login

echo ""
sleep 1
echo "$ ga-mcp-full auth status"
ga-mcp-full auth status
echo ""
sleep 2

echo "$ # tool call: WRITE operation that requires analytics.edit"
echo "$ # (analytics.readonly cannot do this — proves the scope is minimal)"
echo "$ python3 -c 'create_custom_dimension(...) ; archive_custom_dimension(...)'"
sleep 1

if [ -z "${GA_DEMO_PROPERTY_ID:-}" ]; then
  echo ""
  echo "[error] GA_DEMO_PROPERTY_ID not set." >&2
  echo "[error] Set it to a GA4 property ID you own + can safely write to," >&2
  echo "[error] e.g.  export GA_DEMO_PROPERTY_ID=123456789" >&2
  echo "[error] The script creates and immediately archives a throwaway" >&2
  echo "[error] custom dimension named 'oauth_verify_demo' on that property." >&2
  kill -INT "$QUIKGIF_PID" 2>/dev/null || true
  exit 3
fi

GA_DEMO_PROPERTY_ID="${GA_DEMO_PROPERTY_ID}" python3 - <<'PY' 2>&1 | head -20
import asyncio
import os
from ga_mcp.tools.admin.custom_definitions import (
    create_custom_dimension,
    archive_custom_dimension,
)

PROPERTY_ID = os.environ["GA_DEMO_PROPERTY_ID"]
PARAM = "oauth_verify_demo"

async def main():
    print(f"  [write 1/2] create_custom_dimension on property {PROPERTY_ID}...")
    created = await create_custom_dimension(
        property_id=PROPERTY_ID,
        parameter_name=PARAM,
        display_name="OAuth verify demo",
        scope="EVENT",
        description="Throwaway dimension created during OAuth verification demo.",
    )
    resource_name = created["name"]
    dim_id = resource_name.split("/")[-1]
    print(f"  [ok]        created: {resource_name}")

    print(f"  [write 2/2] archive_custom_dimension to clean up...")
    await archive_custom_dimension(
        property_id=PROPERTY_ID,
        custom_dimension_id=dim_id,
    )
    print(f"  [ok]        archived: {resource_name}")
    print(f"\n  [scope: analytics.edit · 1 dimension created + archived]")
    print(f"  [analytics.readonly CANNOT perform either of these calls]")

asyncio.run(main())
PY

echo ""
echo "$ # analytics.edit is the minimum scope that supports the admin write API"
sleep 2

# Step 4: stop recording. SIGINT (not SIGTERM) lets QuikGif flush the
# encoder and write the GIF cleanly. --duration may have already stopped
# it; in that case kill is a no-op.
echo ""
echo "[done] stopping recording..."
kill -INT "$QUIKGIF_PID" 2>/dev/null || true
wait "$QUIKGIF_PID" 2>/dev/null || true

# Give QuikGif a moment to finalize the file
sleep 2

if [ ! -f "${GIF_PATH}" ]; then
  echo "[error] recording file not found at ${GIF_PATH}" >&2
  echo "[error] quikgif log (${QG_LOG}):" >&2
  sed 's/^/  | /' "${QG_LOG}" >&2 2>/dev/null || echo "  (log missing)" >&2
  exit 2
fi

# Step 5: convert to MP4 for YouTube
echo "[post] converting GIF to MP4 (YouTube-friendly)..."
ffmpeg -loglevel error -y \
  -i "${GIF_PATH}" \
  -movflags +faststart \
  -pix_fmt yuv420p \
  -c:v libx264 -crf 20 -preset slow \
  "${MP4_PATH}"

gif_size=$(du -h "${GIF_PATH}" | awk '{print $1}')
mp4_size=$(du -h "${MP4_PATH}" | awk '{print $1}')

cat <<OUT

╭───────────────────────────────────────────────────────────────────╮
│  done                                                             │
╰───────────────────────────────────────────────────────────────────╯

Outputs:
  ${GIF_PATH}  (${gif_size})
  ${MP4_PATH}  (${mp4_size})

Next steps:
  1. Review the MP4 — verify the consent screen + scope are clearly
     visible. Re-run this script if anything is off.
  2. Upload the MP4 to YouTube as Unlisted:
       https://www.youtube.com/upload
  3. Paste the YouTube URL into the Data Access form's "YouTube link"
     field at:
       https://console.cloud.google.com/auth/scopes?project=ga-mcp-full-260416
     Save.
  4. Return to the Verification Center and click "Prepare for
     verification" → "Confirm" to submit.
OUT
