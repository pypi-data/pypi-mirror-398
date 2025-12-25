from pathlib import Path

from zona import util


def test_title(tmp_path: Path):
	a = tmp_path / "my-first-post.md"
	b = tmp_path / "Writing_emails_Post.md"
	assert util.filename_to_title(a) == "My First Post"
	assert util.filename_to_title(b) == "Writing Emails Post"


def test_get_resourcees():
	util.get_resources("templates")
	assert True
