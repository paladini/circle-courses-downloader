# Security policy

This project stores authenticated browser state under `.auth/`.

Never commit:

- `.auth/`
- downloaded videos
- generated manifests that contain signed media URLs

The tool is intended only for personal offline access to content you are
authorized to view. It must not be used to bypass DRM, paywalls, or access
controls.

The CLI doesn't accept terminal passwords, raw cookie headers, or copied browser
tokens. Authentication happens in a dedicated Chromium profile managed by
Playwright.
