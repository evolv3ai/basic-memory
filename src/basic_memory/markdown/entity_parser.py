"""Parser for markdown files into Entity objects.

Uses markdown-it with plugins to parse structured data from markdown content.
"""
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
import dateparser

from markdown_it import MarkdownIt
import frontmatter

from basic_memory.markdown.plugins import observation_plugin, relation_plugin
from basic_memory.markdown.schemas import (
    EntityMarkdown,
    EntityFrontmatter,
    Observation,
    Relation,
)

md = MarkdownIt().use(observation_plugin).use(relation_plugin)

@dataclass
class EntityContent:
    content: str 
    observations: list[Observation] = field(default_factory=list) 
    relations: list[Relation] = field(default_factory=list) 


def parse(content: str) -> EntityContent:
    """Parse markdown content into EntityMarkdown."""

    # Parse content for observations and relations using markdown-it
    observations = []
    relations = []

    if content:
        for token in md.parse(content):
            # check for observations and relations
            if token.meta:
                if "observation" in token.meta:
                    obs = token.meta["observation"]
                    observation = Observation.model_validate(obs)
                    observations.append(observation)
                if "relations" in token.meta:
                    rels = token.meta["relations"]
                    relations.extend([Relation.model_validate(r) for r in rels])

    return EntityContent(
        content=content,
        observations=observations,
        relations=relations,
    )


class EntityParser:
    """Parser for markdown files into Entity objects."""

    def __init__(self, base_path: Path):
        """Initialize parser with base path for relative permalink generation."""
        self.base_path = base_path.resolve()


    def relative_path(self, file_path: Path) -> str:
        """Get file path relative to base_path.

        Example:
            base_path: /project/root
            file_path: /project/root/design/models/data.md
            returns: "design/models/data"
        """
        # Get relative path and remove .md extension
        rel_path = file_path.resolve().relative_to(self.base_path)
        if rel_path.suffix.lower() == ".md":
            return str(rel_path.with_suffix(""))
        return str(rel_path)

    def parse_date(self, value: Any) -> Optional[datetime]:
        """Parse date strings using dateparser for maximum flexibility.

        Supports human friendly formats like:
        - 2024-01-15
        - Jan 15, 2024
        - 2024-01-15 10:00 AM
        - yesterday
        - 2 days ago
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                parsed = dateparser.parse(value)
                if parsed:
                    return parsed
            except Exception:
                pass
        return None

    async def parse_file(self, file_path: Path) -> EntityMarkdown:
        """Parse markdown file into EntityMarkdown."""
        
        absolute_path = self.base_path / file_path
        # Parse frontmatter and content using python-frontmatter
        post = frontmatter.load(str(absolute_path))
        
        # Extract file stat info
        file_stats = absolute_path.stat()

        
        metadata = post.metadata
        metadata["title"] = post.metadata.get("title", file_path.name)
        metadata["type"] = metadata.get("type", "note")
        metadata["created"] = self.parse_date(
            post.metadata.get("created")
        ) or datetime.fromtimestamp(file_stats.st_ctime)
        metadata["modified"] = self.parse_date(
            post.metadata.get("modified")
        ) or datetime.fromtimestamp(file_stats.st_mtime)
        metadata["tags"] = self.parse_tags(post.metadata.get("tags", []))

        # frontmatter
        entity_frontmatter = EntityFrontmatter(
            metadata=post.metadata,
        )

        entity_content = parse(post.content)

        return EntityMarkdown(
            frontmatter=entity_frontmatter,
            content=post.content,
            observations=entity_content.observations,
            relations=entity_content.relations,
        )

    def parse_tags(self, tags: Any) -> list[str]:
        """Parse tags into list of strings."""
        if isinstance(tags, str):
            return [t.strip() for t in tags.split(",") if t.strip()]
        if isinstance(tags, (list, tuple)):
            return [str(t).strip() for t in tags if str(t).strip()]
        return []
