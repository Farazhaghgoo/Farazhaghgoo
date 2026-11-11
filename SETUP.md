# Publish this profile

This repository is `Farazhaghgoo/Farazhaghgoo`. Commit and push to `main`; GitHub shows `README.md` on the profile page. There is no website hosting or build step. The repository must be public.

```text
Farazhaghgoo/
├── README.md
├── SETUP.md
├── CREDITS.md
├── assets/                       # Everything the README shows, plus the control room's data snapshot
├── licenses/                     # Third-party asset and font licenses
├── scripts/
│   ├── update_contributions.py   # Control room   (run by the workflow)
│   ├── build_art.py              # Every other block   (run by hand after a design change)
│   └── source/                   # Artwork the blocks nest: HamiYami phone, work covers, skill icons
└── .github/workflows/
    └── profile-activity.yml
```

Push with git rather than the web uploader: “Add files via upload” silently skips the hidden `.github` folder, and without it nothing refreshes. Pushing a workflow file needs credentials that are allowed to change workflows (Git Credential Manager’s sign-in is; a personal access token needs the `workflow` scope).

## All dark, in every theme

GitHub picks light or dark per visitor, and a README cannot change that. So every block of this README is a dark image: intro, buttons, project and work cards, section labels, control room, toolkit and footer. Visitors on GitHub’s light theme see the same dark panels, with only the page margins around them in white. Each image carries the full text in its alt text for screen readers and search.

## The control room refreshes itself

The workflow **Refresh profile artwork** re-renders the control room every hour, whenever `scripts/update_contributions.py` or the workflow changes, and on demand through **Actions → Refresh profile artwork → Run workflow**. It commits only when the image changed, so most hours add nothing to the history. GitHub can delay scheduled runs by a few minutes when it is busy. There is nothing to update by hand.

Its numbers are GitHub’s own contribution calendar, so the total matches the “contributions in the last year” figure on the profile, private contributions included. On top of the calendar it reads two other public sources: the commit search API, for public commits by this account in any public repository (not only your own; this profile repository is left out), and the profile’s day view, for how many of a day’s contributions were private. The newest public commit messages scroll in the “Latest” panel, so a message you would not want on your profile should not be in a public repository in the first place.

In the control room, colour means how busy a day was: GitHub’s greens, and red for the busiest days. Public and private share a colour; a lock marks private work, which appears as counts only: the private readout, a status light, its share of each day on the year grid, and masked weekly rows in the feed. Those numbers come from your public profile, which shows them because **Settings → Public profile → Include private contributions on my profile** is on. Turn that off and the private part disappears here too. Private repository names and commit messages are never requested, shown or stored, and no token with access to them is involved: the workflow hands the script GitHub’s built-in repository token only to raise the search rate limit, and that token cannot see your private repositories.

If anything GitHub returns looks wrong (an incomplete calendar, changed markup, private counts that vanish), the script stops and the previous image stays. If repository policy blocks workflow writes, allow this workflow to write repository contents. GitHub may pause scheduled jobs after long repository inactivity; the current image stays usable.

To refresh by hand with Python 3.10 or newer:

```sh
python3 scripts/update_contributions.py
```

Without a token it paces itself to the public search limit and takes a few minutes the first time; later runs reuse the private counts already in `assets/contributions.json`.

## Adding a project

1. Add a card. `scripts/build_art.py` holds every block; `wide_card()` is the project card frame. Add a function, call it at the bottom, run the script, and it writes the SVG into `assets/`.
2. Add the project’s name and accent colour to `marquee()` in the same script. The control room colours days by how busy they were, not by project, so it needs no colour for the project; if the repository name differs from the product name, add it to `DISPLAY` in `scripts/update_contributions.py` (as with `EXAMassist` → UniExamer).
3. Add the image to `README.md` with its full description as alt text, and note the verification date in `CREDITS.md`.

## Motion and accessibility

The hero and typing line animate with SVG, without scripts, and reduced-motion picture sources give static versions of both. Every other animated block uses CSS animation that stops under `prefers-reduced-motion` and then shows its final state. No external widget has to respond when someone views the README: the typing SVG includes its font, the skill icons are stored locally, and the HamiYami phone embeds its screenshot.

Professional artwork is illustrative, not a screenshot or a representation of private architecture. No private implementation details are included.
