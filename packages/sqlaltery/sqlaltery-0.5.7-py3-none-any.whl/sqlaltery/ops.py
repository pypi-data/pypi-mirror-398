from typing import Optional, Any, List, ClassVar, Dict, Tuple
import inspect
import contextlib
import sqlalchemy as sa
from sqlalchemy.engine import Connectable
from sqlalchemy.sql import sqltypes, ddl

from . import util

class Operation:
	__slots__ = ('_reverse',)
	
	def __init__(self) -> None:
		self._reverse = None
	
	@property
	def reverse(self) -> 'Operation':
		assert self._reverse is not None
		return self._reverse
	
	def generate_reverse(self, md: sa.MetaData) -> None:
		if self._reverse is not None: return
		self._reverse = self._generate_reverse(md)
		self.apply(md, None)
		self._reverse._reverse = self
	
	def _generate_reverse(self, md: sa.MetaData) -> 'Operation': # pragma: no cover
		raise NotImplementedError('{}._generate_reverse'.format(type(self).__name__))
	
	def apply(self, md: sa.MetaData, conn: Optional[Connectable]) -> None: # pragma: no cover
		raise NotImplementedError('{}.apply'.format(type(self).__name__))
	
	def __repr__(self) -> str: # pragma: no cover
		raise NotImplementedError('{}.__repr__'.format(type(self).__name__))

class _AddSigMeta(type):
	@staticmethod
	def __new__(cls, name, bases, attrs):
		init = attrs.get('__init__')
		if init is not None:
			s = inspect.signature(init)
			attrs['_init_params'] = list(s.parameters.values())[1:]
		return super().__new__(cls, name, bases, attrs)

class _SchemaObjectOperation(Operation, metaclass = _AddSigMeta):
	def __hash__(self):
		return hash((type(self), repr(self)))
	
	def __eq__(self, other):
		if self is other: return True
		if type(self) != type(other): return False
		return repr(self) == repr(other)
	
	def __repr__(self):
		return self.render(util._default_autogen_context())
	
	def render(self, autogen_context):
		argstr = []
		
		saw_default_arg = False
		for p in self._init_params:
			v = getattr(self, p.name)
			not_default = (v != p.default)
			if p.kind == inspect.Parameter.VAR_KEYWORD:
				if v:
					for ak, av in v.items():
						argstr.append('{}={}'.format(ak, util._render(av, autogen_context)))
			elif p.kind == inspect.Parameter.KEYWORD_ONLY or saw_default_arg:
				if not_default:
					argstr.append('{}={}'.format(p.name, util._render(v, autogen_context)))
			else:
				if not_default:
					argstr.append(util._render(v, autogen_context))
				else:
					saw_default_arg = True
		
		x = '{}{}({})'.format(autogen_context.opts['ops_module_prefix'], type(self).__name__, ', '.join(argstr))
		return x

class _AddDropOperation(_SchemaObjectOperation):
	@classmethod
	def FromSchemaObject(cls, so): # pragma: no cover
		raise NotImplementedError('_AddDropOperation.FromSchemaObject')

class _AlterOperation(_SchemaObjectOperation):
	@classmethod
	def FromSchemaObject(cls, so_old, kwargs): # pragma: no cover
		raise NotImplementedError('_AlterOperation.FromSchemaObjects')

UNCHANGED = object()


class AddTable(_AddDropOperation):
	def __init__(self, table_name, columns):
		super().__init__()
		self.table_name = table_name
		self.columns = tuple(c._copy() for c in sorted(columns, key = lambda c: c.name))
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so), so.columns.values())
	
	def apply(self, md, conn):
		table = sa.Table(self.table_name, md, *(c._copy() for c in self.columns))
		if conn is None: return
		with _run_alembic_ddl(conn) as impl:
			for c in table.columns:
				seq = _get_column_default_sequence(c)
				if seq is not None:
					impl._exec(ddl.CreateSequence(seq))
			impl.create_table(table)
	
	def _generate_reverse(self, md):
		return DropTable(self.table_name)

class DropTable(_AddDropOperation):
	def __init__(self, table_name):
		super().__init__()
		self.table_name = table_name
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so))
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		md.remove(table)
		if conn is None: return
		with _run_alembic_ddl(conn) as impl:
			impl.drop_table(table)
			for c in table.columns:
				seq = _get_column_default_sequence(c)
				if seq is not None:
					impl._exec(ddl.DropSequence(seq))
	
	def _generate_reverse(self, md):
		table = _find_table(md, self.table_name)
		return AddTable.FromSchemaObject(table)

