import sys
import os
from bs4 import BeautifulSoup
import re
import time
import json
from stemmar import PorterStemmer

def map_documents(file,document_hash):
	bytes_used = 0

	total_documents = len(document_hash.keys())
	file.write(total_documents.to_bytes(4,byteorder='big'))
	bytes_used += 4

	for idx in range(1,total_documents+1):

		doc_name_len = len(document_hash[idx])
		file.write(doc_name_len.to_bytes(1,byteorder='big'))
		bytes_used += 1

		for char in document_hash[idx]:
			file.write(ord(char).to_bytes(1,byteorder='big'))
			bytes_used+= 1

	return bytes_used

def compression0(dictionary,index_file_name,document_hash):

	token_dictionary = {}
	bytes_pointer = 0

	file = open(index_file_name+'.idx','wb')

	compression_type = 0
	file.write(compression_type.to_bytes(1,byteorder='big'))
	bytes_pointer += 1

	bytes_pointer += map_documents(file,document_hash)

	file.write(len(dictionary.keys()).to_bytes(4,byteorder='big'))
	bytes_pointer += 4

	for index in (dictionary.keys()):

		token_dictionary[index] = bytes_pointer

		length = len(dictionary[index])
		file.write((length).to_bytes(4,byteorder='big'))
		bytes_pointer += 4
		
		for idx in dictionary[index]:
			file.write(idx.to_bytes(4,byteorder='big'))
			bytes_pointer += 4

	file.close()

	file = open(index_file_name+'.dict','w')
	json.dump(token_dictionary,file)
	file.close()

def encode1(number,file):

	if(number==0):
		file.write(number.to_bytes(1,byteorder='big'))
		return 1

	stack = []
	first = True

	while(number>0):
		bits7 = number & (127)
		number = number>>7

		if(first):
			temp = bits7
			first = False
		else:
			temp = bits7+128

		stack.append(temp)

	bytes_used = 0

	while(len(stack)>0):
		file.write(stack.pop().to_bytes(1,byteorder='big'))
		bytes_used += 1

	return bytes_used


def compression1(dictionary,index_file_name,document_hash):

	token_dictionary = {}
	bytes_pointer = 0

	file = open(index_file_name+'.idx','wb')

	compression_type = 1
	file.write(compression_type.to_bytes(1,byteorder='big'))
	bytes_pointer += 1

	bytes_pointer += map_documents(file,document_hash)

	bytes_pointer += encode1(len(dictionary.keys()),file)

	for index in (dictionary.keys()):

		token_dictionary[index] = bytes_pointer

		length = len(dictionary[index])
		bytes_pointer += encode1(length,file)

		previous = 0 							# gap encoding
		for idx in dictionary[index]:
			bytes_pointer += encode1(idx-previous,file)
			previous = idx
	file.close()

	file = open(index_file_name+'.dict','w')
	json.dump(token_dictionary,file)
	file.close()

