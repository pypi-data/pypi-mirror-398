from ts_cli.config.update_artifact_config import UpdateArtifactConfig


class PublishArtifactConfig(UpdateArtifactConfig):
    def __init__(self, args, *, interactive: bool):
        super().__init__(args, interactive=interactive)
        self.force: bool = args.force
