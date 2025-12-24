import unittest
from volta.element import h
from volta.hooks import use_state, use_effect
from volta.reconciler import render
from volta.dom_renderer import InMemoryRenderer, MockNode

class TestVolta(unittest.TestCase):
    def test_basic_render(self):
        container = MockNode("ROOT")
        renderer = InMemoryRenderer()
        
        def App():
            return h("div", {"id": "app"}, 
                h("h1", {}, "Hello Volta"),
                h("p", {}, "This is a paragraph")
            )
            
        render(h(App), container, renderer)
        
        # Verify structure
        # ROOT -> div -> [h1, p]
        self.assertEqual(len(container.children), 1)
        root_div = container.children[0]
        self.assertEqual(root_div.tag, "div")
        self.assertEqual(root_div.props["id"], "app")
        self.assertEqual(len(root_div.children), 2)
        self.assertEqual(root_div.children[0].tag, "h1")
        self.assertEqual(root_div.children[0].children[0].text_content, "Hello Volta")

    def test_state_counter(self):
        container = MockNode("ROOT")
        renderer = InMemoryRenderer()
        
        # We need a way to capture the button to click it for the test
        captured_button = []

        def Counter():
            count, set_count = use_state(0)
            
            def increment():
                set_count(count + 1)
            
            return h("div", {},
                h("span", {}, f"Count: {count}"),
                h("button", {"on_click": increment, "ref_capture": lambda node: captured_button.append(node)}, "Increment")
            )
        
        # Initial Render
        reconciler = render(h(Counter), container, renderer)
        
        div = container.children[0]
        span = div.children[0]
        button = div.children[1]
        
        # Check Initial State
        self.assertIn("Count: 0", span.children[0].text_content)
        
        # Simulate Click
        # We found the button in the tree, we can manually trigger the handler if the renderer attached it.
        # InMemoryRenderer attaches on_click to event_handlers
        self.assertTrue("on_click" in button.event_handlers)
        button.click()
        
        # The reconciler schedule_update is triggered.
        # In our sync implementation, it should have updated immediately on the 'perform_unit_of_work' call inside the set_state.
        
        # Check Updated State
        # Re-fetch children references as they might have been replaced (though keys help reuse)
        div = container.children[0]
        span = div.children[0]
        self.assertIn("Count: 1", span.children[0].text_content)
        
        # Click again
        button = div.children[1]
        button.click()
        div = container.children[0]
        span = div.children[0]
        self.assertIn("Count: 2", span.children[0].text_content)

    def test_list_rendering(self):
        container = MockNode("ROOT")
        renderer = InMemoryRenderer()
        
        def ListComponent():
            items, set_items = use_state(["A", "B", "C"])
            return h("ul", {}, 
                [h("li", {"key": item}, item) for item in items]
            )
            
        render(h(ListComponent), container, renderer)
        
        ul = container.children[0]
        self.assertEqual(len(ul.children), 3)
        self.assertEqual(ul.children[0].children[0].text_content, "A")
        self.assertEqual(ul.children[2].children[0].text_content, "C")

if __name__ == '__main__':
    unittest.main()
