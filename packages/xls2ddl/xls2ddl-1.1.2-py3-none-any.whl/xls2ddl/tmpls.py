data_browser_tmpl = """
{
	"id":"{{tblname}}_tbl",
	"widgettype":"Tabular",
	"options":{
		"width":"100%",
		"height":"100%",
{% if not notitle %}
{% if title %}
		"title":"{{title}}",
{% else %}
		"title":"{{summary[0].title}}",
{% endif %}
{% endif %}
{% if description %}
		"description":"{{description}}",
{% endif %}
{% if toolbar %}
			"toolbar":{{json.dumps(toolbar, indent=4, ensure_ascii=False)}},
{% endif %}
		"css":"card",
{% if editor %}
		"editor":{{json.dumps(editor, indent=4, ensure_ascii=False)}},
{% endif %}
{% if not noedit %}
		"editable":{
{% if new_data_url %}
			"new_data_url": "{{new_data_url}}",
{% else %}
			"new_data_url":{%- raw -%}"{{entire_url('add_{%- endraw -%}{{summary[0].name}}{%- raw -%}.dspy')}}",{%- endraw %}
{% endif %}
{% if delete_data_url %}
			"delete_data_url": "{{delete_data_url}}",
{% else %}
			"delete_data_url":{%- raw -%}"{{entire_url('delete_{%- endraw -%}{{summary[0].name}}{%- raw -%}.dspy')}}",{%- endraw %}
{% endif %}
{% if update_data_url %}
			"update_data_url": "{{update_data_url}}"
{% else %}
			"update_data_url":{%- raw -%}"{{entire_url('update_{%- endraw -%}{{summary[0].name}}{%- raw -%}.dspy')}}"{%- endraw %}
{% endif %}
		},
{% endif %}
{% if get_data_url %}
		"data_url": "{{get_data_url}}",
{% else %}
		"data_url":"{%- raw -%}{{entire_url('./get_{%- endraw -%}{{summary[0].name}}{%- raw -%}.dspy')}}",{%- endraw %}
{% endif %}
		"data_method":"{{data_method or 'GET'}}",
		"data_params":{%- raw -%}{{json.dumps(params_kw, indent=4, ensure_ascii=False)}},{%- endraw %}
		"row_options":{
{% if idField %}
			"idField":"{{idField}}",
{% endif %}
{% if checkField %}
			"checkField":"{{checkField}}",
{% endif %}
{% if browserfields %}
			"browserfields": {{json.dumps(browserfields, indent=4, ensure_ascii=Fasle)}},
{% endif %}
{% if editexclouded %}
			"editexclouded":{{json.dumps(editexclouded, indent=4, ensure_ascii=False)}},
{% endif %}
			"fields":{{fieldliststr}}
		},  
{% if subtables_condition %}
{%- raw -%}{% {%- endraw %}if {{subtables_condition}} {%- raw -%} %}{%- endraw -%}
{% endif %}
{% if content_view %}
		"content_view":{{json.dumps(content_view, indent=4, ensure_ascii=False)}},
{% endif %}
{% if subtables_condition %}
{%- raw -%}{% endif %}{%- endraw %}
{% endif %}
		"page_rows":160,
		"cache_limit":5
	}
{% if bindsstr %}
	,"binds":{{bindsstr}}
{% endif %}
}
"""
get_data_tmpl = """
ns = params_kw.copy()
{% if logined_userid %}
userid = await get_user()
if not userid:
	return {
		"widgettype":"Error",
		"options":{
			"title":"Authorization Error",
			"timeout":3,
			"cwidth":16,
			"cheight":9,
			"message":"Please login"
		}
	}
ns['{{logined_userid}}'] = userid
ns['userid'] = userid
{% endif %}
{% if logined_userorgid %}
userorgid = await get_userorgid()
if not userorgid:
	return {
		"widgettype":"Error",
		"options":{
			"title":"Authorization Error",
			"timeout":3,
			"cwidth":16,
			"cheight":9,
			"message":"Please login"
		}
	}
ns['{{logined_userorgid}}'] = userorgid
ns['userorgid'] = userorgid
{% endif %}
debug(f'get_{{tblname}}.dspy:{ns=}')
if not ns.get('page'):
	ns['page'] = 1 
if not ns.get('sort'):
{% if sortby %}
{% if type(sortby) == type("") %}
	ns['sort'] = '{{sortby}}'
{% else %}
	ns['sort'] = {{json.dumps(sortby)}}
{% endif %}
{% else %}
	ns['sort'] = 'id'
{% endif %}
{% if relation %}
ns['sort'] = '{{relation.outter_field}}_text'
{% endif %}
sql = '''{{sql}}'''
{% if not relation %}
filterjson = params_kw.get('data_filter')
if not filterjson:
	fields = [ f['name'] for f in {{json.dumps(fields, indent=4, ensure_ascii=False)}} ]
	filterjson = default_filterjson(fields, ns)
filterdic = ns.copy()
filterdic['filterstr'] = ''
filterdic['userorgid'] = '${userorgid}$'
filterdic['userid'] = '${userid}$'
if filterjson:
	dbf = DBFilter(filterjson)
	conds = dbf.gen(ns)
	if conds:
		ns.update(dbf.consts)
		conds = f' and {conds}'
		filterdic['filterstr'] = conds
ac = ArgsConvert('[[', ']]')
vars = ac.findAllVariables(sql)
NameSpace = {v:'${' + v + '}$' for v in vars if v != 'filterstr' }
filterdic.update(NameSpace)
sql = ac.convert(sql, filterdic)
{% endif %}
debug(f'{sql=}')
db = DBPools()
dbname = get_module_dbname('{{modulename}}')
async with db.sqlorContext(dbname) as sor:
	r = await sor.sqlPaging(sql, ns) 
	return r
return {
	"total":0,
	"rows":[]
}
"""
data_new_tmpl = """
ns = params_kw.copy()
for k,v in ns.items():
	if v == 'NaN' or v == 'null':
		ns[k] = None
id = params_kw.id
if not id or len(id) > 32:
	id = uuid()
ns['id'] = id
{% for f in confidential_fields or [] %}
if params_kw.get('{{f}}'):
	ns['{{f}}'] = password_encode(params_kw.get('{{f}}'))
{% endfor %}
{% if logined_userid %}
userid = await get_user()
if not userid:
	return {
		"widgettype":"Error",
		"options":{
			"title":"Authorization Error",
			"timeout":3,
			"cwidth":16,
			"cheight":9,
			"message":"Please login"
		}
	}
ns['{{logined_userid}}'] = userid
{% endif %}
{% if logined_userorgid %}
userorgid = await get_userorgid()
if not userorgid:
	return {
		"widgettype":"Error",
		"options":{
			"title":"Authorization Error",
			"timeout":3,
			"cwidth":16,
			"cheight":9,
			"message":"Please login"
		}
	}
ns['{{logined_userorgid}}'] = userorgid
{% endif %}
db = DBPools()
dbname = get_module_dbname('{{modulename}}')
async with db.sqlorContext(dbname) as sor:
	r = await sor.C('{{summary[0].name}}', ns.copy())
	return {
		"widgettype":"Message",
		"options":{
			"user_data":ns,
			"cwidth":16,
			"cheight":9,
			"title":"Add Success",
			"timeout":3,
			"message":"ok"
		}
	}

return {
	"widgettype":"Error",
	"options":{
		"title":"Add Error",
		"cwidth":16,
		"cheight":9,
		"timeout":3,
		"message":"failed"
	}
}
"""
data_update_tmpl = """
ns = params_kw.copy()
for k,v in ns.items():
	if v == 'NaN' or v == 'null':
		ns[k] = None
{% if logined_userid %}
userid = await get_user()
if not userid:
	return {
		"widgettype":"Error",
		"options":{
			"title":"Authorization Error",
			"timeout":3,
			"cwidth":16,
			"cheight":9,
			"message":"Please login"
		}
	}
ns['{{logined_userid}}'] = userid
{% endif %}
{% if logined_userorgid %}
userorgid = await get_userorgid()
if not userorgid:
	return {
		"widgettype":"Error",
		"options":{
			"title":"Authorization Error",
			"timeout":3,
			"cwidth":16,
			"cheight":9,
			"message":"Please login"
		}
	}
ns['{{logined_userorgid}}'] = userorgid
{% endif %}
{% for f in confidential_fields or [] %}
if params_kw.get('{{f}}'):
	ns['{{f}}'] = password_encode(params_kw.get('{{f}}'))
{% endfor %}

db = DBPools()
dbname = get_module_dbname('{{modulename}}')
async with db.sqlorContext(dbname) as sor:
{% if logined_userid or logined_userorgid %}
	ns1 = {
{% if logined_userorgid %}
		"{{logined_userorgid}}": userorgid,
{% endif %}
{% if logined_userid %}
		"{{logined_userid}}": userid,
{% endif %}
		"id": params_kw.id
	}
	recs = await sor.R('{{summary[0].name}}', ns1)
	if len(recs) < 1:
		return {
			"widgettype":"Error",
			"options":{
				"title":"Update Error",
				"cwidth":16,
				"cheight":9,
				"timeout":3,
				"message":"Record no exist or with wrong ownership"
			}
		}
{% endif %}
	r = await sor.U('{{summary[0].name}}', ns)
	debug('update success');
	return {
		"widgettype":"Message",
		"options":{
			"title":"Update Success",
			"cwidth":16,
			"cheight":9,
			"timeout":3,
			"message":"ok"
		} 
	}
		
return {
	"widgettype":"Error",
	"options":{
		"title":"Update Error",
		"cwidth":16,
		"cheight":9,
		"timeout":3,
		"message":"failed"
	}
}
"""
data_delete_tmpl = """
ns = {
	'id':params_kw['id'],
}
{% if logined_userid %}
userid = await get_user()
if not userid:
	return {
		"widgettype":"Error",
		"options":{
			"title":"Authorization Error",
			"timeout":3,
			"cwidth":16,
			"cheight":9,
			"message":"Please login"
		}
	}
ns['{{logined_userid}}'] = userid
{% endif %}
{% if logined_userorgid %}
userorgid = await get_userorgid()
if not userorgid:
	return {
		"widgettype":"Error",
		"options":{
			"title":"Authorization Error",
			"timeout":3,
			"cwidth":16,
			"cheight":9,
			"message":"Please login"
		}
	}
ns['{{logined_userorgid}}'] = userorgid
{% endif %}
db = DBPools()
dbname = get_module_dbname('{{modulename}}')
async with db.sqlorContext(dbname) as sor:
	r = await sor.D('{{summary[0].name}}', ns)
	debug('delete success');
	return {
		"widgettype":"Message",
		"options":{
			"title":"Delete Success",
			"timeout":3,
			"cwidth":16,
			"cheight":9,
			"message":"ok"
		}
	}

debug('Delete failed');
return {
	"widgettype":"Error",
	"options":{
		"title":"Delete Error",
		"timeout":3,
		"cwidth":16,
		"cheight":9,
		"message":"failed"
	}
}
"""

