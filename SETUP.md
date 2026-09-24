# Publish this profile

Copy the contents of this folder into the root of `Farazhaghgoo/Farazhaghgoo`, including the hidden `.github` folder. Replace the old README; keep unrelated repository files.

```text
Farazhaghgoo/
├── README.md
├── SETUP.md
├── CREDITS.md
├── assets/                 # All artwork, logos, animations and activity snapshot
├── licenses/               # Third-party asset and font licenses
├── scripts/
│   └── update_activity.py
└── .github/workflows/
    └── profile-activity.yml
```

Commit and push to `main`. This is a profile README package, so no website hosting or build step is needed. The profile repository must be public.

## Activity refresh

The shipped activity image already contains a real public snapshot, so it works immediately. The included GitHub Actions workflow is configured to refresh it daily at 06:23 UTC, on changes to its script or workflow, or manually through **Actions → Refresh public activity artwork → Run workflow**.

No personal access token or custom secret is required. The script reads GitHub’s publicly visible contribution calendar without authentication. GitHub’s built-in repository token is used only by checkout and the commit step. The job has `contents: write` permission to update `assets/activity.svg` and `assets/activity.json`.

If repository or organization policy blocks workflow writes, allow this workflow to write repository contents or update the images manually. If branch protection requires pull requests, direct bot pushes will be blocked; keep the included static snapshot or adapt the publication step to your repository policy. GitHub may pause scheduled jobs after extended repository inactivity. The current image remains usable if refreshes stop.

To update manually with Python 3.10 or newer:

```sh
python3 scripts/update_activity.py
```

The public calendar is not a measure of total professional work. It can omit private work. Each block represents a real day; height follows GitHub’s activity level, not a fabricated number. Counts and the snapshot date are printed in the image. If GitHub changes its calendar markup, the script fails before replacing the previous snapshot.

## Artwork and accessibility

The hero and introduction animate using SVG, without scripts. Reduced-motion picture sources provide static versions of both. The HMI cover’s small dashed line also respects reduced motion. Essential identity and project descriptions remain available as native text and image alt text.

The entire visible profile uses local image assets. The typing SVG includes its font, and the skill icon strip is stored locally. No external widget has to respond when someone views the README. Clicking a project cover opens its public repository.

Professional artwork is illustrative, not a screenshot or a representation of private architecture. No private implementation details are included.

The preview HTML outside this folder is for local review and approximates GitHub spacing. GitHub controls the final Markdown typography and layout. This package has not been pushed and its GitHub Actions workflow has not run on your account yet.
