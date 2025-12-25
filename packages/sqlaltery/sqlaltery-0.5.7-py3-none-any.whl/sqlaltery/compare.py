from typing import Iterable, Dict, Tuple, Any, Optional, Union, Set, List
from collections import defaultdict
import sqlalchemy as sa

from . import ops
from .util import _table_name, _is_auto_constraint, _equal_types, _render_potential_expr, _render, _default_autogen_context

Attrs = Dict[str, Any]
SchemaObject = Union[
	sa.Table, sa.Column, sa.ForeignKeyConstraint,
	sa.UniqueConstraint, sa.PrimaryKeyConstraint,
	sa.CheckConstraint, sa.Index,
]

def diff_md(md_old: sa.MetaData, md_new: sa.MetaData) -> List[ops.Operation]:
	matches = list(_match_schema_objects(md_old, md_new))
	
	matched_tables = set()
	for t, _, so_old, so_new in matches:
		if t is not sa.Table: continue
		if so_old is None: continue
		if so_new is None: continue
		matched_tables.add(so_old)
		matched_tables.add(so_new)
	
	ops = []
	for t, key, so_old, so_new in matches:
		# If it's part of a new or old table, ignore
		if t is sa.Column:
			tbl = (so_new if so_old is None else so_old).table
			if tbl not in matched_tables:
				continue
		
		for op in _diff_schema_object(t, so_old, so_new):
			order = (_ORDERING['{}{}'.format(_op_change(op), t.__name__)], key, len(ops))
			ops.append((order, op))
	return [tpl[1] for tpl in sorted(ops)]

MatchRecord = Tuple[type, Any, Optional[SchemaObject], Optional[SchemaObject]]

def _match_schema_objects(md_old: sa.MetaData, md_new: sa.MetaData) -> Iterable[MatchRecord]:
	by_type = defaultdict(dict) # type: Dict[type, Tuple[Optional[SchemaObject], Optional[SchemaObject]]]
	
	for so_old in _iter_schema_objects(md_old):
		t = type(so_old)
		key = _get_key(t, so_old)
		d = by_type[t]
		if key in d: # pragma: no cover
			raise ValueError("duplicate db object found for key {!r}".format(key))
		d[key] = (so_old, None)
	
	for so_new in _iter_schema_objects(md_new):
		t = type(so_new)
		key = _get_key(t, so_new)
		d = by_type[t]
		if key in d:
			if d[key][1] is not None: # pragma: no cover
				raise ValueError("duplicate db object found for key {!r}".format(key))
			d[key] = (d[key][0], so_new)
		else:
			d[key] = (None, so_new)
	
	for t, d in by_type.items():
		for key, (so_old, so_new) in d.items():
			yield t, key, so_old, so_new

def _op_change(op: ops.Operation) -> str:
	n = type(op).__name__
	for pre in ('Add', 'Drop', 'Alter'):
		if n.startswith(pre): return pre
	raise ValueError("invalid op {!r}".format(op)) # pragma: no cover

_ORDERING = {
	'DropCheckConstraint': 0,
	'DropForeignKeyConstraint': 1,
	'DropUniqueConstraint': 2,
	'DropPrimaryKeyConstraint': 3,
	'DropIndex': 4,
	'DropColumn': 5,
	'DropTable': 6,
	'AddTable': 10,
	'AddColumn': 11,
	'AddIndex': 12,
	'AddPrimaryKeyConstraint': 13,
	'AddUniqueConstraint': 14,
	'AddForeignKeyConstraint': 15,
	'AddCheckConstraint': 16,
	'AlterColumn': 20,
	'AlterTable': 21,
}

def _diff_schema_object(t: type, so_old: Optional[SchemaObject], so_new: Optional[SchemaObject]) -> Iterable[ops.Operation]:
	AddCls, DropCls, AlterCls = _get_op_classes(t)
	
	if so_old is None:
		assert so_new is not None
		yield AddCls.FromSchemaObject(so_new)
		return
	
	if so_new is None:
		assert so_old is not None
		yield DropCls.FromSchemaObject(so_old)
		return
	
	kwargs = _diff_schema_object_impl(t, so_old, so_new)
	if not kwargs:
		return
	
	if AlterCls is None:
		yield DropCls.FromSchemaObject(so_old)
		yield AddCls.FromSchemaObject(so_new)
	else:
		yield AlterCls.FromSchemaObject(so_old, kwargs)

