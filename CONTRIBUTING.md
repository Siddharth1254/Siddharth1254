# Notes to self

This repo is my GitHub profile. Keep it boring to maintain.

1. **Edit in one place only.** Either github.com *or* locally for a given change — never both
   at the same time. Editing in two places is how the README ended up with `<<<<<<<` markers.
2. **Always `git pull --rebase` before editing locally.**
   ```bash
   git pull --rebase origin main
   ```
3. **Never edit generated files.** Snake, stats, top-langs, streak and heatmap SVGs live on the
   `output` branch and are rebuilt daily by `.github/workflows/profile-art.yml`. To change them,
   change the workflow or `scripts/`, then run the workflow from the Actions tab.
4. **Only I commit to `main`.** Bots publish to `output`, nowhere else.
5. **Before pushing:** `bash scripts/check_readme.sh` (conflict markers, missing `./assets/…`
   paths, malformed SVGs). The same check runs in CI as `readme-check.yml`.
6. **SVG rules:** GitHub renders SVGs through `<img>`, so animate with SMIL or CSS keyframes only.
   No JavaScript, no external fonts or images.
7. **The ASCII portrait is a one-off.** Regenerate it by hand when the avatar changes:
   ```bash
   python scripts/prep_photo.py && python scripts/make_ascii_svg.py
   ```