def _get_column_default_sequence(c):
	sd = c.server_default
	if not sd: return None
	if not isinstance(sd, sa.DefaultClause): return None
	if not isinstance(sd.arg, sa.sql.functions.next_value): return None
	return sd.arg.sequence

class AlterTable(_AlterOperation):
	def __init__(self, table_name, *, name = UNCHANGED):
		super().__init__()
		self.table_name = table_name
		self.name = name
	
	@classmethod
	def FromSchemaObject(cls, so_old, kwargs):
		return cls(util._table_name(so_old), **kwargs)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		if self.name is not UNCHANGED:
			d = dict(md.tables)
			del d[table.name]
			table.name = self.name
			d[table.name] = table
			md.tables = type(md.tables)(d)
		if conn is None: return
		if self.name is not UNCHANGED:
			with _run_alembic_ddl(conn) as impl:
				impl.rename_table(self.table_name, self.name)
	
	def _generate_reverse(self, md):
		table = _find_table(md, self.table_name)
		kwargs = {}
		if self.name is not UNCHANGED:
			kwargs['name'] = table.name
		op = AlterTable.FromSchemaObject(table, kwargs)
		if self.name is not UNCHANGED:
			op.table_name = self.name
		return op


class AddColumn(_AddDropOperation):
	def __init__(self, table_name, column):
		super().__init__()
		self.table_name = table_name
		self.column = column._copy()
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so.table), so)
	
	def apply(self, md, conn):
		tbl = _find_table(md, self.table_name)
		c = self.column._copy()
		c._set_parent(tbl, all_names = {}, allow_replacements = False)
		if conn is None: return
		with _run_alembic_ddl(conn) as impl:
			impl.add_column(tbl.name, c)
	
	def _generate_reverse(self, md):
		_ = _find_table(md, self.table_name)
		return DropColumn(self.table_name, self.column.name)

class DropColumn(_AddDropOperation):
	def __init__(self, table_name, column_name):
		super().__init__()
		self.table_name = table_name
		self.column_name = column_name
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so.table), so.name)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		c = _find_column(table, self.column_name)
		if conn is not None:
			with _run_alembic_ddl_batch(conn, md, self.table_name, schema = None) as impl:
				impl.drop_column(c.name)
		table._columns.remove(c)
	
	def _generate_reverse(self, md):
		table = _find_table(md, self.table_name)
		c = _find_column(table, self.column_name)
		return AddColumn.FromSchemaObject(c)

class AlterColumn(_AlterOperation):
	def __init__(self, table_name, column_name, *, name = UNCHANGED, type = UNCHANGED, nullable = UNCHANGED, server_default = UNCHANGED, server_onupdate = UNCHANGED):
		super().__init__()
		self.table_name = table_name
		self.column_name = column_name
		self.name = name
		self.type = type
		self.nullable = nullable
		self.server_default = server_default
		self.server_onupdate = server_onupdate
	
	@classmethod
	def FromSchemaObject(cls, so_old, kwargs):
		return cls(util._table_name(so_old.table), so_old.name, **kwargs)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		c = _find_column(table, self.column_name)
		kwargs = {}
		if self.name is not UNCHANGED:
			kwargs['new_column_name'] = self.name
		if self.type is not UNCHANGED:
			kwargs['type_'] = self.type
		if self.nullable is not UNCHANGED:
			kwargs['nullable'] = self.nullable
		if self.server_default is not UNCHANGED:
			kwargs['server_default'] = self.server_default
		if self.server_onupdate is not UNCHANGED:
			kwargs['server_onupdate'] = self.server_onupdate
		
		if not kwargs:
			return
		
		kwargs['existing_type'] = c.type
		kwargs['existing_nullable'] = c.nullable
		kwargs['existing_server_default'] = c.server_default
		kwargs['existing_server_onupdate'] = c.server_onupdate
		
		if conn is not None:
			with _run_alembic_ddl_batch(conn, md, self.table_name, schema = None) as impl:
				impl.alter_column(self.column_name, **kwargs)
		
		if self.name is not UNCHANGED:
			table._columns.remove(c)
			c.name = self.name
			c.key = self.name
			table._columns.add(c)
		if self.type is not UNCHANGED:
			c.type = self.type
		if self.nullable is not UNCHANGED:
			c.nullable = self.nullable
		if self.server_default is not UNCHANGED:
			c.server_default = self.server_default
		if self.server_onupdate is not UNCHANGED:
			c.server_onupdate = self.server_onupdate
	
	def _generate_reverse(self, md):
		table = _find_table(md, self.table_name)
		c = _find_column(table, self.column_name)
		kwargs = {}
		if self.name is not UNCHANGED:
			kwargs['name'] = c.name
		if self.type is not UNCHANGED:
			kwargs['type'] = c.type
		if self.nullable is not UNCHANGED:
			kwargs['nullable'] = c.nullable
		if self.server_default is not UNCHANGED:
			kwargs['server_default'] = c.server_default
		if self.server_onupdate is not UNCHANGED:
			kwargs['server_onupdate'] = c.server_onupdate
		op = AlterColumn.FromSchemaObject(c, kwargs)
		if self.name is not UNCHANGED:
			op.column_name = self.name
		return op


