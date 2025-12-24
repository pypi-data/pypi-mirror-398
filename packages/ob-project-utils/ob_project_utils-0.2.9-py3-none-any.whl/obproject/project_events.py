from metaflow import FlowMutator
from metaflow.integrations import ArgoEvent


def event_name(name, project, branch):
    return f"prj.{project}.{branch}.{name}"


class ProjectEvent:
    def __init__(self, name, project, branch):
        self.project = project
        self.branch = branch
        self.event = event_name(name, project, branch)

    def publish(self, payload=None):
        ArgoEvent(self.event).publish(payload=payload)

    def safe_publish(self, payload=None):
        ArgoEvent(self.event).safe_publish(payload=payload)


class project_trigger(FlowMutator):
    def init(self, *args, **kwargs):
        self.event_suffix = kwargs.get("event")
        if self.event_suffix is None:
            raise AttributeError("Specify an event name: @project_trigger(event=NAME)")

    def pre_mutate(self, mutable_flow):
        from .projectbase import resolve_scope, _sanitize_branch_name

        project_config = dict(mutable_flow.configs).get("project_config")
        project_spec = dict(mutable_flow.configs).get("project_spec")
        if project_config is None:
            raise KeyError("You can apply @project_trigger only to ProjectFlows")
        else:
            project, read_branch = resolve_scope(project_config, project_spec)
            # For triggers, use read_branch if specified, otherwise derive from project_spec or default
            if read_branch:
                branch = read_branch
            elif project_spec and project_spec.get("branch"):
                branch = _sanitize_branch_name(project_spec["branch"])
            else:
                # Local dev: derive from git or use a default
                import subprocess
                try:
                    git_email = subprocess.check_output(
                        ["git", "config", "user.email"], stderr=subprocess.DEVNULL
                    ).decode().strip()
                    branch = _sanitize_branch_name(f"user.{git_email}")
                except Exception:
                    branch = "user_local"
            event = event_name(self.event_suffix, project, branch)
            mutable_flow.add_decorator(
                "trigger", deco_kwargs={"event": event}, duplicates=mutable_flow.ERROR
            )
