#!/usr/bin/env python
from typing import List, Tuple, Union

from bashhistory.configs import BashHistorySelectArgs

OP_REGEXP = "REGEXP"


def add_filter_if_valid(
  filters: List[str],
  params: List,
  field: str,
  maybe_add: Union[List, str, int],
  sql_operator: str = "=",
):
  if maybe_add:
    if isinstance(maybe_add, list) and len(maybe_add) == 1:
      maybe_add = maybe_add[0]

    if isinstance(maybe_add, list):
      filters.append("%s IN (%s)" % (field, ", ".join("?" * len(maybe_add))))
      params.extend(maybe_add)
    else:
      filters.append("%s %s ?" % (field, sql_operator))
      params.append(maybe_add)


def create_sql(query: str, params: list) -> str:
  if not params:
    return query

  parsed_query_parts = []
  query_parts = query.split("?")
  for index, param in enumerate(params):
    query_part = query_parts[index]
    parsed_query_parts.append(query_part)

    if isinstance(param, str):
      param_str = "'%s'" % (param.replace("'", "''"))
    elif isinstance(param, bool):
      param_str = "TRUE" if param else "FALSE"
    else:
      param_str = str(param)

    parsed_query_parts.append(param_str)

  parsed_query_parts.append(query_parts[-1])

  return "".join(parsed_query_parts)


def query_builder(args: BashHistorySelectArgs, use_command_line: bool = False) -> Tuple[str, list]:
  params = []

  filters = ["1"]

  add_filter_if_valid(filters, params, "exit_code", args.exit_code)
  add_filter_if_valid(filters, params, "host", args.host, "LIKE")
  add_filter_if_valid(filters, params, "host", args.host_regex, sql_operator=OP_REGEXP)
  add_filter_if_valid(filters, params, "pwd", args.dir)
  add_filter_if_valid(filters, params, "pwd", args.dir_regex, sql_operator=OP_REGEXP)
  add_filter_if_valid(filters, params, "user", args.user)

  if args.pattern:
    pattern_type = OP_REGEXP
    if args.pattern_exact:
      pattern_type = "="
    elif args.pattern_sql:
      pattern_type = "LIKE"

    add_filter_if_valid(filters, params, "command", args.pattern, pattern_type)

  if use_command_line:
    field_and_columns = []
    for col in args.columns:
      field_and_columns.append("'%s'" % col)
      field_and_columns.append(col)
    select_columns = "JSON_OBJECT(%s)" % ", ".join(field_and_columns)
  else:
    select_columns = ", ".join(args.columns)

  sql = """
    SELECT %s
    FROM commands
    WHERE %s
    ORDER BY %s
    LIMIT ?
  """ % (
    select_columns,
    " AND ".join(filters),
    args.limit_order,
  )
  params.append(args.limit)
  return sql, params