class AddPrimaryKey(_AddDropOperation):
	def __init__(self, table_name, columns, *, name = None, deferrable = None, initially = None):
		super().__init__()
		self.table_name = table_name
		self.columns = columns
		self.name = name
		self.deferrable = deferrable
		self.initially = initially
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(
			util._table_name(so.table), tuple(str(c.name) for c in so.columns),
			name = so.name,
			deferrable = so.deferrable, initially = so.initially,
		)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		pk = sa.PrimaryKeyConstraint(
			*self.columns, name = self.name, deferrable = self.deferrable,
			initially = self.initially,
		)
		pk._set_parent(table)
		if conn is None:
			return
		with _run_alembic_ddl_batch(conn, md, self.table_name, schema = None) as impl:
			impl.create_primary_key(self.name, self.columns)
	
	def _generate_reverse(self, md):
		_ = _find_table(md, self.table_name)
		return DropPrimaryKey(self.table_name, self.name)

class DropPrimaryKey(_AddDropOperation):
	def __init__(self, table_name, constraint_name = None):
		super().__init__()
		self.table_name = table_name
		self.constraint_name = constraint_name
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so.table), so.name)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		c = _find_constraint(table, self.constraint_name, sa.PrimaryKeyConstraint)
		if conn is not None:
			with _run_alembic_ddl_batch(conn, md, self.table_name, schema = None) as impl:
				impl.drop_constraint(c.name, type_ = 'primary')
		table.constraints.remove(c)
	
	def _generate_reverse(self, md):
		table = _find_table(md, self.table_name)
		c = _find_constraint(table, self.constraint_name, sa.PrimaryKeyConstraint)
		return AddPrimaryKey.FromSchemaObject(c)


class AddForeignKey(_AddDropOperation):
	def __init__(self, table_name, columns, reftable, refcolumns, *, name = None, onupdate = None, ondelete = None, deferrable = None, initially = None, match = None):
		super().__init__()
		self.table_name = table_name
		self.columns = columns
		self.reftable = reftable
		self.refcolumns = refcolumns
		self.name = name
		self.onupdate = onupdate
		self.ondelete = ondelete
		self.deferrable = deferrable
		self.initially = initially
		self.match = match
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(
			util._table_name(so.table), tuple(str(c.name) for c in so.columns),
			util._table_name(so.referred_table), tuple(str(e.column.name) for e in so.elements),
			name = so.name, onupdate = so.onupdate, ondelete = so.ondelete,
			deferrable = so.deferrable, initially = so.initially, match = so.match,
		)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		fk = sa.ForeignKeyConstraint(
			self.columns, tuple('{}.{}'.format(self.reftable, c) for c in self.refcolumns), name = self.name,
			onupdate = self.onupdate, ondelete = self.ondelete,
			deferrable = self.deferrable, initially = self.initially, match = self.match,
		)
		fk._set_parent(table)
		if conn is None:
			return
		with _run_alembic_ddl_batch(conn, md, self.table_name, schema = None) as impl:
			impl.create_foreign_key(
				self.name, self.reftable, self.columns, self.refcolumns,
				onupdate = self.onupdate, ondelete = self.ondelete,
				deferrable = self.deferrable, initially = self.initially, match = self.match,
			)
	
	def _generate_reverse(self, md):
		_ = _find_table(md, self.table_name)
		return DropForeignKey(self.table_name, self.name)

