from zona.markdown import md_to_html


def test_render():
	content = "# Hello World!"
	out = md_to_html(content, None)
	assert "<h1" in out
	assert "Hello World!" in out
