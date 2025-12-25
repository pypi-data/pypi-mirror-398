# 1.8.0

- Added incremental rebuilds to preview server

# 1.7.1

- Added experimental readtime to template engine

# 1.7.0

- Added subtitle metadata option

# 1.6.2

- Hard breaks and other void elements are no longer mangled by HTML
  post-processing.

# 1.6.1

- Fixed Markdown not being properly HTML escaped.

# 1.6.0

- Refactor: link resolution is now in an HTML post-process step, separate from
  Markdown rendering.
- Added Markdown admonitions.
- Added HTML comment stripping to Markdown renderer (raw HTML unaffected).

# 1.5.0

- Added `build_time` variable to templates.
- Added config options for build time formatting.
- Added config option for footer template name.
- Fixed post list not being correctly generated in preview server rebuilds.

# 1.4.1

- Removed redundant post list generation.
- Added `trace` log level, decluttered `debug` logs.
- Live preview no longer serves pages during ongoing builds.
  - As a consequence, building is now thread-safe.

# 1.4.0

- Added `--strict` build option, returning a non-zero exit status on build
  warnings.
- Non-self internal links with anchors are now resolved properly.
- Improved link validation logic, added email link validation.
- Improved regex performance.
- Added root path stripping to log output.

# 1.3.0

- Added `template` command for managing user templates.
- Added command aliases.
- Help message no longer shows Typer completion options.
- Tweaked command help descriptions.

# 1.2.2

- Added RSS feed generation.
- Added default post description to configuration.
- Added time-of-day support to post `date` frontmatter parsing.
- `zona init` now only writes `footer.md` to the templates directory.

# 1.2.1

- Added `--version` flag to CLI.

# 1.2.0

- Improved the appearance and semantics of post navigation buttons.
  - Navigation now follows "newer/older" logic.
- Added hover symbols to page titles.
- Improved the styling of hover symbols and links.

# 1.1.0

- Major improvements to default stylesheet.
- Frontmatter option to ignore file.
- Improvements to title and date rendering in templates.
- Added smooth scrolling to default stylesheet.
- Fixed a crash when user templates directory was missing when starting the
  server.
- Added "next/previous" navigation buttons to posts.
- User template directory is now merged with defaults instead of it being one or
  the other.

# 1.0.0

Initial release!
