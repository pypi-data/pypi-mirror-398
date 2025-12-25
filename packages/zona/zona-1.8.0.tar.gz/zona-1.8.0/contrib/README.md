# Extras

This directory contains extra scripts to help with both the _development_ and
_usage_ of Zona.

- `zona-new.nu`
  - Nushell script to speed up creating new blog posts.
- `zona-sort.nu`
  - Nushell script to sort posts by date and draft status, and open with editor.
- `zona.kak`
  - [Kakoune](https://kakoune.org) integration plugin. See the
    [usage guide](#kakoune).

## Kakoune

The Kakoune integration allows you to conveniently start and stop the Zona live
preview without needing a separate terminal window. Available commands and
options are also documented here.

### Installation

Copy `zona.kak` to your `autoload` directory. At some point in your `kakrc`, add
`require-module zona`. Changing options must come after this line.

### Usage

Use the provided commands to start the preview server and open pages. The server
is automatically killed when Kakoune exists.

### Options

All available options are strings.

- `zona_url`
  - Url of the zona server. You won't need to change this.
- `zona_path`
  - Full path to the zona project. This should be the directory containing
    `config.yml`. Feel free to modify `zona.kak`, or use `set-option` after
    loading the module.
- `zona_cmd`
  - Command for zona. For example, you might need `"uvx zona"`.
- `zona_url_cmd`
  - Command to open URL in a browser. The URL is the first argument.

### Commands

- `zona-start-preview`
  - Starts the preview server, and opens the current page after a short delay.
- `zona-open`
  - Open the current page, likely in a new tab.
- `zona-date`
  - Update the current page's frontmatter to today's date.
- `zona-stop-preview`
  - Kills the preview server.
