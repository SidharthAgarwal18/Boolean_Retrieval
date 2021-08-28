import sys
import os
import json
import re
from stemmar import PorterStemmer
import time

def intersection_of_lists(posting1,posting2):
	intersection_posting = []

	len1 = len(posting1)
	start1 = 0
	len2 = len(posting2)
	start2 = 0

	while(start1<len1 and start2<len2):

		if(posting1[start1]==posting2[start2]):
			intersection_posting.append(posting1[start1])
			start1 += 1
			start2 += 1

		elif(posting1[start1]>posting2[start2]):
			start2 += 1

		else:
			start1 += 1

	return intersection_posting

def stem_token(token,porter):
	output = ''
	word = ''

	for char in token:
		if char.isalpha():
			word += char.lower()
		else:
			if word:
				output += porter.stem(word,0,len(word)-1)
				word = ''
			output += char.lower()
	if word:
		output += porter.stem(word,0,len(word)-1)

	return output

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

def decode4_next(file,new_first):

	if(len(new_first)<5):
		new_first += extend_strbyte(bin(int.from_bytes(file.read(1),byteorder='big'))[2:])
	
	k_str = new_first[0:5]
	num_str = new_first[5:]

	k_bits = int(k_str,2)
	if(k_bits==0):
		return 1,num_str

	while(len(num_str)<k_bits):
		num_str += extend_strbyte(bin(int.from_bytes(file.read(1),byteorder='big'))[2:])

	number_str = num_str[0:k_bits]
	remain_str = num_str[k_bits:]

	return int(number_str,2) + (1<<k_bits),remain_str
	


def decode4(bytes_pointer,indexfile_name):

	file = open(indexfile_name,"rb")
	file.seek(bytes_pointer,0)

	list_len, new_first = decode4_next(file,"")
	this_posting_list = []

	previous = 0
	for idx in range(list_len):

		document_id, new_first = decode4_next(file,new_first)
		this_posting_list.append(document_id+previous)
		previous = document_id + previous

	file.close()
	return this_posting_list

def parse_queries(queryfile_name,porter):

	file = open(queryfile_name,'r')
	query_list = []

	query_lines = re.split('\n',file.read())

	for query in query_lines:
		if query=="":
			continue

		this_query_list = re.split(' |,|\\.|\n|:|;|"|`|\'|{{|}}|[|]|\)|\(',query)
		stemmed_query_list = []
		
		for this_query in this_query_list:
			if this_query!= "":
				stemmed_query_list.append(stem_token(this_query,porter))

		query_list.append(stemmed_query_list)

	file.close()
	#print(query_list)
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
	elif(comp_type==4):
		posting_dictionary[term] = decode4(bytes_pointer,indexfile_name)
	else:
		posting_dictionary[term] = decode3(bytes_pointer,indexfile_name)

	return posting_dictionary[term]

def write_results(query_num,document_name,resultfile_name):
	file = open(resultfile_name,"a")

	file.write("Q"+str(query_num)+" ")
	file.write(str(document_name)+" ")

	if document_name != "NULL":
		file.write(str(1.0)+"\n")
	else:
		file.write(str(0.0)+"\n")


def return_doc_mapping(file):
	document_hash = {}
	total_documents = int.from_bytes(file.read(4),byteorder='big')

	for doc_i in range(total_documents):
		doc_name_len = int.from_bytes(file.read(1),byteorder='big')

		name = ""
		for name_idx in range(doc_name_len):
			name = name + chr(int.from_bytes(file.read(1),byteorder='big'))

		document_hash[doc_i+1] = name

	return document_hash


def answer_queries(query_list,comp_type,posting_dictionary,token_dictionary,indexfile_name,resultfile_name,document_mapping):
	query_num = 0

	file = open(resultfile_name,"w")
	file.close()

	for query_num,query in enumerate(query_list):

		null_query = False

		if(token_dictionary.get(query[0])==None):
			null_query = True
			#write_results(query_num,query[0],resultfile_name)
			continue

		first_list = decompress(query[0],comp_type,posting_dictionary,token_dictionary,indexfile_name)

		if(len(query)==1):

			for document_idx in first_list:
				write_results(query_num,document_mapping[(document_idx)],resultfile_name)

			#write_results(query_num,document_mapping[(first_list[0])],resultfile_name)
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
				#write_results(query_num,query[i],resultfile_name)
				continue

			intersection_list = min_list

			for this_qpl in query_posting_lists:
				intersection_list = intersection_of_lists(intersection_list,this_qpl)

			for document_idx in intersection_list:
				write_results(query_num,document_mapping[document_idx],resultfile_name)
			

			"""
			for document_id in min_list:
				find_all = True

				for this_qpl in query_posting_lists:
					if(not binary_search(document_id,this_qpl)):
						find_all = False
						break

				if(find_all):
					write_results(query_num,document_mapping[document_id],resultfile_name)
					break

			if not find_all:
				write_results(query_num,"NULL",resultfile_name)
			"""
			



num_arguments = len(sys.argv)

queryfile_name = sys.argv[1]
resultfile_name = sys.argv[2]
indexfile_name = sys.argv[3]
dictfile_name = sys.argv[4]

START_TIME = time.time()

json_file = open(dictfile_name,"r")
token_dictionary = json.load(json_file)
json_file.close()

posting_dictionary = {}


file = open(indexfile_name,"rb")
comp_type = int.from_bytes(file.read(1),byteorder='big')
new_indexfile_name = indexfile_name

if(comp_type>2 and comp_type!=4):
	comp_type = 3

	file.close()
	os.system("python -m snappy -d "+indexfile_name+" "+indexfile_name+"_temp")

	file = open(indexfile_name+"_temp","rb")
	file.read(1)
	new_indexfile_name = indexfile_name + '_temp'


document_mapping = return_doc_mapping(file)
file.close()


porter = PorterStemmer()
query_list = parse_queries(queryfile_name,porter)

print('Time for loading stuffs: '+str(time.time()-START_TIME))
SECOND_TIME = time.time()
answer_queries(query_list,comp_type,posting_dictionary,token_dictionary,new_indexfile_name,resultfile_name,document_mapping)

print('Time for answering queries: '+str(time.time()-SECOND_TIME))

if(comp_type>2 and comp_type!=4):
	os.remove(indexfile_name+"_temp")