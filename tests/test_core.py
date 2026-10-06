import unittest

from path_component_case_conflict_checker import Conflict, find_conflicts


class TestFindConflicts(unittest.TestCase):
    def test_no_conflicts(self):
        self.assertEqual(find_conflicts(["a/b", "c/d", "e/f"]), [])

    def test_single_path(self):
        self.assertEqual(find_conflicts(["a/b"]), [])

    def test_empty_list(self):
        self.assertEqual(find_conflicts([]), [])

    def test_simple_case_conflict(self):
        result = find_conflicts(["Foo/bar", "foo/bar"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key, "foo/bar")
        self.assertEqual(result[0].paths, ("Foo/bar", "foo/bar"))

    def test_multiple_components_differ(self):
        result = find_conflicts(["Foo/Bar", "foo/bar"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key, "foo/bar")
        self.assertEqual(result[0].paths, ("Foo/Bar", "foo/bar"))

    def test_no_conflict_when_components_differ(self):
        self.assertEqual(find_conflicts(["Foo/bar", "foo/qux"]), [])

    def test_no_conflict_at_different_depth(self):
        self.assertEqual(find_conflicts(["a/Foo", "Foo"]), [])

    def test_three_way_conflict(self):
        result = find_conflicts(["Foo", "FOO", "foo"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key, "foo")
        self.assertEqual(result[0].paths, ("Foo", "FOO", "foo"))

    def test_mixed_conflicting_and_not(self):
        result = find_conflicts(["a/b", "A/B", "c/d", "A/B", "e/f"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key, "a/b")
        self.assertEqual(result[0].paths, ("a/b", "A/B", "A/B"))

    def test_multiple_independent_conflicts(self):
        result = find_conflicts(["Foo", "foo", "Bar", "bar"])
        keys = [c.key for c in result]
        self.assertEqual(set(keys), {"foo", "bar"})
        # Groups ordered by first-seen member.
        self.assertEqual(keys, ["foo", "bar"])
        for c in result:
            self.assertEqual(len(c.paths), 2)

    def test_order_preserved_within_group(self):
        result = find_conflicts(["FOO", "foo", "Foo"])
        self.assertEqual(result[0].paths, ("FOO", "foo", "Foo"))

    def test_conflict_grouping_preserves_input_order(self):
        # Even though 'bar' appears before 'Foo' in input, the conflict
        # groups are ordered by first appearance of each key.
        result = find_conflicts(["bar", "Foo", "BAR", "foo"])
        keys = [c.key for c in result]
        self.assertEqual(keys, ["bar", "foo"])


class TestEdgeCases(unittest.TestCase):
    def test_repeated_slashes_collapsed(self):
        # `a//b` and `a/b` should be considered the same logical path
        # and thus a conflict.
        result = find_conflicts(["a//b", "a/b"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key, "a/b")

    def test_leading_and_trailing_slashes_kept(self):
        # Leading/trailing slashes are kept as components-of-context.
        # `/foo` and `foo` are NOT the same path here.
        self.assertEqual(find_conflicts(["/foo", "foo"]), [])

    def test_trailing_slash_collision(self):
        result = find_conflicts(["foo/", "Foo/"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key, "foo")

    def test_dot_components(self):
        # `.` is a real component and can collide.
        result = find_conflicts(["./Foo", "./foo"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key, "./foo")

    def test_unicode_case_folding(self):
        # The German ß uppercases to SS; lowercasing SS yields ss, but
        # lowercasing ß yields ß. These are NOT equal under .lower(),
        # so they should not conflict.
        self.assertEqual(find_conflicts(["Straße", "STRASSE"]), [])

    def test_simple_unicode_conflict(self):
        result = find_conflicts(["Café", "café"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key, "café")


class TestConflictDataclass(unittest.TestCase):
    def test_post_init_rejects_mismatched_key(self):
        with self.assertRaises(ValueError):
            Conflict(key="foo", paths=("bar",))

    def test_post_init_accepts_consistent(self):
        c = Conflict(key="foo", paths=("Foo", "FOO"))
        self.assertEqual(c.key, "foo")
        self.assertEqual(c.paths, ("Foo", "FOO"))

    def test_conflict_is_hashable(self):
        c = Conflict(key="foo", paths=("Foo",))
        # Should not raise.
        hash(c)


class TestInputValidation(unittest.TestCase):
    def test_non_list_input_raises(self):
        with self.assertRaises(TypeError):
            find_conflicts(("a", "b"))  # type: ignore[arg-type]

    def test_non_str_element_raises(self):
        with self.assertRaises(TypeError):
            find_conflicts(["a", 1])  # type: ignore[list-item]


if __name__ == "__main__":
    unittest.main()
