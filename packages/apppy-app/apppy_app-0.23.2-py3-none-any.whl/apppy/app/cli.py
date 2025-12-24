from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TypeVar

import anyio
import click

from apppy.app import ApiApp, MinimalApp
from apppy.clients import py_root_dir, py_src_dir, runtime_dir, ts_root_dir
from apppy.clients.codegen import write_module, write_module_init
from apppy.clients.codegen.pyproject import write_client_pyproject_toml
from apppy.clients.codegen.runtime import write_runtime
from apppy.clients.codegen.typescript import write_codegen_cjs
from apppy.clients.graphql import load_graphql_schema
from apppy.fastql import FastQL

MA = TypeVar("MA", bound=MinimalApp)


def make_min_app_cli(
    app_type: type[MA],
    *,
    app_name: str,
) -> click.Group:
    @click.group(name="run", help=f"Run a command for the {app_name} server")
    def group() -> None:
        pass

    @group.command("check-server")
    def check_server():
        """Construct an instance of the application.

        This will help determine if there's a configuration issue.
        It is useful to run ahead of integration testing.
        """
        kwargs = {
            "env_name": "ci",
            "log_level": "debug",
        }

        app_instance = app_type.create(**kwargs)
        assert app_instance is not None

    return group


AA = TypeVar("AA", bound=ApiApp)


