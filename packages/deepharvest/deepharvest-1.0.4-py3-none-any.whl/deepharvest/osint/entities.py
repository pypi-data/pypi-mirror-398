"""
Entity Extraction for OSINT
"""

import re
import logging
from typing import Dict, List, Set
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract entities from web content"""

    # Email regex pattern
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    # Phone number patterns (international)
    PHONE_PATTERNS = [
        re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"),  # International
        re.compile(r"\(\d{3}\)\s?\d{3}[-.\s]?\d{4}"),  # US format
        re.compile(r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}"),  # US format without parentheses
    ]

    # Username patterns (social media, GitHub, etc.)
    USERNAME_PATTERNS = [
        re.compile(r"@([A-Za-z0-9_]+)"),  # Twitter/X, Instagram
        re.compile(r"github\.com/([A-Za-z0-9_-]+)"),  # GitHub
        re.compile(r"linkedin\.com/in/([A-Za-z0-9_-]+)"),  # LinkedIn
    ]

    # Domain extraction
    DOMAIN_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)"
    )

    def extract(self, html: str, url: str) -> Dict[str, List[str]]:
        """
        Extract all entities from HTML content

        Returns:
            Dict with keys: emails, phones, usernames, domains
        """
        entities = {"emails": [], "phones": [], "usernames": [], "domains": []}

        try:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()

            # Extract emails
            emails = self._extract_emails(text, html)
            entities["emails"] = list(set(emails))

            # Extract phone numbers
            phones = self._extract_phones(text)
            entities["phones"] = list(set(phones))

            # Extract usernames
            usernames = self._extract_usernames(text, html, url)
            entities["usernames"] = list(set(usernames))

            # Extract domains
            domains = self._extract_domains(text, html, url)
            entities["domains"] = list(set(domains))

        except Exception as e:
            logger.error(f"Entity extraction error: {e}")

        return entities

    def _extract_emails(self, text: str, html: str) -> List[str]:
        """Extract email addresses"""
        emails = set()

        # Extract from text
        for match in self.EMAIL_PATTERN.finditer(text):
            email = match.group(0).lower()
            # Filter out common false positives
            if not any(skip in email for skip in ["example.com", "test@", "noreply", "no-reply"]):
                emails.add(email)

        # Extract from mailto links
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("mailto:"):
                    email = href.replace("mailto:", "").split("?")[0].lower()
                    if "@" in email:
                        emails.add(email)
        except:
            pass

        return list(emails)

    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers"""
        phones = set()

        for pattern in self.PHONE_PATTERNS:
            for match in pattern.finditer(text):
                phone = match.group(0).strip()
                # Filter out short numbers (likely not phones)
                digits = re.sub(r"\D", "", phone)
                if len(digits) >= 10:  # Minimum 10 digits
                    phones.add(phone)

        return list(phones)

    def _extract_usernames(self, text: str, html: str, url: str) -> List[str]:
        """Extract usernames from social media links and mentions"""
        usernames = set()

        # Extract from text patterns
        for pattern in self.USERNAME_PATTERNS:
            for match in pattern.finditer(text):
                username = match.group(1)
                if len(username) >= 2 and len(username) <= 30:
                    usernames.add(username)

        # Extract from HTML links
        try:
            soup = BeautifulSoup(html, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]

                # GitHub
                if "github.com/" in href:
                    match = re.search(r"github\.com/([A-Za-z0-9_-]+)", href)
                    if match:
                        usernames.add(f"github:{match.group(1)}")

                # Twitter/X
                if "twitter.com/" in href or "x.com/" in href:
                    match = re.search(r"(?:twitter|x)\.com/([A-Za-z0-9_]+)", href)
                    if match:
                        usernames.add(f"twitter:{match.group(1)}")

                # LinkedIn
                if "linkedin.com/in/" in href:
                    match = re.search(r"linkedin\.com/in/([A-Za-z0-9_-]+)", href)
                    if match:
                        usernames.add(f"linkedin:{match.group(1)}")

                # Instagram
                if "instagram.com/" in href:
                    match = re.search(r"instagram\.com/([A-Za-z0-9_.]+)", href)
                    if match:
                        usernames.add(f"instagram:{match.group(1)}")
        except:
            pass

        return list(usernames)

    def _extract_domains(self, text: str, html: str, url: str) -> List[str]:
        """Extract domain names"""
        domains = set()
        base_domain = urlparse(url).netloc

        # Extract from text
        for match in self.DOMAIN_PATTERN.finditer(text):
            domain = match.group(1).lower()
            # Filter out common false positives
            if (
                domain
                and "." in domain
                and not any(skip in domain for skip in ["example", "localhost", "test"])
            ):
                domains.add(domain)

        # Extract from HTML links
        try:
            soup = BeautifulSoup(html, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                try:
                    parsed = urlparse(href)
                    if parsed.netloc:
                        domain = parsed.netloc.lower()
                        if domain != base_domain and "." in domain:
                            domains.add(domain)
                except:
                    pass
        except:
            pass

        return list(domains)