class DropForeignKey(_AddDropOperation):
	def __init__(self, table_name, constraint_name):
		super().__init__()
		self.table_name = table_name
		self.constraint_name = constraint_name
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so.table), so.name)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		c = _find_constraint(table, self.constraint_name, sa.ForeignKeyConstraint)
		if conn is not None:
			with _run_alembic_ddl_batch(conn, md, self.table_name) as impl:
				impl.drop_constraint(c.name, type_ = 'foreignkey')
		table.constraints.remove(c)
	
	def _generate_reverse(self, md):
		table = _find_table(md, self.table_name)
		c = _find_constraint(table, self.constraint_name, sa.ForeignKeyConstraint)
		return AddForeignKey.FromSchemaObject(c)


class AddUnique(_AddDropOperation):
	def __init__(self, table_name, columns, *, name = None, deferrable = None, initially = None):
		super().__init__()
		self.table_name = table_name
		self.columns = columns
		self.name = name
		self.deferrable = deferrable
		self.initially = initially
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(
			util._table_name(so.table), tuple(str(c.name) for c in so.columns),
			name = so.name, deferrable = so.deferrable, initially = so.initially,
		)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		uq = sa.UniqueConstraint(
			*self.columns, name = self.name, deferrable = self.deferrable, initially = self.initially,
		)
		uq._set_parent(table)
		if conn is None:
			return
		with _run_alembic_ddl_batch(conn, md, self.table_name) as impl:
			impl.create_unique_constraint(
				self.name, self.columns, deferrable = self.deferrable, initially = self.initially
			)
	
	def _generate_reverse(self, md):
		_ = _find_table(md, self.table_name)
		return DropUnique(self.table_name, self.name)

class DropUnique(_AddDropOperation):
	def __init__(self, table_name, constraint_name):
		super().__init__()
		self.table_name = table_name
		self.constraint_name = constraint_name
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so.table), so.name)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		c = _find_constraint(table, self.constraint_name, sa.UniqueConstraint)
		if conn is not None:
			with _run_alembic_ddl_batch(conn, md, self.table_name) as impl:
				impl.drop_constraint(c.name, type_ = 'unique')
		table.constraints.remove(c)
	
	def _generate_reverse(self, md):
		table = _find_table(md, self.table_name)
		c = _find_constraint(table, self.constraint_name, sa.UniqueConstraint)
		return AddUnique.FromSchemaObject(c)


class AddCheck(_AddDropOperation):
	def __init__(self, table_name, sqltext, *, name = None, deferrable = None, initially = None):
		super().__init__()
		self.table_name = table_name
		if isinstance(sqltext, str):
			sqltext = sa.text(sqltext)
		self.sqltext = sqltext
		self.name = name
		self.deferrable = deferrable
		self.initially = initially
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so.table), so.sqltext, name = so.name, deferrable = so.deferrable, initially = so.initially)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		ck = sa.CheckConstraint(self.sqltext, name = self.name)
		ck._set_parent(table)
		if conn is None:
			return
		with _run_alembic_ddl_batch(conn, md, self.table_name) as impl:
			impl.create_check_constraint(self.name, self.sqltext)
	
	def _generate_reverse(self, md):
		_ = _find_table(md, self.table_name)
		return DropCheck(self.table_name, self.name)

class DropCheck(_AddDropOperation):
	def __init__(self, table_name, constraint_name):
		super().__init__()
		self.table_name = table_name
		self.constraint_name = constraint_name
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so.table), so.name)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		c = _find_constraint(table, self.constraint_name, sa.CheckConstraint)
		if conn is not None:
			with _run_alembic_ddl_batch(conn, md, self.table_name) as impl:
				impl.drop_constraint(c.name, type_ = 'check')
		table.constraints.remove(c)
	
	def _generate_reverse(self, md):
		table = _find_table(md, self.table_name)
		c = _find_constraint(table, self.constraint_name, sa.CheckConstraint)
		return AddCheck.FromSchemaObject(c)


