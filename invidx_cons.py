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

def encode4(previous_last,number,file):

	paramk = len(bin(number)[2:])

	k_str = bin(paramk-1)[2:]

	while(len(k_str)<5):
		k_str = "0"+k_str

	compressed_bin_str = previous_last + k_str + bin(number)[3:] # Last k-1 bits

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

	previous_last = ""
	for index in (dictionary.keys()):

		token_dictionary[index] = bytes_pointer

		length = len(dictionary[index])
		previous_last,temp_pointer = encode2(previous_last,length,file)
		bytes_pointer += temp_pointer

		if previous_last!="":
			bits_left = 8 - len(previous_last)
			final_bin = int(previous_last,2)
			final_bin = final_bin<<bits_left

			file.write(final_bin.to_bytes(1,byteorder='big'))

			bytes_pointer += 1
			previous_last = ""

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


def compression4(dictionary,index_file_name,document_hash):
	token_dictionary = {}
	bytes_pointer = 0

	file = open(index_file_name+'.idx','wb')
	compression_type = 4
	file.write(compression_type.to_bytes(1,byteorder='big'))

	bytes_pointer += 1

	bytes_pointer += map_documents(file,document_hash)

	previous_last,temp_pointer = encode4("",len(dictionary.keys()),file)
	bytes_pointer += temp_pointer

	previous_last = ""

	for index in (dictionary.keys()):

		token_dictionary[index] = bytes_pointer

		length = len(dictionary[index])
		previous_last,temp_pointer = encode4(previous_last,length,file)
		bytes_pointer += temp_pointer

		if previous_last!="":

			bits_left = 8 - len(previous_last)
			final_bin = int(previous_last,2)
			final_bin = final_bin<<bits_left

			file.write(final_bin.to_bytes(1,byteorder='big'))

			bytes_pointer += 1
			previous_last = ""

		previous = 0 							# gap encoding
		for idx in dictionary[index]:

			previous_last,temp_pointer = encode4(previous_last,idx-previous,file)
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

	return output

def return_xml(xml_filename):
	file = open(xml_filename,"r")
	Lines = file.read()
	lines = re.split('\n',Lines)
	return lines

def extend_strbyte(small_str):
	x = 8 - len(small_str)

	new_str = ""
	for index in range(x):
		new_str += "0"

	new_str += small_str
	return new_str

def ENCODE(new_file,value,str_last,comp_type):

	if(comp_type==0 or comp_type==3):
		new_file.write(value.to_bytes(4,byteorder='big'))
		return 4,""

	if(comp_type==1):
		bytes_used_here = encode1(value,new_file)
		return bytes_used_here,""

	if(comp_type==2):
		str_last,bytes_used_here = encode2(str_last,value,new_file)
		return bytes_used_here,str_last

	str_last,bytes_used_here = encode4(str_last,value,new_file)
	return bytes_used_here,str_last

def merge_dictionaries(prev_filename,previous_dictionary,curr_dictionary,new_filename,comp_type):

	new_dictionary = {}
	new_bytes_pointer = 0
	new_bytes_used = 0

	new_file = open(new_filename,"wb")

	if prev_filename!=None:
		prev_file = open(prev_filename,"rb")

	for key in previous_dictionary.keys():

		pointer_start = previous_dictionary[key][0]
		bytes_used = previous_dictionary[key][1]
		bits_used = previous_dictionary[key][2]
		last_doc = previous_dictionary[key][3]
		length_list = previous_dictionary[key][4]

		prev_file.seek(pointer_start,0)

		if (comp_type==2 or comp_type==4) and bits_used!=0:

			if bytes_used>1:
				prev_posting_list = prev_file.read(bytes_used-1)
				new_file.write(prev_posting_list)

			str_last = extend_strbyte(bin(int.from_bytes(prev_file.read(1),byteorder='big'))[2:])
			str_last = str_last[0:bits_used]

			new_bytes_used += (bytes_used - 1)
		else:
			prev_posting_list = prev_file.read(bytes_used)
			new_file.write(prev_posting_list)

			str_last = ""
			new_bytes_used += bytes_used

		if(curr_dictionary.get(key)):

			for value in curr_dictionary[key]:

				temp_bytes,str_last = ENCODE(new_file,(value-last_doc),str_last,comp_type)
				new_bytes_used += temp_bytes
				last_doc = value if comp_type!=0 else 0
				length_list += 1
		
		bits_used = len(str_last)
		if str_last!="":
			bits_left = 8 - bits_used

			final_bin = int(str_last,2)
			final_bin = final_bin<<bits_left

			new_file.write(final_bin.to_bytes(1,byteorder='big'))

			new_bytes_used += 1
			str_last = ""

		new_dictionary[key] = [new_bytes_pointer,new_bytes_used,bits_used,last_doc,length_list]
		new_bytes_pointer += new_bytes_used
		new_bytes_used = 0

	for key in curr_dictionary.keys():

		if(previous_dictionary.get(key)==None):

			new_bytes_used = 0
			str_last = ""
			length_list = 0
			last_doc = 0

			for value in curr_dictionary[key]:

				temp_bytes,str_last = ENCODE(new_file,(value-last_doc),str_last,comp_type)
				new_bytes_used += temp_bytes
				last_doc = value if comp_type!=0 else 0
				length_list += 1

			bits_used = len(str_last)

			if(bits_used!=0):

				bits_left = 8 - len(str_last)
				final_bin = int(str_last,2)
				final_bin = final_bin<<bits_left

				new_file.write(final_bin.to_bytes(1,byteorder='big'))

				new_bytes_used += 1
				str_last = ""

			new_dictionary[key] = [new_bytes_pointer,new_bytes_used,bits_used,last_doc,length_list]
			new_bytes_pointer += new_bytes_used
			new_bytes_used = 0

	previous_dictionary.clear()
	curr_dictionary.clear()
	new_file.close()

	del previous_dictionary
	del curr_dictionary

	if(prev_filename!=None):
		prev_file.close()
		os.remove(prev_filename)

	return new_dictionary