def encode2(previous_last,number,file):

	l_x = len(bin(number)[2:])
	ll_x = len(bin(l_x)[2:])

	Ull_x = ""
	i = 1
	while(i<ll_x):
		Ull_x = Ull_x + "1"
		i = i + 1
	Ull_x = Ull_x + "0"

	compressed_bin_str = previous_last + Ull_x + (bin(l_x)[2:])[1:] + (bin(number)[2:])[1:]

	bytes_needed = (len(compressed_bin_str)//8)
	bits_left = (len(compressed_bin_str)%8)

	if(bits_left==0):
		temp_last = ""
	else:
		temp_last = compressed_bin_str[(len(compressed_bin_str)-bits_left):]
		compressed_bin_str = compressed_bin_str[0:(len(compressed_bin_str)-bits_left)]

	if compressed_bin_str!="":
		file.write(int(compressed_bin_str,2).to_bytes(bytes_needed,byteorder='big'))

	return (temp_last,bytes_needed)


def compression2(dictionary,index_file_name,document_hash):

	token_dictionary = {}
	bytes_pointer = 0

	file = open(index_file_name+'.idx','wb')
	compression_type = 2
	file.write(compression_type.to_bytes(1,byteorder='big'))

	bytes_pointer += 1

	bytes_pointer += map_documents(file,document_hash)

	previous_last,temp_pointer = encode2("",len(dictionary.keys()),file)
	bytes_pointer += temp_pointer

	for index in (dictionary.keys()):

		token_dictionary[index] = bytes_pointer

		length = len(dictionary[index])
		previous_last,temp_pointer = encode2(previous_last,length,file)
		bytes_pointer += temp_pointer

		previous = 0 							# gap encoding
		for idx in dictionary[index]:

			previous_last,temp_pointer = encode2(previous_last,idx-previous,file)
			bytes_pointer += temp_pointer
			previous = idx

		if previous_last!="":

			bits_left = 8 - len(previous_last)
			final_bin = int(previous_last,2)
			final_bin = final_bin<<bits_left

			file.write(final_bin.to_bytes(1,byteorder='big'))

			bytes_pointer += 1
			previous_last = ""

	file.close()

	file = open(index_file_name+'.dict','w')
	json.dump(token_dictionary,file)
	file.close()	


def compression3(dictionary,index_file_name,document_hash):

	token_dictionary = {}
	bytes_pointer = 0

	file = open(index_file_name+'_temp'+'.idx','wb')

	compression_type = 3
	file.write(compression_type.to_bytes(1,byteorder='big'))
	bytes_pointer += 1

	bytes_pointer += map_documents(file,document_hash)

	file.write(len(dictionary.keys()).to_bytes(4,byteorder='big'))

	bytes_pointer += 4

	for index in (dictionary.keys()):

		token_dictionary[index] = bytes_pointer

		length = len(dictionary[index])
		file.write((length).to_bytes(4,byteorder='big'))

		bytes_pointer += 4
		
		previous = 0
		for idx in dictionary[index]:
			file.write((idx-previous).to_bytes(4,byteorder='big'))
			previous = idx
			bytes_pointer += 4

	file.close()

	os.system("python -m snappy -c "+index_file_name+"_temp.idx "+index_file_name+".idx")
	os.remove(index_file_name+"_temp.idx")

	file = open(index_file_name+'.dict','w')
	json.dump(token_dictionary,file)
	file.close()


def return_stopset(stoplist_path):
	file = open(stoplist_path,"r")
	Lines = file.read()
	lines = re.split('\n',Lines)

	stop_set = set()
	for line in lines:
		stop_set.add(line)

	return stop_set

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

	#print(term+"___ "+output)
	return output

def return_xml(xml_filename):
	file = open(xml_filename,"r")
	Lines = file.read()
	lines = re.split('\n',Lines)
	return lines



START_TIME = time.time()

num_arguments = len(sys.argv)
collection_path = sys.argv[1]				# 0th index argument is .py filename
index_file_name = sys.argv[2]
stopwords_set = return_stopset(sys.argv[3]) if num_arguments>=4 else []
compression = int(sys.argv[4])
xml_tags = return_xml(sys.argv[5]) if num_arguments>=6 else ["DOCNO","HEAD","TEXT"]

porter = PorterStemmer()

document_index = 1
document_hash = {}
dictionary = {}

collection = os.listdir(collection_path)


for file_name in collection:

	file = open(collection_path+file_name,"r")
	file_string = file.read()

	documents = re.split("</DOC>",file_string)

	for document in documents:

		if document=="":
			continue

		document = document + "</DOC>"
		document = BeautifulSoup(document,'xml')

		docno = document.find_all("DOCNO",limit=1)
		if(len(docno)==0):
			continue

		document_hash[document_index] = docno[0].get_text()
		document_terms_list = []

		tag_blocks = document.find_all(xml_tags[1:])

		for tag_block in tag_blocks:
			tag_string = tag_block.get_text()
			tag_term_list = re.split(' |,|\\.|\n|:|;|"|`|\'|(|)|{|}|[|]',tag_string)
			document_terms_list = document_terms_list + tag_term_list

		for term in document_terms_list:

			if(term not in stopwords_set and term!=""):

				term = stem_token(term,porter)

				if(dictionary.get(term)==None):
					dictionary[term] = [document_index]

				elif(dictionary[term][-1]!=document_index):
					dictionary[term].append(document_index)

		document_index += 1

	file.close()

print("Time for reading files: "+str(time.time()-START_TIME))

if(compression==0):
	compression0(dictionary,index_file_name,document_hash)
elif(compression==1):
	compression1(dictionary,index_file_name,document_hash)
elif(compression==2):
	compression2(dictionary,index_file_name,document_hash)
elif(compression==3):
	compression3(dictionary,index_file_name,document_hash)

print("Total number of tokens: "+str(len(dictionary.keys())))
print("Total number of documents: "+str(document_index-1))
print("Total time taken: "+str(time.time()-START_TIME))

#print_keys = list(dictionary.keys())
#for index in [107,1007,1792,728,693]:
#	print(dictionary[print_keys[index]])
#	print('\n')

