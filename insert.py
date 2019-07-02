# -*- coding: utf-8 -*-
from utils import processExcelFile

#----------
filename = './data/spreadsheet.xlsx'
sheet_name='sheet_1'
table = 'sheet_1'

create_table = True
processExcelFile(filename, sheet_name, table, create_table)


#---------- keep going for all the sheets in your spreadsheet
