# tenerra-geo
GEO / HCOS category authority

## ANYA social image

The source for `assets/images/anya-og.png` is `assets/og/anya-og.html`. To regenerate the image from a fresh checkout:

```sh
npm ci
npx playwright install chromium
npm run render:og
```

Rendering also requires `curl` and network access to Google Fonts. The image is not yet wired into page metadata.
