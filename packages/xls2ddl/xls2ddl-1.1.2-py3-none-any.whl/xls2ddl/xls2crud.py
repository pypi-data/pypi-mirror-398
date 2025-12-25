import os
import sys
import codecs
import json
import argparse

from appPublic.dictObject import DictObject
from appPublic.folderUtils import listFile, _mkdir
from appPublic.myTE import MyTemplateEngine
from appPublic.argsConvert import ArgsConvert
from xls2ddl.xlsxData import xlsxFactory
from xls2ddl.tmpls import (
	data_browser_tmpl, 
	get_data_tmpl, 
	data_new_tmpl, 
	data_update_tmpl, 
	data_delete_tmpl, 
	check_changed_tmpls
)

"""
usage:
xls2crud.py dbname models_dir uidir
"""

def build_dbdesc(models_dir: list) -> dict:
	print(f'{models_dir=}')
	mdirs = []
	if isinstance(models_dir, list):
		mdirs = models_dir
	else:
		mdirs = [models_dir]
	db_desc = {}
	for models_dir in mdirs:
		for f in listFile(models_dir, suffixs=['.xlsx']):
			print(f'{f} handle ...')
			x = xlsxFactory(f)
			d = x.get_data()
			tbname = d.summary[0].name
			db_desc.update({tbname:d})
		for f in listFile(models_dir, suffixs=['.json']):
			print(f'{f} handle ...')
			with codecs.open(f, 'r', 'utf-8') as fh:
				d = json.load(fh)
			tbname = d['summary'][0]['name']
			db_desc.update({tbname:d})
	return db_desc

def subtable2toolbar(desc):
	if desc.subtables is None:
		return
	if desc.toolbar is None:
		desc.toolbar = DictObject(**{
			"tools":[]
		})
	tools = desc.toolbar.tools or []
	binds = desc.binds or []
	for st in desc.subtables:
		tools.append({
			"selected_row": True,
			"name": st.subtable,
			"icon":"{{entire_url('/imgs/" + st.subtable + ".svg')}}",
			"label": st.title
		})
		bind = {
			"wid":"self",
			"event":st.subtable,
			"actiontype": "urlwidget",
			"target":"PopupWindow",
			"popup_options":{
				"title":st.title or st.subtable,
				"icon": "{{entire_url('/appbase/get_icon.dspy')}}?id="+st.subtable,
				"resizable": True,
				"height":"70%",
				"width":"70%"
			},
			"params_mapping": {
				"mapping":{
					"id": st.field,
					"referer_widget":"referer_widget"
				},
				"need_other":False
			},
			"options":{
				"method":"POST",
				"params":{},
				"url":st.url or "{{entire_url('../" + st.subtable + "')}}"
			}
		}
		if st.mapping:
			bind['params_mapping']['mapping'].update(st.mapping)
		binds.append(bind);
	
	desc.toolbar.tools = tools
	desc.binds = binds
	
def build_crud_ui(crud_data: dict, dbdesc: dict):
	uidir = crud_data.output_dir
	tables = [ k for k in dbdesc.keys() ]
	desc = dbdesc[crud_data.tblname].copy()
	desc.update(crud_data.params.copy())
	subtable2toolbar(desc)
	binds = desc.binds or []
	if desc.relation:
		desc.checkField = 'has_' + desc.relation.param_field 
		binds.append({
            "wid":"self",
            "event":"row_check_changed",
            "actiontype":"urlwidget",
            "target":"self",
            "options":{
                "params":{},
                "url":"{{entire_url('check_changed.dspy')}}"
            }
        })
	desc.bindsstr = json.dumps(binds, indent=4, ensure_ascii=False)
	desc.update({
		"tblname":crud_data.tblname,
		"dbname":crud_data.dbname
	})
	build_table_crud_ui(uidir, desc)

def build_table_crud_ui(uidir: str, desc: dict) -> None:
	_mkdir(uidir)
	build_data_browser(uidir, desc)
	if desc.relation:
		build_check_changed(uidir, desc)
	else:
		build_data_new(uidir, desc)
		build_data_update(uidir, desc)
		build_data_delete(uidir, desc)
	build_get_data(uidir, desc)

