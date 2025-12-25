"""Tests for ContentEditor"""

from praisonaiwp.editors.content_editor import ContentEditor


class TestContentEditor:
    """Test ContentEditor functionality"""

    def test_replace_at_line(self, sample_post_content):
        """Test replacing text at specific line"""
        editor = ContentEditor()

        # Replace at line 2
        result = editor.replace_at_line(
            sample_post_content,
            2,
            "Welcome to Our Site",
            "My Website Title"
        )

        lines = result.split('\n')
        assert "My Website Title" in lines[1]
        assert "Welcome to Our Site" in lines[9]  # Line 10 unchanged (0-indexed line 9)

    def test_replace_nth_occurrence(self, sample_post_content):
        """Test replacing nth occurrence"""
        editor = ContentEditor()

        # Replace 1st occurrence
        result = editor.replace_nth_occurrence(
            sample_post_content,
            "Welcome to Our Site",
            "First Site",
            1
        )

        assert result.count("First Site") == 1
        assert result.count("Welcome to Our Site") == 1

        # Replace 2nd occurrence
        result = editor.replace_nth_occurrence(
            sample_post_content,
            "Welcome to Our Site",
            "Second Site",
            2
        )

        assert result.count("Second Site") == 1
        assert result.count("Welcome to Our Site") == 1

    def test_replace_in_range(self):
        """Test replacing in line range"""
        content = "line1\nline2\nline3\nline4\nline5"
        editor = ContentEditor()

        result = editor.replace_in_range(content, 2, 4, "line", "LINE")

        lines = result.split('\n')
        assert lines[0] == "line1"  # Unchanged
        assert lines[1] == "LINE2"  # Changed
        assert lines[2] == "LINE3"  # Changed
        assert lines[3] == "LINE4"  # Changed
        assert lines[4] == "line5"  # Unchanged

    def test_replace_with_context(self):
        """Test context-aware replacement"""
        content = """before1
target text
after1

before2
target text
after2"""

        editor = ContentEditor()

        # Replace only when after "before1"
        result = editor.replace_with_context(
            content,
            "target text",
            "REPLACED",
            before="before1"
        )

        assert result.count("REPLACED") == 1
        assert result.count("target text") == 1

    def test_find_occurrences(self, sample_post_content):
        """Test finding occurrences"""
        editor = ContentEditor()

        occurrences = editor.find_occurrences(
            sample_post_content,
            "Welcome to Our Site"
        )

        assert len(occurrences) == 2
        assert occurrences[0][0] == 2  # Line 2
        assert occurrences[1][0] == 10  # Line 10 (not 8)

    def test_preview_changes(self):
        """Test preview changes"""
        content = "line1\nline2\nline3"
        editor = ContentEditor()

        def replace_op(c, old, new):
            return c.replace(old, new)

        preview = editor.preview_changes(content, "line2", "LINE2", replace_op)

        assert preview['total_changes'] == 1
        assert preview['changes'][0]['line'] == 2
        assert preview['changes'][0]['old'] == "line2"
        assert preview['changes'][0]['new'] == "LINE2"

    def test_replace_at_invalid_line(self):
        """Test replacing at invalid line number"""
        content = "line1\nline2\nline3"
        editor = ContentEditor()

        # Line out of range
        result = editor.replace_at_line(content, 10, "line", "LINE")

        # Should return unchanged
        assert result == content

    def test_replace_nth_occurrence_not_found(self):
        """Test replacing nth occurrence when n is too large"""
        content = "text1\ntext2"
        editor = ContentEditor()

        # Try to replace 5th occurrence (doesn't exist)
        result = editor.replace_nth_occurrence(content, "text", "TEXT", 5)

        # Should return unchanged
        assert result == content
