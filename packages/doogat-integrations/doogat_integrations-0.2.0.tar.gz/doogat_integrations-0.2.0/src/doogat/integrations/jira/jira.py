from buvis.pybase.adapters.jira.domain.jira_issue_dto import JiraIssueDTO
from buvis.pybase.configuration import Configuration
from buvis.pybase.adapters import JiraAdapter as BuvisJiraAdapter
from doogat.core.domain.entities import ProjectZettel
from doogat.integrations.jira.assemblers.project_zettel_jira_issue import (
    ProjectZettelJiraIssueDTOAssembler,
)


class JiraAdapter(BuvisJiraAdapter):
    def __init__(self: "JiraAdapter", cfg: Configuration) -> None:
        self._cfg = cfg
        self._adapter = BuvisJiraAdapter(self._cfg)

    def create_from_project(self, project: ProjectZettel) -> JiraIssueDTO:
        cfg_defaults = self._cfg.get_configuration_item("defaults")

        if isinstance(cfg_defaults, dict):
            defaults = cfg_defaults.copy()
        else:
            msg = f"Can't get the defaults from:\n{cfg_defaults}"
            raise ValueError(msg)

        assembler = ProjectZettelJiraIssueDTOAssembler(defaults=defaults)
        dto = assembler.to_dto(project)

        return self._adapter.create(dto)