def alter_field(field:dict, desc:DictObject) -> dict:
	name = field['name']
	ret = field.copy()
	alters = desc.browserfields.alters
	if alters:
		[ ret.update(alters[k]) for k in alters.keys() if k == name ]
	return ret

def field_list(desc: dict) -> list:
	fs = []
	for f in desc.fields:
		if desc.codes and f.name in [c.field for c in desc.codes]:
			d = get_code_desc(f, desc)
		else:
			d = setup_ui_info(f, confidential_fields=desc.confidential_fields or [])
		"""
		use alters to modify fields
		"""
		d = alter_field(d, desc)
		fs.append(d)
	return fs

def get_code_desc(field: dict, desc: dict) -> dict:
	d = DictObject(**field.copy())
	if not desc.codes:
		return None
	for c in desc.codes:
		if d.name == c.field:
			d.label = d.title or d.name
			d.uitype = 'code'
			d.valueField = d.name
			d.textField = d.name + '_text'
			d.params = {
				'dbname':"{{get_module_dbname('" + desc.modulename + "')}}",
				'table':c.table,
				'tblvalue':c.valuefield,
				'tbltext':c.textfield,
				'valueField':d.valueField,
				'textField':d.textField
			}
			if c.cond:
				d.params['cond'] = c.cond
				ac = ArgsConvert('[[', ']]')
				vars = ac.findAllVariables(c.cond)
				for v in vars:
					d.params[v] = '{{params_kw.' + v + '}}'
			d.dataurl = "{{entire_url('/appbase/get_code.dspy')}}"
			return d
	return None

def setup_ui_info(field:dict, confidential_fields=[]) ->dict:
	d = DictObject(**field.copy())
	if d.length:
		d.cwidth = d.length if d.length < 18 else 18
		if d.cwidth < 4:
			d.cwidth = 4;
	else:
		d.length = 0

	if d.type == 'date':
		d.uitype = 'date'
		d.length = 0
	elif d.type == 'time':
		d.uitype = 'time'
		d.length = 0
	elif d.type in ['int', 'short', 'long', 'longlong']:
		d.uitype = 'int'
		d.length = 0
	elif d.type == 'text':
		d.uitype = 'text'
	elif d.type in ['float', 'double', 'decimal']:
		d.uitype = 'float'
	else:
		if d.name in confidential_fields:
			d.uitype = 'password'
		elif d.name.endswith('_date') or d.name.endswith('_dat'):
			d.uitype = 'date'
			d.length = 0
		else:
			d.uitype = 'str'
	d.datatype = d.type
	d.label = d.title or d.name
	return d

def construct_get_data_sql(desc: dict) -> str:
	shortnames = [c for c in 'bcdefghjklmnopqrstuvwxyz']
	infos = []
	if desc.relation and desc.codes:
		param_field = "${" + desc.relation.param_field + "}$"
		for code in desc.codes:
			if code.field == desc.relation.outter_field:
				return f"""select '$[{desc.relation.param_field}]$' as {desc.relation.param_field}, 
case when b.{desc.relation.param_field} is NULL then 0 else 1 end has_{desc.relation.param_field},
a.{code.valuefield} as {code.field}, 
a.{code.textfield} as {code.field}_text
from {code.table} a left join 
(select * from {desc.tblsql or desc.tblname} where {desc.relation.param_field} ={param_field}) b 
	on a.{code.valuefield} = b.{code.field}
"""
	if not desc.codes or len(desc.codes) == 0:
		return f"select * from {desc.tblsql or desc.tblname} where 1=1 " + ' [[filterstr]]'

	for i, c in enumerate(desc.codes):
		shortname = shortnames[i]
		cond = '1 = 1'
		if c.cond:
			cond = c.cond
		csql = f"""(select {c.valuefield} as {c.field}, 
			{c.textfield} as {c.field}_text from {c.table} where {cond})"""
		infos.append([f'{shortname}.{c.field}_text', f"{csql} {shortname} on a.{c.field} = {shortname}.{c.field}"])
	bt = f'(select * from {desc.summary[0].name} where 1=1' + " [[filterstr]]) a"
	infos.insert(0, ['a.*', bt]) 
	fields = ', '.join([i[0] for i in infos])
	tables = ' left join '.join([i[1] for i in infos])
	return f"""select {fields}
from {tables}"""

