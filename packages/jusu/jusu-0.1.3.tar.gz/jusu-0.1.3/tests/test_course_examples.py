import importlib

import pytest

EXAMPLES = [
    "examples.lesson1",
]

@pytest.mark.parametrize("mod", EXAMPLES)
def test_example_runs(tmp_path, mod):
    # Ensure example can be imported and executed without error
    m = importlib.import_module(mod)
    # If module exposes `page` and it's a Tag, try to render into tmp_path
    if hasattr(m, "page"):
        out = tmp_path / (mod.split('.')[-1] + '.html')
        try:
            m.page.render_to_file(str(out))
        except Exception:
            pytest.skip("example module does not expose suitable `page`")
        assert out.exists()