def _diff_schema_object_impl(t, so_old, so_new):
	# Checks marked `pragma: no cover` will never be hit because of
	# the nature the matching algorithm.
	
	kwargs = {}
	if so_new.name != so_old.name: # pragma: no cover
		kwargs['name'] = so_new.name
	
	if t is sa.Table:
		return kwargs
	
	autogen_context = _default_autogen_context()
	if t is sa.Column:
		if not _equal_types(so_new.type, so_old.type):
			kwargs['type'] = so_new.type
		if so_new.nullable != so_old.nullable:
			kwargs['nullable'] = so_new.nullable
		if _render(so_new.server_default, autogen_context) != _render(so_old.server_default, autogen_context):
			kwargs['server_default'] = so_new.server_default
		if _render(so_new.server_onupdate, autogen_context) != _render(so_old.server_onupdate, autogen_context):
			kwargs['server_onupdate'] = so_new.server_onupdate
		return kwargs
	
	if t is sa.PrimaryKeyConstraint:
		if so_new.deferrable != so_old.deferrable:
			kwargs['deferrable'] = so_new.deferrable
		if so_new.initially != so_old.initially:
			kwargs['initially'] = so_new.initially
		if _cols(so_new.columns) != _cols(so_old.columns):
			kwargs['columns'] = _cols(so_new.columns)
		return kwargs
	
	if t is sa.Index:
		if so_new.unique != so_old.unique:
			kwargs['unique'] = so_old.unique
		if _cols(so_new.columns) != _cols(so_old.columns):
			kwargs['columns'] = _cols(so_new.columns)
		return kwargs
	
	if t is sa.ForeignKeyConstraint:
		if _cols(so_new.columns) != _cols(so_old.columns):
			kwargs['columns'] = _cols(so_new.columns)
		if _table_name(so_new.referred_table) != _table_name(so_old.referred_table):
			kwargs['reftable'] = _table_name(so_new.referred_table)
		if _cols(e.column for e in so_new.elements) != _cols(e.column for e in so_old.elements):
			kwargs['refcolumns'] = _cols(e.column for e in so_new.elements)
		if so_new.onupdate != so_old.onupdate:
			kwargs['onupdate'] = so_new.onupdate
		if so_new.ondelete != so_old.ondelete:
			kwargs['ondelete'] = so_new.ondelete
		if so_new.deferrable != so_old.deferrable:
			kwargs['deferrable'] = so_new.deferrable
		if so_new.initially != so_old.initially:
			kwargs['initially'] = so_new.initially
		if so_new.match != so_old.match:
			kwargs['match'] = so_old.match
		return kwargs
	
	if t is sa.UniqueConstraint:
		if _cols(so_new.columns) != _cols(so_old.columns):
			kwargs['columns'] = _cols(so_new.columns)
		if so_new.deferrable != so_old.deferrable:
			kwargs['deferrable'] = so_new.deferrable
		if so_new.initially != so_old.initially:
			kwargs['initially'] = so_new.initially
		return kwargs
	
	if t is sa.CheckConstraint:
		if _render_potential_expr(so_new.sqltext) != _render_potential_expr(so_old.sqltext):
			kwargs['sqltext'] = so_new.sqltext
		if so_new.deferrable != so_old.deferrable:
			kwargs['deferrable'] = so_new.deferrable
		if so_new.initially != so_old.initially:
			kwargs['initially'] = so_new.initially
		return kwargs
	
	raise TypeError("unknown schema object type {}".format(t)) # pragma: no cover

def _cols(cs):
	return tuple(c.name for c in cs)

def _get_key(t, so):
	if t is sa.Table:
		return _table_name(so)
	
	tbl = _table_name(so.table)
	name = so.name
	
	if name:
		return (tbl, name)
	
	if t is sa.PrimaryKeyConstraint:
		return tbl
	if t is sa.ForeignKeyConstraint:
		return (
			tbl, _table_name(so.referred_table),
			tuple(c.name for c in so.columns),
			tuple(e.column.name for e in so.elements)
		)
	if t is sa.UniqueConstraint:
		return (tbl, tuple(c.name for c in so.columns))
	if t is sa.CheckConstraint:
		return (tbl, _render_potential_expr(so.sqltext))
	
	raise TypeError("unknown schema object type {}".format(t)) # pragma: no cover

def _get_op_classes(t):
	n = t.__name__
	if n.endswith('Constraint'):
		n = n[:-len('Constraint')]
	for prefix in ('Add', 'Drop', 'Alter'):
		yield getattr(ops, '{}{}'.format(prefix, n), None)

def _iter_schema_objects(md: sa.MetaData) -> Iterable[SchemaObject]:
	for t in md.tables.values():
		yield t
		yield from t.columns.values()
		yield from t.indexes
	for t in md.tables.values():
		for c in t.constraints:
			if _is_auto_constraint(c): continue
			yield c
