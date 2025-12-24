"""
archive.py - ZIP/TAR/EPUB extraction
"""

import logging
import zipfile
import tarfile
import io
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ArchiveExtractor:
    """Extract content from archive files (ZIP, TAR, EPUB)"""

    async def extract_zip(self, content: bytes) -> Dict[str, Any]:
        """Extract text from ZIP file"""
        result = {"files": [], "text": ""}

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                for name in zip_file.namelist():
                    if name.endswith((".txt", ".html", ".xml")):
                        try:
                            text = zip_file.read(name).decode("utf-8", errors="ignore")
                            result["files"].append({"name": name, "text": text})
                            result["text"] += text + "\n\n"
                        except:
                            pass
        except Exception as e:
            logger.error(f"Error extracting ZIP: {e}")

        return result

    async def extract_tar(self, content: bytes) -> Dict[str, Any]:
        """Extract text from TAR file"""
        result = {"files": [], "text": ""}

        try:
            with tarfile.open(fileobj=io.BytesIO(content)) as tar_file:
                for member in tar_file.getmembers():
                    if member.isfile() and member.name.endswith((".txt", ".html", ".xml")):
                        try:
                            text = (
                                tar_file.extractfile(member).read().decode("utf-8", errors="ignore")
                            )
                            result["files"].append({"name": member.name, "text": text})
                            result["text"] += text + "\n\n"
                        except:
                            pass
        except Exception as e:
            logger.error(f"Error extracting TAR: {e}")

        return result

    async def extract_epub(self, content: bytes) -> Dict[str, Any]:
        """Extract text from EPUB file (EPUB is a ZIP with specific structure)"""
        result = {"title": "", "text": "", "chapters": []}

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as epub:
                # EPUB structure: find .html/.xhtml files in OEBPS or similar
                for name in epub.namelist():
                    if name.endswith((".html", ".xhtml", ".htm")):
                        try:
                            text = epub.read(name).decode("utf-8", errors="ignore")
                            result["chapters"].append({"name": name, "text": text})
                            result["text"] += text + "\n\n"
                        except:
                            pass
        except Exception as e:
            logger.error(f"Error extracting EPUB: {e}")

        return result
