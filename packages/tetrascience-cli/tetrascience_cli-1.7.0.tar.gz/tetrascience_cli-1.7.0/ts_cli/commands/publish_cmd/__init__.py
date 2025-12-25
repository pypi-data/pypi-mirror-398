import argparse
import os
import textwrap
from collections.abc import Iterable
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

import simplejson as json

from ts_cli.api import TsApi
from ts_cli.commands.init_cmd.kinds import KINDS
from ts_cli.commands.utils import existing_folder_type, private_namespace_type
from ts_cli.config.api_config import ApiConfig
from ts_cli.config.publish_artifact_config import PublishArtifactConfig
from ts_cli.config.util import to_version

from ...errors.critical_error import CriticalError
from ...util.emit import emit_error, emit_info
from .archive_utils import compress_directory, copy_included_files_to
from .common_artifact_utils import update_manifest
from .errors import ArtifactBuildError
from .ids_utils import update_ids
from .protocol_utils import update_protocol
from .validation.source_validator import validate_source
from .validation.upload_validator import UploadValidator, bytes_as_human_readable_string

DEFAULT_EXCLUDE_FOLDERS = {
    ".git",
    "venv",
    ".venv",
    "__test__",
    "__tests__",
}


def add_publish_parser(subparsers):
    """
    Adds the `publish` subparser
    :param subparsers:
    :return:
    """
    publish_cmd_args(
        subparsers.add_parser(
            "publish",
            help="Publish artifact identified by namespace/slug:version",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent(
                f"""
                Publish an artifact to the Tetra Data Platform. For example:

                    ts-cli publish .

                where "." is the path to the artifact source code.
                The source code positional argument defaults to the current working directory.

                The following artifact configuration fields are required:
                    type, namespace, slug, version
                The publish command will sequentially check each of the following locations
                  for each configuration:
                    1. The respective command argument.
                        Example: --type protocol
                    2. A manifest.json file in the root of the artifact directory
                    3. A protocol.{"{yaml,yml,json}"} file in the root of the artifact directory
                    4. A schema.json file in the root of the artifact directory
                    5. A pyproject.toml file in the root of the artifact directory
                For the namespace field, the publish command will additionally look for
                  a configured org (see below).
                For the version field, the publish command will additionally look for a
                  pyproject.toml file in the root of the artifact directory
                Use --interactive to be walked through setting up each of the fields

                The following TDP API configuration fields are required:
                    org, api_url, auth_token, ignore_ssl
                The publish command will sequentially check each of the following locations
                  for each configuration:
                    1. The respective command argument.
                        Example: --org my-org --auth-token q1w2e3 --api-url https://api.tdp
                        Note that ignore_ssl is set to true by the flag --ignore-ssl,
                          and set to false with --enforce-ssl
                    2. The yaml or json formatted configuration file
                        provided in a command argument.
                        Example: --config ./config.json
                    3. In the process's environment variables.
                        The fields are prefixed with "TS_" and in all uppercase.
                        Example: export TS_ORG=my-org TS_API_URL=https://api.tdp
                    4. The yaml or json formatted file at "~/.config/tetrascience/config"

                Use --exclude to omit files and folders from being added published artifact.
                These paths are relative to the current working directory, not the artifact
                directory.
                The following folders are automatically omitted from the root of the artifact
                directory:
                    {", ".join(DEFAULT_EXCLUDE_FOLDERS)}

                Use --include to re-include a file or folder that has been excluded.
            """
            ),
        )
    )


def publish_cmd_args(parser: argparse.ArgumentParser):
    """
    Adds publish command arguments to the parser
    :param parser:
    :return:
    """
    artifact_config = parser.add_argument_group("Artifact Configuration")
    artifact_config.add_argument(
        "--type",
        type=str,
        choices=KINDS,
        help="artifact type",
    )
    artifact_config.add_argument(
        "--namespace",
        type=private_namespace_type,
        help="Artifact namespace configuration",
    )
    artifact_config.add_argument(
        "--slug", type=str.lower, help="Artifact slug configuration"
    )
    artifact_config.add_argument(
        "--version", type=to_version, help="Artifact version configuration"
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="interactively set up Artifact configuration",
    )
    parser.add_argument(
        "source",
        type=existing_folder_type,
        help="path to folder to be uploaded",
        nargs="?",
        default=os.getcwd(),
    )
    parser.add_argument(
        "--exclude", help="folder or file to exclude", type=str, action="append"
    )
    parser.add_argument(
        "--include",
        help="folder to include, overriding excluded folders",
        type=str,
        action="append",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="force overwrite of an existing artifact",
    )
    parser.add_argument(
        "--no-verify", action="store_true", help="skip artifact validation"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="skip actual artifact publishing"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output for debugging",
    )

    api_config = parser.add_argument_group("API Configuration")
    ssl_group = api_config.add_mutually_exclusive_group()
    ssl_group.add_argument(
        "--ignore-ssl",
        "-k",
        action="store_true",
        help="ignore the SSL certificate verification",
    )
    ssl_group.add_argument(
        "--enforce-ssl",
        "-e",
        dest="ignore_ssl",
        action="store_false",
        help="do not ignore SSL certificate verification",
    )
    api_config.set_defaults(ignore_ssl=None)
    api_config.add_argument(
        "--profile", help="The name of the configuration profile to use", type=str
    )
    api_config.add_argument("--org", help="org slug", type=str)
    api_config.add_argument("--api-url", help="platform API URL", type=str)
    api_config.add_argument("--auth-token", help="authorization token", type=str)
    api_config.add_argument(
        "--config",
        "-c",
        help="yaml or json formatted file with an API configuration",
        type=argparse.FileType("r"),
    )
    parser.set_defaults(func=publish)


