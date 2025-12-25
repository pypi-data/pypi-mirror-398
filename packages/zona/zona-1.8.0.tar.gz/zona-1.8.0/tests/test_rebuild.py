from pathlib import Path

from zona.builder import ZonaBuilder


def write_config(root: Path):
	(root / "config.yml").write_text("feed:\n  enabled: false\n")


def test_rebuild_updates_markdown(tmp_path: Path):
	write_config(tmp_path)
	content = tmp_path / "content"
	content.mkdir()
	page = content / "about.md"
	other = content / "contact.md"
	page.write_text("# Hello")
	other.write_text("# Contact")

	builder = ZonaBuilder(tmp_path, tmp_path / "public")
	builder.build()

	about_out = tmp_path / "public" / "about" / "index.html"
	contact_out = tmp_path / "public" / "contact" / "index.html"
	original_contact = contact_out.read_text()

	page.write_text("# Updated")
	builder.rebuild(changed={page}, deleted=set(), added=set())

	assert "Updated" in about_out.read_text()
	assert contact_out.read_text() == original_contact


def test_rebuild_adds_post_updates_nav(tmp_path: Path):
	write_config(tmp_path)
	content = tmp_path / "content" / "blog"
	content.mkdir(parents=True)

	first = content / "first.md"
	first.write_text(
		"""---
title: First
date: 2024-01-01
---

# First
"""
	)
	builder = ZonaBuilder(tmp_path, tmp_path / "public")
	builder.build()

	first_out = tmp_path / "public" / "blog" / "first" / "index.html"
	assert ">newr</a>" not in first_out.read_text()

	second = content / "second.md"
	second.write_text(
		"""---
title: Second
date: 2025-01-01
---

# Second
"""
	)
	builder.rebuild(changed=set(), deleted=set(), added={second})

	assert ">newr</a>" in first_out.read_text()


def test_rebuild_deletes_static(tmp_path: Path):
	write_config(tmp_path)
	static = tmp_path / "content" / "static"
	static.mkdir(parents=True)
	style = static / "style.css"
	style.write_text("body { color: red; }")

	builder = ZonaBuilder(tmp_path, tmp_path / "public")
	builder.build()

	out_style = tmp_path / "public" / "static" / "style.css"
	assert out_style.exists()

	style.unlink()
	builder.rebuild(changed=set(), deleted={style}, added=set())

	assert not out_style.exists()
