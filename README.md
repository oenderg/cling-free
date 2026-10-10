# cling-free

[FuzzyIdeas/Cling](https://github.com/FuzzyIdeas/Cling) with the Pro gating removed, rebuilt from
upstream automatically. GPL-3.0, in both directions.

> Unofficial. Not affiliated with or endorsed by The Low Tech Guys. If Cling is useful to you,
> the author sells Pro for €15 at [lowtechguys.com/cling](https://lowtechguys.com/cling), and
> that is what pays for the project.

## Install

Requires macOS 14 or newer. Universal binary, Apple Silicon and Intel.

```bash
curl -fsSL https://raw.githubusercontent.com/oenderg/cling-free/main/tools/install.sh | bash
```

It downloads the [latest release](https://github.com/oenderg/cling-free/releases/latest),
verifies the signature, backs up whatever Cling you already have into
`~/Library/Application Support/Cling-backups/`, installs, and launches.

No `sudo`, and it doesn't want your password: `/Applications` is writable by admin users and
`tccutil` acts on your own TCC database. If a `curl | bash` one-liner ever asks for a password,
that's your cue to read it first — [this one is short](tools/install.sh).

Then grant **Full Disk Access** in System Settings → Privacy & Security, which Cling needs to
index the whole disk. The installer opens the right pane for you.

<details>
<summary>Manual install, if you'd rather not pipe a script into bash</summary>

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

The `xattr` line matters when you download through a browser. Browsers tag downloads with
`com.apple.quarantine`, and these builds aren't notarized, so Gatekeeper blocks the first launch.
The installer script sidesteps this by downloading with `curl`, which never sets the flag.

The `tccutil` line clears the permission entry belonging to your previous Cling. macOS binds a
grant to the bundle ID *and* the code signature, so a grant made for upstream's Developer ID
build won't transfer.

</details>

Your existing Cling settings and indexes carry over untouched — same bundle ID, same defaults
domain. Your upstream Cling is backed up before it's replaced.

## What's different from upstream

| | Upstream 3.x | cling-free |
|---|---|---|
| Search scopes | Home, Library, Applications; System and Root with Pro | all |
| Results | 500, or up to 10,000 with Pro | up to 10,000 |
| External volumes, Everything index | Pro | on |
| Quick filters, folder filters, scripts | Pro | on |
| File server | Pro | on |
| 14-day trial, Paddle licence check | yes | none at launch; the licence page shows "Licensed on this Mac" |
| Send securely | works | **off** — see below |
| Error reports to upstream's Sentry | sent when enabled in Settings | removed |
| Auto-update | upstream's feed | this repo's feed, signed with this repo's key |

Everything else is upstream's code, unmodified.

**Send securely is disabled.** Upstream's project depends on a package called `WarpDrop` that is
referenced by a path on the author's own machine (`../../../Github/alin23/warpdrop/swift`) and
isn't published, so a clean checkout can't even resolve its dependencies. This fork substitutes a
stub with the same API that reports "not available" instead of sending anything.

## How it works

The patch is a script, not a fork's worth of diverging commits.
[`tools/unlock_pro.py`](tools/unlock_pro.py) runs against a pristine upstream tag and does five
things:

1. Defines `proactive` (the flag every Pro gate in Cling reads) as `true`, along with `validReq`,
   `invalidReq` and `invalidReq3`. Upstream's public sources call all four but no longer define
   them, so without these the project doesn't compile.
2. Replaces the app's `pro.checkProLicense()` call with `pro.enablePro()` and clears the trial
   flag, so the app doesn't ask Paddle about a trial or licence at launch and the Settings and
   filter UI see an active licence. The Paddle SDK is still linked in: the "Buy" and "Manage"
   buttons on the licence page are upstream's and would still reach Paddle if you press them.
3. Repoints the private `WarpDrop` package at the stub in [`tools/stubs`](tools/stubs).
4. Points Sparkle at this repo's appcast and EdDSA public key, so the app can't update itself
   into the official, locked build.
5. Turns off Sentry reporting.

Every edit is anchored on a declaration or literal call rather than a line number, and a missing
anchor is a hard failure: a red build beats a silently locked one.

Branches:

- **`tooling`** is the source of truth: this README, the workflows, `tools/`.
- **`main`** is rebuilt daily as *upstream `main` + one commit of tooling*, so GitHub's
  comparison view reads "1 commit ahead" and the diff against upstream is exactly the tooling.
  It is force-pushed; never edit it directly.
- **`unlocked`** is the pristine upstream release tag with the patch applied, regenerated on each
  new release. This is the exact source every release binary is built from.

A workflow checks for a new upstream release every hour, and a daily run backs it up. When there is
a new release it regenerates `unlocked`, builds on a macOS runner, signs, publishes a release and
updates the appcast.

## When the pipeline breaks

Upstream changes Cling often (about one release a week), and the patch anchors on its source, so
now and then a release changes something the patch relies on. The fork is built to notice and
recover:

- A failed `sync-upstream` run opens one `ci-failure` issue (later failures comment on it) and
  closes it itself when a run passes again. Nothing is published from a failed run, so the last
  good release stays in place.
- [`auto-fix.yml`](.github/workflows/auto-fix.yml) then runs Claude with the rules in
  [`CLAUDE.md`](CLAUDE.md). If the cause is drift in the unlock script it opens a pull request
  against `tooling`. For anything else it only comments.
- It can only change `tools/unlock_pro.py` and `tools/stubs/`, and only a little. Every pull request
  must pass three required checks before it can merge: `check-scope` (those files only, from a base
  branch copy of the check that a pull request can't edit), `verify-unlock` (the patch applies to the
  newest upstream release and [`verify_unlock.py`](tools/verify_unlock.py) approves the diff) and
  `verify-build` (the patched source builds into a universal, validly signed app).
- Auto-merge is off by default. Set the repository variable `AUTO_MERGE` to `true` to let Claude ask
  for it; GitHub still merges only after the checks pass.

## Signing

Builds are signed with a self-signed certificate and not notarized. The designated requirement is
`identifier "com.lowtechguys.Cling" and certificate leaf = H"…"`, which doesn't change from build
to build, so Full Disk Access survives updates. Check yours:

```bash
codesign -d -r- /Applications/Cling.app
```

## Build it yourself

```bash
git clone --depth 1 --branch v3.0.0 https://github.com/FuzzyIdeas/Cling.git src
git clone --branch tooling https://github.com/oenderg/cling-free.git ci
python3 ci/tools/unlock_pro.py src
bash ci/tools/build.sh src 3.0.0 "$PWD/dist"
```

You'll need Xcode with the same major version upstream builds with. Without `SIGN_IDENTITY` set
the app is ad-hoc signed, which works but loses its permission grants on every rebuild.

## Licence

Cling is GPL-3.0 and so is this repository. The unlock patch and tooling are published under the
same licence, and the exact source of every binary is the `unlocked` branch.
