from pathlib import Path

from graphql import GraphQLSchema, build_schema


def load_graphql_schema(schema_path: Path) -> GraphQLSchema:
    sdl = schema_path.read_text(encoding="utf-8")
    return build_schema(sdl)
