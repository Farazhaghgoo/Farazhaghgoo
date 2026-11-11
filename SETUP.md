# Publish this profile

This repository is `Farazhaghgoo/Farazhaghgoo`. Commit and push to `main`; GitHub shows `README.md` on the profile page. There is no website hosting or build step. The repository must be public.

```text
Farazhaghgoo/
├── README.md
├── SETUP.md
├── CREDITS.md
├── assets/                 # All artwork, logos, animations and data snapshots
├── licenses/               # Third-party asset and font licenses
├── scripts/
│   ├── update_activity.py  # Contribution landscape   (run by the workflow)
│   ├── update_shiplog.py   # Commit stream            (run by the workflow)
│   ├── build_art.py        # Hand-designed covers     (run by hand after a design change)
│   └── source/             # Source image for the HamiYami phone
└── .github/workflows/
    └── profile-activity.yml
```

Push with git rather than the web uploader: “Add files via upload” silently skips the hidden `.github` folder, and without it nothing refreshes. Pushing a workflow file needs credentials that are allowed to change workflows (Git Credential Manager’s sign-in is; a personal access token needs the `workflow` scope).

## Activity and commit stream refresh

Both images ship with a real public snapshot, so they work immediately. The workflow **Refresh profile artwork** re-renders them daily at 06:23 UTC, on changes to `scripts/` or the workflow, or manually through **Actions → Refresh profile artwork → Run workflow**. It commits only when an image actually changed.

No personal access token or custom secret is required. `update_activity.py` reads GitHub’s publicly visible contribution calendar without authentication. `update_shiplog.py` reads that calendar, the public commit search API and the profile’s public day view; the workflow hands it GitHub’s built-in repository token only to raise the search rate limit. That token cannot see your private repositories. The job has `contents: write` permission to update `assets/activity.*` and `assets/shiplog.*`.

If repository or organization policy blocks workflow writes, allow this workflow to write repository contents or update the images manually. If branch protection requires pull requests, direct bot pushes will be blocked; keep the included snapshots or adapt the publication step to your repository policy. GitHub may pause scheduled jobs after extended repository inactivity. The current images remain usable if refreshes stop.

To update manually with Python 3.10 or newer:

```sh
python3 scripts/update_activity.py
```

```sh
python3 scripts/update_shiplog.py
```

The public calendar is not a measure of total professional work. It can omit private work. Each block represents a real day; height follows GitHub’s activity level, not a fabricated number. Counts, the busiest day and the snapshot date are printed in the image. If GitHub changes its calendar markup, the script fails before replacing the previous snapshot.

The commit stream covers the last 90 days. Its totals and daily bars are GitHub’s own contribution counts. Public commits are found by author across every public repository, not only your own, and the feed shows the newest three per project, without merge commits and without this profile repository. A commit message you would not want on your profile should not be in a public repository in the first place; the feed repeats it verbatim.

Private work appears as counts only: a share of the total, the lime part of each daily bar, and one masked row per week. Those numbers come from your public profile, which shows them because **Settings → Public profile → Include private contributions on my profile** is on. Turn that off and the private part disappears here too. Private repository names and commit messages are never requested, shown or stored, and no token with access to them is involved.

## Adding a project

1. Add a cover. `scripts/build_art.py` holds the designs for the newer covers and the shared card frame; add a function, run the script, and it writes the SVG into `assets/`.
2. Add the project’s name and accent colour to `marquee()` in the same script, and to `REPO_COLORS` in `scripts/update_shiplog.py` so its commits use the same colour.
3. Add a table cell to `README.md`, and note the verification date in `CREDITS.md`.

## Artwork and accessibility

The hero and introduction animate using SVG, without scripts. Reduced-motion picture sources provide static versions of both. Every other animated image (the marquee, the feature card, the covers, the section labels, the commit stream and the activity ripple) uses CSS animation that stops under `prefers-reduced-motion`. Essential identity and project descriptions remain available as native text and image alt text.

The entire visible profile uses local image assets. The typing SVG includes its font, the skill icon strip is stored locally, and the HamiYami phone embeds its screenshot. No external widget has to respond when someone views the README. Clicking a project cover opens its public repository; the HamiYami card opens the live demo.

Professional artwork is illustrative, not a screenshot or a representation of private architecture. No private implementation details are included.

GitHub controls the final Markdown typography and layout. Every image, section labels included, keeps its dark surface in both GitHub themes; the page background and the text between images follow each visitor’s own theme, which a README cannot change.
