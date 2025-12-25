# -*- coding:utf-8 -*-
import sys
import io
import sys
from traceback import print_exc

import codecs
import json
from sqlor.ddl_template_sqlserver import sqlserver_ddl_tmpl
from sqlor.ddl_template_mysql import mysql_ddl_tmpl
from sqlor.ddl_template_oracle import oracle_ddl_tmpl
from sqlor.ddl_template_postgresql import postgresql_ddl_tmpl

from appPublic.myTE import MyTemplateEngine
from appPublic.folderUtils import listFile
from xls2ddl.xlsxData import CRUDData, xlsxFactory

tmpls = {
	"sqlserver":sqlserver_ddl_tmpl,
	"mysql":mysql_ddl_tmpl,
	"oracle":oracle_ddl_tmpl,
	"postgresql":postgresql_ddl_tmpl
}

def xls2ddl(xlsfile,dbtype):
	data = None
	if xlsfile.endswith('json'):
		with codecs.open(xlsfile,'r','utf-8') as f:
			data = json.load(f)
	else:
		d = xlsxFactory(xlsfile)
		if d is None:
			print(xlsfile, 'can not read data')
			return
		data = d.get_data()
	if data is None:
		print(xlsfile, 'not data return from XLSX file')
		return
	tmpl = tmpls.get(dbtype.lower())
	if tmpl is None:
		raise Exception('%s database not implemented' % dbtype)
	e = MyTemplateEngine([])
	s = e.renders(tmpl,data)
	# print(data.data)
	if data.data:
		ins = gen_insert(data)
		s = f"{s}\n{ins}\n"
	return s

def gen_insert(xls):
	tbl = xls.summary[0].name
	lines = []
	for d in xls.data:
		ks = []
		vs = []
		for k,v in d.items():
			ks.append(k)
			if isinstance(v, str):
				vs.append(f"'{v}'")
			else:
				vs.append(str(v))
		
		line = f"insert into {tbl} ({','.join(ks)}) values ({','.join(vs)});"
		lines.append(line)
	return "\n".join(lines)

def model2ddl(folder,dbtype):
	ddl_str = ''
	for f in listFile(folder, suffixs=['xlsx']):
		try:
			ddl_str += f'\n-- {f}\n'
			s = xls2ddl(f,dbtype)
			ddl_str = f"{ddl_str}\n{s}\n"

		except Exception as e:
			print('Exception:',e,'f=',f)
			print_exc()
	return ddl_str

def main():
	##解决windows 终端中输出中文出现 
	# UnicodeEncodeError: 'gbk' codec can't encode character '\xa0' in position 20249
	# 错误
	# BEGIN
	# sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
	sys.stdout.reconfigure(encoding='utf-8')
	#
	# END
	if len(sys.argv) < 3:
		print('Usage:%s dbtype folder' % sys.argv[0])
		sys.exit(1)

	s = model2ddl(sys.argv[2], sys.argv[1])
	print(s)

if __name__ == '__main__':
	main()

