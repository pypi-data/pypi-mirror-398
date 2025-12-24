"""
Storage Processor - Handles article persistence.

Maps to v4.1 Phase 9, Step 34: publish-to-wordpress + storage

Supports:
- Supabase PostgreSQL (primary)
- Local file system (fallback)
- Metadata extraction and indexing
"""

import logging
import json
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class StorageProcessor:
    """Handle article storage and persistence."""

    @staticmethod
    def store(
        article: Dict[str, Any],
        job_id: str,
        html_content: str,
        storage_type: str = "supabase",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Store article data and HTML.

        Args:
            article: Validated article dictionary
            job_id: Unique job identifier
            html_content: Rendered HTML article
            storage_type: 'supabase' or 'file'

        Returns:
            Tuple of (success: bool, result: dict)
        """
        try:
            if storage_type == "supabase":
                return StorageProcessor._store_supabase(article, job_id, html_content)
            elif storage_type == "file":
                return StorageProcessor._store_file(article, job_id, html_content)
            else:
                return False, {"error": f"Unknown storage type: {storage_type}"}
        except Exception as e:
            logger.error(f"Storage failed: {e}")
            return False, {"error": str(e)}

    @staticmethod
    def _store_supabase(article: Dict[str, Any], job_id: str, html_content: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Store to Supabase (requires SUPABASE_URL and SUPABASE_KEY env vars).

        Args:
            article: Article data
            job_id: Job ID
            html_content: Rendered HTML

        Returns:
            Tuple of (success, result)
        """
        try:
            # Try to import and use Supabase client if available
            try:
                from supabase import create_client
            except ImportError:
                logger.warning("Supabase client not installed, falling back to file storage")
                return StorageProcessor._store_file(article, job_id, html_content)

            # Get credentials from environment
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url or not key:
                logger.warning("Supabase credentials not found, falling back to file storage")
                return StorageProcessor._store_file(article, job_id, html_content)

            # Create client
            client = create_client(url, key)

            # Prepare article record
            record = {
                "job_id": job_id,
                "headline": article.get("Headline", ""),
                "meta_title": article.get("Meta_Title", ""),
                "meta_description": article.get("Meta_Description", ""),
                "article_data": article,
                "html_content": html_content,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            # Upsert to articles table
            response = client.table("articles").upsert(record).execute()

            logger.info(f"✅ Article stored in Supabase (job_id={job_id})")

            return True, {
                "storage_type": "supabase",
                "job_id": job_id,
                "table": "articles",
                "rows_affected": len(response.data) if response.data else 0,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Supabase storage failed: {e}, falling back to file")
            return StorageProcessor._store_file(article, job_id, html_content)

    @staticmethod
    def _store_file(article: Dict[str, Any], job_id: str, html_content: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Store to local file system as fallback.

        Saves to: ./output/{job_id}/

        Args:
            article: Article data
            job_id: Job ID
            html_content: Rendered HTML

        Returns:
            Tuple of (success, result)
        """
        try:
            # Create output directory
            output_dir = Path("output") / job_id
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save HTML
            html_path = output_dir / "index.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Save article data as JSON
            data_path = output_dir / "article.json"
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(article, f, indent=2, ensure_ascii=False)

            # Save metadata
            metadata = {
                "job_id": job_id,
                "headline": article.get("Headline", ""),
                "created_at": datetime.now().isoformat(),
                "files": {
                    "html": str(html_path),
                    "data": str(data_path),
                },
            }
            meta_path = output_dir / "metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"✅ Article stored locally ({output_dir})")

            return True, {
                "storage_type": "file",
                "job_id": job_id,
                "output_dir": str(output_dir),
                "html_path": str(html_path),
                "data_path": str(data_path),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"File storage failed: {e}")
            return False, {"error": str(e)}

    @staticmethod
    def extract_metadata(article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from article for indexing.

        Args:
            article: Article dictionary

        Returns:
            Metadata dictionary
        """
        return {
            "headline": article.get("Headline", ""),
            "slug": StorageProcessor._generate_slug(article.get("Headline", "")),
            "meta_title": article.get("Meta_Title", ""),
            "meta_description": article.get("Meta_Description", ""),
            "image_url": article.get("image_url", ""),
            "read_time": article.get("read_time", 5),
            "publication_date": article.get("publication_date", ""),
            "word_count": StorageProcessor._estimate_word_count(article),
            "sections_count": StorageProcessor._count_sections(article),
            "faq_count": len(article.get("faq_items", [])),
            "paa_count": len(article.get("paa_items", [])),
            "citations_count": article.get("citation_count", 0),
        }

    @staticmethod
    def _generate_slug(headline: str) -> str:
        """Generate URL slug from headline."""
        if not headline:
            return ""
        return (
            headline.lower()
            .strip()
            .replace(" ", "-")
            .replace("'", "")
            .replace('"', "")
            .replace("?", "")
            .replace("!", "")
            .replace(",", "")
            .replace(".", "")
        )

    @staticmethod
    def _estimate_word_count(article: Dict[str, Any]) -> int:
        """Estimate word count from article content."""
        total = 0

        # Count words in main fields
        for key in ["Headline", "Intro", "Meta_Description"]:
            if key in article:
                total += len(str(article[key]).split())

        # Count words in sections
        for i in range(1, 10):
            content_key = f"section_{i:02d}_content"
            if content_key in article:
                total += len(str(article[content_key]).split())

        return total

    @staticmethod
    def _count_sections(article: Dict[str, Any]) -> int:
        """Count non-empty sections."""
        count = 0
        for i in range(1, 10):
            title_key = f"section_{i:02d}_title"
            if article.get(title_key, "").strip():
                count += 1
        return count
