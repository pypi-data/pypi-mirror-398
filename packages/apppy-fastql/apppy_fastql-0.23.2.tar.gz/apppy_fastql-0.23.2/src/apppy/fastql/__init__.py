import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from pathlib import Path
from types import UnionType
from typing import (  # noqa: UP035
    Annotated,
    Any,
    List,
    Optional,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

import inflection
import strawberry
from fastapi import Request
from strawberry.annotation import StrawberryAnnotation
from strawberry.fastapi import GraphQLRouter
from strawberry.fastapi.context import BaseContext
from strawberry.http.ides import GraphQL_IDE
from strawberry.printer import print_schema
from strawberry.printer.printer import PrintExtras, print_args
from strawberry.types.field import StrawberryField, StrawberryUnion
from strawberry.types.fields.resolver import StrawberryResolver

from apppy.fastql.annotation.error import valid_fastql_type_error
from apppy.fastql.annotation.input import valid_fastql_type_input
from apppy.fastql.annotation.output import extract_concrete_type, valid_fastql_type_output
from apppy.logger import WithLogger


class FastQL(WithLogger):
    """
    A convenience class to support IOC with respect to graphql.

    Its include_mutation and include_query can be used in a similar
    way to FastAPI's include_router.
    """

    def __init__(self):
        self._mutations = []
        self._queries = []
        self._types_error = []
        self._types_id = []
        self._types_input = []
        self._types_output = []

        self._graphql_schema: strawberry.Schema | None = None

    ##### ##### ##### Build Schema ##### ##### #####

    def _attach_fields_to_namespace(
        self, resolvers: dict[str, Callable[..., Any]], namespace: dict[str, Any]
    ) -> None:
        for attr_name, resolver in resolvers.items():
            resolver_name = getattr(resolver, "__name__", "<unknown>")
            return_type = resolver._fastql_return_type  # type: ignore[attr-defined]
            error_types = resolver._fastql_error_types  # type: ignore[attr-defined]
            permission_instances = resolver._fastql_permission_instances  # type: ignore[attr-defined]
            skip_permission_checks = resolver._skip_permission_checks  # type: ignore[attr-defined]

            if not valid_fastql_type_output(return_type):
                return_type_name = getattr(return_type, "__name__", "<unknown>")
                raise TypeError(
                    f"Return type {return_type_name} for {resolver_name} must be a valid @fastql_type_output type."  # noqa: E501
                )
            self._register_type_output(resolver._fastql_return_type)  # type: ignore[attr-defined]

            sig = inspect.signature(resolver)
            for param in sig.parameters.values():
                if param.name in {"self", "info"}:
                    continue
                if param.annotation is inspect.Parameter.empty:
                    continue
                if not valid_fastql_type_input(param.annotation):
                    raise TypeError(
                        f"Parameter {param.annotation.__name__} of {resolver_name} must be a valid @fastql_type_input type."  # noqa: E501
                    )
                self._register_type_input(param.annotation)

            if error_types:
                for error_type in error_types:
                    if not valid_fastql_type_error(error_type):
                        raise TypeError(
                            f"Error type of {resolver_name} must be a valid @fastql_type_error type."  # noqa: E501
                        )
                    self._register_type_error(error_type)

                union_name_python = f"{attr_name}_result"
                union_name = "".join(word.capitalize() for word in union_name_python.split("_"))
                result_union = Annotated[
                    Union[return_type, *error_types], strawberry.union(union_name)  # type: ignore[valid-type]
                ]

                @wraps(resolver)  # type: ignore[arg-type]
                async def wrapped_resolver(
                    *args,
                    __resolver=resolver,
                    __error_types=error_types,
                    __permission_instances=permission_instances,
                    __skip_permission_checks=skip_permission_checks,
                    **kwargs,
                ):
                    try:
                        info = kwargs["info"]
                        if not __skip_permission_checks:
                            for permission in __permission_instances:
                                if not permission.has_permission(None, info):
                                    return permission.graphql_client_error_class(
                                        *permission.graphql_client_error_args()
                                    )
                        return await __resolver(*args, **kwargs)
                    except __error_types as e:
                        return e

                typed_resolver = cast(Callable[..., Any], wrapped_resolver)
                namespace[attr_name] = StrawberryField(
                    graphql_name=inflection.camelize(attr_name, uppercase_first_letter=False),
                    python_name=attr_name,
                    base_resolver=StrawberryResolver(typed_resolver),
                    type_annotation=StrawberryAnnotation(result_union),
                    is_subscription=False,
                )
            else:
                namespace[attr_name] = strawberry.field(
                    resolver,
                    name=inflection.camelize(attr_name, uppercase_first_letter=False),
                )

    def _compose_mutations(self, name: str = "Mutation") -> Any:
        namespace: dict[str, Any] = {}

        for instance in self._mutations:
            cls = type(instance)
            if not getattr(cls, "_fastql_is_mutation", False):
                continue

            resolvers = self._extract_fastql_resolvers(
                instance, cls, expected_decorator_flag="_fastql_is_mutation"
            )
            self._attach_fields_to_namespace(resolvers, namespace)

        return strawberry.type(type(name, (), namespace))

    def _compose_queries(self, name: str = "Query") -> Any:
        namespace: dict[str, Any] = {}

        for instance in self._queries:
            cls = type(instance)
            if not getattr(cls, "_fastql_is_query", False):
                continue

            resolvers = self._extract_fastql_resolvers(
                instance, cls, expected_decorator_flag="_fastql_is_query"
            )

            self._attach_fields_to_namespace(resolvers, namespace)

        return strawberry.type(type(name, (), namespace))

    def _extract_fastql_resolvers(
        self,
        instance: Any,
        cls: type,
        expected_decorator_flag: str,
    ) -> dict[str, Callable[..., Any]]:
        """
        Returns a mapping of field name -> callable resolver that matches
        the expected fastql_query_field or fastql_mutation_field decorators.
        Raises if mismatched decorators are detected.
        """
        resolvers: dict[str, Callable[..., Any]] = {}

        for attr_name in dir(instance):
            if attr_name.startswith("_"):
                continue

            attr = getattr(instance, attr_name)

            if isinstance(attr, StrawberryField):
                base = attr.base_resolver
                if isinstance(base, StrawberryResolver):
                    resolver = base.wrapped_func.__get__(instance, cls)
                else:
                    resolver = base
            else:
                resolver = attr

            if not callable(resolver):
                continue

            # Validate that the method is marked as a mutation or query
            is_query_field = hasattr(resolver, "_fastql_query_field")
            is_mutation_field = hasattr(resolver, "_fastql_mutation_field")

            if expected_decorator_flag == "_fastql_is_query" and is_mutation_field:
                raise TypeError(
                    f"{cls.__name__}.{attr_name} is marked as a mutation field inside a query class"
                )
            if expected_decorator_flag == "_fastql_is_mutation" and is_query_field:
                raise TypeError(
                    f"{cls.__name__}.{attr_name} is marked as a query field inside a mutation class"
                )
            # Validate that we have an acceptable return/output type
            return_type = hasattr(resolver, "_fastql_return_type")
            if return_type is None:
                raise TypeError(
                    f"{cls.__name__} is will be included in fastql schema but has no return type"
                )

            resolvers[attr_name] = resolver

        if not resolvers:
            kind = "query" if expected_decorator_flag == "_fastql_is_query" else "mutation"
            raise ValueError(
                f"{cls.__name__} is marked as a {kind} class but defines no valid {kind} fields."
            )

        return resolvers

    def _include_mutation(self, mutation_instance: Any) -> None:
        self._logger.info(
            "Registering FastQL mutation",
            extra={"mutation_type": mutation_instance.__class__.__name__},
        )
        self._mutations.append(mutation_instance)

    def _include_query(self, query_instance: Any) -> None:
        self._logger.info(
            "Registering FastQL query", extra={"query_type": query_instance.__class__.__name__}
        )
        self._queries.append(query_instance)

    def _register_type_error(self, error_type: Any) -> None:
        if error_type in self._types_error:
            return

        if not hasattr(error_type, "_fastql_type_error"):
            return

        self._logger.info(
            "Registering FastQL error type", extra={"error_type": error_type.__name__}
        )
        self._types_error.append(error_type)

    def _register_type_id(self, id_type: Any) -> None:
        if id_type in self._types_id:
            return

        if not hasattr(id_type, "_fastql_type_id"):
            return

        self._logger.info("Registering FastQL id type", extra={"id_type": id_type.__name__})
        self._types_id.append(id_type)

    def _register_type_input(self, input_type: Any) -> None:
        if input_type in self._types_input:
            return

        # Special case: Register any typed id on the
        # input type.
        if hasattr(input_type, "_fastql_type_id"):
            self._register_type_id(input_type)
            return

        if not hasattr(input_type, "_fastql_type_input"):
            return

        self._logger.info(
            "Registering FastQL intput type", extra={"input_type": input_type.__name__}
        )
        self._types_input.append(input_type)

        # Recursively check field types
        for field_type in getattr(input_type, "__annotations__", {}).values():
            self._register_type_input(field_type)

    def _register_type_output(self, output_type: Any) -> None:
        output_type = extract_concrete_type(output_type)
        if output_type in self._types_output:
            return

        # Special case: Register any typed id on the
        # output type.
        if hasattr(output_type, "_fastql_type_id"):
            self._register_type_id(output_type)
            return

        if not hasattr(output_type, "_fastql_type_output"):
            return

        self._logger.info(
            "Registering FastQL output type", extra={"output_type": output_type.__name__}
        )
        self._types_output.append(output_type)

        # Recursively check field types
        for field_type in getattr(output_type, "__annotations__", {}).values():
            self._register_type_output(field_type)

    def extract_mutation_field_metadata(
        self,
        instance: Any,
    ) -> dict[str, Any] | None:
        """
        Returns a mapping of field name -> field resolver
        """
        cls = type(instance)
        if not getattr(cls, "_fastql_is_mutation", False):
            return None

        resolvers = self._extract_fastql_resolvers(
            instance, cls, expected_decorator_flag="_fastql_is_mutation"
        )

        mutation_metadata: dict[str, Any] = {}
        self._attach_fields_to_namespace(resolvers=resolvers, namespace=mutation_metadata)

        return mutation_metadata

    def extract_query_field_metadata(
        self,
        instance: Any,
    ) -> dict[str, Any] | None:
        """
        Returns a mapping of field name -> field resolver
        """
        cls = type(instance)
        if not getattr(cls, "_fastql_is_query", False):
            return None

        resolvers = self._extract_fastql_resolvers(
            instance, cls, expected_decorator_flag="_fastql_is_query"
        )

        query_metadata: dict[str, Any] = {}
        self._attach_fields_to_namespace(resolvers=resolvers, namespace=query_metadata)

        return query_metadata

    def include_in_schema(self, instance: Any) -> None:
        cls = type(instance)
        if getattr(cls, "_fastql_is_query", False):
            self._include_query(instance)
        elif getattr(cls, "_fastql_is_mutation", False):
            self._include_mutation(instance)
        else:
            self._logger.critical(
                "Query or mutation is missing fastql decorator. Please add @fastql_query() or "
                + "@fastql_mutation() to the class.",
                stack_info=True,
                extra={"cls": cls.__name__},
            )
            raise TypeError(
                "Query or mutation is missing fastql decorator. Please add @fastql_query() or "
                + f"@fastql_mutation() to the class: {cls.__name__}"
            )

    ##### ##### ##### Properties and Runtime ##### ##### #####

    def create_router(
        self,
        context_getter: Callable[[Request], BaseContext | Awaitable[BaseContext]],
        graphiql: bool,
    ) -> GraphQLRouter[BaseContext, None]:
        graphql_ide: GraphQL_IDE | None = "graphiql" if graphiql else None
        return GraphQLRouter[BaseContext, None](
            schema=self.schema,
            path="/graphql",
            context_getter=context_getter,
            graphql_ide=graphql_ide,
        )

    @property
    def all_types(self) -> list[type]:
        return sorted(
            set(self._types_error + self._types_id + self._types_input + self._types_output),
            key=lambda cls: cls.__name__,
        )

    @property
    def all_types_map(self) -> dict[str, type]:
        return {cls.__name__: cls for cls in self.all_types}

    @property
    def mutations_raw(self) -> list[Any]:
        return self._mutations

    @property
    def mutations_map(self) -> dict[str, type]:
        m_map: dict[str, type] = {}
        for m in self._mutations:
            cls = type(m)
            m_map[cls.__name__] = m

        return m_map

    @property
    def queries_raw(self) -> list[Any]:
        return self._queries

    @property
    def queries_map(self) -> dict[str, type]:
        q_map: dict[str, type] = {}
        for q in self._queries:
            cls = type(q)
            q_map[cls.__name__] = q

        return q_map

    @property
    def schema(self) -> strawberry.Schema:
        if self._graphql_schema is None:
            self._graphql_schema = strawberry.Schema(
                query=self._compose_queries(),
                mutation=self._compose_mutations(),
            )

        return self._graphql_schema

    @property
    def types_error_metadata(self) -> list[tuple[str, list[str]]]:
        """
        Returns a list of (error_type_name, field_names) for each error type.
        """
        result: list[tuple[str, list[str]]] = []
        for cls in self._types_error:
            try:
                annotations = get_type_hints(cls)
            except Exception:
                annotations = getattr(cls, "__annotations__", {})
            result.append((cls.__name__, list(annotations.keys())))

        result.sort(key=lambda item: item[0])
        return result

    @property
    def types_error_raw(self) -> list[type]:
        return self._types_error

    @property
    def types_id_raw(self) -> list[type]:
        return self._types_id

    @property
    def types_id_metadata(self) -> list[str]:
        return sorted(cls.__name__ for cls in self._types_id)

    @property
    def types_input_metadata(self) -> list[tuple[str, list[str]]]:
        result = []
        for cls in self._types_input:
            try:
                annotations = get_type_hints(cls)
            except Exception:
                annotations = getattr(cls, "__annotations__", {})
            result.append((cls.__name__, list(annotations.keys())))
        result.sort(key=lambda item: item[0])
        return result

    @property
    def types_input_raw(self) -> list[type]:
        return self._types_input

    @property
    def types_output_metadata(self) -> list[tuple[str, list[str]]]:
        """
        Returns a list of (type_name, field_names) for each output type.
        Useful for generating GraphQL fragments.
        """
        result: list[tuple[str, list[str]]] = []
        for cls in self._types_output:
            try:
                annotations = get_type_hints(cls)
            except Exception:
                annotations = getattr(cls, "__annotations__", {})  # fallback
            result.append((cls.__name__, list(annotations.keys())))

        result.sort(key=lambda item: item[0])  # sort by type name
        return result

    @property
    def types_output_raw(self) -> list[type]:
        return self._types_output

    ##### ##### ##### Codegen ##### ##### #####

    def collect_and_print_fragments(
        self,
        typename: str,
        visited: set[str],
        fragments: dict[str, str],
    ) -> None:
        if typename in visited:
            return

        visited.add(typename)
        cls = self.all_types_map.get(typename)
        if not cls:
            return

        try:
            annotations = get_type_hints(cls)
        except Exception:
            annotations = getattr(cls, "__annotations__", {})

        lines = [f"fragment {typename} on {typename} {{"]

        for field_name, field_type in annotations.items():
            field_name_camel = inflection.camelize(field_name, uppercase_first_letter=False)
            nested_type = None

            origin = get_origin(field_type)
            args = get_args(field_type)

            # CASE: Optional and Union[X, Y, None] and X | Y
            if origin in (Optional, Union, UnionType):
                for arg in args:
                    arg_name = getattr(arg, "__name__", None)
                    if arg_name and arg_name in self.all_types_map:
                        nested_type = arg_name
                        break
            # CASE: List[X] and list[X]
            elif origin in (list, List):  # noqa: UP006
                (inner_type,) = args
                inner_type_name = getattr(inner_type, "__name__", None)
                if inner_type_name and inner_type_name in self.all_types_map:
                    nested_type = inner_type_name
                    # Recurse into the list's inner type
                    self.collect_and_print_fragments(nested_type, visited, fragments)
                    lines.append(f"    {field_name_camel} {{")
                    lines.append(f"        ...{nested_type}")
                    lines.append("    }")
                    continue
            elif hasattr(field_type, "__name__") and field_type.__name__ in self.all_types_map:
                nested_type = field_type.__name__

            if nested_type:
                # Recurse first so nested fragments are available
                self.collect_and_print_fragments(nested_type, visited, fragments)
                lines.append(f"    {field_name_camel} {{")
                lines.append(f"        ...{nested_type}")
                lines.append("    }")
            else:
                lines.append(f"    {field_name_camel}")

        lines.append("}")
        fragments[typename] = "\n".join(lines)

    def collect_and_print_mutations(
        self,
        mutation_class_name: str,
        visited: set[str],
        mutations: dict[str, str],
    ) -> None:
        if mutation_class_name in visited:
            return

        visited.add(mutation_class_name)

        m = self.mutations_map[mutation_class_name]
        if m is None:
            return

        schema = self.schema
        m_field_metadata = self.extract_mutation_field_metadata(m)
        if m_field_metadata is None:
            # This should not happen
            # Very edge case in which we pass in a
            # non-mutation instance
            return

        for _, m_metadata in m_field_metadata.items():
            if isinstance(m_metadata, StrawberryField):
                m_name = f"{m_metadata.graphql_name}Mutation"
                m_name = m_name[0].upper() + m_name[1:]
                m_args = {
                    f"${arg.python_name}": schema.schema_converter.from_argument(arg)
                    for arg in m_metadata.arguments
                }
                lines = [
                    f"mutation {m_name}{print_args(m_args, schema=schema, extras=PrintExtras())} {{"
                ]

                gql_name = m_metadata.graphql_name
                gql_args = [
                    f"{m_arg_name.strip('$')}: {m_arg_name}" for m_arg_name, _ in m_args.items()
                ]
                gql_args_str = f"({','.join(gql_args)})" if len(gql_args) > 0 else ""
                lines.append(f"    {gql_name}{gql_args_str} {{")

                if isinstance(m_metadata.type, StrawberryUnion):
                    for gql_type_annotation in m_metadata.type.type_annotations:
                        gql_result_type = gql_type_annotation.evaluate()
                        gql_result_type_name = gql_result_type.__name__
                        lines.append(f"        ... on {gql_result_type_name} {{")
                        lines.append(f"            ... {gql_result_type_name}")
                        lines.append("        }")
                else:
                    gql_result_type = m_metadata.type  # type: ignore[assignment]
                    gql_result_type_name = gql_result_type.__name__
                    lines.append(f"        ... on {gql_result_type_name} {{")
                    lines.append(f"            ... {gql_result_type_name}")
                    lines.append("        }")

                lines.append("        __typename")
                lines.append("    }")
                lines.append("}")

                mutations[m_name] = "\n".join(lines)

    def collect_and_print_queries(
        self,
        query_class_name: str,
        visited: set[str],
        queries: dict[str, str],
    ) -> None:
        if query_class_name in visited:
            return

        visited.add(query_class_name)

        q = self.queries_map[query_class_name]
        if q is None:
            return

        schema = self.schema
        q_field_metadata = self.extract_query_field_metadata(q)
        if q_field_metadata is None:
            # This should not happen
            # Very edge case in which we pass in a
            # non-query instance
            return

        for _, q_metadata in q_field_metadata.items():
            if isinstance(q_metadata, StrawberryField):
                q_name = f"{q_metadata.graphql_name}Query"
                q_name = q_name[0].upper() + q_name[1:]
                q_args = {
                    f"${arg.python_name}": schema.schema_converter.from_argument(arg)
                    for arg in q_metadata.arguments
                }
                lines = [
                    f"query {q_name}{print_args(q_args, schema=schema, extras=PrintExtras())} {{"
                ]

                gql_name = q_metadata.graphql_name
                gql_args = [
                    f"{q_arg_name.strip('$')}: {q_arg_name}" for q_arg_name, _ in q_args.items()
                ]
                gql_args_str = f"({','.join(gql_args)})" if len(gql_args) > 0 else ""
                lines.append(f"    {gql_name}{gql_args_str} {{")

                if isinstance(q_metadata.type, StrawberryUnion):
                    for gql_type_annotation in q_metadata.type.type_annotations:
                        gql_result_type = gql_type_annotation.evaluate()
                        gql_result_type_name = gql_result_type.__name__
                        lines.append(f"        ... on {gql_result_type_name} {{")
                        lines.append(f"            ... {gql_result_type_name}")
                        lines.append("        }")
                else:
                    gql_result_type = q_metadata.type  # type: ignore[assignment]
                    gql_result_type_name = gql_result_type.__name__
                    lines.append(f"        ... on {gql_result_type_name} {{")
                    lines.append(f"            ... {gql_result_type_name}")
                    lines.append("        }")

                lines.append("        __typename")
                lines.append("    }")
                lines.append("}")

                queries[q_name] = "\n".join(lines)

    def print_schema(self) -> str:
        return print_schema(self.schema)

    def write_graphql_file(
        self, base_dir: str, file_name: str, file_content: str, file_header: str | None = None
    ) -> None:
        graphql_path = Path(base_dir, file_name)
        graphql_path.parent.mkdir(parents=True, exist_ok=True)

        with open(graphql_path, "w") as f:
            if file_header is not None:
                f.write(file_header)
            f.write(file_content)