check_changed_tmpls = """
is_checked = params_kw.get('has_{{relation.param_field}}')
debug(f'{params_kw=}, {is_checked=}')
dbname = get_module_dbname('{{modulename}}')
if is_checked == 'true':
	ns = {
		"id":uuid(),
		"{{relation.param_field}}":params_kw.{{relation.param_field}},
		"{{relation.outter_field}}":params_kw.{{relation.outter_field}}
	}
	db = DBPools();
	async with db.sqlorContext(dbname) as sor:
		await sor.C('{{tblname}}', ns)

	return  {
		"widgettype":"Message",
		"options":{
			"title":"Success",
			"message":"record add success",
			"timeout":2
		}
	}
else:
	ns = {
		"{{relation.param_field}}":params_kw.{{relation.param_field}},
		"{{relation.outter_field}}":params_kw.{{relation.outter_field}}
	}
	sql = "delete from {{tblname}} where {{relation.param_field}}=" + "${" + "{{relation.param_field}}" + "}$" + " and {{relation.outter_field}}=" + "${" + "{{relation.outter_field}}" + "}$"
	db = DBPools()
	async with db.sqlorContext(dbname) as sor:
		await sor.sqlExe(sql, ns)

	return  {
		"widgettype":"Message",
		"options":{
			"title":"Success",
			"message":"delete record success",
			"timeout":3
		}
	}
"""