def filter_backslash(s):
	if s is None:
		return s
	ls = s.split('\\/')
	return '/'.join(ls)
	
def build_data_browser(pat: str, desc: dict):
	desc = desc.copy()
	desc.fieldliststr = json.dumps(field_list(desc), ensure_ascii=False, indent=4)
	e = MyTemplateEngine([])
	s = e.renders(data_browser_tmpl, desc)
	with codecs.open(os.path.join(pat, f'index.ui'), 'w', "utf-8") as f:
		f.write(filter_backslash(s))

def build_data_new(pat: str, desc: dict):
	e = MyTemplateEngine([])
	desc = desc.copy()
	s = e.renders(data_new_tmpl, desc)
	with codecs.open(os.path.join(pat, f'add_{desc.tblname}.dspy'), 'w', "utf-8") as f:
		f.write(filter_backslash(s))

def build_data_update(pat: str, desc: dict):
	e = MyTemplateEngine([])
	desc = desc.copy()
	s = e.renders(data_update_tmpl, desc)
	with codecs.open(os.path.join(pat, f'update_{desc.tblname}.dspy'), 'w', "utf-8") as f:
		f.write(filter_backslash(s))

def build_data_delete(pat: str, desc: dict):
	e = MyTemplateEngine([])
	desc = desc.copy()
	s = e.renders(data_delete_tmpl, desc)
	with codecs.open(os.path.join(pat, f'delete_{desc.tblname}.dspy'), 'w', "utf-8") as f:
		f.write(filter_backslash(s))

def build_get_data(pat: str, desc: dict):
	e = MyTemplateEngine([])
	desc = desc.copy()
	desc.sql = construct_get_data_sql(desc)
	s = e.renders(get_data_tmpl, desc)
	with codecs.open(os.path.join(pat, f'get_{desc.tblname}.dspy'), 'w', "utf-8") as f:
		f.write(filter_backslash(s))

def build_check_changed(pat:str, desc:dict):
    e = MyTemplateEngine([])
    desc = desc.copy()
    s = e.renders(check_changed_tmpls, desc)
    with codecs.open(os.path.join(pat, 'check_changed.dspy'), 'w', "utf-8") as f:
        f.write(filter_backslash(s))

if __name__ == '__main__':
	"""
	crud_json has following format
	{
		"tblname",
		"params"
	}
	"""
	parser = argparse.ArgumentParser('xls2crud')
	parser.add_argument('-m', '--models_dir')
	parser.add_argument('-o', '--output_dir')
	parser.add_argument('modulename')
	parser.add_argument('files', nargs='*')
	args = parser.parse_args()
	if len(args.files) < 1:
		print(f'Usage:\n{sys.argv[0]} [-m models_dir] [-o output_dir] json_file ....\n')
		sys.exit(1)
	ns = {k:v for k, v in os.environ.items()}
	for fn in args.files:
		print(f'handle {fn}')
		crud_data = {}
		with codecs.open(fn, 'r', 'utf-8') as f:
			a = json.load(f)
			ac = ArgsConvert('${','}$')
			a = ac.convert(a,ns)
			crud_data = DictObject(**a)
		if args.models_dir:
			crud_data.models_dir = args.models_dir
		models_dir = crud_data.models_dir
		if args.output_dir:
			tblname = crud_data.alias or crud_data.tblname
			crud_data.output_dir = os.path.join(args.output_dir, tblname)
		crud_data.params.modulename = args.modulename
		dbdesc = build_dbdesc(models_dir)
		build_crud_ui(crud_data, dbdesc)

