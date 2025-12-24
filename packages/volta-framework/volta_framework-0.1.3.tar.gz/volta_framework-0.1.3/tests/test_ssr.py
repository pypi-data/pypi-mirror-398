
import unittest
import sys
import os
from io import StringIO
from unittest.mock import patch, MagicMock

# Ensure volta is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from volta.html_renderer import HTMLRenderer
from volta.reconciler import render
from volta.element import h
from volta.transpiler import transpile

class TestSSR(unittest.TestCase):
    def test_simple_render_string(self):
        """Test that HTMLRenderer produces correct HTML string"""
        renderer = HTMLRenderer()
        root = renderer.create_instance("div", {"id": "test"})
        child = renderer.create_instance("span", {"className": "greeting"})
        text = renderer.create_text_instance("Hello")
        
        renderer.append_child(child, text)
        renderer.append_child(root, child)
        
        html = str(root)
        self.assertIn('<div id="test">', html)
        self.assertIn('<span class="greeting">Hello</span></div>', html)
        
    def test_double_root_bug(self):
        """Verify the double root rendering bug is gone"""
        renderer = HTMLRenderer()
        root = renderer.create_instance("div", {"id": "root"})
        
        # Simulate what the Reconciler does
        # It appends children.
        child = renderer.create_instance("h1", {})
        renderer.append_child(child, renderer.create_text_instance("Header"))
        renderer.append_child(root, child)
        
        html = str(root)
        # Should be <div id="root"><h1>Header</h1></div>
        # Bug was producing: <div id="root"><h1>Header</h1></div><div id="root"><h1>Header</h1></div>
        
        self.assertEqual(html.count('<div id="root">'), 1)
        # Expect <h1>...</h1> inside <div>...</div>. So only one </div>
        self.assertEqual(html.count('</div>'), 1) 

    def test_transpiler_simple(self):
        source = "<div>Hello</div>"
        transpiled = transpile(source)
        self.assertIn('h("div"', transpiled)
        # Transpiler might use single or double quotes
        self.assertTrue("'Hello'" in transpiled or '"Hello"' in transpiled)

if __name__ == "__main__":
    unittest.main()