def argument_to_files_relative_to(argument, relative_to):
    """
    Maps a file provided by the user to a file path relative to `relative_to`
    :param argument:
    :param relative_to:
    :return:
    """
    if argument is None:
        return set()
    if isinstance(argument, Iterable):
        return set(map(lambda path: os.path.relpath(Path(path), relative_to), argument))
    return {os.path.relpath(argument, relative_to)}


def monitor_artifact_build(ts_api: TsApi, build_id: str):
    """
    Print artifact build logs to the console
    :param ts_api:
    :param build_id:
    :return:
    """
    print("Build started", flush=True)
    print("Note: A local script interruption doesn't stop a remote build!", flush=True)

    prev_next = None

    artifact_build_error_str = "child process exited with code 1,"

    while True:
        build_info = ts_api.get_task_script_build_info(build_id)
        build_complete = build_info.get("build", {}).get("buildComplete")
        build_status = build_info.get("build", {}).get("buildStatus")

        sleep(3)

        events, prev_next = ts_api.get_task_script_build_logs(build_id, prev_next)

        if len(events) > 0:
            print("\r", end="", flush=True)
        elif not build_complete:
            print(".", end="", flush=True)

        for event in events:
            msg_text = event.get("message", "").strip()
            if msg_text:
                print(msg_text, flush=True)
                if artifact_build_error_str in msg_text:
                    raise ArtifactBuildError(
                        f"Artifact Build process failure:\n{msg_text}"
                    )

        if build_complete:
            last_status = build_status
            break

    print("", flush=True)

    if last_status == "FAILED":
        raise CriticalError("Build failed.")


def publish(args):
    """
    The actual publish command implementation
    :param args:
    :return:
    """
    artifact_config = PublishArtifactConfig(args, interactive=args.interactive)
    api_config = ApiConfig(args)
    ts_api = TsApi(api_config, verbose=getattr(args, "verbose", False))

    with TemporaryDirectory() as temp_directory:
        copy_included_files_to(
            src_dir=args.source,
            dst_dir=temp_directory,
            inclusions=argument_to_files_relative_to(args.include, args.source),
            exclusions=argument_to_files_relative_to(args.exclude, args.source).union(
                DEFAULT_EXCLUDE_FOLDERS
            ),
        )

        manifest = update_manifest(temp_directory, artifact_config)
        if artifact_config.type == "protocol":
            update_protocol(temp_directory, manifest)
        elif artifact_config.type == "ids":
            update_ids(temp_directory, manifest)

        if args.no_verify is not True:
            validate_source(
                path=temp_directory,
                exiting=True,
                validator_type=artifact_config.type,
                api_config=api_config,
            )
        else:
            emit_info("Skipping artifact validation because 'no-verify' flag was set")

        zip_bytes = compress_directory(temp_directory)

    upload_size_checker = UploadValidator(
        upload_content=zip_bytes, artifact_type=artifact_config.type, exiting=True
    )
    upload_size_checker.validate()

    print(f"Uploading {bytes_as_human_readable_string(len(zip_bytes))}", flush=True)
    if args.dry_run is not True:
        response = ts_api.upload_artifact(artifact_config, zip_bytes)

        print(json.dumps(response, indent="\t", sort_keys=True), flush=True)

        build_id = response.get("build", {}).get("id", None)
        if build_id:
            monitor_artifact_build(ts_api, build_id)
            print(
                json.dumps(
                    {
                        "type": artifact_config.type,
                        "namespace": artifact_config.namespace,
                        "slug": artifact_config.slug,
                        "version": artifact_config.version,
                    },
                    indent="\t",
                    sort_keys=False,
                ),
                flush=True,
            )
        elif (
            artifact_config.type == "task-script" or artifact_config.type == "connector"
        ):
            emit_error("No build ID found in platform response")
    else:
        raise CriticalError("Skipping artifact upload because 'dry-run' flag was set")
