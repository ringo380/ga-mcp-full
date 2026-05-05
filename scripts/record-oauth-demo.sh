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
# then demonstrates a GA4 admin WRITE call that uses the scope (creates
# and immediately archives a throwaway custom dimension to prove the
# analytics.edit scope is the minimum required — analytics.readonly
# cannot perform either call). ffmpeg records the screen directly to
# MP4 via macOS avfoundation. Upload the MP4 to YouTube (Unlisted is
# fine) and paste the URL into the Google Console Data Access form.
#
# Usage:
#   export GA_DEMO_PROPERTY_ID=<your GA4 property id>
#   ./scripts/record-oauth-demo.sh
#
# Requires on $PATH:
#   ga-mcp-full, ffmpeg (with avfoundation; the Homebrew build has it),
#   python3 (with the ga-mcp-full package installed)
#
# Why ffmpeg avfoundation instead of QuikGif: QuikGif's free tier caps
# recordings at 30s, which isn't enough for the OAuth browser flow plus
# the create+archive write demo. ffmpeg avfoundation has no such cap
# and ships with the existing dependency set.

set -euo pipefail

for tool in ga-mcp-full ffmpeg python3; do
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

# Detect the avfoundation device index for "Capture screen 0". Index
# differs per machine depending on attached cameras / virtual cams.
SCREEN_IDX=$(ffmpeg -f avfoundation -list_devices true -i "" 2>&1 \
  | awk -F'[][]' '/Capture screen 0/ {print $2; exit}')
if [ -z "${SCREEN_IDX}" ]; then
  echo "error: ffmpeg could not find a 'Capture screen 0' avfoundation device." >&2
  echo "       Run: ffmpeg -f avfoundation -list_devices true -i \"\"" >&2
  echo "       and confirm screen capture is permitted for this terminal in" >&2
  echo "       System Settings > Privacy & Security > Screen Recording." >&2
  exit 1
fi

OUTPUT_DIR="${HOME}/Desktop"
STAMP=$(date +%Y%m%d-%H%M%S)
MP4_PATH="${OUTPUT_DIR}/ga-mcp-full-oauth-demo-${STAMP}.mp4"
FFMPEG_LOG="${OUTPUT_DIR}/ga-mcp-full-oauth-demo-${STAMP}.ffmpeg.log"

cat <<INTRO

╭───────────────────────────────────────────────────────────────────╮
│  ga-mcp-full OAuth verification demo recorder                     │
╰───────────────────────────────────────────────────────────────────╯

This script will:
  1. Clear any cached ga-mcp-full OAuth credentials
  2. Start an ffmpeg screen recording (full display, no time cap)
  3. Run \`ga-mcp-full auth login\` — your browser will open
  4. PAUSE for you to click through Google's consent screen
  5. Run a WRITE tool call (create + archive a custom dimension) that
     can ONLY succeed with the analytics.edit scope
  6. Stop recording (signals ffmpeg to flush the MP4)

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

Detected screen capture device index: ${SCREEN_IDX}

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
echo "[prep] starting ffmpeg screen recording (full screen, no cap)..."
echo "[prep] recording will save to: ${MP4_PATH}"
echo ""

# Step 2: start ffmpeg screen recording in background.
# avfoundation input "<screen_idx>:none" means video-only (no audio).
# -framerate 24 keeps file size sane while still smooth enough for a
# terminal demo. -pix_fmt yuv420p is required for QuickTime / YouTube
# compatibility. -movflags +faststart puts the moov atom at the front
# so the upload streams while still loading.
# stdin must come from /dev/null or ffmpeg interprets terminal input as
# 'q' to quit.
ffmpeg -hide_banner -loglevel error -y \
  -f avfoundation -framerate 24 -capture_cursor 1 -i "${SCREEN_IDX}:none" \
  -c:v libx264 -preset veryfast -crf 23 \
  -pix_fmt yuv420p -movflags +faststart \
  "${MP4_PATH}" \
  </dev/null >"${FFMPEG_LOG}" 2>&1 &
FFMPEG_PID=$!

# Give ffmpeg ~2s to initialize before the narration starts. If it
# died (permissions, bad device), bail loudly.
sleep 2
if ! kill -0 "${FFMPEG_PID}" 2>/dev/null; then
  echo "[error] ffmpeg exited during startup. Log:" >&2
  sed 's/^/  | /' "${FFMPEG_LOG}" >&2 2>/dev/null || echo "  (log missing)" >&2
  exit 2
fi

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

# stderr is intentionally NOT merged into stdout — if the Python block
# fails, set -e + pipefail will surface the error without it being
# silently swallowed by a `head` truncation. Keep stdout (the narrated
# success path) at full length.
GA_DEMO_PROPERTY_ID="${GA_DEMO_PROPERTY_ID}" python3 - <<'PY'
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

# Step 4: stop recording. SIGINT (not SIGTERM) lets ffmpeg flush the
# moov atom and write a playable MP4. SIGTERM mid-encode produces a
# truncated file that QuickTime won't open.
echo ""
echo "[done] stopping recording..."
kill -INT "$FFMPEG_PID" 2>/dev/null || true
wait "$FFMPEG_PID" 2>/dev/null || true

# Give the filesystem a beat to settle
sleep 1

if [ ! -f "${MP4_PATH}" ]; then
  echo "[error] recording file not found at ${MP4_PATH}" >&2
  echo "[error] ffmpeg log (${FFMPEG_LOG}):" >&2
  sed 's/^/  | /' "${FFMPEG_LOG}" >&2 2>/dev/null || echo "  (log missing)" >&2
  exit 2
fi

mp4_size=$(du -h "${MP4_PATH}" | awk '{print $1}')

cat <<OUT

╭───────────────────────────────────────────────────────────────────╮
│  done                                                             │
╰───────────────────────────────────────────────────────────────────╯

Output:
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
