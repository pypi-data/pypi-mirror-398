import os
from metaflow import (
    FlowSpec,
    Config,
    config_expr,
    project,
    get_namespace,
    namespace,
    Task,
    pyproject_toml_parser,
    FlowMutator,
    pypi_base,
)

from subprocess import check_output

from .assets import Asset, _sanitize_branch_name
from .evals_logger import EvalsLogger
from .project_events import ProjectEvent

project_ctx = None


def toml_parser(cfgstr):
    try:
        # python >= 3.11
        import tomllib as toml
    except ImportError:
        import toml
    return toml.loads(cfgstr)


def resolve_scope(project_config, project_spec):
    """
    Resolve asset read branch from config.

    Returns: (project, read_branch)

    - Deployed (project_spec set): read from project_spec.branch
    - Local dev: read from [dev-assets].branch if specified, else None (use write branch)
    """
    project = project_config["project"]

    if project_spec:
        # Deployed: read from deployment branch
        return project, project_spec["branch"]

    # Local dev: read from [dev-assets].branch if specified
    dev_config = project_config.get("dev-assets", {})
    read_branch = dev_config.get("branch")  # None if not specified

    return project, read_branch


class ProjectContext:
    def __init__(self, flow):
        from metaflow import current

        self.flow = flow
        self.project_config = flow.project_config
        self.project_spec = flow.project_spec

        self.project, config_read_branch = resolve_scope(
            self.project_config, self.project_spec
        )

        # Write branch is always the Metaflow branch (from @project decorator)
        # Sanitize for asset API compatibility
        raw_branch = current.branch_name
        self.write_branch = _sanitize_branch_name(raw_branch)

        # Read branch: use config override if specified, else same as write
        if config_read_branch:
            self.read_branch = _sanitize_branch_name(config_read_branch)
        else:
            self.read_branch = self.write_branch

        # backwards compatibility: self.branch reflects the configured read branch
        self.branch = self.read_branch

        # Read asset: for consuming existing assets
        self._read_asset = Asset(
            project=self.project, branch=self.read_branch, read_only=True
        )
        # Write asset: for registering new assets
        self._write_asset = Asset(
            project=self.project, branch=self.write_branch, read_only=False
        )

        # Default asset property uses write branch (backwards compatible)
        self.asset = self._write_asset

        self.evals = EvalsLogger(project=self.project, branch=self.write_branch)

        if self.read_branch != self.write_branch:
            print(f"Asset client: read from {self.project}/{self.read_branch}")
            print(f"Asset client: write to {self.project}/{self.write_branch}")
        else:
            print(f"Asset client: {self.project}/{self.write_branch} (read-write)")

    def publish_event(self, name, payload=None):
        ProjectEvent(name, project=self.project, branch=self.branch).publish(payload)

    def safe_publish_event(self, name, payload=None):
        ProjectEvent(name, project=self.project, branch=self.branch).safe_publish(
            payload
        )

    def register_data(self, name, artifact, annotations=None, tags=None, description=None):
        """
        Register a Metaflow artifact as a data asset.

        Use this when your data is stored as a flow artifact. For external data
        (S3, databases, etc.), use register_external_data().

        Args:
            name: Asset name/id
            artifact: Flow artifact name (self.<artifact>)
            annotations: Optional dict of metadata key-value pairs
            tags: Optional dict of tag key-value pairs
            description: Optional human-readable description

        Example:
            self.features = compute_features(data)
            self.prj.register_data("fraud_features", "features",
                annotations={"row_count": len(self.features)},
                tags={"version": "v2", "source": "postgres"})
        """
        if hasattr(self.flow, artifact):
            # Merge user annotations with artifact reference
            all_annotations = {"artifact": artifact}
            if annotations:
                all_annotations.update(annotations)

            self.asset.register_data_asset(
                name,
                kind="artifact",
                annotations=all_annotations,
                tags=tags,
                description=description
            )
            print(f"📦 Registered data asset: {name}")
            if annotations:
                print(f"   Annotations: {', '.join(f'{k}={v}' for k, v in annotations.items())}")
        else:
            raise AttributeError(
                f"The flow doesn't have an artifact '{artifact}'. Is self.{artifact} set?"
            )

    def register_external_data(self, name, blobs, kind, annotations=None, tags=None, description=None):
        """
        Register external data as a data asset.

        Use this for data living outside Metaflow artifacts: S3 objects, database
        tables, API endpoints, etc. Common in sensor flows, notebooks, and deployments.

        Args:
            name: Asset name/id
            blobs: List of URIs/references to the data (e.g., ["s3://bucket/file.csv"])
            kind: Data type identifier (e.g., "s3_object", "snowflake_table", "postgres_table")
            annotations: Optional dict of metadata
            tags: Optional dict of tags
            description: Optional human-readable description

        Examples:
            # S3 data detected by sensor
            self.prj.register_external_data("raw_sales",
                blobs=["s3://data-lake/sales/2024-01-01.parquet"],
                kind="s3_object",
                annotations={"size_bytes": 1024000, "row_count": 50000},
                tags={"source": "sensor", "format": "parquet"})

            # Snowflake table reference
            self.prj.register_external_data("transactions",
                blobs=["snowflake://prod.analytics.transactions"],
                kind="snowflake_table",
                annotations={"last_updated": "2024-01-01T00:00:00Z"})

            # From notebook or deployment
            self.prj.register_external_data("user_features",
                blobs=["postgresql://db.public.features"],
                kind="postgres_table")
        """
        self.asset.register_data_asset(
            name,
            kind=kind,
            blobs=blobs,
            annotations=annotations,
            tags=tags,
            description=description
        )
        print(f"📦 Registered external data asset: {name} (kind={kind})")
        if annotations:
            print(f"   Annotations: {', '.join(f'{k}={v}' for k, v in annotations.items())}")

    def register_model(self, name, artifact, annotations=None, tags=None, description=None):
        """
        Register a Metaflow artifact as a model asset.

        Use this for trained models stored as flow artifacts. For external models
        (HuggingFace Hub, checkpoint directories, etc.), use register_external_model().

        Args:
            name: Asset name/id
            artifact: Flow artifact name (self.<artifact>) containing the model
            annotations: Optional dict of metadata (accuracy, f1, training_time, etc.)
            tags: Optional dict of tags (model_type, framework, status, etc.)
            description: Optional human-readable description

        Example:
            self.model = train(features)
            self.prj.register_model("fraud_model", "model",
                annotations={"accuracy": 0.94, "f1_score": 0.91},
                tags={"framework": "sklearn", "status": "validated"})
        """
        if hasattr(self.flow, artifact):
            # Merge user annotations with artifact reference
            all_annotations = {"artifact": artifact}
            if annotations:
                all_annotations.update(annotations)

            self.asset.register_model_asset(
                name,
                kind="artifact",
                annotations=all_annotations,
                tags=tags,
                description=description
            )
            print(f"🧠 Registered model asset: {name}")
            if annotations:
                print(f"   Annotations: {', '.join(f'{k}={v}' for k, v in annotations.items())}")
        else:
            raise AttributeError(
                f"The flow doesn't have an artifact '{artifact}'. Is self.{artifact} set?"
            )

    def register_external_model(self, name, blobs, kind, annotations=None, tags=None, description=None):
        """
        Register an external model as a model asset.

        Use this for models living outside Metaflow artifacts: HuggingFace Hub,
        checkpoint directories, model registries, API endpoints, etc. Common in
        notebooks, deployments, and checkpoint-based workflows.

        Args:
            name: Asset name/id
            blobs: List of URIs/references to the model (e.g., ["s3://models/checkpoint/"])
            kind: Model type identifier (e.g., "checkpoint_dir", "huggingface", "mlflow")
            annotations: Optional dict of metadata
            tags: Optional dict of tags
            description: Optional human-readable description

        Examples:
            # Checkpoint directory from training
            from metaflow import current
            self.prj.register_external_model("training_checkpoints",
                blobs=[current.checkpoint.directory],
                kind="checkpoint_dir",
                annotations={"best_epoch": 42, "best_loss": 0.123},
                tags={"framework": "pytorch", "status": "training"})

            # HuggingFace model reference
            self.prj.register_external_model("base_llm",
                blobs=["meta-llama/Llama-3.1-8B-Instruct"],
                kind="huggingface",
                annotations={"context_length": 8192},
                tags={"model_type": "llm", "provider": "meta"})

            # MLflow model URI
            self.prj.register_external_model("production_model",
                blobs=["models:/fraud_detector/production"],
                kind="mlflow",
                annotations={"mlflow_run_id": "abc123"})
        """
        self.asset.register_model_asset(
            name,
            kind=kind,
            blobs=blobs,
            annotations=annotations,
            tags=tags,
            description=description
        )
        print(f"🧠 Registered external model asset: {name} (kind={kind})")
        if annotations:
            print(f"   Annotations: {', '.join(f'{k}={v}' for k, v in annotations.items())}")

    def get_data(self, name, instance="latest"):
        """
        Get a data asset instance.

        Reads from the read_branch (e.g., main for prod assets during local dev).

        Args:
            name: Asset name/id
            instance: Version to retrieve ("latest", "v123", "latest-1")

        Returns:
            The artifact data for the specified version
        """
        ref = self._read_asset.consume_data_asset(name, instance=instance)
        kind = ref["data_properties"]["data_kind"]
        if kind == "artifact":
            ns = get_namespace()
            try:
                namespace(None)
                task = Task(ref["created_by"]["entity_id"])
                artifact = ref["data_properties"]["annotations"]["artifact"]

                return task[artifact].data
            finally:
                namespace(ns)
        else:
            raise AttributeError(
                f"Data asset '{name}' doesn't seem like an artifact. It is of kind '{kind}'"
            )


class project_pypi(FlowMutator):
    def pre_mutate(self, mutable_flow):
        # Allow skipping pypi_base for local development
        # Set OBPROJECT_SKIP_PYPI_BASE=1 to run flows without dependency isolation
        if os.getenv("OBPROJECT_SKIP_PYPI_BASE") == "1":
            return

        project_config = dict(mutable_flow.configs).get("project_config")
        project_deps = dict(mutable_flow.configs).get("project_deps")
        include_pyproject = project_config.get("dependencies", {}).get(
            "include_pyproject_toml", True
        )
        if include_pyproject and project_deps["packages"]:
            mutable_flow.add_decorator(
                pypi_base, deco_kwargs=project_deps, duplicates=mutable_flow.ERROR
            )


@project_pypi
@project(name=config_expr("project_config.project"))
class ProjectFlow(FlowSpec):
    project_config = Config(
        "project_config", default="obproject.toml", parser=toml_parser
    )
    project_deps = Config(
        "project_deps", default_value="", parser=pyproject_toml_parser
    )
    project_spec = Config("project_spec", default_value="{}")

    @property
    def prj(self):
        global project_ctx
        if project_ctx is None:
            project_ctx = ProjectContext(self)
        return project_ctx