def final_disk_write(previous_dictionary,index_file_name,counter,document_hash,compression):
	
	token_dictionary = {}
	bytes_pointer = 0
	str_last = ""

	if compression==3:
		final_file = open(index_file_name+'_temp.idx',"wb")
	else:
		final_file = open(index_file_name+'.idx',"wb")

	final_file.write(compression.to_bytes(1,byteorder='big'))
	bytes_pointer += 1

	bytes_pointer += map_documents(final_file,document_hash)

	temp_bytes,str_last = ENCODE(final_file,len(previous_dictionary.keys()),str_last,compression)
	bytes_pointer += temp_bytes

	prev_file = open(index_file_name+str(counter),"rb")
	str_last = ""

	for key in previous_dictionary.keys():

		token_dictionary[key] = bytes_pointer
		list_length = previous_dictionary[key][4]

		temp_bytes,str_last = ENCODE(final_file,list_length,str_last,compression)
		bytes_pointer += temp_bytes

		if str_last!="":
			bits_used = len(str_last)
			bits_left = 8 - bits_used

			final_bin = int(str_last,2)
			final_bin = final_bin<<bits_left

			final_file.write(final_bin.to_bytes(1,byteorder='big'))

			bytes_pointer += 1
			str_last = ""

		prev_bytes_pointer = previous_dictionary[key][0]
		prev_bytes_used = previous_dictionary[key][1]
		prev_file.seek(prev_bytes_pointer,0)

		prev_byte_str = prev_file.read(prev_bytes_used)
		final_file.write(prev_byte_str)

		bytes_pointer += prev_bytes_used

	final_file.close()
	prev_file.close()

	os.remove(index_file_name+str(counter))

	if(compression==3):
		os.system("python -m snappy -c "+index_file_name+"_temp.idx "+index_file_name+".idx")
		os.remove(index_file_name+"_temp.idx")

	file = open(index_file_name+'.dict','w')
	json.dump(token_dictionary,file)
	file.close()


START_TIME = time.time()

num_arguments = len(sys.argv)
collection_path = sys.argv[1]				# 0th index argument is .py filename
index_file_name = sys.argv[2]
stopwords_set = return_stopset(sys.argv[3])
compression = int(sys.argv[4])
xml_tags = return_xml(sys.argv[5])
once_memory_overloaded = False

if(compression==5):
	print("not implemented")
	sys.exit()

porter = PorterStemmer()

document_index = 1
document_hash = {}
dictionary = {}

collection = os.listdir(collection_path)

previous_dictionary = {}
previous_filename = None
counter = 0

for file_name in collection:

	file = open(os.path.join(collection_path,file_name),"r")
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
			tag_term_list = re.split(' |,|\\.|\n|:|;|"|\'|`|{{|}}|[|]|\)|\(',tag_string)
			document_terms_list = document_terms_list + tag_term_list

		first = True
		for term in document_terms_list:

			if(term not in stopwords_set and term!=""):

				term = stem_token(term,porter)

				if(dictionary.get(term)==None):
					dictionary[term] = [document_index]

				elif(dictionary[term][-1]!=document_index):
					dictionary[term].append(document_index)

				memory_overload = first and (document_index%100000==0)
				if(memory_overload):

					#print('External merging initiated')
					once_memory_overloaded = True
					previous_dictionary = merge_dictionaries(previous_filename,previous_dictionary,dictionary,index_file_name+str((counter+1)%2),compression)
					counter = (counter + 1)%2
					previous_filename = index_file_name + str(counter)
					#print('External merging finished')
					first = False

					dictionary = {}

		document_index += 1

	file.close()

#print("Time for reading files: "+str(time.time()-START_TIME))

if(once_memory_overloaded):
	#print('External merging initiated')
	previous_dictionary = merge_dictionaries(previous_filename,previous_dictionary,dictionary,index_file_name+str((counter+1)%2),compression)
	#print('External merging finished')
	counter = (counter+1)%2
	final_disk_write(previous_dictionary,index_file_name,counter,document_hash,compression)
elif(compression==0):
	compression0(dictionary,index_file_name,document_hash)
elif(compression==1):
	compression1(dictionary,index_file_name,document_hash)
elif(compression==2):
	compression2(dictionary,index_file_name,document_hash)
elif(compression==3):
	compression3(dictionary,index_file_name,document_hash)
elif(compression==4):
	compression4(dictionary,index_file_name,document_hash)
else:
	print("not implemented")


#print("Total number of tokens: "+str(len(dictionary.keys())))
#print("Total number of documents: "+str(document_index-1))
#print("Total time taken: "+str(time.time()-START_TIME))