def make_api_app_cli(
    app_type: type[AA],
    *,
    app_name: str,
    default_port: int,
) -> click.Group:
    def _create_and_run_app(debug: bool, **kwargs) -> None:
        try:
            app_type.run(app_name, debug, **kwargs)
        except KeyboardInterrupt:
            # Gracefully shutdown on keyboard interrupt
            sys.exit(0)

    @click.group(name="run", help=f"Run a command for the {app_name} server")
    def group() -> None:
        pass

    @group.command("check-server")
    def check_server():
        """Construct an instance of the application.

        This will help determine if there's a configuration issue.
        It is useful to run ahead of integration testing.
        """
        kwargs = {
            "env_name": "ci",
            "log_level": "debug",
        }

        app_instance = app_type.create(**kwargs)  # type: ignore[invalid-argument-type]
        assert app_instance is not None

        # Simulate the asynchronous part of the app startup
        async def _async_app_startup():
            async with app_instance.fastapi().router.lifespan_context(app_instance.fastapi()):
                pass

        anyio.run(_async_app_startup)

    @group.command("run-debug")
    @click.option(
        "--port",
        required=False,
        default=default_port,
        type=click.INT,
        help="The port on which to run the application",
    )
    def server_debug(port: int):
        """Run an instance of the application in a local environment in full debug mode"""

        kwargs = {
            "env_name": "local",
            "log_level": "debug",
            "port": port,
        }
        # NOTE: This is slightly different from the --debug flags below
        # as this will create a fully hot-reloadable server using only
        # default values whereas the --debug flags setup debug mode for
        # the server is the specified environment.
        _create_and_run_app(debug=True, **kwargs)

    @group.command("run-local")
    @click.option(
        "--port",
        required=False,
        default=default_port,
        type=click.INT,
        help="The port on which to run the application",
    )
    def server_local(port: int):
        """Run an instance of the application in a local environment"""
        """Run the app in a local environment."""
        kwargs = {
            "env_name": "local",
            "log_level": "debug",
            "port": port,
        }
        _create_and_run_app(debug=False, **kwargs)

    @group.command("run-server")
    @click.option(
        "--debug",
        required=False,
        default=False,
        is_flag=True,
        type=click.BOOL,
        help="Enable debug mode",
    )
    @click.option(
        "--port",
        required=False,
        default=default_port,
        type=click.INT,
        help="The port on which to run the application",
    )
    def server(debug: bool, port: int):
        """Run an instance of the application.

        This does not force any particular environment, but
        rather reads it from the APP_ENV (or equivalent) environment variable.
        """
        kwargs = {
            "log_level": "debug" if debug else "info",
            "port": port,
        }
        _create_and_run_app(debug=False, **kwargs)

    @group.command("client-py")
    @click.argument(
        "app_dir",
        required=True,
        type=click.Path(file_okay=False, dir_okay=True, writable=True),
    )
    @click.option(
        "--graphql-dir",
        required=True,
        default=f"graphql/__generated__/{app_name}",
        type=click.Path(file_okay=False, dir_okay=True, writable=True),
    )
    @click.option(
        "--schema-file",
        default=f"{app_name}.schema.graphql",
        required=True,
        type=click.Path(file_okay=True, dir_okay=False, writable=True),
    )
    def client_py(
        app_dir: str,
        graphql_dir: str,
        schema_file: str,
    ):
        root_dir = py_root_dir(Path(app_dir))
        root_dir.mkdir(parents=True, exist_ok=True)
        write_client_pyproject_toml(root_dir, app_name)

        src_dir = py_src_dir(Path(app_dir), app_name)
        src_dir.mkdir(parents=True, exist_ok=True)
        write_module_init(src_dir)

        runtime_out_dir = runtime_dir(Path(app_dir), app_name)
        runtime_out_dir.mkdir(parents=True, exist_ok=True)
        write_runtime(runtime_out_dir)

        schema_path = Path(graphql_dir) / "schema" / schema_file
        fragments_dir = Path(graphql_dir) / "fragments"
        mutations_dir = Path(graphql_dir) / "mutations"
        queries_dir = Path(graphql_dir) / "queries"

        schema = load_graphql_schema(schema_path)
        num_mutations = 0
        for m_path in mutations_dir.rglob("*.graphql"):
            write_module(
                out_dir=src_dir,
                graphql_fragments_dir=fragments_dir,
                graphql_file_path=m_path,
                schema=schema,
            )
            num_mutations += 1

        click.secho(
            f"✅ Generated {num_mutations} mutation file(s) in '{src_dir}'",
            fg="green",
        )

        num_queries = 0
        for q_path in queries_dir.rglob("*.graphql"):
            write_module(
                out_dir=src_dir,
                graphql_fragments_dir=fragments_dir,
                graphql_file_path=q_path,
                schema=schema,
            )
            num_queries += 1

        click.secho(
            f"✅ Generated {num_queries} query file(s) in '{src_dir}'",
            fg="green",
        )

    @group.command("client-ts")
    @click.argument(
        "app_dir",
        required=True,
        type=click.Path(file_okay=False, dir_okay=True, writable=True),
    )
    @click.option(
        "--graphql-dir",
        required=True,
        default=f"graphql/__generated__/{app_name}",
        type=click.Path(file_okay=False, dir_okay=True, writable=True),
    )
    @click.option(
        "--schema-file",
        default=f"{app_name}.schema.graphql",
        required=True,
        type=click.Path(file_okay=True, dir_okay=False, writable=True),
    )
    @click.option(
        "--codegen-add-version",
        default="5.0.3",
        required=True,
        type=click.STRING,
    )
    @click.option(
        "--codegen-cli-version",
        default="5.0.7",
        required=True,
        type=click.STRING,
    )
    @click.option(
        "--codegen-introspection-version",
        default="4.0.3",
        required=True,
        type=click.STRING,
    )
    @click.option(
        "--codegen-typed-document-node-version",
        default="5.1.2",
        required=True,
        type=click.STRING,
    )
    @click.option(
        "--codegen-typescript-version",
        default="4.1.6",
        required=True,
        type=click.STRING,
    )
    @click.option(
        "--codegen-typescript-operations-version",
        default="4.6.1",
        required=True,
        type=click.STRING,
    )
    def client_ts(
        app_dir: str,
        graphql_dir: str,
        schema_file: str,
        codegen_add_version: str = "5.0.3",
        codegen_cli_version: str = "5.0.7",
        codegen_introspection_version: str = "4.0.3",
        codegen_typed_document_node_version: str = "5.1.2",
        codegen_typescript_version: str = "4.1.6",
        codegen_typescript_operations_version: str = "4.6.1",
    ):
        app_path = Path(app_dir)
        root_path = ts_root_dir(app_path)
        root_path.mkdir(parents=True, exist_ok=True)

        schema_path = Path(graphql_dir) / "schema" / schema_file
        fragments_dir = Path(graphql_dir) / "fragments"
        mutations_dir = Path(graphql_dir) / "mutations"
        queries_dir = Path(graphql_dir) / "queries"

        client_dir = root_path.relative_to(app_path)
        codegen_cjs = write_codegen_cjs(
            out_dir=root_path,
            app_name=app_name,
            schema_path=schema_path.relative_to(app_path),
            fragments_dir=fragments_dir.relative_to(app_path),
            mutations_dir=mutations_dir.relative_to(app_path),
            queries_dir=queries_dir,
            client_dir=client_dir,
        )

        npm_pkgs = [
            f"@graphql-codegen/cli@{codegen_cli_version}",
            f"@graphql-codegen/add@{codegen_add_version}",
            f"@graphql-codegen/introspection@{codegen_introspection_version}",
            f"@graphql-codegen/typescript@{codegen_typescript_version}",
            f"@graphql-codegen/typescript-operations@{codegen_typescript_operations_version}",
            f"@graphql-codegen/typed-document-node@{codegen_typed_document_node_version}",
            "graphql@^16",
        ]
        npm_install_cmd = ["npm", "install", "-D", "--prefix", str(client_dir), *npm_pkgs]
        subprocess.run(npm_install_cmd, check=True, cwd=app_dir)

        npm_env = {**os.environ, "NODE_PATH": str(client_dir / "node_modules")}
        codegen_bin = client_dir / "node_modules/.bin/graphql-codegen"
        ts_codegen_cmd = [str(codegen_bin), "--config", str(codegen_cjs)]
        subprocess.run(ts_codegen_cmd, check=True, cwd=app_dir, env=npm_env)

        # The codegen.cjs file is meant to be temporary
        # as it will only be used during typescript code generation
        # so remove it after the processing is complete
        codegen_cjs.unlink()

    def _reorder_schema(schema_content: str) -> str:
        # HACK: We need to reorder the schema definition a little
        # bit in order for some of the codegen tools to work correctly
        # Unfortunately, the native print_schema utility in Strawberry
        # does not allow this so we have to do it here.

        # CASE: More GraphQLError interface to the top
        pattern = r"(interface GraphQLError\s+{[^}]+})"
        match = re.search(pattern, schema_content)
        if match:
            definition = match.group(1)
            schema_content = schema_content.replace(definition, "")
            return f"{definition}\n\n{schema_content}"

        return schema_content

    @group.command("graphql-gen")
    @click.argument(
        "base_dir",
        required=True,
        default=f"graphql/__generated__/{app_name}",
        type=click.Path(file_okay=False, dir_okay=True, writable=True),
    )
    @click.option(
        "--include-fragments",
        default=False,
        required=True,
        is_flag=True,
        help="Generate GraphQL fragment files",
    )
    @click.option(
        "--include-mutations",
        default=False,
        required=True,
        is_flag=True,
        help="Generate GraphQL mutation files",
    )
    @click.option(
        "--include-queries",
        default=False,
        required=True,
        is_flag=True,
        help="Generate GraphQL query files",
    )
    @click.option(
        "--include-schema",
        default=False,
        required=True,
        is_flag=True,
        help="Generate GraphQL schema file",
    )
    @click.option(
        "--schema-file",
        default=f"{app_name}.schema.graphql",
        required=True,
        type=click.Path(file_okay=True, dir_okay=False, writable=True),
    )
    def graphql_gen(
        base_dir: str,
        include_fragments: bool,
        include_mutations: bool,
        include_queries: bool,
        include_schema: bool,
        schema_file: str,
    ):
        """Auto-generate GraphQL files"""

        # NOTE: All Graphql generation happens in this one function
        # to avoid having to load the FastQL instance multiple times

        kwargs = {
            "env_name": "ci",
            "log_level": "warning",
        }
        app_instance = app_type.create(**kwargs)  # type: ignore[invalid-argument-type]
        fastql: FastQL = app_instance.fastql()

        if include_fragments:
            fragments: dict[str, str] = {}
            types_visited: set[str] = set()

            for typename, _ in fastql.types_output_metadata:
                fastql.collect_and_print_fragments(typename, types_visited, fragments)

            for typename, _ in fastql.types_error_metadata:
                fastql.collect_and_print_fragments(typename, types_visited, fragments)

            fragment_header = (
                "# This fragment file is automatically generated. DO NOT EDIT MANUALLY.\n\n"
            )

            for name, content in fragments.items():
                fastql.write_graphql_file(
                    base_dir=f"{base_dir}/fragments",
                    file_name=f"{name}Fragment.graphql",
                    file_content=content,
                    file_header=fragment_header,
                )

            click.secho(
                f"✅ Generated {len(fragments)} fragment file(s) in '{base_dir}/fragments'",
                fg="green",
            )

        if include_mutations:
            if not include_fragments:
                click.secho(
                    "Unable to generate mutations without --include-fragments",
                    fg="red",
                )
                sys.exit(1)

            mutations: dict[str, str] = {}
            mutations_visited: set[str] = set()

            mutation_header = (
                "# This mutation file is automatically generated. DO NOT EDIT MANUALLY.\n\n"
            )
            for m in fastql.mutations_raw:
                fastql.collect_and_print_mutations(type(m).__name__, mutations_visited, mutations)

            for name, content in mutations.items():
                fastql.write_graphql_file(
                    base_dir=f"{base_dir}/mutations",
                    file_name=f"{name}.graphql",
                    file_content=content,
                    file_header=mutation_header,
                )

            click.secho(
                f"✅ Generated {len(mutations)} mutation file(s) in '{base_dir}/mutations'",
                fg="green",
            )

        if include_queries:
            if not include_fragments:
                click.secho(
                    "Unable to generate queries without --include-fragments",
                    fg="red",
                )
                sys.exit(1)

            queries: dict[str, str] = {}
            queries_visited: set[str] = set()

            query_header = "# This query file is automatically generated. DO NOT EDIT MANUALLY.\n\n"
            for q in fastql.queries_raw:
                fastql.collect_and_print_queries(type(q).__name__, queries_visited, queries)

            for name, content in queries.items():
                fastql.write_graphql_file(
                    base_dir=f"{base_dir}/queries",
                    file_name=f"{name}.graphql",
                    file_content=content,
                    file_header=query_header,
                )

            click.secho(
                f"✅ Generated {len(queries)} query file(s) in '{base_dir}/queries'",
                fg="green",
            )

        if include_schema:
            schema_header = (
                "# This schema file is automatically generated. DO NOT EDIT MANUALLY.\n\n"
            )
            schema_content = fastql.print_schema()
            schema_content = _reorder_schema(schema_content)
            fastql.write_graphql_file(
                base_dir=f"{base_dir}/schema",
                file_name=schema_file,
                file_content=schema_content,
                file_header=schema_header,
            )
            click.secho(f"✅ Generated schema file '{base_dir}/schema/{schema_file}'", fg="green")

    return group
