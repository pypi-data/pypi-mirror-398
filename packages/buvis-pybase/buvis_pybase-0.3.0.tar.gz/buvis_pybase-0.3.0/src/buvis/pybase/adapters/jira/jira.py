import os

from buvis.pybase.adapters.jira.domain.jira_issue_dto import JiraIssueDTO
from buvis.pybase.configuration import Configuration
from jira import JIRA


class JiraAdapter:
    def __init__(self: "JiraAdapter", cfg: Configuration) -> None:
        self._cfg = cfg
        if self._cfg.get_configuration_item_or_default("proxy", None):
            os.environ.pop("https_proxy")
            os.environ.pop("http_proxy")
            os.environ["https_proxy"] = str(self._cfg.get_configuration_item("proxy"))
        if not self._cfg.get_configuration_item_or_default(
            "server",
            None,
        ) or not self._cfg.get_configuration_item_or_default(
            "token",
            None,
        ):
            msg = "Server and token must be provided"
            raise ValueError(msg)
        self._jira = JIRA(
            server=str(self._cfg.get_configuration_item("server")),
            token_auth=str(self._cfg.get_configuration_item("token")),
        )

    def create(self, issue: JiraIssueDTO) -> JiraIssueDTO:
        new_issue = self._jira.create_issue(
            fields={
                "assignee": {"key": issue.assignee, "name": issue.assignee},
                "customfield_10001": issue.feature,
                "customfield_10501": {"value": issue.team},
                "customfield_12900": {"value": issue.region},
                "customfield_11502": issue.ticket,
                "description": issue.description,
                "issuetype": {"name": issue.issue_type},
                "labels": issue.labels,
                "priority": {"name": issue.priority},
                "project": {"key": issue.project},
                "reporter": {"key": issue.reporter, "name": issue.reporter},
                "summary": issue.title,
            }
        )
        # some custom fields aren't populated on issue creation
        # so I have to update them after issue creation
        new_issue = self._jira.issue(new_issue.key)
        new_issue.update(customfield_10001=issue.feature)
        new_issue.update(customfield_12900={"value": issue.region})

        return JiraIssueDTO(
            project=new_issue.fields.project.key,
            title=new_issue.fields.summary,
            description=new_issue.fields.description,
            issue_type=new_issue.fields.issuetype.name,
            labels=new_issue.fields.labels,
            priority=new_issue.fields.priority.name,
            ticket=new_issue.fields.customfield_11502,
            feature=new_issue.fields.customfield_10001,
            assignee=new_issue.fields.assignee.key,
            reporter=new_issue.fields.reporter.key,
            team=new_issue.fields.customfield_10501.value,
            region=new_issue.fields.customfield_12900.value,
            id=new_issue.key,
            link=new_issue.permalink(),
        )
