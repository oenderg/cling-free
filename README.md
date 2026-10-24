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
# download Cling-<version>-unlocked.dmg from the releases page and open it, then:
osascript -e 'quit app "Cling"'
ditto /Applications/Cling.app ~/Desktop/Cling-backup.app   # if you have one already
rm -rf /Applications/Cling.app
ditto "/Volumes/Cling <version>/Cling.app" /Applications/Cling.app
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

> [!WARNING]
> Commits to this repo have been paused because of blatant stealing. Work will continue privately.

<p align="center">
    <a href="https://lowtechguys.com/cling"><img width="128" height="128" src="Cling/Assets.xcassets/AppIcon.appiconset/icon_256x256.png" style="filter: drop-shadow(0px 2px 4px rgba(80, 50, 6, 0.2));"></a>
    <h1 align="center"><code style="text-shadow: 0px 3px 10px rgba(8, 0, 6, 0.35); font-size: 3rem; font-family: ui-monospace, Menlo, monospace; font-weight: 800; background: transparent; color: #4d3e56; padding: 0.2rem 0.2rem; border-radius: 6px">Cling</code></h1>
    <h4 align="center" style="padding: 0; margin: 0; font-family: ui-monospace, monospace;">Instant fuzzy find any file</h4>
    <h6 align="center" style="padding: 0; margin: 0; font-family: ui-monospace, monospace; font-weight: 400;">Act on it in the same instant</h6>
</p>

<p align="center">
    <a href="https://files.lowtechguys.com/releases/Cling.dmg">
        <img width=200 src="https://files.lowtechguys.com/macos-app.svg">
    </a>
</p>

### Installation

