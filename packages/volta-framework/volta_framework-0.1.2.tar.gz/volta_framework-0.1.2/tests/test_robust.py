
import unittest
from volta import h, fragment, use_state, use_effect, use_ref, use_memo, use_callback, create_context, use_context, render
from volta.dom_renderer import InMemoryRenderer, MockNode
from volta.html_renderer import HTMLRenderer
from volta.transpiler import transpile

class TestVoltaRobust(unittest.TestCase):

    def setUp(self):
        self.root = MockNode("ROOT")
        self.renderer = InMemoryRenderer()

    # --- Transpiler Tests ---
    def test_transpiler_simple(self):
        jsx = '<div>Hello</div>'
        py = transpile(jsx)
        self.assertIn('h("div", {},', py)
        self.assertIn("'Hello'", py)

    def test_transpiler_props(self):
        jsx = '<div id="1" className={cls}></div>'
        py = transpile(jsx)
        # Transpiler uses repr() which often uses single quotes for simple strings
        # "id": '1'
        self.assertTrue('"id": \'1\'' in py or "'id': '1'" in py or '"id": "1"' in py)
        self.assertIn('"className": cls', py)

    def test_transpiler_nested(self):
        jsx = '<ul><li>A</li></ul>'
        py = transpile(jsx)
        self.assertIn('h("ul", {},', py)
        self.assertIn('h("li", {},', py)

    # --- HTML Renderer Tests ---
    def test_html_renderer(self):
        root = HTMLRenderer().create_instance("div", {"id": "test"})
        # We need a dummy wrapper for render if we want to test reconciler + html, 
        # or just test the string output of the classes.
        
        # Testing Reconciler + HTMLRenderer
        def App():
            return h("span", {"class": "bold"}, "Content")
            
        render(h(App), root, HTMLRenderer())
        self.assertEqual(str(root), '<div id="test"><span class="bold">Content</span></div>')

    # --- Hooks Tests ---

    def test_use_state_functional_update(self):
        # Test updating state with a function lambda x: x+1
        def Counter():
            count, set_count = use_state(0)
            
            def inc():
                set_count(lambda c: c + 1)
            
            return h("button", {"onClick": inc}, count)

        render(h(Counter), self.root, self.renderer)
        btn = self.root.children[0]
        self.assertEqual(btn.children[0].text_content, "0")
        
        # Click
        btn.event_handlers["onClick"]()
        self.assertEqual(self.root.children[0].children[0].text_content, "1")

    def test_use_effect_lifecycle(self):
        effects_log = []
        
        def EffectComp():
            count, set_count = use_state(0)
            
            def effect():
                effects_log.append(f"Run {count}")
                def cleanup():
                    effects_log.append(f"Cleanup {count}")
                return cleanup
            
            use_effect(effect, [count])
            
            return h("button", {"onClick": lambda: set_count(count + 1)}, "Next")

        render(h(EffectComp), self.root, self.renderer)
        self.assertEqual(effects_log, ["Run 0"])
        
        # Update
        self.root.children[0].event_handlers["onClick"]()
        # Should clean up 0 and run 1
        self.assertEqual(effects_log, ["Run 0", "Cleanup 0", "Run 1"])

    def test_use_ref(self):
        def RefComp():
            ref = use_ref(0)
            count, set_count = use_state(0)
            
            def inc():
                ref["current"] += 1
                set_count(count + 1)
                
            return h("div", {}, f"Ref: {ref['current']}", h("button", {"onClick": inc}))

        render(h(RefComp), self.root, self.renderer)
        div = self.root.children[0]
        self.assertIn("Ref: 0", div.children[0].text_content)
        
        # Click button
        div.children[1].event_handlers["onClick"]()
        
        # Ref persists
        self.assertIn("Ref: 1", self.root.children[0].children[0].text_content)

    def test_use_memo(self):
        calculations = 0
        def MemoComp():
            count, set_count = use_state(0)
            other, set_other = use_state(0)
            
            def expensive():
                nonlocal calculations
                calculations += 1
                return count * 2
                
            val = use_memo(expensive, [count])
            
            return h("div", {
                "onUpdateCount": lambda: set_count(count + 1),
                "onUpdateOther": lambda: set_other(other + 1)
            }, val)

        render(h(MemoComp), self.root, self.renderer)
        self.assertEqual(calculations, 1) # Initial
        
        div = self.root.children[0]
        # Update Other -> Deps didn't change -> Should not recalc
        div.event_handlers["onUpdateOther"]()
        self.assertEqual(calculations, 1)
        
        # Update Count -> Deps changed -> Recalc
        div.event_handlers["onUpdateCount"]()
        self.assertEqual(calculations, 2)


    def test_context(self):
        ThemeCtx = create_context("light")
        
        def Child():
            theme = use_context(ThemeCtx)
            return h("span", {}, theme)
            
        def App():
            theme, set_theme = use_state("dark")
            return h(ThemeCtx.Provider, {"value": theme},
                h("div", {}, h(Child)),
                h("button", {"onClick": lambda: set_theme("blue")})
            )
            
        render(h(App), self.root, self.renderer)
        span = self.root.children[0].children[0]
        self.assertEqual(span.children[0].text_content, "dark")
        
        # Update Context Provider
        self.root.children[1].event_handlers["onClick"]()
        
        span = self.root.children[0].children[0]
        self.assertEqual(span.children[0].text_content, "blue")

    # --- Reconciliation Tests ---

    def test_keyed_list_reordering(self):
        def ListApp():
            # State: [A, B, C] -> [C, A, B] (Rotate)
            items, set_items = use_state(["A", "B", "C"])
            
            def rotate():
                new_items = [items[2], items[0], items[1]]
                set_items(new_items)
                
            return h("div", {},
                h("ul", {}, [h("li", {"key": i}, i) for i in items]),
                h("button", {"onClick": rotate})
            )
            
        render(h(ListApp), self.root, self.renderer)
        ul = self.root.children[0].children[0]
        li_elements = ul.children
        self.assertEqual([li.children[0].text_content for li in li_elements], ["A", "B", "C"])
        
        # Capture original mock node instances to verify reuse
        original_node_a = li_elements[0]
        
        # Rotate
        self.root.children[0].children[1].event_handlers["onClick"]()
        
        ul = self.root.children[0].children[0]
        li_elements = ul.children
        self.assertEqual([li.children[0].text_content for li in li_elements], ["C", "A", "B"])
        
        # Verify A was reused (not recreated)
        self.assertIs(li_elements[1], original_node_a, "Node A should be the exact same instance moved")

    def test_conditional_rendering_unmount(self):
        # Test mounting and unmounting
        def CondApp():
            show, set_show = use_state(True)
            return h("div", {"onClick": lambda: set_show(not show)},
                h("span", {}, "Visible") if show else None
            )
            
        render(h(CondApp), self.root, self.renderer)
        div = self.root.children[0]
        self.assertEqual(len(div.children), 1)
        self.assertEqual(div.children[0].tag, "span")
        
        # Toggle
        div.event_handlers["onClick"]()
        div = self.root.children[0]
        self.assertEqual(len(div.children), 0)
        
        # Toggle back
        div.event_handlers["onClick"]()
        div = self.root.children[0]
        self.assertEqual(len(div.children), 1)

if __name__ == '__main__':
    unittest.main()
