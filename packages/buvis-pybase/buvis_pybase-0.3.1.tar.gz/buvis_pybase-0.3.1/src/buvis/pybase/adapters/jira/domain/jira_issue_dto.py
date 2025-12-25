from dataclasses import dataclass
from typing import Optional

@dataclass
class JiraIssueDTO:
    project: str
    title: str
    description: str
    issue_type: str
    labels: list
    priority: str
    ticket: str
    feature: str
    assignee: str
    reporter: str
    team: str
    region: str
    id: Optional[str] = None
    link: Optional[str] = None