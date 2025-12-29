from typing import List

from ..core.chapter import Chapter
from ..exceptions.epub_exceptions import TOCError


class TOCGenerator:
    """Tool class for generating EPUB table of contents"""

    @staticmethod
    def create_nav_content(chapters: List[Chapter]) -> str:
        """Generate navigation content with proper EPUB3 structure"""
        try:

            if not chapters:
                # Return minimal TOC for empty chapters with required li element
                return """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh" xml:lang="zh">
<head>
    <title>Table of Contents</title>
    <meta charset="utf-8"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>Table of Contents</h1>
        <ol>
            <li>No chapters available</li>
        </ol>
    </nav>
</body>
</html>"""

            nav_content = [
                '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh" xml:lang="zh">',
                "<head>",
                "    <title>Table of Contents</title>",
                '    <meta charset="utf-8"/>',
                "</head>",
                "<body>",
                '    <nav epub:type="toc" id="toc">',
                "        <h1>Table of Contents</h1>",
                "        <ol>",
            ]

            # Build the TOC structure recursively
            def build_toc_level(
                chapter_list: List[Chapter], start_idx: int, target_level: int
            ) -> int:
                """Recursively build TOC for a specific level"""
                i = start_idx
                while i < len(chapter_list):
                    chapter = chapter_list[i]
                    current_level = {"h1": 1, "h2": 2, "h3": 3, "intro": 0}[
                        chapter.level
                    ]

                    if current_level < target_level:
                        # We've gone up a level, stop processing this level
                        break
                    elif current_level == target_level:
                        # Add this chapter at current level
                        nav_content.append(
                            f'            <li><a href="{chapter.file_name}">{chapter.title}</a>'
                        )

                        # Check if next chapter is a child (higher level)
                        if i + 1 < len(chapter_list):
                            next_level = {"h1": 1, "h2": 2, "h3": 3, "intro": 0}[
                                chapter_list[i + 1].level
                            ]
                        else:
                            next_level = 0

                        if next_level > current_level:
                            # Has children at some higher level, create nested list
                            nav_content.append("                <ol>")
                            original_i = i
                            # Find the actual level of the next chapter and process it
                            actual_next_level = {"h1": 1, "h2": 2, "h3": 3, "intro": 0}[
                                chapter_list[i + 1].level
                            ]
                            end_i = build_toc_level(
                                chapter_list, i + 1, actual_next_level
                            )
                            # Only add closing </ol> if we actually processed children
                            if end_i > original_i + 1:
                                nav_content.append("                </ol>")
                            else:
                                # Remove the empty <ol> if no children were processed
                                nav_content.pop()
                            # Continue from where the recursion left off
                            i = end_i - 1  # -1 because i += 1 will happen at the end

                        nav_content.append("            </li>")
                        i += 1
                    else:
                        # Skip chapters at deeper levels (they're handled by recursion)
                        i += 1

                return i

            # Process all chapters using hierarchical structure
            if chapters:
                # First, add intro chapter if it exists
                intro_processed = False
                for i, chapter in enumerate(chapters):
                    if chapter.level == "intro":
                        nav_content.append(
                            f'            <li><a href="{chapter.file_name}">{chapter.title}</a></li>'
                        )
                        intro_processed = True
                        break

                # Then process h1 chapters and their children
                if intro_processed:
                    start_idx = 1  # Skip intro
                else:
                    start_idx = 0

                build_toc_level(chapters, start_idx, 1)  # Start from h1 level

            nav_content.extend(
                ["        </ol>", "    </nav>", "</body>", "</html>"])

            return "\n".join(nav_content)

        except Exception as e:
            raise TOCError(f"Error generating table of contents: {e}")
