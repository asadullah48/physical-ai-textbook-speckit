"""MDX parser for extracting content from textbook chapters.

This module parses MDX files and extracts structured content including:
- Frontmatter metadata (title, description, week, etc.)
- Code blocks with language and metadata
- Text content for RAG embedding
- Exercise definitions
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class CodeBlock:
    """Represents a code block from MDX content."""

    language: str
    code: str
    title: Optional[str] = None
    line_start: int = 0


@dataclass
class Exercise:
    """Represents an exercise from MDX content."""

    title: str
    difficulty: str
    estimated_time: int
    exercise_type: str
    content: str
    hint: Optional[str] = None


@dataclass
class ContentChunk:
    """A chunk of content for embedding."""

    text: str
    section: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedMDX:
    """Result of parsing an MDX file."""

    # Metadata from frontmatter
    title: str
    description: str
    module_id: str
    chapter_id: str
    week: Optional[int] = None
    estimated_time: Optional[int] = None
    difficulty: Optional[str] = None
    learning_objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    # Content
    sections: Dict[str, str] = field(default_factory=dict)
    code_blocks: List[CodeBlock] = field(default_factory=list)
    exercises: List[Exercise] = field(default_factory=list)
    chunks: List[ContentChunk] = field(default_factory=list)

    # Raw content for full-text search
    raw_text: str = ""


class MDXParser:
    """Parser for MDX files with frontmatter and custom components."""

    # Regex patterns
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(
        r"```(\w+)?(?:\s+title=\"([^\"]+)\")?\n(.*?)```", re.DOTALL
    )
    EXERCISE_PATTERN = re.compile(
        r"<Exercise\s+(.*?)>(.*?)</Exercise>", re.DOTALL
    )
    EXERCISE_ATTR_PATTERN = re.compile(
        r'(\w+)=(?:"([^"]*)"|{(\d+|\w+)})'
    )
    JSX_IMPORT_PATTERN = re.compile(r"^import\s+.*?from\s+['\"].*?['\"];?\s*$", re.MULTILINE)
    JSX_COMPONENT_PATTERN = re.compile(r"<(\w+)[^>]*/>|<(\w+)[^>]*>.*?</\2>", re.DOTALL)

    # Components to strip (but preserve content)
    STRIP_COMPONENTS = ["Tabs", "TabItem", "Exercise"]

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """Initialize parser.

        Args:
            chunk_size: Target size for content chunks (in characters).
            chunk_overlap: Overlap between consecutive chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_file(self, file_path: Path) -> ParsedMDX:
        """Parse an MDX file.

        Args:
            file_path: Path to the MDX file.

        Returns:
            ParsedMDX object with extracted content.
        """
        content = file_path.read_text(encoding="utf-8")
        return self.parse_content(content, file_path)

    def parse_content(self, content: str, file_path: Optional[Path] = None) -> ParsedMDX:
        """Parse MDX content string.

        Args:
            content: Raw MDX content.
            file_path: Optional file path for context.

        Returns:
            ParsedMDX object with extracted content.
        """
        # Extract module and chapter IDs from path
        module_id = ""
        chapter_id = ""
        if file_path:
            parts = file_path.parts
            for i, part in enumerate(parts):
                if part.startswith("module-"):
                    module_id = part
                    if i + 1 < len(parts):
                        chapter_id = parts[i + 1].replace(".mdx", "")
                    break

        # Parse frontmatter
        frontmatter = self._parse_frontmatter(content)

        # Remove frontmatter from content
        content_body = self.FRONTMATTER_PATTERN.sub("", content)

        # Remove imports
        content_body = self.JSX_IMPORT_PATTERN.sub("", content_body)

        # Extract code blocks
        code_blocks = self._extract_code_blocks(content_body)

        # Extract exercises
        exercises = self._extract_exercises(content_body)

        # Extract sections
        sections = self._extract_sections(content_body)

        # Clean content for text extraction
        clean_text = self._clean_content(content_body)

        # Create chunks for embedding
        chunks = self._create_chunks(clean_text, sections, module_id, chapter_id)

        return ParsedMDX(
            title=frontmatter.get("title", ""),
            description=frontmatter.get("description", ""),
            module_id=module_id,
            chapter_id=chapter_id,
            week=frontmatter.get("week"),
            estimated_time=frontmatter.get("estimated_time"),
            difficulty=frontmatter.get("difficulty"),
            learning_objectives=frontmatter.get("learning_objectives", []),
            prerequisites=frontmatter.get("prerequisites", []),
            keywords=frontmatter.get("keywords", []),
            sections=sections,
            code_blocks=code_blocks,
            exercises=exercises,
            chunks=chunks,
            raw_text=clean_text,
        )

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract and parse YAML frontmatter."""
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}

        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}

    def _extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """Extract code blocks from content."""
        blocks = []
        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            blocks.append(
                CodeBlock(
                    language=match.group(1) or "text",
                    title=match.group(2),
                    code=match.group(3).strip(),
                    line_start=content[:match.start()].count("\n") + 1,
                )
            )
        return blocks

    def _extract_exercises(self, content: str) -> List[Exercise]:
        """Extract Exercise components from content."""
        exercises = []
        for match in self.EXERCISE_PATTERN.finditer(content):
            attrs = {}
            for attr_match in self.EXERCISE_ATTR_PATTERN.finditer(match.group(1)):
                key = attr_match.group(1)
                value = attr_match.group(2) or attr_match.group(3)
                if key == "estimatedTime":
                    attrs["estimated_time"] = int(value)
                elif key == "type":
                    attrs["exercise_type"] = value
                else:
                    attrs[key] = value

            exercises.append(
                Exercise(
                    title=attrs.get("title", "Untitled Exercise"),
                    difficulty=attrs.get("difficulty", "beginner"),
                    estimated_time=attrs.get("estimated_time", 10),
                    exercise_type=attrs.get("exercise_type", "conceptual"),
                    content=match.group(2).strip(),
                    hint=attrs.get("hint"),
                )
            )
        return exercises

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections by headings."""
        sections = {}
        current_section = "Introduction"
        current_content = []

        lines = content.split("\n")
        for line in lines:
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = heading_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _clean_content(self, content: str) -> str:
        """Clean content for text extraction."""
        # Remove code blocks (keep description, remove code)
        content = self.CODE_BLOCK_PATTERN.sub("[code example]", content)

        # Remove JSX components but keep inner content for some
        content = re.sub(r"<Tabs>|</Tabs>|<TabItem[^>]*>|</TabItem>", "", content)
        content = self.EXERCISE_PATTERN.sub(r"\2", content)

        # Remove remaining JSX
        content = re.sub(r"<[^>]+/>", "", content)
        content = re.sub(r":::\w+.*?:::", "", content, flags=re.DOTALL)

        # Clean up whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip()

    def _create_chunks(
        self,
        text: str,
        sections: Dict[str, str],
        module_id: str,
        chapter_id: str,
    ) -> List[ContentChunk]:
        """Create chunks for embedding."""
        chunks = []
        chunk_index = 0

        for section_name, section_text in sections.items():
            # Clean section text
            clean_text = self._clean_content(section_text)
            if not clean_text:
                continue

            # Split into chunks
            words = clean_text.split()
            current_chunk = []
            current_length = 0

            for word in words:
                current_chunk.append(word)
                current_length += len(word) + 1

                if current_length >= self.chunk_size:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(
                        ContentChunk(
                            text=chunk_text,
                            section=section_name,
                            chunk_index=chunk_index,
                            metadata={
                                "module_id": module_id,
                                "chapter_id": chapter_id,
                                "section": section_name,
                            },
                        )
                    )
                    chunk_index += 1

                    # Keep overlap
                    overlap_words = current_chunk[-10:]  # ~50 chars
                    current_chunk = overlap_words
                    current_length = sum(len(w) + 1 for w in overlap_words)

            # Add remaining content
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) > 50:  # Skip very small chunks
                    chunks.append(
                        ContentChunk(
                            text=chunk_text,
                            section=section_name,
                            chunk_index=chunk_index,
                            metadata={
                                "module_id": module_id,
                                "chapter_id": chapter_id,
                                "section": section_name,
                            },
                        )
                    )
                    chunk_index += 1

        return chunks


def parse_mdx_directory(docs_path: Path) -> List[ParsedMDX]:
    """Parse all MDX files in a directory.

    Args:
        docs_path: Path to the docs directory.

    Returns:
        List of ParsedMDX objects.
    """
    parser = MDXParser()
    results = []

    for mdx_file in docs_path.rglob("*.mdx"):
        try:
            parsed = parser.parse_file(mdx_file)
            results.append(parsed)
        except Exception as e:
            print(f"Error parsing {mdx_file}: {e}")

    return results
