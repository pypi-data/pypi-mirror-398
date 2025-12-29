import re
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

@dataclass
class SinkInfo:
    provider: str
    category: str
    country: str  # "US", "EU", "Unknown", "Region-Dependent"
    gdpr_risk: str # "high", "medium", "low", "variable"
    notes: str

class SinkResolver:
    """
    Resolves domain names and URLs to known external sinks (SaaS, Cloud, AI Providers).
    Helps determine Data Sovereignty and GDPR risks.
    """

    # Static Knowledge Base of known domains
    # Format: domain -> metadata
    KNOWN_DOMAINS = {
        # AI Providers
        "api.openai.com": {
            "provider": "OpenAI",
            "country": "US",
            "category": "AI_MODEL",
            "gdpr_risk": "high",
            "notes": "Standard OpenAI API. Data processed in US."
        },
        "api.anthropic.com": {
            "provider": "Anthropic",
            "country": "US",
            "category": "AI_MODEL",
            "gdpr_risk": "high",
            "notes": "Anthropic API."
        },
        "api.mistral.ai": {
            "provider": "Mistral AI",
            "country": "EU", # Headquartered in France
            "category": "AI_MODEL",
            "gdpr_risk": "low",
            "notes": "European AI provider (France)."
        },
        
        # Analytics & Logging
        "sentry.io": {
            "provider": "Sentry",
            "country": "US", # Defaults to US unless configured otherwise
            "category": "LOGGING",
            "gdpr_risk": "medium",
            "notes": "Sentry SaaS. US-hosted by default."
        },
        "o450.ingest.sentry.io": { # Common ingest pattern
             "provider": "Sentry",
            "country": "US",
            "category": "LOGGING",
            "gdpr_risk": "medium",
            "notes": "Sentry Ingest."
        },
        "analytics.google.com": {
            "provider": "Google Analytics",
            "country": "US",
            "category": "ANALYTICS",
            "gdpr_risk": "medium",
            "notes": "Google Analytics."
        },
        "api.segment.io": {
            "provider": "Segment",
            "country": "US",
            "category": "ANALYTICS",
            "gdpr_risk": "medium",
            "notes": "Segment (Twilio)."
        },
        "heapanalytics.com": {
            "provider": "Heap",
            "country": "US",
            "category": "ANALYTICS",
            "gdpr_risk": "medium",
            "notes": "Heap Analytics."
        },
        "mixpanel.com": {
            "provider": "Mixpanel",
            "country": "US",
            "category": "ANALYTICS",
            "gdpr_risk": "medium",
            "notes": "Mixpanel."
        }
    }

    # Regex patterns for dynamic matching (Cloud Providers, etc.)
    DYNAMIC_PATTERNS = [
        # AWS S3 with Region
        # e.g. s3.eu-central-1.amazonaws.com
        {
            "pattern": r"s3\.([a-z0-9-]+)\.amazonaws\.com",
            "provider": "AWS S3",
            "category": "CLOUD_STORAGE",
            "handler": "_handle_aws_region"
        },
        # AWS Generic
        {
            "pattern": r".*\.amazonaws\.com",
            "provider": "AWS",
            "category": "CLOUD_INFRA",
            "country": "Region-Dependent",
            "gdpr_risk": "variable",
            "notes": "AWS Service. Region depends on subdomain or config."
        },
        # Azure Blob Storage
        # e.g. myaccount.blob.core.windows.net
        {
            "pattern": r".*\.blob\.core\.windows\.net",
            "provider": "Azure Blob Storage",
            "category": "CLOUD_STORAGE",
            "country": "Region-Dependent",
            "gdpr_risk": "variable",
            "notes": "Azure Storage. Physical location depends on Storage Account region configuration."
        },
        # Azure Generic
        {
            "pattern": r".*\.azurewebsites\.net",
            "provider": "Azure App Service",
            "category": "CLOUD_INFRA",
            "country": "Region-Dependent",
            "gdpr_risk": "variable",
            "notes": "Azure App Service."
        },
        # Google Cloud Storage
        {
            "pattern": r"storage\.googleapis\.com",
            "provider": "Google Cloud Storage",
            "category": "CLOUD_STORAGE",
            "country": "Region-Dependent",
            "gdpr_risk": "variable",
            "notes": "GCS. Region depends on bucket config."
        }
    ]

    def resolve(self, url_or_domain: str) -> Optional[SinkInfo]:
        """
        Analyze a URL or domain and return SinkInfo if a match is found.
        """
        if not url_or_domain:
            return None

        # 1. Clean input (remove protocol, path) to get hostname
        hostname = self._extract_hostname(url_or_domain)
        if not hostname:
            return None

        # 2. Check Exact Matches
        if hostname in self.KNOWN_DOMAINS:
            info = self.KNOWN_DOMAINS[hostname]
            return SinkInfo(
                provider=info["provider"],
                category=info["category"],
                country=info["country"],
                gdpr_risk=info["gdpr_risk"],
                notes=info["notes"]
            )

        # 3. Check Dynamic Patterns
        for entry in self.DYNAMIC_PATTERNS:
            match = re.search(entry["pattern"], hostname)
            if match:
                if "handler" in entry:
                    # Call specific handler method
                    handler_method = getattr(self, entry["handler"])
                    return handler_method(match, entry)
                else:
                    # Return static info from pattern
                    return SinkInfo(
                        provider=entry["provider"],
                        category=entry["category"],
                        country=entry.get("country", "Unknown"),
                        gdpr_risk=entry.get("gdpr_risk", "variable"),
                        notes=entry.get("notes", "")
                    )

        return None

    def _extract_hostname(self, url: str) -> Optional[str]:
        """Extract hostname from URL or return string if it looks like a domain"""
        # Simple regex for hostname extraction
        # Remove protocol
        clean = re.sub(r'^https?://', '', url)
        # Remove path/query
        clean = clean.split('/')[0].split('?')[0]
        # Remove port
        clean = clean.split(':')[0]
        
        if '.' in clean:
            return clean.lower()
        return None

    def _handle_aws_region(self, match: re.Match, entry: Dict[str, Any]) -> SinkInfo:
        """
        Extracts region from AWS URLs like s3.eu-central-1.amazonaws.com
        """
        region = match.group(1)
        country = "Unknown"
        gdpr_risk = "variable"
        
        # Basic mapping of AWS regions to locations
        if region.startswith("eu-"):
            country = "EU"
            gdpr_risk = "low"
        elif region.startswith("us-"):
            country = "US"
            gdpr_risk = "medium" # CLOUD Act applies even if in US
        elif region.startswith("ap-"):
            country = "APAC"
        elif region.startswith("sa-"):
            country = "South America"
        
        return SinkInfo(
            provider=entry["provider"],
            category=entry["category"],
            country=f"{country} ({region})",
            gdpr_risk=gdpr_risk,
            notes=f"AWS S3 Bucket in {region}"
        )
