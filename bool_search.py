import sys
import os
import json
import re

def decode0(bytes_pointer,indexfile_name):

	file = open(indexfile_name,"rb")
	file.seek(bytes_pointer,0)

	list_len = int.from_bytes(file.read(4),byteorder='big')
	this_posting_list = []

	for idx in range(list_len):
		document_id = int.from_bytes(file.read(4),byteorder='big')
		this_posting_list.append(document_id)

	file.close()
	return this_posting_list

def decode1_next(file):

	byte_int = int.from_bytes(file.read(1),byteorder='big')
	number = byte_int & 127

	while(byte_int>=128):
		byte_int = int.from_bytes(file.read(1),byteorder='big')
		number = (number<<7) + (byte_int & 127)

	return number

def decode1(bytes_pointer,indexfile_name):

	file = open(indexfile_name,"rb")
	file.seek(bytes_pointer,0)

	list_len = decode1_next(file)
	this_posting_list = []

	previous = 0
	for idx in range(list_len):
		document_id = decode1_next(file) + previous
		this_posting_list.append(document_id)
		previous = document_id

	file.close()
	return this_posting_list

def extend_strbyte(small_str):
	x = 8 - len(small_str)

	new_str = ""
	for index in range(x):
		new_str += "0"

	new_str += small_str
	return new_str

def decode2_next(file,new_first):
	ones_finished = False
	ones = 0

	string_after10 = ""

	for index in range(len(new_first)):
		if new_first[index]=='1':
			ones += 1
		else:
			string_after10 = new_first[(index+1):]
			ones_finished=True
			break

	while(not ones_finished):
		byte_str = extend_strbyte(bin(int.from_bytes(file.read(1),byteorder='big'))[2:])

		for index in range(len(byte_str)):
			if byte_str[index]=='1':
				ones+=1
			else:
				string_after10 = byte_str[(index+1):]
				ones_finished=True
				break

	ll_x = ones+1

	byte_str = string_after10
	while(len(byte_str)<ll_x-1):
		byte_str = byte_str + extend_strbyte(bin(int.from_bytes(file.read(1),byteorder='big'))[2:])

	byte_str_int = int(byte_str[0:(ll_x-1)],2) if byte_str[0:(ll_x-1)]!="" else 0
	l_x = byte_str_int + (1<<(ll_x-1))

	remain_str = byte_str[(ll_x-1):]

	while(len(remain_str)<l_x-1):
		remain_str = remain_str + extend_strbyte(bin(int.from_bytes(file.read(1),byteorder='big'))[2:])

	return_str = remain_str[(l_x-1):]

	remain_str_int = int(remain_str[0:(l_x-1)],2) if remain_str[0:(l_x-1)]!="" else 0
	decoded_number = remain_str_int + (1<<(l_x-1))

	return decoded_number,return_str


def decode2(bytes_pointer,indexfile_name):

	file = open(indexfile_name,"rb")
	file.seek(bytes_pointer,0)

	list_len, new_first = decode2_next(file,"")
	this_posting_list = []

	previous = 0
	for idx in range(list_len):

		document_id, new_first = decode2_next(file,new_first)
		this_posting_list.append(document_id+previous)
		previous = document_id + previous

	file.close()
	return this_posting_list


def decode3(bytes_pointer,indexfile_name):

	file = open(indexfile_name,"rb")
	file.seek(bytes_pointer,0)

	list_len = int.from_bytes(file.read(4),byteorder='big')
	this_posting_list = []

	previous = 0
	for idx in range(list_len):
		document_id = int.from_bytes(file.read(4),byteorder='big') + previous
		this_posting_list.append(document_id)
		previous = document_id

	file.close()
	return this_posting_list


def parse_queries(queryfile_name):

	file = open(queryfile_name,'r')
	query_list = []

	query_lines = re.split('\n',file.read())

	for query in query_lines:
		query_list.append(re.split(' ',query))

	file.close()
	return query_list

