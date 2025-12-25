"""Web scraping for email extraction."""

import re
import threading
import requests
from typing import Set
from .models import Company


class WebScraper:
    """Simple web scraper for extracting emails."""

    def __init__(self, excluded_keywords: list[str]):
        self.excluded_keywords = excluded_keywords
        self.visited_websites: Set[str] = set()
        self.visited_lock = threading.Lock()

    def extract_emails_from_company(self, company: Company) -> str:
        """Extract emails from company website."""
        if not company.website:
            return ''

        with self.visited_lock:
            if company.website in self.visited_websites:
                return ''
            self.visited_websites.add(company.website)

        # Check if company name or website contains excluded keywords
        if self._is_excluded(company.name) or self._is_excluded(company.website):
            return ''

        try:
            response = requests.get(
                company.website,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            response.raise_for_status()
            html = response.text

            pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(pattern, html)

            excluded = [
                'example.com', 'test.com', 'samplesite.com',
                'wix.com', 'wixpress.com', 'wixsite.com',
                'squarespace.com', 'domain.com', 'yourdomain.com',
                'wordpress.com', 'weebly.com', 'godaddy.com',
                'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp',
                'placeholder', 'email@', '@email', 'noreply',
                'no-reply', 'donotreply', 'mailer-daemon',
                '@localhost', '@example', '@test', '@domain',
                'yourname@', 'youremail@', 'name@', 'user@',
                'admin@example', 'info@example', 'support@example',
                '@sentry.', '@bugsnag.', '@raygun.',
                'privacy@', '@2x.', '@3x.'
            ]

            valid_emails = []
            seen = set()

            for email in emails:
                email_lower = email.lower()

                # Skip if contains any excluded pattern
                if any(ex in email_lower for ex in excluded):
                    continue

                # Skip if email looks like a hash/token (more than 20 chars before @)
                local_part = email.split('@')[0]
                if len(local_part) > 20 and not '.' in local_part:
                    continue

                # Skip if already seen
                if email_lower in seen:
                    continue

                seen.add(email_lower)
                valid_emails.append(email)

            return ', '.join(sorted(valid_emails)) if valid_emails else ''

        except:
            return ''

    def _is_excluded(self, text: str) -> bool:
        """Check if text contains excluded keywords."""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.excluded_keywords)
