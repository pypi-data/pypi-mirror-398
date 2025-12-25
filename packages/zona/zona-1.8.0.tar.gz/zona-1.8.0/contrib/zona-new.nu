#!/usr/bin/env -S nu -n --no-std-lib
# Author: Daniel Fichtinger
# License: BSD-3

# This script makes it convenient to create a new blog post.
# User is prompted for title, filename, date, description, draft status.
# Optionally open the editor.

# helper function. creates the post from given metadata record.
def create_post [meta: record, dry: bool] {
  # assume cwd is project root
  let file = "content/blog/" ++ $meta.filename
  # get final frontmatter
  let fm = $meta | reject filename

  # generate delimited yaml string
  let out = "---"
  | append ($fm | to yaml)
  | str trim --right
  | append "---"
  | str join (char newline)
  if (not $dry) {
    $out | save $file
    # prompt for opening editor
    print 'Edit? (y/n)'
    loop {
      let key = (input listen --types [key])
      if ($key.code == 'y') {
        ^$env.EDITOR $file
        exit 0
      } else if ($key.code == 'n') {
        exit 0
      }
    }
  } else {
    print $out
    print 'Dry run, not writing file.'
  }
}

def main [--dry-run (-d)] {
  let title: string = (input "Title: ")
  print 'Note: filename will have .md appended automatically.'
  let fn: path = (
    (input --default ($title | str kebab-case) "Filename: ") ++ '.md'
  )
  def dfmt [] {
    $in | format date "%Y-%m-%d"
  }
  let date: string = (
    input --default (date now | dfmt)
    "Date: "
    | date from-human
    | dfmt
  )
  let draft: bool = (
    input --default 'true' "Draft: " | into bool
  )
  let desc: string = (
    input --default 'none' "Description: "
    | if ($in != 'none') { $in }
  )

  let meta = {
    title: $title,
    filename: $fn
    date: $date
    draft: $draft
    description: $desc
  }

  print "This file will be created:"
  print $meta
  print "Ok? (y/n)"

  loop {
    let key = (input listen --types [key])
    if ($key.code == 'y') {
      create_post $meta $dry_run
      exit 0
    } else if ($key.code == 'n') {
      print 'Aborting.'
      exit 1
    }
  }
}

