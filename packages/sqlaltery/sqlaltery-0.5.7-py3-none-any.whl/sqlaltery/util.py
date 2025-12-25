from typing import Any
import datetime
import sqlalchemy as sa
from sqlalchemy.sql import sqltypes
from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate import render as alembic_render
from alembic import util as alembic_util
from alembic.ddl.impl import DefaultImpl

class AlembicDuckDBImpl(DefaultImpl):
	__dialect__ = 'duckdb'

#def _copy_metadata(md: sa.MetaData) -> sa.MetaData:
#	md_copy = sa.MetaData()
#	for t in md.sorted_tables:
#		t.tometadata(md_copy)
#	return md_copy

def _is_auto_constraint(constraint: Any) -> bool:
	if not constraint._create_rule: return False
	if not hasattr(constraint._create_rule, 'target'): return False
	if not isinstance(constraint._create_rule.target, sqltypes.TypeEngine): return False
	return True

def _equal_types(t1: sqltypes.TypeEngine, t2: sqltypes.TypeEngine) -> bool:
	return _render_type(t1) == _render_type(t2)

def _render(x: Any, autogen_context: AutogenContext):
	if isinstance(x, sqltypes.TypeEngine):
		return alembic_render._repr_type(x, autogen_context)
	if isinstance(x, sa.sql.functions.next_value):
		return '{}sql.functions.next_value({})'.format(
			autogen_context.opts['sqlalchemy_module_prefix'],
			_render(x.sequence, autogen_context),
		)
	if isinstance(x, sa.DefaultClause):
		return _render(x.arg, autogen_context)
	if isinstance(x, sa.FunctionElement):
		return 'sa.text({})'.format(_render_potential_expr(x))
	if isinstance(x, sa.TextClause):
		return 'sa.text({!r})'.format(x.text)
	if isinstance(x, sa.Column):
		return _render_column(x, autogen_context)
	if isinstance(x, sa.sql.ClauseElement):
		return _render_potential_expr(x)
	if isinstance(x, sa.Sequence):
		return autogen_context.opts['sqlalchemy_module_prefix'] + repr(x).replace(', metadata=MetaData()', '')
	if isinstance(x, tuple):
		if not x:
			return '()'
		if isinstance(x[0], str):
			return repr(x)
		return '(\n{})'.format(''.join(
			(autogen_context.opts['indent'] + _render(y, autogen_context) + ',\n') for y in x
		))
	return repr(x)

def _render_type(t: Any) -> str:
	return repr(t)

def _table_name(table: sa.Table) -> str:
	if table.schema:
		return '{}.{}'.format(table.schema, table.name)
	return table.name

def _render_potential_expr(value: Any, dialect: Any = None) -> str:
	if not isinstance(value, sa.sql.ClauseElement):
		return repr(value)
	return repr(str(value.compile(dialect = dialect, compile_kwargs = {
		'literal_binds': True, 'include_table': False
	})))

def _render_column(column, autogen_context):
	# From alembic.autogenerate.render
	
	rendered = alembic_render._user_defined_render("column", column, autogen_context)
	if rendered is not False:
		return rendered
	
	opts = []
	
	server_default = column.server_default
	if server_default:
		rendered = _render_server_default(server_default, autogen_context)
		if rendered: opts.append(("server_default", rendered))
	
	server_onupdate = column.server_onupdate
	if server_onupdate:
		rendered = _render_server_default(server_onupdate, autogen_context)
		if rendered: opts.append(("server_onupdate", rendered))
	
	if column.autoincrement is not None and column.autoincrement != alembic_util.sqla_compat.AUTOINCREMENT_DEFAULT:
		opts.append(("autoincrement", column.autoincrement))
	
	if column.nullable != True:
		opts.append(("nullable", column.nullable))
	
	if column.system:
		opts.append(("system", column.system))
	
	args = [alembic_render._repr_type(column.type, autogen_context)] + [
		'{}={}'.format(kwname, val) for kwname, val in opts
	]
	# TODO: for non-ascii colname, assign a "key"
	return '{prefix}Column({name!r}, {args})'.format(
		prefix = alembic_render._sqlalchemy_autogenerate_prefix(autogen_context),
		name = alembic_render._ident(column.name),
		args = ', '.join(args)
	)

def _render_server_default(x, autogen_context):
	if isinstance(x, sa.DefaultClause):
		return _render(x.arg, autogen_context)
	return alembic_render._render_server_default(x, autogen_context)

def _indent(txt: str, autogen_context: AutogenContext) -> str:
	return '\n'.join(autogen_context.opts['indent'] + l for l in txt.splitlines())

def _default_autogen_context(indent: str = '\t') -> AutogenContext:
	return AutogenContext(None, opts = {
		'sqlalchemy_module_prefix': 'sa.',
		'user_module_prefix': None,
		'ops_module_prefix': 'ops.',
		'indent': indent,
	})

def utcnow() -> datetime.datetime:
	return datetime.datetime.now(datetime.timezone.utc)
