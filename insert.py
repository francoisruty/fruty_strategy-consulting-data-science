# -*- coding: utf-8 -*-
from utils import processExcelFile

#----------
filename = './data/spreadsheet.xlsx'
sheet_name='sheet_1'
table = 'sheet_1'

create_table = True
offset = 0
processExcelFile(filename, sheet_name, table, create_table, offset)


#---------- keep going for all the sheets in your spreadsheet
