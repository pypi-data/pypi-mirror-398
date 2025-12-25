import os
import copy
import codecs
import json

import sys
import argparse
from appPublic.argsConvert import ArgsConvert
from appPublic.dictObject import DictObject
from xls2ddl.xls2crud import build_dbdesc, build_crud_ui
from xls2ddl.singletree import build_tree_ui
def main():
	"""
	crud_json has following format
	{
		"tblname",
		"params"
	}
	"""
	parser = argparse.ArgumentParser('xls2crud')
	parser.add_argument('-m', '--models_dir', nargs='+', help="models dirs")
	parser.add_argument('-o', '--output_dir')
	parser.add_argument('modulename')
	parser.add_argument('files', nargs='*')
	args = parser.parse_args()
	if len(args.files) < 1:
		print(f'Usage:\n{sys.argv[0]} [-m models_dir] [-o output_dir] json_file ....\n')
		sys.exit(1)
	print(args)
	ns = {k:v for k, v in os.environ.items()}
	dbdesc = build_dbdesc(args.models_dir)
	dbdesc = DictObject(**dbdesc)
	print(f'{type(dbdesc)}')
	for fn in args.files:
		print(f'handle {fn}')
		crud_data = {}
		with codecs.open(fn, 'r', 'utf-8') as f:
			a = json.load(f)
			ac = ArgsConvert('${','}$')
			a = ac.convert(a,ns)
			crud_data = DictObject(**a)
			tblname = crud_data.alias or crud_data.tblname
			crud_data.output_dir = os.path.join(args.output_dir, tblname)
		# print(f'{fn}\n{json.dumps(crud_data, indent=4, ensure_ascii=False)}')
		crud_data.params.modulename = args.modulename
		crud_data.params.tblname = crud_data.tblname
		db = dbdesc.copy()
		if crud_data.uitype == 'tree':
			build_tree_ui(crud_data, db)
			continue
		build_crud_ui(crud_data, db)
if __name__ == '__main__':
	main()