- Download the app from the [website](https://lowtechguys.com/cling) and drag it to your `Applications` folder
- If you use [homebrew](https://brew.sh/), run `brew install --cask thelowtechguys-cling`

![screenshot](https://lowtechguys.com/static/img/cling-ui.png)

### Features

- **Fuzzy search across millions of files** in under 100ms
- **Search bar** that floats over any app like Spotlight, or sits pinned to the desktop as a small search field
- **App launcher** in the search bar: installed apps whose names match come first
- **Folder icons** on the search bar's paths, with an icon you pick for each drive
- **Quick Filters** for file types (Images, Videos, Documents, Code, PDFs, etc.) and folder restrictions
- **Act on files instantly** with hotkeys, scripts, drag and drop, or batch rename
- **Smart defaults** showing your most recently changed files on launch
- **Search history** with `Up`/`Down` arrow cycling, `Tab` completion, and `Cmd+Down` to browse all history
- **Extension-aware queries** like `.png icon` or `.pdf invoice`
- **Search operators** to filter and exclude results as you type
- **Configurable search scopes** (Home, Library, Cloud Storage, Applications, System, Root) with `.fsignore` support
- **External volume indexing** with persistent indexes that work even when unmounted, and live updates while connected
- **Cloud storage** search across iCloud Drive, Dropbox, Google Drive and other cloud folders, files kept online only included, without downloading them
- **Live filesystem tracking** via FSEvents
- **Index size view** showing how many files each scope and folder adds to the index, with a way to prune the ones you don't need
- **Send securely** to share files over an encrypted, auto-expiring link
- **CLI tool** for terminal-based searching
- **MCP server** so an AI agent can search, explain why a file is missing and change indexes, ignore rules, filters and settings
- **the Everything index**: every file on the local disks, with no ignore rules, like Everything on Windows, or turned off entirely

---

### Pro features

Cling is free to use with Home, Library, Cloud Storage and Applications search scopes. A **Cling Pro** licence unlocks:

- **Additional search scopes**: System, Root
- **External volume indexing** with persistent indexes, and an *External drives* filter to find which drive holds a file
- **the Everything index** of every file on the local disks
- **File server** to search this Mac and download its files from a browser on your phone or another computer
- **Quick Filters** for file types and custom queries
- **Custom folder filters** for saved folder sets
- **Scripts** to run custom actions on files
- **Up to 10,000 results** (free is capped at 500)

### Pricing

Cling starts with a **14-day free trial** automatically, no payment details needed. After the trial, the app continues to work in **Free mode** with Home, Library, Cloud Storage and Applications scopes, up to 500 results.

A Pro license costs **€15**, one-time purchase, for life. It can be activated on up to **5 personal Mac devices**.

*Activating a 6th Mac automatically deactivates the oldest one, so the license can be used indefinitely as you change machines.*

### Raycast extension

[Cling's Raycast extension](https://www.raycast.com/alin/cling) can fuzzy search files instantly, act on files and save often used queries from the same familiar Raycast interface.

### Alfred workflow

Cling ships an Alfred workflow that fuzzy searches files with `cl`, opens them in the editor, terminal or shelf app set in Cling, and reindexes with `clreindex`. Install it from **Settings > General** in Cling.

---

### Comparison with other apps

#### Spotlight, Alfred, Raycast

Cling is similar to these apps in that it provides instant search results, but the key differences are:

- **Fuzzy search**: find files with partial or misspelled queries
- **System files**: search system files, hidden files, dotfiles, and app data that the Spotlight index doesn't include
- **Extension filtering**: quickly narrow results by file type without crafting complex queries

#### ProFind, HoudahSpot, EasyFind, Tembo, Find Any File

Cling is very much **not** like these apps.

They are all file search apps that provide advanced search features, allowing you to craft complex queries using metadata and file content to dig deep into your filesystem and find as many files as possible.

Cling is for quickly finding one or more specific files by roughly knowing the name, and then doing something with the file immediately like:

- copying it for sending on chat
- adding to a shelf like Yoink
- opening it in an app like Pixelmator
- uploading it using Dropshare
- executing a script on the file

**Cling is not an app for finding all files that match a complex query.**

---

### Performance considerations

#### Memory usage

Cling uses between 60 and 100 MB of memory with 1.6 million files indexed.

Each search scope and each drive has its own index, saved as a file on disk. Cling maps those files into memory instead of reading them in: macOS loads the pages a search needs straight from the file, and drops them again whenever it needs the room. A loaded index adds almost nothing to Cling's memory until something changes it.

What does count:

- **File changes**: a change rewrites the few pages that hold it, and the first change also builds a lookup table, a few megabytes for a scope with a few hundred thousand files
- **Extension table**: one table of file extensions shared by every index, usually under 10 MB
- **Search buffers**: a search over millions of files works in memory that goes back to the system as soon as the search is done

The **Everything** index stays on disk until you turn it on, and leaves memory 10 minutes after you turn it off or close the window. Turning Everything off in Settings > Search can also delete its saved index.

On disk, an index takes about 160 bytes per file. The index size view in the status bar shows each index's files, size on disk, memory and when it was last indexed in full.

#### CPU usage

The most CPU-intensive operations are:

- **Indexing**: when Cling is indexing your filesystem for the first time, it will keep the CPU busy for a few dozen seconds
- **Following changes**: the indexes follow file changes as they happen, through FSEvents, instead of being re-indexed on a schedule
- **Fuzzy search**: when you type in the search bar, Cling searches every index in parallel, across all cores

When Cling launches, each index catches up by replaying the file changes made since it was saved. While Cling is closed, a small background job gathers those changes every few hours, waiting for a moment when you're not using the Mac, so the next launch has less to replay. It can be turned off with *Watch file events while the app is quit* in Settings > Search.

A scope is walked again from scratch only when there is no history to replay: after a macOS update, when its ignore rules changed while Cling was closed, or when macOS threw away its file change history. External drives follow their changes the same way while connected, and are walked again once a week by default, once the drive has gone a minute without changes. Both can be changed per drive in Settings > Drives & Volumes. A drive unplugged without ejecting is walked again only when you ask, from the offer to reindex it shown when you search it.

Searching will consume CPU in short bursts. In a Release build, a typical search across 9+ million files completes in under 100ms. When Cling is in background, it will pause searching and consume very little CPU for processing file changes.

#### Battery usage

The impact on battery is proportional to how many searches you do and how many file changes happen in the background.

Even though a search will look like it's consuming 100% CPU of multiple cores, it's a very fast operation and the battery energy used isn't that high in the long term.

Processing and indexing file changes is very efficient and barely touches battery life. Walking a scope again waits while the battery is under 30%.

---

### How it works

```
Filesystem ──► fts_read (local) / FileManager (external)
                        │
                        ▼
              ┌───────────────────────┐
              │  Binary Index (.idx)  │  one per scope/volume
              │  parallel arrays:     │  persists across launches
              │   · path bytes (LC)   │  saved again after 20k changes or 6h
              │   · 64-bit bitmasks   │
              │   · basename bitmasks │
              │   · word boundaries   │
              │   · extension IDs     │
              └────────┬──────────────┘
                       │ mmap: pages read on demand,
                       │ copied only when a change writes them
                       ▼
              ┌───────────────────────┐
              │  Search Engines       │◄── FSEvents (live updates)
              │  · per-scope (Home,   │◄── replay since last save (launch)
              │    Apps, Library, …) │◄── catch-up journal (while closed)
              │  · per-volume         │◄── MDQuery  (recents)
              │  · Everything         │
              │  · recents            │
              └────────┬──────────────┘
                       │
                    query  →  parse into fuzzy / extension /
                              folder / dir-segment tokens
                       │
                       ▼
              Phase 1: Filter (parallel across cores)
               · 64-bit bitmask precheck
               · extension ID (UInt16 compare)
               · folder prefix (sorted index or byte scan)
               · dir-segment literal substring
               · excluded paths (O(1) set lookup)
               · QuickFilter pre-filtered pools
                       │
                       ▼
              Phase 2: Score (parallel across cores)
               · fzf fuzzy scoring (basename + full path)
               · multi-token independent scoring
               · SIMD byte search for long paths
               · boundary/camelCase/delimiter bonuses
               · typo pass: one letter extra, missing,
                 swapped or mistyped (two in long words)
                       │
                       ▼
              Every engine in parallel (TaskGroup)
               · merged once all of them finish
               · a search still running after 150ms
                 shows what the finished ones found
                       │
                       ▼
              Merge + Rank
               · quality gate (top-third filter)
               · composite rank: score, importance,
                 prefix match, basename match, depth
               · misspelt names after exact matches
               · deduplicate by path
                       │
                       ▼
                    Results
```
