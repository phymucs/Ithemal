import mysql.connector
import struct
import sys
from mysql.connector import errorcode
import re
import os

#mysql specific functions
def create_connection(database):
    cnx = None
    try:
        cnx = mysql.connector.connect(user='root',password='mysql7788#',database=database,port='43562');
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    return cnx

#dynamorio specific encoding details
def get_opcode_opnd_dict(opcode_start, opnd_start):
    sym_dict = dict()
    with open('encoding.h','r') as f:
        opcode_num = opcode_start
        opnd_num = opnd_start
        for line in f:
            opcode_re = re.search('/\*.*\*/.*OP_([a-zA-Z_0-9]+),.*', line)
            if opcode_re != None:
                sym_dict[opcode_num] = opcode_re.group(1)
                opcode_num = opcode_num + 1
            opnd_re = re.search('.*DR_([A-Za-z_0-9]+),.*', line)
            if opnd_re != None:
                sym_dict[opnd_num] = opnd_re.group(1)
                opnd_num = opnd_num + 1
        f.close()

    return sym_dict

def read_offsets(filename):
    offsets_filename = filename
    offsets = list()
    with open(offsets_filename,'r') as f:
        for line in f:
            for value in line.split(','):
                offsets.append(int(value))
        f.close()
    assert len(offsets) == 5
    return offsets
    
def get_sym_dict(filename):

    offsets = read_offsets(filename)
    sym_dict = get_opcode_opnd_dict(opcode_start = offsets[0],opnd_start = offsets[1])
   
    sym_dict[offsets[2]] = 'int_immed'
    sym_dict[offsets[3]] = 'float_immed'

    return sym_dict, offsets[4]


 
#data reading function
def get_data(cnx, format, cols):
    try:
        cur = cnx.cursor(buffered=True)

        #code column is mandatory
        columns = 'code'
        for col in cols:
            columns += ',' + col
        columns += ''

        sql = 'SELECT ' + columns + ' FROM code'
        print sql
        data = list()
        cur.execute(sql)
        print cur.rowcount
        row = cur.fetchone()
        while row != None:
            item = list()
            code = list()
            if format == 'text':
                for value in row[0].split(','):
                    if value != '':
                        code.append(int(value))
            elif format == 'bin':
                if len(row[0]) % 2 != 0:
                    row = cur.fetchone()
                    continue
                for i in range(0,len(row[0]),2): 
                    slice = row[0][i:i+2]
                    convert = struct.unpack('h',slice)
                    code.append(int(convert[0]))
            
            item.append(code)
            for i in range(len(cols)):
                item.append(row[i + 1])
            data.append(item)
            row = cur.fetchone()
    except Exception as e:
        print e
    else:
        return data