def binary_search(document_id,posting_list):

	if posting_list==[]:
		return False

	start = 0
	end = len(posting_list) - 1

	while(start<end):
		mid = start + (end-start)//2

		if(posting_list[mid]==document_id):
			return True
		if(posting_list[mid]<document_id):
			start = mid+1
		else:
			end = mid-1

	if(posting_list[start]==document_id):
		return True

	return False

def decompress(term,comp_type,posting_dictionary,token_dictionary,indexfile_name):

	if(posting_dictionary.get(term)!=None):
		return posting_dictionary[term]

	bytes_pointer = token_dictionary[term]

	if(comp_type==0):
		posting_dictionary[term] = decode0(bytes_pointer,indexfile_name)
	elif(comp_type==1):
		posting_dictionary[term] = decode1(bytes_pointer,indexfile_name)
	elif(comp_type==2):
		posting_dictionary[term] = decode2(bytes_pointer,indexfile_name)
	else:
		posting_dictionary[term] = decode3(bytes_pointer,indexfile_name)

	return posting_dictionary[term]

def write_results(query_num,document_name,resultfile_name):
	file = open(resultfile_name,"a")

	file.write("Q"+str(query_num)+"\t")
	file.write(str(document_name)+"\t")

	if document_name != "NULL":
		file.write(str(1.0)+"\n")
	else:
		file.write(str(0.0)+"\n")


def answer_queries(query_list,comp_type,posting_dictionary,token_dictionary,indexfile_name,resultfile_name,document_mapping):
	query_num = 0

	file = open(resultfile_name,"w")
	file.close()

	for query_num,query in enumerate(query_list):

		null_query = False

		if(token_dictionary.get(query[0])==None):
			null_query = True
			write_results(query_num,"NULL",resultfile_name)
			continue

		first_list = decompress(query[0],comp_type,posting_dictionary,token_dictionary,indexfile_name)

		if(len(query)==1):
			write_results(query_num,first_list[0],resultfile_name)
		else:
			query_posting_lists = [first_list]
			min_len = len(first_list)
			min_list = first_list

			for i in range(1,len(query)):

				if(token_dictionary.get(query[i])==None):
					null_query = True
					break

				temp_list = decompress(query[i],comp_type,posting_dictionary,token_dictionary,indexfile_name)
				query_posting_lists.append(temp_list)

				if min_len>len(temp_list):
					min_list = temp_list
					min_len = len(temp_list)

			if null_query:
				write_results(query_num,"NULL",resultfile_name)
				continue

			for document_id in min_list:
				find_all = True

				for this_qpl in query_posting_lists:
					if(not binary_search(document_id,this_qpl)):
						find_all = False
						break

				if(find_all):
					write_results(query_num,document_id,resultfile_name)
					break

			if not find_all:
				write_results(query_num,"NULL",resultfile_name)



num_arguments = len(sys.argv)

queryfile_name = sys.argv[1]
resultfile_name = sys.argv[2]
indexfile_name = sys.argv[3]
dictfile_name = sys.argv[4]

json_file = open(dictfile_name,"r")
token_dictionary = json.load(json_file)
json_file.close()

posting_dictionary = {}


file = open(indexfile_name,"rb")
comp_type = int.from_bytes(file.read(1),byteorder='big')
new_indexfile_name = indexfile_name

if(comp_type>2):
	comp_type = 3

	file.close()
	os.system("python -m snappy -d "+indexfile_name+" "+indexfile_name+"_temp")

	file = open(indexfile_name+"_temp","rb")
	file.read(1)
	new_indexfile_name = indexfile_name + '_temp'

file.close()


query_list = parse_queries(queryfile_name)
document_mapping = {}


answer_queries(query_list,comp_type,posting_dictionary,token_dictionary,new_indexfile_name,resultfile_name,document_mapping)

#toke_dict_keys = list(token_dictionary.keys())
#for i in [107,1007,1792,728,693]:
#	print(decode3(token_dictionary[toke_dict_keys[i]],new_indexfile_name))
#	print('\n')

if(comp_type>2):
	os.remove(indexfile_name+"_temp")