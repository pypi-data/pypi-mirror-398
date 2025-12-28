from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Vulnerability(BaseModel):
    """Normalized vulnerability model"""
    issue_id: str = Field(description="Unique vulnerability identifier")
    severity: str = Field(description="Vulnerability severity (low, medium, high, critical)")
    cvss_score: Optional[float] = Field(None, description="CVSS score if available")
    cves: List[str] = Field(default_factory=list, description="Associated CVE identifiers")
    project_id: str = Field(description="Project identifier")
    purl: Optional[str] = Field(None, description="Package URL")
    status: str = Field(description="Vulnerability status")
    title: str = Field(description="Vulnerability title")
    description: Optional[str] = Field(None, description="Vulnerability description")
    introduced_date: Optional[str] = Field(None, description="Date vulnerability was introduced")
    disclosed_date: Optional[str] = Field(None, description="Date vulnerability was disclosed")
    
    @classmethod
    def from_snyk_response(cls, data: Dict[str, Any]) -> "Vulnerability":
        """Create Vulnerability from Snyk API response"""
        attributes = data.get("attributes", {})
        
        # Extract CVEs from identifiers
        cves = []
        for identifier in attributes.get("identifiers", {}).get("CVE", []):
            cves.append(identifier)
        
        # Extract CVSS score
        cvss_score = None
        cvss_data = attributes.get("severities", [])
        for severity_data in cvss_data:
            if severity_data.get("source") == "Snyk" and "score" in severity_data:
                cvss_score = severity_data["score"]
                break
        
        return cls(
            issue_id=data.get("id", ""),
            severity=attributes.get("effective_severity_level", "unknown").lower(),
            cvss_score=cvss_score,
            cves=cves,
            project_id=data.get("relationships", {}).get("scan_item", {}).get("data", {}).get("id", ""),
            purl=attributes.get("coordinates", [{}])[0].get("representation", []) if attributes.get("coordinates") else None,
            status=attributes.get("status", "unknown"),
            title=attributes.get("title", ""),
            description=attributes.get("description", ""),
            introduced_date=attributes.get("created_at"),
            disclosed_date=attributes.get("disclosed_at")
        )


class PaginatedResponse(BaseModel):
    """Paginated API response wrapper"""
    data: List[Dict[str, Any]]
    links: Dict[str, str] = Field(default_factory=dict)
    
    @property
    def has_next(self) -> bool:
        return "next" in self.links
    
    @property
    def next_url(self) -> Optional[str]:
        return self.links.get("next")