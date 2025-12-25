from typing import Optional, Any, List, Iterable, Union
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import sqlalchemy as sa
from sqlalchemy.engine import Engine, Connectable

from .ops import Operation
from .migration import Migration
from . import render, util

Pathlike = Union[str, Path]

class SQLAltery:
	def __init__(self, dir: Pathlike = 'migrations', *, indent: str = '\t') -> None:
		"""
			dir: migration file directory (need not exist)
			indent: indent string for generated migrations
		"""
		self._dir = Path(str(dir))
		self._indent = indent
		self._migrations = None
	
	def generate(self, md: sa.MetaData) -> None:
		ops = self._diff(md)
		if not ops:
			return
		self._save_migration(ops)
	
	def diff(self, md: sa.MetaData) -> str:
		ops = self._diff(md)
		if not ops: return ''
		return render.ops_to_text(ops, indent = self._indent)
	
	def _diff(self, md_head: sa.MetaData) -> List[Operation]:
		self._load_migrations()
		
		md_migrations = sa.MetaData()
		for op in self._collect_ops(0):
			op.apply(md_migrations, None)
		
		from .compare import diff_md
		return list(diff_md(md_migrations, md_head))
	
	@contextmanager
	def connect_to(self, engine: Engine) -> 'Migrator':
		with engine.begin() as conn:
			yield Migrator(self, conn)
	
	def _load_migrations(self) -> List[Migration]:
		if self._migrations is None:
			self._migrations = list(_iter_migrations(self._dir))
			md = sa.MetaData()
			for m in self._migrations:
				for op in m.ops:
					op.generate_reverse(md)
		return self._migrations
	
	def _save_migration(self, ops: List[Operation]) -> None:
		migrations = self._load_migrations()
		migration = Migration(len(migrations) + 1, ops)
		migrations.append(migration)
		filename = self._dir / '{:03}.py'.format(migration.number)
		filename.parent.mkdir(exist_ok = True, parents = True)
		with filename.open('w') as fh:
			render.render_migration(migration, fh, indent = self._indent)
	
	def _collect_ops(self, start: int, end: Optional[int] = None) -> List[Operation]:
		migrations = self._load_migrations()
		if end is None:
			end = len(migrations)
		(idx1, idx2) = sorted((start, end))
		ops = []
		for m in migrations[idx1:idx2]:
			ops.extend(m.ops)
		if start > end:
			ops = [o.reverse for o in reversed(ops)]
		return ops

class Migrator:
	def __init__(self, altery: SQLAltery, conn: Connectable) -> None:
		self.altery = altery
		self.conn = conn
		# Metadata for internal migration table
		self._md = sa.MetaData()
		self._table = sa.Table('sqlaltery_migration', self._md,
			sa.Column('order', sa.Integer, nullable = False),
			sa.Column('revision', sa.Integer, nullable = False),
			sa.Column('date_applied', sa.DateTime(timezone = True), nullable = False, default = util.utcnow),
		)
	
	def migrate(self, revision: Optional[int] = None, *, initial: int) -> None:
		migrations = self.altery._load_migrations()
		
		if revision is None:
			revision = len(migrations)
		
		if revision > len(migrations): # pragma: no cover
			raise ValueError("Invalid revision {!r}".format(revision))
		
		rev_db = self.get_db_revision()
		if rev_db is None:
			self._set_db_revision(initial)
			rev_db = initial
		
		if rev_db > len(migrations): # pragma: no cover
			raise ValueError("Invalid DB revision {!r}".format(rev_db))
		
		md = sa.MetaData()
		for op in self.altery._collect_ops(0, rev_db):
			op.apply(md, None)
		for op in self.altery._collect_ops(rev_db, revision):
			op.apply(md, self.conn)
		
		self._set_db_revision(revision)
	
	def get_db_revision(self) -> Optional[int]:
		t = self._table
		if not _table_exists(self.conn, t):
			return None
		q = sa.select(t.c['revision']).order_by(sa.desc(t.c['order'])).limit(1)
		return self.conn.execute(q).scalar()
	
	def _set_db_revision(self, revision: int) -> None:
		t = self._table
		if not _table_exists(self.conn, t):
			self._md.create_all(self.conn)
		q = sa.select(sa.func.max(t.c['order']))
		order = self.conn.execute(q).scalar()
		if order is None:
			order = -1
		q = sa.insert(t).values(revision = revision, order = order + 1)
		self.conn.execute(q)

def _table_exists(conn: Connectable, t: sa.Table) -> bool:
	return sa.inspect(conn).has_table(t.name)

def _iter_migrations(directory: Path) -> Iterable[Migration]:
	from importlib import util
	
	if not directory.exists():
		return
	
	base = '.'.join(directory.parts)
	
	for p in sorted(directory.iterdir()):
		if p.name == '__init__.py': continue
		if p.suffix != '.py': continue
		spec = util.spec_from_file_location('{}.{}'.format(base, p.stem), str(p))
		mod = util.module_from_spec(spec)
		spec.loader.exec_module(mod)
		yield Migration(int(p.stem), mod.OPS)
