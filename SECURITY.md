# Security Policy

This project can store authenticated browser state in `.auth/session.json` and `.auth/session-browser-profile/`.

Never commit:

- `.auth/`
- downloaded videos
- generated manifests that contain signed media URLs

The tool is intended only for personal offline access to content you are authorized to view. It should not be used to bypass DRM, paywalls, or access controls.
