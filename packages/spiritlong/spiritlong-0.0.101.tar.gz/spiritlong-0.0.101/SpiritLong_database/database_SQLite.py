#!/usr/bin/python3
# coding=utf-8
##################################################################
#              ____     _     _ __  __                 
#             / __/__  (_)___(_) /_/ /  ___  ___  ___ _
#            _\ \/ _ \/ / __/ / __/ /__/ _ \/ _ \/ _ `/
#           /___/ .__/_/_/ /_/\__/____/\___/_//_/\_, / 
#              /_/                              /___/  
# 
# Copyright (c) 2025 Chongqing Spiritlong Technology Co., Ltd.
# All rights reserved.
# @author	arthuryang
# @brief	SQLite驱动
##################################################################

# 假设每个SQLite文件只使用一个数据库

import	sqlite3
import	os
import	re
import	SpiritLong_excel
import	SpiritLong_utility

class SQLiteDatabase(object):
	def __init__(self, filename):
		# 数据库文件
		self.database_filename	= filename

		# 打开数据库
		self.database	= sqlite3.connect(filename)

	## 析构函数
	def __del__(self):
		# 关闭数据库
		self.database.close()

	## 执行SQL语句
	# 其他函数中应调用此函数来执行SQL语句
	# 私有方法，避免从外部直接调用
	#	SQL_string	要执行的SQL语句
	#	need_result	查询语句返回查询结果
	#	return_ID	当need_result==False时，返回插入语句的ID，多条语句将会返回第一个新纪录的ID；当need_result==True时，返回受影响的行数
	def _execute(self, SQL_string, need_result=False, return_ID=False):
		result	= None
		try:
			cursor 		= self.database.cursor()

			# 执行SQL语句
			cursor.execute(SQL_string)

			if need_result:
				columns = [desc[0] for desc in cursor.description]
				result = [dict(zip(columns, row)) for row in cursor.fetchall()]
			elif return_ID:
				# 获取第一个新插入记录的ID
				result	= cursor.lastrowid
			else:
				result	= cursor.rowcount
				
			cursor.close()

			return result
		except Exception as ex:
			# 回滚
			self.database.rollback()
			return None
	
	## 查询一条记录
	def query_single(self, SQL_string, *args):
		result	= self._execute(SQL_string+" LIMIT 1", need_result=True)
		return result[0] if result else None
	
	## 查询所有记录
	def query(self, SQL_string, *args):
		return self._execute(SQL_string, need_result=True)
	
	## 插入记录，若ID已经存在，则更新该记录。本实现中，insert包含了update
	#	table	要插入的表
	#	records	记录的列表[{}]
	# 如果只有一条记录，则返回其ID；否则返回None
	def insert(self, table, records):
		if not records:
			print("新增/更新0条记录")
			return None
		
		if isinstance(records, dict):
			records		= [records]

		if not isinstance(records, list):
			print("记录要用列表")
			return None
		
		# 已有ID的列表
		SQL_string	= f"SELECT ID FROM `{table}`"
		result		= self.query(SQL_string)
		ID_all		= [int(i['ID']) for i in result]

		# 把没有ID的选出来
		records_insert	= []
		records_update	= []
		for r in records:
			if 'ID' in r and not r['ID']:
				# 有ID而为空，去掉之
				r.pop('ID')

			if 'ID' not in r:
				# 无ID
				records_insert.append(r)
			else:
				# 有ID
				if ID_all and int(r['ID']) in ID_all:
					# ID已经存在
					records_update.append(r)
				else:
					# ID不存在
					records_insert.append(r)
		result	= None

		# UPDATE		
		if records_update:
			self.update(table, records_update)		

		# INSERT
		if records_insert: 	
			# 所有出现了的字段名合并到一个列表
			field_names_set	= set()
			for r in records_insert:
				field_names_set	= field_names_set.union(set(r.keys()))
			field_names	= list(field_names_set)

			# 构建赋值的值列表：若该字段若没有，则尝试设置为NULL
			value_strings	= []
			for r in records_insert:
				# 将每个记录的值生成字符串添加到values，要进行转义处理
				values	= []
				for f in field_names:
					if f not in r or r[f] is None:
						values.append(f"NULL")
					elif isinstance(r[f], str):
						v	= r[f]
						values.append(f"'{self.replace(v)}'")
					elif isinstance(r[f], float) or isinstance(r[f], decimal.Decimal) or isinstance(r[f], int):
						# 直接转换成字符串
						v	= str(r[f])
						values.append(f"'{self.replace(v)}'")
					elif isinstance(r[f], datetime.datetime):
						# 日期时间处理为标准格式
						v	= f"{r[f]:%Y-%m-%d %H:%M:%S}"
						values.append(f"'{self.replace(v)}'")
					else:
						# 其他数据类型都按JSON来处理
						v	= json.dumps(r[f], ensure_ascii=False)
						values.append(f"'{self.replace(v)}'")
				value_strings.append(f"( {','.join(values)} )")			
			SQL_string	= f"INSERT INTO `{table}` (`{'`,`'.join(field_names)}`) VALUES {','.join(value_strings)}"

			# 执行INSERT之前先查询最大ID
			max_ID	= 0
			if self.redis:
				result	= self.query(f"SELECT MAX(ID) FROM `{table}`")
				try:
					max_ID	= int(result[0]['MAX(ID)'])
				except Exception:
					# 有可能是空表，此时会返回[{'MAX(ID)':'NULL'}]
					max_ID	= 0
			
			# 执行
			try:
				result	= self._execute(SQL_string, return_ID=True)
				print(f"表{table}新增{len(records_insert) if result else 0}条记录，last_ID={result}")
			except Exception as ex:
				print(f"表{table}新增{len(records_insert)}条记录失败：{ex}")
				return
		return result
	
	## 更新记录
	# 	table	记录所在的表
	# 	records	一条或多条记录的列表，每个记录必须包含ID，更新字段可以不一致
	# 返回ID_list
	def update(self, table, records):
		if not records:
			print(f"update {table}：没有需要更新的数据")
			return False
		
		if isinstance(records, dict):
			records	= [records]
			
		# 对每一条记录进行更新
		ID_list	= []
		for r in records:
			if 'ID' not in r:
				# 必须要包含ID字段
				continue
			ID	= int(r['ID'])
			
			field_value_pairs	= []
			for f in r:
				if f!='ID':
					# 注意值要用单引号包起来，且内容需要处理
					v	= 'NULL' if r[f] is None else f"'{self.replace(r[f])}'"
					field_value_pairs.append(f"`{f}`={v}")
			SQL_string = f"UPDATE `{table}` SET {','.join(field_value_pairs)} WHERE ID={ID}"

			# 执行
			n	= self._execute(SQL_string)

			if n==1:
				# UPDATE返回受影响的行数，指定了ID应该只有一行受影响，此时表示成功更新
				# 注意：如果该记录每个域的新值都与旧值相同，即没有改变，则不会返回1
				ID_list.append(ID)
				self.logger.info(f"表{table}更新ID={ID}")

		print(f"表{table}更新了{len(ID_list)}条记录")

		return ID_list
	
	## 删除记录
	def delete(self, table, ID):
		SQL_string	= f"DELETE FROM `{table}` WHERE `ID`={ID}"
		self._execute(SQL_string)

		# 更新redis
		self.update_redis(table, ID_list=[ID])

	
	############################### 工具 ###############################

	## 获取数据库的结构
	def get_schema(self):
		# 读取表
		result	= self.query(f'''PRAGMA table_list''')
		tables	= [{'table_name':r['name']} for r in result if not r['name'].startswith('sqlite_')]

		if tables==None:
			# 操作失败
			return None

		for t in tables:
			t['fields']	= []
			result	= self.query(f'''PRAGMA table_info("{t['table_name']}") ''')
			if result:
				for r in result:
					# index=0的列必须为ID，类型为INTEGER，且为Primary Key
					t['fields'].append({
						'name'		: r['name'],
						'index'		: r['cid'],
						'type'		: r['type'],
						'notnull'	: r['notnull'],
						'default'	: r['dflt_value'],
					})
		return tables

	## 导出数据表结构到excel
	# 注意：SQLITE无法对表和字段进行注释，只能在DDL中存放对应的注释
	def export_excel_schema(self, filename=None):
		if not filename:
			# 使用默认文件名
			name	= os.path.basename(self.database_filename)
			name	= os.path.splitext(name)[0]
			filename	= f"SQLITE数据库结构{name}.xlsx"

		tables	= self.get_schema()
		fields	= [
			'序号',	
			'字段名',	
			'说明',	
			'类型',	
			'默认值',	
			'必填',	
		]
		
		records	= []
		table_title_lines	= []
		for t in tables:
			# 从DDL中获取注释
			result	= self.query(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{t['table_name']}'")
			result	= re.search(r"(?P<head>.*)\((?P<fields>.*)\)", result[0]['sql'], re.M|re.S)
			head	= result.group('head').split('--', 1)
			table_comment	= head[1] if len(head)>1 else ''
			body	= result.group('fields').split('\n')
			field_comment	= {}
			for f in body:
				result	= re.search(r"\s(?P<name>\S+).*--(?P<comment>.*)", f, re.M|re.S)
				if result:
					# 名称可能被方括号标注了，需要去掉
					name	= result.group('name').replace('[', '').replace(']', '').strip()
					field_comment[name]	= result.group('comment').strip()
			
			# 表名和表注释
			records.append({
				# 注意：对应表头就是叫字段名
				'字段名'	: t['table_name'],
				'说明'		: table_comment,
			})
			table_title_lines.append(len(records))

			# 每个字段一行
			for i, f in enumerate(t['fields']):
				if f['name']=='ID':
					# 总是假设ID是在第一个位置
					continue
				comment	= field_comment[f['name']] if f['name'] in field_comment else ""
				records.append({
					'序号'		: i,
					'字段名'	: f['name'],
					'说明'		: comment,
					'类型'		: f['type'],
					'默认值'	: f['default'],
					'必填'		: '●' if f['notnull'] else "",
				})

		# 写入excel
		book	= SpiritLong_excel.open_xlsx(filename, read_only=False)
		sheet	= book.create_sheet('表结构') if '表结构' not in book.sheetnames else book['表结构']
		SpiritLong_excel.records_to_sheet(sheet, {
				'titles'	: fields,
				'records'	: records
			})
		
		# 设置每个表的表头和ID样式
		format_table_name	= {
				'font'		: SpiritLong_excel.cell_font(color='FFFFFF'),
				'fill'		: SpiritLong_excel.cell_fill(color='FC760F'),
		}
		format_table_comment	= {
				'font'		: SpiritLong_excel.cell_font(color='FC760F'),
		}
	
		format_ID	= {
				'font'		: SpiritLong_excel.cell_font(color='4169E1'),
		}

		# 注意要加上标题行
		table_title_lines	= [i+1 for i in table_title_lines]
		for line in range(2, sheet.max_row+1):
			if line in table_title_lines:
				SpiritLong_excel.set_cell_format(sheet, line, 2, **format_table_name)
				SpiritLong_excel.set_cell_format(sheet, line, 3, **format_table_comment)
			else:
				SpiritLong_excel.set_cell_format(sheet, line, 1, **format_ID)
		
		
		SpiritLong_excel.close_xlsx(book, filename)
		
	## 从excel导入数据结构表，写入到一个文件，若此文件已经存在，则将覆盖
	def import_excel_schema(self, filename):
		# 读取excel文件
		book	= SpiritLong_excel.open_xlsx(filename)
		sheet	= book['表结构']
		records	= SpiritLong_excel.get_records_with_title(sheet)
		book.close()

		# 清空本数据库所有的表
		tables	= self.get_schema()
		for t in tables:
			self._execute(f"DROP TABLE [{t['table_name']}]")

		# 分析表结构
		tables	= []
		table	= {}
		for i in range(len(records)):
			r	= records[i]
			if not r['序号']:
				# 这是表的开头
				table	= {
					'table_name'	: r['字段名'],
					'comment'	: r['说明'],
					'fields'	: [],
				}
				tables.append(table)
				continue
			table['fields'].append({
				'name'		: r['字段名'],
				'comment'	: r['说明'].strip() if r['说明'] else '',
				'type'		: r['类型'].strip() if r['类型'] else '',
				'default'	: f'DEFAULT {r['默认值'].strip()}' if r['默认值'] else '',
				'null'		: 'NOT NULL' if r['必填'] else '',
			})

		# 逐个添加表
		for t in tables:
			# 可以在方括号中使用保留字
			SQL_string	= f'''CREATE TABLE [{t['table_name']}] -- {t['comment'].strip() if t['comment'] else ''}\n(\n'''
			
			fields		= ['\tID\tINTEGER PRIMARY KEY']
			if len(t['fields'])>1:
				# 不止一个ID列的情况
				fields[0]	+= ','

			for i, f in enumerate(t['fields']):
				if f['name']=='ID':
					continue
				properties	= [f['type']]
				if f['null']:
					properties.append(f['null'])
				if f['default']:
					properties.append(f['default'])
				line	= f"\t[{f['name']}]\t{' '.join(properties)}{',' if i+1<len(t['fields']) else ''}{f'\t-- {f['comment']}' if f['comment'] else ''}"
				fields.append(line)
			SQL_string	+= f'{'\n'.join(fields)}\n);\n'

			print(SQL_string)
			self._execute(SQL_string)
		

if __name__ == '__main__':
	b	= SQLiteDatabase('test.sqlite')
	
	# r	= b.query('SELECT * FROM sqlite_master WHERE type="table";')
	# for f in r[0]:
	# 	print(f"{f}\t{r[0][f]}")
	# print('-----------------')

	# r	= b.query('PRAGMA table_list')
	
	# r	= b.get_schema()
	#print(r)
	
	schema_filename	= "SQLITE数据库结构test.xlsx"
	b.export_excel_schema()
	
	schema_filename	= "SQLITE数据库结构test1.xlsx"
	b.import_excel_schema(schema_filename)