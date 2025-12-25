#!/usr/bin/env -S nu -n --no-std-lib

# Author: Daniel Fichtinger
# License: BSD-3
# Depends: fuzzel

# This script makes it convenient to open existing blog posts for editing.
# Posts with frontmatter are processed and sorted by date.
# User can filter by 'all' and 'drafts'.
# Fuzzel is used to select a post to edit.

# parses the markdown frontmatter
# and sorts by date
def frontmatter-sort [path: directory, drafts: bool = false] {
  ls ($"($path)/**/*.md" | into glob)
  | get name
  | each {|file|
    let fm = (open $file
    | split row '---'
    | get 1 | from yaml)
    {
      file: ($file),
      title: $fm.title,
      date: (
        if ($fm | get date? | is-empty) { null } else { $fm.date | into datetime }
      ),
      draft: (
        if ($fm | get draft? | is-empty) { false } else { $fm.draft }
      ),
    }
  }
  | where ( if $drafts { $it.draft == true } else { true } )
  | where date != null
  | sort-by --reverse date
}

# sort files, select one, and edit it
def main [path: directory = "content/blog", --print (-p), --drafts (-d)] {
  let fm = frontmatter-sort $path $drafts
  let selection = ($fm.title
    | enumerate
    | each {|row| $"($row.index + 1) ($row.item)" }
    | str join (char newline)
    # user makes a selection
    | fuzzel --dmenu)
  if (not ($selection | is-empty)) {
    let idx = ($selection | split row " " | get 0 | into int) - 1
    let post = $fm | get $idx
    if (not $print) { ^$env.EDITOR $post.file } else { print $post.file }
  } else { exit 1 }
}
