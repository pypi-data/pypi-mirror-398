"""Content editing with line/occurrence-specific operations"""

from typing import Callable, Dict, List, Optional, Tuple

from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


class ContentEditor:
    """Advanced content editing with precision operations"""

    @staticmethod
    def replace_at_line(content: str, line_num: int, old: str, new: str) -> str:
        """
        Replace text at specific line number

        Args:
            content: Original content
            line_num: Line number (1-indexed)
            old: Text to find
            new: Replacement text

        Returns:
            Modified content
        """
        lines = content.split('\n')

        if 0 < line_num <= len(lines):
            lines[line_num - 1] = lines[line_num - 1].replace(old, new)
            logger.debug(f"Replaced text at line {line_num}")
        else:
            logger.warning(f"Line {line_num} out of range (1-{len(lines)})")

        return '\n'.join(lines)

    @staticmethod
    def replace_nth_occurrence(content: str, old: str, new: str, n: int = 1) -> str:
        """
        Replace the nth occurrence of text

        Args:
            content: Original content
            old: Text to find
            new: Replacement text
            n: Which occurrence to replace (1-indexed)

        Returns:
            Modified content
        """
        count = 0
        result = []

        for line in content.split('\n'):
            if old in line:
                count += 1
                if count == n:
                    line = line.replace(old, new, 1)
                    logger.debug(f"Replaced occurrence #{n}")
            result.append(line)

        return '\n'.join(result)

    @staticmethod
    def replace_in_range(
        content: str,
        start_line: int,
        end_line: int,
        old: str,
        new: str
    ) -> str:
        """
        Replace text in line range

        Args:
            content: Original content
            start_line: Start line (1-indexed, inclusive)
            end_line: End line (1-indexed, inclusive)
            old: Text to find
            new: Replacement text

        Returns:
            Modified content
        """
        lines = content.split('\n')

        for i in range(start_line - 1, min(end_line, len(lines))):
            if 0 <= i < len(lines):
                lines[i] = lines[i].replace(old, new)

        logger.debug(f"Replaced text in lines {start_line}-{end_line}")

        return '\n'.join(lines)

    @staticmethod
    def replace_with_context(
        content: str,
        old: str,
        new: str,
        before: Optional[str] = None,
        after: Optional[str] = None
    ) -> str:
        """
        Replace text only when surrounded by specific context

        Args:
            content: Original content
            old: Text to find
            new: Replacement text
            before: Text that should appear before (optional)
            after: Text that should appear after (optional)

        Returns:
            Modified content
        """
        lines = content.split('\n')
        result = []

        for i, line in enumerate(lines):
            if old in line:
                # Check context
                before_match = not before or (i > 0 and before in lines[i-1])
                after_match = not after or (i < len(lines)-1 and after in lines[i+1])

                if before_match and after_match:
                    line = line.replace(old, new)
                    logger.debug(f"Replaced text with context at line {i+1}")

            result.append(line)

        return '\n'.join(result)

    @staticmethod
    def find_occurrences(content: str, pattern: str) -> List[Tuple[int, str]]:
        """
        Find all occurrences with line numbers

        Args:
            content: Content to search
            pattern: Text to find

        Returns:
            List of (line_number, line_content) tuples
        """
        occurrences = []

        for i, line in enumerate(content.split('\n'), 1):
            if pattern in line:
                occurrences.append((i, line.strip()))

        logger.debug(f"Found {len(occurrences)} occurrences of '{pattern}'")

        return occurrences

    @staticmethod
    def preview_changes(
        content: str,
        old: str,
        new: str,
        operation: Callable
    ) -> Dict[str, any]:
        """
        Preview what changes will be made

        Args:
            content: Original content
            old: Text to find
            new: Replacement text
            operation: Operation function to apply

        Returns:
            Dictionary with change details
        """
        new_content = operation(content, old, new)

        old_lines = content.split('\n')
        new_lines = new_content.split('\n')

        changes = []
        for i, (old_line, new_line) in enumerate(zip(old_lines, new_lines), 1):
            if old_line != new_line:
                changes.append({
                    'line': i,
                    'old': old_line.strip(),
                    'new': new_line.strip()
                })

        return {
            'total_changes': len(changes),
            'changes': changes
        }
