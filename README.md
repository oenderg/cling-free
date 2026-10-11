<h1><img src="tools/assets/icon-free.png" width="72" align="absmiddle">&nbsp;cling-free</h1>

**[Cling](https://github.com/FuzzyIdeas/Cling) with Pro unlocked for free.** An unofficial macOS build of the instant fuzzy file finder, rebuilt automatically from every upstream release, signed, with working auto-updates. GPL-3.0, in both directions.

> Not affiliated with or endorsed by The Low Tech Guys. If Cling is useful to you, the author sells Pro for €15 at [lowtechguys.com/cling](https://lowtechguys.com/cling), and that is what pays for the project.

## Install

Requires macOS 14 or newer. Universal binary, Apple Silicon and Intel.

```bash
curl -fsSL https://raw.githubusercontent.com/oenderg/cling-free/main/tools/install.sh | bash
```

It downloads the [latest release](https://github.com/oenderg/cling-free/releases/latest), verifies the signature, backs up whatever Cling you already have into `~/Library/Application Support/Cling-backups/`, installs, and launches. No `sudo`, and it doesn't want your password. If a `curl | bash` one-liner ever asks for one, that's your cue to read it first: [this one is short](tools/install.sh).

Then grant **Full Disk Access** in System Settings → Privacy & Security, which Cling needs to index the whole disk. The installer opens the right pane for you. Your existing settings and indexes carry over (same bundle ID), and your upstream Cling is backed up before it's replaced.

<details>
<summary><b>Manual install</b>, if you'd rather not pipe a script into bash</summary>

```bash
# download and unzip Cling-<version>-unlocked.zip from the releases page, then:
osascript -e 'quit app "Cling"'
ditto /Applications/Cling.app ~/Desktop/Cling-backup.app   # if you have one already
rm -rf /Applications/Cling.app
ditto ~/Downloads/Cling.app /Applications/Cling.app
xattr -dr com.apple.quarantine /Applications/Cling.app
tccutil reset SystemPolicyAllFiles com.lowtechguys.Cling
open /Applications/Cling.app
```

The `xattr` line matters when you download through a browser: browsers tag downloads with `com.apple.quarantine`, and these builds aren't notarized, so Gatekeeper blocks the first launch. The installer script sidesteps this by downloading with `curl`. The `tccutil` line clears the permission entry belonging to your previous Cling, because macOS binds a grant to the bundle ID *and* the code signature.

</details>

<details>
<summary><b>What's different from upstream</b></summary>

| | Upstream 3.x | cling-free |
|---|---|---|
| Search scopes | Home, Library, Cloud Storage, Applications; System and Root with Pro | all |
| Results | 500, or up to 10,000 with Pro | up to 10,000 |
| External volumes, Everything index | Pro | on |
| Quick filters, folder filters, scripts | Pro | on |
| File server | Pro | on |
| 14-day trial, Paddle licence check | yes | none at launch; the licence page shows "Licensed on this Mac" |
| Send securely | works | **off**, see below |
| Error reports to upstream's Sentry | sent when enabled in Settings | removed |
| Auto-update | upstream's feed | this repo's feed, signed with this repo's key |

Everything else is upstream's code, unmodified, apart from a temporary two-line rename in `VolumeLive.swift` that works around a compiler bug in Xcode 26.6, the newest Xcode on GitHub's runners ([upstream PR #39](https://github.com/FuzzyIdeas/Cling/pull/39)). It skips itself once upstream has the fix.

**Send securely is disabled.** Upstream's project depends on a package called `WarpDrop` that is referenced by a path on the author's own machine and isn't published, so a clean checkout can't even resolve its dependencies. This fork substitutes a stub with the same API that reports "not available" instead of sending anything.

</details>

<details>
<summary><b>How it works</b></summary>

The patch is a script, not a fork's worth of diverging commits. [`tools/unlock_pro.py`](tools/unlock_pro.py) runs against a pristine upstream tag and does five things (plus the temporary rename above):

1. Defines `proactive` (the flag every Pro gate in Cling reads) as `true`, along with `validReq`, `invalidReq` and `invalidReq3`. Upstream's public sources call all four but no longer define them, so without these the project doesn't compile.
2. Replaces the app's `pro.checkProLicense()` call with `pro.enablePro()` and clears the trial flag, so the app doesn't ask Paddle about a trial or licence at launch. The Paddle SDK is still linked in: the "Buy" and "Manage" buttons on the licence page are upstream's and would still reach Paddle if you press them.
3. Repoints the private `WarpDrop` package at the stub in [`tools/stubs`](tools/stubs).
4. Points Sparkle at this repo's appcast and EdDSA public key, so the app can't update itself into the official, locked build.
5. Turns off Sentry reporting.

Every edit is anchored on a declaration or literal call rather than a line number, and a missing anchor is a hard failure: a red build beats a silently locked one.

Branches:

- **`tooling`** is the source of truth: the README source, the workflows, `tools/`.
- **`main`** is rebuilt as *upstream `main` + one commit of tooling*, so GitHub's comparison view reads "1 commit ahead". It is force-pushed; never edit it directly.
- **`unlocked`** is the pristine upstream release tag with the patch applied, regenerated on each new release. This is the exact source every release binary is built from.

A workflow checks for a new upstream release every hour, and a daily run backs it up. When there is one it regenerates `unlocked`, builds on a macOS runner, signs, publishes a release and updates the appcast. If a release can't be built, nothing is published and the previous release stays in place.

</details>

<details>
<summary><b>Signing</b></summary>

Builds are signed with a self-signed certificate and not notarized. The designated requirement is `identifier "com.lowtechguys.Cling" and certificate leaf = H"…"`, which doesn't change from build to build, so Full Disk Access survives updates. Check yours:

```bash
codesign -d -r- /Applications/Cling.app
```

</details>

<details>
<summary><b>Build it yourself</b></summary>

```bash
git clone --depth 1 --branch v3.2.0 https://github.com/FuzzyIdeas/Cling.git src
git clone --branch tooling https://github.com/oenderg/cling-free.git ci
python3 ci/tools/unlock_pro.py src
bash ci/tools/build.sh src 3.2.0 "$PWD/dist"
```

You'll need Xcode with the same major version upstream builds with. Without `SIGN_IDENTITY` set the app is ad-hoc signed, which works but loses its permission grants on every rebuild.

</details>

<details>
<summary><b>Licence</b></summary>

Cling is GPL-3.0 and so is this repository. The unlock patch and tooling are published under the same licence, and the exact source of every binary is the `unlocked` branch.

</details>

---

> ### Below is upstream's README, unmodified
>
> Install with the command above, not the download button or `brew`: those give the **official, locked** build. Pricing and the "Pro features" list don't apply to this build, and "Send securely" is off.

---

