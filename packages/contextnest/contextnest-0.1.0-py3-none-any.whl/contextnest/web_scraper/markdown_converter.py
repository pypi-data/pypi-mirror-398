"""
Markdown converter to convert HTML/DOM content to Markdown.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from html_to_markdown import convert
from bs4 import BeautifulSoup


# Default output directory for markdown files
DEFAULT_OUTPUT_DIR = Path.home() / '.contextnest' / "output"


class MarkdownConverter:
    """
    Converts HTML content to Markdown.
    
    This class cleans HTML content and uses an LLM to produce
    well-formatted Markdown output.
    """
    
    # Elements to remove during cleaning
    REMOVE_TAGS = [
        'script', 'style', 'noscript', 'iframe', 'svg', 'canvas',
        'video', 'audio', 'map', 'object', 'embed',
    ]
    
    # Attributes to remove for cleaner HTML
    REMOVE_ATTRS = [
        'style', 'onclick', 'onload', 'onerror', 'class', 'id',
        'data-*', 'aria-*', 'role',
    ]

    def __init__(
        self, output_dir: Optional[Path] = None,
    ):
        """
        Initialize the Markdown converter.
        
        Args:
            output_dir: Directory to save markdown files
        """
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def clean_html(self, html: str) -> str:
        """
        Clean HTML content by removing unnecessary elements.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Cleaned HTML content
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove unwanted tags
        for tag in self.REMOVE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove comments
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove hidden elements
        for element in soup.find_all(attrs={"hidden": True}):
            element.decompose()
        for element in soup.find_all(attrs={"style": re.compile(r"display:\s*none", re.I)}):
            element.decompose()
        
        # Try to find main content area
        main_content = None
        for selector in ['main', 'article', '[role="main"]', '#content', '.content', '#main']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if main_content:
            # Use main content area
            return str(main_content)
        
        # Fallback: use body or entire document
        body = soup.find('body')
        if body:
            return str(body)
        
        return str(soup)
    
    def extract_text_content(self, html: str) -> str:
        """
        Extract main text content from HTML for smaller LLM context.
        
        Args:
            html: Cleaned HTML content
            
        Returns:
            Extracted text with basic structure hints
        """
        soup = BeautifulSoup(html, 'lxml')
        
        lines = []
        
        for element in soup.descendants:
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                lines.append(f"{'#' * level} {element.get_text(strip=True)}")
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    lines.append(text)
            elif element.name == 'li':
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"- {text}")
            elif element.name == 'a' and element.get('href'):
                text = element.get_text(strip=True)
                href = element.get('href')
                if text and href:
                    lines.append(f"[{text}]({href})")
            elif element.name == 'code':
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"`{text}`")
            elif element.name == 'pre':
                text = element.get_text()
                if text:
                    lines.append(f"```\n{text}\n```")
        
        return '\n\n'.join(lines)
    
    def convert_to_markdown(self, html: str, url: Optional[str] = None) -> str:
        """
        Convert HTML content to Markdown.
        
        Args:
            html: HTML content to convert
            url: Optional source URL for context
            
        Returns:
            Markdown content
        """
        # Clean the HTML
        cleaned_html = self.clean_html(html)
        
        markdown = convert(cleaned_html)
        
        return markdown
    
    def save_markdown(
        self,
        content: str,
        url: str,
        filename: Optional[str] = None,
    ) -> Path:
        """
        Save markdown content to a file.
        
        Args:
            content: Markdown content to save
            url: Source URL (used for filename if not provided)
            filename: Optional custom filename
            
        Returns:
            Path to the saved file
        """
        if not filename:
            # Generate filename from URL
            parsed = urlparse(url)
            domain = parsed.netloc.replace('.', '_')
            path_part = parsed.path.strip('/').replace('/', '_')[:50]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if path_part:
                filename = f"{domain}_{path_part}_{timestamp}.md"
            else:
                filename = f"{domain}_{timestamp}.md"
        
        # Sanitize filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        filepath = self.output_dir / filename
        
        # Add metadata header
        header = f"""---
source: {url}
scraped_at: {datetime.now().isoformat()}
---

"""
        
        filepath.write_text(header + content, encoding='utf-8')
        
        return filepath
