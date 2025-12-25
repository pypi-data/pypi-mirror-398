from typing import TextIO

from . import ops, util
from .migration import Migration

def render_migration(migration: Migration, buf: TextIO, *, indent: str = '\t') -> None:
	autogen_context = util._default_autogen_context()
	autogen_context.imports = {
		'import sqlalchemy as sa',
		'from sqlaltery import ops',
	}
	autogen_context.opts['indent'] = indent
	
	ops_str = []
	for op in migration.ops:
		ops_str.append(op.render(autogen_context))
	
	for imp in sorted(autogen_context.imports):
		buf.write(imp)
		buf.write('\n')
	buf.write('\n')
	
	if not ops_str:
		buf.write('OPS = []\n')
		return
	
	buf.write('OPS = [\n')
	for op_str in ops_str:
		buf.write(util._indent(op_str, autogen_context))
		buf.write(',\n')
	buf.write(']\n')

def ops_to_text(ops, *, indent: str = '\t') -> str:
	autogen_context = util._default_autogen_context()
	autogen_context.opts['indent'] = indent
	ops_str = []
	for op in ops:
		ops_str.append(op.render(autogen_context))
	return '\n'.join(ops_str)