class AddIndex(_AddDropOperation):
	def __init__(self, table_name, columns, *, name = None, unique = False, **dialect_kw):
		super().__init__()
		self.table_name = table_name
		self.columns = columns
		self.name = name
		self.unique = unique
		self.dialect_kw = dialect_kw
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(
			util._table_name(so.table), tuple(str(c.name) for c in so.columns),
			name = so.name, unique = so.unique, **so.dialect_kwargs,
		)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		ix = sa.Index(self.name, *self.columns, unique = self.unique, **self.dialect_kw)
		ix._set_parent(table)
		if conn is None:
			return
		with _run_alembic_ddl_batch(conn, md, self.table_name) as impl:
			impl.create_index(self.name, self.columns, unique = self.unique, **self.dialect_kw)
	
	def _generate_reverse(self, md):
		_ = _find_table(md, self.table_name)
		return DropIndex(self.table_name, self.name)

class DropIndex(_AddDropOperation):
	def __init__(self, table_name, index_name):
		super().__init__()
		self.table_name = table_name
		self.index_name = index_name
	
	@classmethod
	def FromSchemaObject(cls, so):
		return cls(util._table_name(so.table), so.name)
	
	def apply(self, md, conn):
		table = _find_table(md, self.table_name)
		index = _find_index(table, self.index_name)
		if conn is not None:
			with _run_alembic_ddl_batch(conn, md, self.table_name) as impl:
				impl.drop_index(self.index_name)
		table.indexes.remove(index)
	
	def _generate_reverse(self, md):
		table = _find_table(md, self.table_name)
		index = _find_index(table, self.index_name)
		return AddIndex.FromSchemaObject(index)

def _find_table(md, table_name):
	table = md.tables.get(table_name)
	if table is None: # pragma: no cover
		raise ValueError("can't find {} {!r}".format(sa.Table.__name__, table_name))
	return table

def _find_column(table, column_name):
	c = table.columns.get(column_name)
	if c is None: # pragma: no cover
		raise ValueError("can't find {} {!r} on table {!r}".format(sa.Column.__name__, column_name, table.name))
	return c

def _find_constraint(table, constraint_name, t):
	for c in table.constraints:
		if type(c) != t: continue
		if c.name == constraint_name: return c
	raise ValueError("can't find {} {!r} on table {!r}".format(t.__name__, constraint_name, table.name)) # pragma: no cover

def _find_index(table, index_name):
	for c in table.indexes:
		if c.name == index_name: return c
	raise ValueError("can't find {} {!r} on table {!r}".format(sa.Index.__name__, index_name, table.name)) # pragma: no cover


class DataOperation(Operation):
	def __init__(self, forwards: Any, backwards: Optional[Any] = None) -> None:
		super().__init__()
		self.forwards = _standardize_custom_op(forwards)
		self.backwards = _standardize_custom_op(backwards)
	
	def apply(self, md: sa.MetaData, conn: Optional[Connectable] = None) -> None:
		if conn is None: return
		self.forwards(md, conn)
	
	def _generate_reverse(self, md) -> Operation:
		cls = type(self)
		return cls(self.backwards, self.forwards)

def _standardize_custom_op(obj: Any) -> Any:
	if obj is None: return None
	if isinstance(obj, (str, sa.sql.base.Executable)):
		return lambda md, conn: (conn and conn.execute(obj))
	assert callable(obj)
	return obj

@contextlib.contextmanager
def _run_alembic_ddl(conn):
	impl = _alembic_ops_impl(conn)
	yield impl
	for q in impl.output_buffer_list:
		conn.execute(sa.text(q))

@contextlib.contextmanager
def _run_alembic_ddl_batch(conn, md, table_name, *, schema = None):
	from alembic.operations import batch
	from alembic.operations.base import BatchOperations
	table = md.tables[table_name]
	impl = _alembic_ops_impl(conn)
	mock = _MockHasImpl(impl)
	impl_batch = batch.BatchOperationsImpl(
		mock, table_name, schema, 'auto', table,
		(), {}, (), {}, None, None,
	)
	batch_op = BatchOperations(mock, impl = impl_batch)
	yield batch_op
	impl_batch.flush()
	for q in impl.output_buffer_list:
		conn.execute(sa.text(q))

class _MockHasImpl:
	def __init__(self, impl):
		self.impl = impl
		self.opts = {}

def _alembic_ops_impl(conn):
	from io import StringIO
	from alembic.ddl.impl import DefaultImpl
	dialect = conn.dialect
	impl_cls = DefaultImpl.get_by_dialect(dialect)
	impl = impl_cls(dialect, None, True, None, StringIO(), {})
	impl.output_buffer_list = []
	impl.static_output = lambda text: impl.output_buffer_list.append(text)
	return impl
