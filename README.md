# Twitch NoAds on Kodi

![Banner](assets/banner.webp)

**Fork** of [anxdpanic/plugin.video.twitch](https://github.com/anxdpanic/plugin.video.twitch) with client-side ad filtering.

> **Original addon:** [anxdpanic/plugin.video.twitch](https://github.com/anxdpanic/plugin.video.twitch) – the upstream project this fork is based on.
> Please support the original developers!

> **DISCLAIMER — USE AT YOUR OWN RISK**
>
> This fork filters Twitch ads client-side. This violates Twitch's Terms of Service and may result in an account ban.
> Use at your own risk. The legitimate way to watch ad-free on Twitch is Turbo or a channel subscription (supported by the original addon).
>
> **Note:** The ad filtering is not 100% foolproof. Twitch constantly changes their ad delivery methods, so occasionally ads may still slip through. If you see ads, please report them with a debug log so we can update the detection rules.

---

## Features

- **Ad-free playback** – Twitch ad segments are filtered out via a local HTTP proxy
- **Transparent proxy** – sits between InputStream Adaptive and Twitch, no external services needed
- **Segment caching** – media segments are cached locally for smooth playback
- **Playlist caching** – HLS playlists are cached to reduce Twitch API calls
- **Manifest caching** – processed manifests are cached for faster refreshes
- **Threaded server** – handles multiple parallel requests efficiently
- **Multiple ad detection methods:**
  - `EXT-X-DATERANGE` tags with ad classes (`twitch-ad`, `twitch-stitched-ad`, `preroll`, `midroll`, `postroll`, etc.)
  - Keyword-based DATERANGE fallback for unknown ad classes
  - `EXT-X-CUE-OUT` / `EXT-X-CUE-IN` markers
  - Known ad URL patterns (`/ad/`, `amazon-adsystem`, etc.)
- **Quality selection** – choose between Source, 1080p60, 720p60, 480p, 360p, 160p, Audio Only
- **Login support** – device code login for Turbo/subscriber benefits
- **Multi-language** – supports 50+ languages via Kodi's language system

---

## How it works

A local HTTP proxy (`adblock_proxy.py`) sits between InputStream Adaptive and Twitch:

1. When playback starts, the addon starts a local proxy on `127.0.0.1` with a random port.
2. The Twitch HLS playlist URL is passed to the proxy.
3. When InputStream Adaptive requests the manifest, the proxy fetches the real playlist from Twitch, removes ad segments, and serves the filtered playlist.
4. Ad segments are detected via:
   - `EXT-X-DATERANGE` tags with ad classes (`twitch-ad`, `amazon`, etc.)
   - Known ad URL patterns (`/ad/`, `amazon-adsystem`, etc.)
5. Media segments are proxied transparently to Twitch.
6. The proxy is stopped when playback ends or is stopped.

---

## Requirements

- **Kodi 20 (Nexus)** or newer
- **InputStream Adaptive** addon (installed automatically as dependency)
- **script.module.python.twitch** (installed automatically as dependency)
- **script.module.requests** (installed automatically as dependency)

---

## Installation

### From ZIP

1. Download the repository as a ZIP file.
2. In Kodi, go to **Add-ons → Install from zip file**.
3. Select the downloaded ZIP file.

### From Source

1. Clone or download this repository.
2. In Kodi, go to **Add-ons → Install from zip file**.
3. Navigate to the repository folder and select it.

---

## Login

1. Go to **Settings → Login → Login (device code)**
2. Visit [twitch.tv/activate](https://www.twitch.tv/activate) on any device, sign in, and enter the code shown in Kodi

The add-on stores the tokens and refreshes them automatically. Automatic refresh requires a public Client ID — the bundled Client ID cannot refresh tokens, so you will be asked to log in again once the token expires. To enable automatic refresh:

1. Register your own application at [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps)
   (OAuth Redirect URL: `http://localhost`, Client Type: **Public**)
2. Enter its Client ID in **Settings → Developer → OAuth Client ID**
3. Log in again via **Settings → Login → Login (device code)**

---

## Ad-Free Playback (Turbo / Subscriptions)

If your Twitch account has Turbo, or you are subscribed to a channel, you can use **Settings → Subscriber and Turbo Benefits → Login: ad-free playback / Turbo (device code)** and authorize with that account to watch without ads (where Twitch grants it).

---

## FAQ

**Q: I can't find the Twitch.tv add-on in the Kodi add-on manager!**

> Make sure you are using at least Kodi 20 (Nexus).

**Q: I'm having issues with the playback of streams (buffering, dropping, stuttering).**

> This Add-on does not handle any aspect of the playback of Twitch streams (that would be the Kodi Video Player), it simply tells Kodi what to play.
> The Add-on does however provide Quality Options which may help if your internet connection / computer specs are below requirements for HD streams.
> Try making sure that the Kodi Add-on "InputStream Adaptive" is installed, and Adaptive Quality is enabled in Twitch.tv's Add-on settings.

**Q: Some streams don't start at all.**

> This can happen occasionally due to Twitch server issues or rate limiting. Try again in a few minutes, or try a different quality setting.

**Q: I still see ads on some streams.**

> Twitch constantly changes their ad delivery methods. If you see ads, please open an issue with a debug log so we can update the detection rules.

---

## Troubleshooting

### Enable Debug Logging

1. Go to **Settings → System → Logging**
2. Enable **Enable debug logging**
3. Reproduce the issue
4. Find the log at `~/.kodi/temp/kodi.log`

### Common Issues

| Issue | Solution |
|---|---|
| Streams won't start | Check that InputStream Adaptive is installed and enabled |
| Buffering / stuttering | Try a lower quality setting in the addon settings |
| Token expired | Re-login via Settings → Login |
| Ads still appearing | Update to the latest version; report with debug log |

---

## Changelog

See [changelog.txt](changelog.txt) for the full list of changes.

---

## License

This project is licensed under the **GPL-3.0-only** license. See [LICENSES/GPL-3.0-only](LICENSES/GPL-3.0-only) for the full text.

### Third-Party Licenses

This addon includes or depends on the following third-party libraries:

- **[python-twitch](https://github.com/ingwinlu/python-twitch)** by [ingwinlu](https://github.com/ingwinlu) – MIT License
- **[requests](https://github.com/psf/requests)** by [Python Software Foundation](https://github.com/psf) – Apache License 2.0

---

## Support

- **Issues:** [GitHub Issues](https://github.com/zelect0r/plugin.video.twitch.noads/issues)
- **Forum:** [Twitch Addon Forum](https://twitchaddon.panicked.xyz/forum)

---

## Donate

If you find this addon useful, consider supporting development:

[![zelect0r](https://img.shields.io/badge/zelect0r-Ko--Fi%2Fzelect0r-ff5e5b?logo=ko-fi&logoColor=white)](https://ko-fi.com/zelect0r)


