<h1>zona</h1>

[zona](https://git.ficd.sh/ficd/zona) is an _opinionated_ static site generator
written in Python. From a structured directory of Markdown content, zona builds
a simple static website. It's designed to get out of your way and let you focus
on writing.

**What do I mean by opinionated?** I built zona primarily for myself. I've tried
making it flexible by exposing as many variables as possible to the template
engine. However, if you're looking for something stable, complete, and fully
configurable, zona may not be for you. If you want a minimal Markdown blog and
are comfortable with modifying `jinja2` templates and CSS, then you're in luck.

For an example of a website built with zona, please see
[ficd.sh](https://ficd.sh). For a list of known problems, see
[Known Problems](#known-problems).

<!--toc:start-->

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Commands](#commands)
  - [Getting Started](#getting-started)
  - [Building](#building)
  - [Live Preview](#live-preview)
    - [Live Reload](#live-reload)
    - [How It Works](#how-it-works)
  - [Site Layout](#site-layout)
  - [Templates](#templates)
    - [Internal Templates](#internal-templates)
    - [User Templates](#user-templates)
    - [Footer](#footer)
  - [RSS Feed Generation](#rss-feed-generation)
  - [Internal Link Resolution](#internal-link-resolution)
  - [Syntax Highlighting](#syntax-highlighting)
  - [Markdown Extensions](#markdown-extensions)
  - [Image Labels](#image-labels)
  - [Frontmatter](#frontmatter)
  - [Post List](#post-list)
- [Configuration](#configuration)
  - [Sitemap](#sitemap)
  - [Ignore List](#ignore-list)
  - [Drafts](#drafts)
- [Known Problems](#known-problems)
- [Extras](#extras)
- [Contributing](#contributing)

<!--toc:end-->

## Features

- Fast build times (`~150ms` for a site with over 2000 lines of Markdown).
- Validation with warnings and strict build option.
- Live preview server:
  - Automatic rebuild of site on file changes.
  - Live refresh in browser preview.
- `jinja2` template support with sensible defaults included.
  - Basic page, blog post, post list.
- RSS feed generation.
- Glob ignore.
- YAML frontmatter.
- Easily configurable sitemap header.
- Site footer written in Markdown.
- Smart site layout discovery.
  - Blog posts are automatically discovered and rendered accordingly (can be
    overridden in frontmatter).
- Smart internal link resolution.
- Extended Markdown renderer:
  - Syntax highlighting.
    - Includes Kakoune syntax and [Ashen] highlighting.
  - [Image labels](#image-labels).
  - Many `python-markdown` extensions enabled, including footnotes, tables,
    abbreviations, etc.
  - LaTeX support.

## Installation

Zona can be installed as a Python package. Instructions for
[`uv`](https://docs.astral.sh/uv/) are provided.

```sh
# install latest release
uv tool install zona
# install bleeding edge from git
uv tool install 'git+https://git.ficd.sh/ficd/zona'
# you can also run without installation
uvx zona build --help
```

## Usage

### Commands

> [!NOTE]
> Commands are prefixed with `zona`: `zona <cmd> [<options>] [<args>]`.
>
> Options and arguments are not listed here. Please consult the `--help` menu.

| Command     | Aliases   | Description                                                                                            |
| ----------- | --------- | ------------------------------------------------------------------------------------------------------ |
| `init`      | None      | Create required directory structure, write default config and stylesheet                               |
| `build`     | `make, b` | Build the website and write it to an output directory.                                                 |
| `serve`     | `preview` | Build the website and serve a [live preview](#live-preview).                                           |
| `templates` | `temp`    | List available internal template names, write them to user template directory for later customization. |

### Getting Started

To set up a new website, create a new directory and run `zona init` inside of
it. This creates the required directory structure and writes the default
configuration file. The default templates and default stylesheet are also
written.

### Building

To build the website, run `zona build`. The project root is discovered according
to the location of `config.yml`. By default, the output directory is called
`public`, and saved inside the root directory.

If you don't want discovery, you can specify the project root as the first
argument to `zona build`. You may specify a path for the output using the
`--output/-o` flag. The `--draft/-d` flag includes draft posts in the output.

### Live Preview

To make the writing process as frictionless as possible, zona ships with a live
preview server. It spins up an HTTP server, meaning that internal links work
properly (this is not the case if you simply open the `.html` files in your
browser.)

Additionally, the server watches for changes to all source files, and rebuilds
the website when they're modified. _Note: the entire website is rebuilt — this
ensures that links are properly resolved._

Drafts are enabled by default in live preview. Use `--final/-f` to disable them.
By default, the build outputs to a temporary directory. Use `-o/--output` to
override this.

**Note**: if the live preview isn't working as expected, try restarting the
server. If you change the configuration, the server must also be restarted. The
live preview uses the same function as `zona build` internally; this means that
the output is also written to disk --- a temporary directory by default, unless
overridden with `-o/--output`.

#### Live Reload

Optionally, live reloading of the browser is also provided. With this feature
(enabled by default), your browser will automatically refresh open pages
whenever the site is rebuilt. The live reloading requires JavaScript support
from the browser — this is why the feature is optional.

To start a preview server, use `zona serve`. You can specify the root directory
as its first argument. Use the `--host` to specify a host name (`localhost` by
default) and `--port/-p` to specify a port (default: `8000`).

The `--live-reload/--no-live-reload` option overrides the value set in the
[config](#configuration) (`true` by default). _Automatic site rebuilds are not
affected_.

If you are scrolled to the bottom of the page in the browser, and you extend the
height of the page by adding new content, you will automatically be scrolled to
the _new_ bottom after reloading. You may tune the tolerance threshold in the
[configuration](#configuration).

#### How It Works

The basic idea is this: after a rebuild, the server needs to notify your browser
to refresh the open pages. We implement this using a small amount of JavaScript.
The server injects a tiny script into any HTML page it serves; which causes your
browser to open a WebSocket connection with the server. When the site is
rebuilt, the server notifies your browser via the WebSocket, which reloads the
page.

Unfortunately, there is no way to implement this feature without using
JavaScript. **JavaScript is _only_ used for the live preview feature. The script
is injected by the server, and never written to the HTML files in the output
directory.**

### Site Layout

The following demonstrates a simple zona project layout:

```
config.yml
content/
templates/
public/
```

The **root** of the zona **project** _must_ contain the configuration file,
`config.yml`, and a directory called `content`. A directory called `templates`
is optional, and merged with the defaults if it exists. `public` is the built
site output — it's recommended to add this path to your `.gitignore`.

The `content` directory is the **root of the website**. Think of it as the
**content root**. For example, suppose your website is hosted at `example.com`.
`content/blog/index.md` corresponds to `example.com/blog`,
`content/blog/my-post.md` becomes `example.com/blog/my-post`, etc.

- Internal links are resolved **relative to the `content` directory.**
- Templates are resolved relative to the `template` directory.

Markdown files inside a certain directory (`content/blog` by default) are
automatically treated as _blog posts_. This means they are rendered with the
`page` template, and included in the `post_list`, which can be included in your
site using the `post_list` template.

### Templates

Zona has two kinds of templates: **internal** and **user**.

#### Internal Templates

**Internal** templates are packaged with Zona and serve as sensible defaults.
For example, the `base` template provides the base for all other templates,
`basic` represents a regular page, `page` models a blog post, etc. Certain
template names are automatically used by Zona depending on the site layout
discovery.

#### User Templates

If there exists a `templates` directory in your project, its contents will be
merged with the internal templates. In case of name collisions, **user templates
are prioritized**. This means that you are able to **override** internal
templates, or write completely new ones.

For example, let's see how to **override** an internal template. First, we use
the `templates` command to view the available options:

```sh
zona templates --list
```

Suppose you want to replace the `page` template. It may be helpful to start with
the existing file as a base for your modifications. In that case, you can copy
it to your template directory:

```sh
zona templates page
```

Since the template directory contains `page.html`, Zona will prioritize it over
the internal one — any modifications you make will be used. If you _remove_
`page.html` from the directory, Zona will return to using the internal template.

> [!TIP]
> Don't be afraid to experiment! If you mess up any templates, you can always
> delete them and use `zona templates` to start over fresh.

It's also possible to completely avoid using internal templates by copying _all_
of them to your directory:

```sh
zona templates --all
```

Any _new_ templates you create (i.e. they _don't_ share a name with an internal
template) become available for use. To apply a certain template to a page, set
the `template` option in its [frontmatter](#frontmatter).

> [!TIP]
> Templates are interpreted by the
> [`jinja2`](https://jinja.palletsprojects.com/en/stable/) engine. When
> referring to them in page [frontmatter](#frontmatter), the `.html` extension
> is optional. If you create a template with a _different_ extension, then you
> must include it.

The following public variables are made available to the template engine:

| Name         | Description                                                                        |
| ------------ | ---------------------------------------------------------------------------------- |
| `content`    | The content of this page.                                                          |
| `url`        | The resolved URL of this page.                                                     |
| `metadata`   | The frontmatter of this page (_merged with defaults_).                             |
| `header`     | The sitemap header in HTML form. Can be `False`.                                   |
| `footer`     | The footer in HTML form. Can be `False`.                                           |
| `is_post`    | Whether this page is a post.                                                       |
| `newer`      | URL of the newer post in the post list.                                            |
| `older`      | URL of the older post in the post list.                                            |
| `build_time` | The build time string formatted according to [`build.time.format`](#configuration) |

> [!WARNING]
> Here be dragons. Technically, the engine has access to other objects, such as
> the `post_list` and `Item` objects. However, these are currently for internal
> use only, and do _not_ guarantee a stable API.

#### Footer

There is a special template for the site footer. Its name is set in the
[configuration](#configuration), and it defaults to `footer.md`. Unlike other
templates, the footer can be a Markdown file. It only has access to one
variable: `build_time`. If the template is a Markdown file, the variable is
substituted by the template engine, and then rendered into Markdown. If the
template is HTML, the variable is substituted and the rest is left as-is.

> [!TIP]
> Links are not resolved in the footer. If you include any, verify their
> correctness with `zona serve`.

### RSS Feed Generation

Zona can also generates an RSS feed containing your blog posts. This feature is
disabled by default, and you can enable it in the
[configuration](#configuration).

The default location is a file called `rss.xml` in the content root. All RSS
related configuration is specified in `config.yml`. If you plan to use the feed,
make sure to replace the placeholder `link`, `title`, `description`, and
`author` configuration values before you set `enabled: true`.

### Internal Link Resolution

When zona encounters links in Markdown documents, it attempts to resolve them as
internal links. Links beginning with `/` are resolved relative to the content
root; otherwise, they are resolved relative to the Markdown file. If the link
resolves to an existing file that is part of the website, it's replaced with an
appropriate web-server-friendly link. Otherwise, the link isn't changed.

For example, suppose the file `blog/post1.md` has a link `./post2.md`. The HTML
output will contain the link `/blog/post2` (which corresponds to
`/blog/post2/index.html`). Link resolution is applied to _all_ internal links,
including those pointing to static resources like images. Links are only
modified if they point to a real file that's not included in the ignore list.

### Syntax Highlighting

Zona uses [Pygments] to provide syntax highlighting for fenced code blocks. The
following Pygments plugins are included:

- [pygments-kakoune](https://codeberg.org/ficd/pygments-kakoune)
  - A lexer providing for highlighting Kakoune code. Available under the `kak`
    and `kakrc` aliases.
- [pygments-ashen](https://codeberg.org/ficd/ashen/tree/main/item/pygments/README.md)
  - An implementation of the [Ashen](https://codeberg.org/ficd/ashen) theme for
    Pygments.

If you want to use any external Pygments styles or lexers, they must be
available in zona's Python environment. For example, you can give zona access to
[Catppucin](https://github.com/catppuccin/python):

```yaml
# config.yml
markdown:
  syntax_highlighting:
    theme: catppucin-mocha
```

Then, run zona with the following `uv` command:

```sh
uvx --with catppucin zona build
```

Inline syntax highlighting is also provided via a `python-markdown` extension.
If you prefix inline code with a shebang followed by the language identifier, it
will be highlighted. For example:

```
`#!python print(f"I love {foobar}!", end="")`
will be rendered as
`print(f"I love {foobar}!", end="")`
(the #!lang is stripped)
```

### Markdown Extensions

- [BetterEm](https://facelessuser.github.io/pymdown-extensions/extensions/betterem/)
- [SuperFences](https://facelessuser.github.io/pymdown-extensions/extensions/superfences/)
  - `disable_indented_code_blocks=True`
- [Extra](https://python-markdown.github.io/extensions/extra/)
  - Excluding Fenced Code Blocks.
- [Caret](https://facelessuser.github.io/pymdown-extensions/extensions/caret/)
- [Tilde](https://facelessuser.github.io/pymdown-extensions/extensions/tilde/)
- [Sane Lists](https://python-markdown.github.io/extensions/sane_lists/)
- [EscapeAll](https://facelessuser.github.io/pymdown-extensions/extensions/escapeall/)
  - `hardbreak=True`
- [LaTeX2MathML4Markdown](https://gitlab.com/parcifal/l2m4m/-/tree/develop?ref_type=heads)
  - Disable per-file with the `math: false` frontmatter option.

### Image Labels

A feature unique to zona is **image labels**. They make it easy to annotate
images in your Markdown documents. The alt text Markdown element is rendered as
the label — with support for inline Markdown. Consider this example:

```markdown
![This **image** has _markup_.](static/markdown.png)
```

The above results in the following HTML:

```html
<div class="image-container"><img src="static/markdown.png" title=
""> <small>This <strong>image</strong> has
<em>markup</em>.</small></div>
```

The `image-container` class is provided as a convenience for styling. The
default stylesheet centers the label under the image. Note: _links_ inside image
captions are not currently supported. I am looking into a solution.

### Frontmatter

YAML frontmatter can be used to configure the metadata of documents. All of them
are optional. `none` is used when the option is unset. The following options are
available:

| Key           | Type & Default                    | Description                                                                                            |
| ------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `title`       | `str` = title-cased filename.     | Title of the page.                                                                                     |
| `subtitle`    | `str \| none` = `none`            | Subtitle of the page.                                                                                  |
| `description` | `str \| none` = `none`            | Description. If omitted, default from [config](#configuration) will be used.                           |
| `date`        | Date string = file modified time. | Displayed on blog posts and used for post_list sorting.                                                |
| `show_title`  | `bool` = `true`                   | Whether `metadata.title` should be included in the template.                                           |
| `header`      | `bool` = `true`                   | Whether the header sitemap should be rendered.                                                         |
| `footer`      | `bool` = `true`                   | Whether the footer should be rendered.                                                                 |
| `template`    | `str \| none` = `none`            | Template to use for this page. Relative to `templates/`, `.html` extension optional.                   |
| `post`        | `bool \| none` = `none`           | Whether this page is a **post**. `true`/`false` is _absolute_. Leave it unset for automatic detection. |
| `draft`       | `bool` = `false`                  | Whether this page is a draft. See [drafts](#drafts) for more.                                          |
| `ignore`      | `bool` = `false`                  | Whether this page should be ignored in _both_ `final` and `draft` contexts.                            |
| `math`        | `bool` = `true`                   | Whether the LaTeX extension should be enabled for this page.                                           |

**Note**: you can specify the date in any format that can be parsed by
[`python-dateutil`](https://pypi.org/project/python-dateutil/).

### Post List

Suppose you want `example.com/blog` to be a _post list_ page, and you want
`example.com/blog/my-post` to be a post. You would first create
`content/blog/index.md` and add the following frontmatter:

```markdown
---
title: Blog
post: false
template: post_list
---

Welcome to my blog! Please find a list of my posts below.
```

Setting `post: false` is necessary because, by default, all documents inside
`content/blog` are considered to be posts unless explicitly disabled in the
frontmatter. We don't want the post list to list _itself_ as a post.

Then, you'd create `content/blog/my-post.md` and populate it:

```markdown
---
title: My First Post
date: July 5, 2025
---
```

Because `my-post` is inside the `blog` directory, `post: true` is implied. If
you wanted to put it somewhere outside `blog`, you would need to set
`post: true` for it to be included in the post list.

## Configuration

Zona is configured in YAML format. The configuration file is called `config.yml`
and it **must** be located in the root of the project — in the same directory as
`content` and `templates`.

Your configuration will be merged with the defaults. `zona init` also writes a
copy of the default configuration to the correct location. If it exists, you'll
be prompted before overwriting it.

**Note:** Currently, not every configuration value is actually used. Only the
useful settings are listed here.

Please see the default configuration:

```yaml
feed:
  enabled: true
  timezone: UTC
  path: rss.xml
  link: https://example.com
  title: Zona Website
  description: My zona website.
  language: en
  author:
    name: John Doe
    email: john@doe.net
sitemap:
  Home: /
ignore:
  - .marksman.toml
markdown:
  image_labels: true
  tab_length: 2
  syntax_highlighting:
    enabled: true
    theme: ashen
    wrap: false
  links:
    external_new_tab: true
build:
  clean_output_dir: true
  include_drafts: false
  footer_name: "footer.md"
  time:
    timezone: "UTC"
    format: "%Y-%m-%d %H:%M %Z"
blog:
  dir: blog
  defaults:
    description: A blog post
server:
  reload:
    enabled: true
    scroll_tolerance: 100
```

| Name                                   | Description                                                                                     |
| -------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `feed.enabled`                         | Whether RSS feed should be generated. **Off by default**.                                       |
| `feed.timezime`                        | Timezone to use for post `pubDate` values. Must be an IANA compliant string.                    |
| `feed.path`                            | Location of the feed, relative to content root.                                                 |
| `feed.link`                            | The base URL of the website.                                                                    |
| `feed.title`                           | Website title.                                                                                  |
| `feed.description`                     | Website description.                                                                            |
| `feed.language`                        | String specifying website's language code.                                                      |
| `author.name`                          | Your full name.                                                                                 |
| `author.email`                         | Your email address.                                                                             |
| `sitemap`                              | Sitemap dictionary. See [Sitemap](#sitemap).                                                    |
| `ignore`                               | List of paths to ignore. See [Ignore List](#ignore-list).                                       |
| `markdown.tab_length`                  | How many spaces should be considered an indentation level.                                      |
| `markdown.syntax_highlighting.enabled` | Whether code should be highlighted.                                                             |
| `markdown.syntax_highlighting.theme`   | [Pygments] style for highlighting.                                                              |
| `markdown.syntax_highlighting.wrap`    | Whether the resulting code block should be word wrapped.                                        |
| `markdown.links.external_new_tab`      | Whether external links should be opened in a new tab.                                           |
| `build.clean_output_dir`               | Whether previous build artifacts should be cleared when building. Recommended to leave this on. |
| `build.include_drafts`                 | Whether drafts should be included by default.                                                   |
| `build.time.timezone`                  | Timezone for the build time used in templates.                                                  |
| `build.time.format`                    | Python `strftime` format string for build time used in templates.                               |
| `build.footer_name`                    | Name of the special [footer](#footer) template.                                                 |
| `blog.dir`                             | Name of a directory relative to `content/` whose children are automatically considered posts.   |
| `blog.defaults.description`            | Default description for blog posts with no `description` in their frontmatter.                  |
| `server.reload.enabled`                | Whether the preview server should use [live reload](#live-preview).                             |
| `server.reload.scroll_tolerance`       | The distance, in pixels, from the bottom to still count as "scrolled to bottom".                |

### Sitemap

You can define a sitemap in the configuration file. This is a list of links that
will be rendered at the top of every page. The `sitemap` is a dictionary of
`string` to `string` pairs, where each key is the displayed text of the link,
and the value if the `href`. Consider this example:

```yaml
sitemap:
  Home: /
  About: /about
  Blog: /blog
  Git: https://git.ficd.sh/ficd
```

### Ignore List

You can set a list of glob patterns in the [configuration](#configuration) that
should be ignored by zona. This is useful because zona makes a copy of _every_
file it encounters inside the `content` directory, regardless of its type. The
paths must be relative to the `content` directory.

### Drafts

zona allows you to begin writing content without including it in the final build
output. If you set `draft: true` in a page's frontmatter, it will be marked as a
draft. Drafts are completely excluded from `zona build` unless the `--draft`
flag is specified. They are enabled by default in `zona serve` unless the
`--final` flag is used.

[Ashen]: https://codeberg.org/ficd/ashen
[Pygments]: https://pygments.org/

## Known Problems

Please see the upstream [issues](https://git.ficd.sh/ficd/zona/issues).

## Extras

For extra scripts, including [Kakoune](https://kakoune.org) editor integration,
please see [`contrib`](./contrib).

## Contributing

Please see [CONTRIBUTING.md](./CONTRIBUTING.md)
