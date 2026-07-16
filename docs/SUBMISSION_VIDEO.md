# Submission video provenance

The final Devpost video is built deterministically by
`scripts/build_submission_video.py`. It uses only repository assets and screenshots
captured from the public HTTPS demo on July 16, 2026.

Published video: <https://youtu.be/llfCoDkt1DE> (`2:20`, public, copyright check
completed with no issue found).

## Exact-content boundary

- The cold-to-learned-recall screenshots are from a fresh, session-isolated synthetic
  namespace on the public Amazon Lightsail deployment.
- The displayed result is `2` incidents, `1` human-confirmed outcome, `1` reusable
  memory, and `8` ordered audit events.
- The recalled evidence shown in the video reports similarity `0.784`, calibrated
  confidence `0.667`, and decision score `0.523` for that isolated run.
- The architecture image distinguishes the active deterministic embedding provider
  from the Bedrock path that remains blocked by an account-level Runtime restriction.
- The narration does not claim a successful Bedrock invocation.
- No credential, token, private endpoint, account identifier, email, or support-case
  page is shown.

## Rebuild

On macOS with Pillow, `ffmpeg`, `ffprobe`, and the built-in `say` command:

```bash
python3 scripts/build_submission_video.py
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  submission_assets/labrecall-ai-devpost-demo.mp4
```

The script writes the upload-ready MP4, YouTube and Devpost thumbnails, English SRT
captions, and a complete scene and narration manifest to `submission_assets/`. The
final duration assertion is strict: the build fails at 180 seconds or longer.
