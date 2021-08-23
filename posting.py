import sys
import os
from bs4 import BeautifulSoup
import re

def compression0(dictionary,index_file_name):

	file = open(index_file_name+'.idx','wb')
	compression_type = 0
	file.write(compression_type.to_bytes(1,byteorder='big'))
	file.write(len(dictionary.keys()).to_bytes(4,byteorder='big'))

	for index in (dictionary.keys()):
		length = len(dictionary[index])
		file.write((length).to_bytes(4,byteorder='big'))
		
		for id in dictionary[index]:
			file.write(id.to_bytes(4,byteorder='big'))
	file.close()

def encode1(number,file):
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

	while(len(stack)>0):
		file.write(stack.pop().to_bytes(1,byteorder='big'))


def compression1(dictionary,index_file_name):

	file = open(index_file_name+'.idx','wb')
	compression_type = 1
	file.write(compression_type.to_bytes(1,byteorder='big'))
	encode1(len(dictionary.keys()),file)

	for index in (dictionary.keys()):
		length = len(dictionary[index])
		encode1(length,file)

		previous = 0 							# gap encoding
		for id in dictionary[index]:
			encode1(id-previous,file)
			previous = id
	file.close()



def return_stoplist(stoplist_path):
	file = open(stoplist_path,"r")
	Lines = file.read()
	lines = re.split('\n',Lines)
	return lines


num_arguments = len(sys.argv)
collection_path = sys.argv[1]				# 0th index argument is .py filename


index_file_name = sys.argv[2]
stopwords_list = return_stoplist(sys.argv[3]) if num_arguments>=4 else []
compression = int(sys.argv[4])
xml_tags = ["HEAD","TEXT"]

document_index = 0
document_hash = {}
dictionary = {}


collection = os.listdir(collection_path)

for file_name in collection:

	if(file_name=="ap890520"):
		continue

	file = open(collection_path+file_name,"r")
	file_string = file.read()

	contents = BeautifulSoup(file_string,'xml')
	documents = contents.find_all("DOC")

	for document in documents:

		docno = document.find_all("DOCNO")
		if(len(docno)==0):
			continue

		document_hash[document_index] = docno[0].get_text()
		document_terms_list = []


		for tag in xml_tags:
			tag_blocks = document.find_all(tag)

			for tag_block in tag_blocks:
				tag_string = tag_block.get_text()
				tag_term_list = re.split(' |,|\\.|\n|:|;|"|\'',tag_string)

				document_terms_list = document_terms_list + tag_term_list

		for term in document_terms_list:

			if(term not in stopwords_list):

				if(term not in dictionary):
					dictionary[term] = [document_index]

				elif(dictionary[term][-1]!=document_index):
					dictionary[term].append(document_index)

		document_index += 1

	file.close()

if(compression==0):
	compression0(dictionary,index_file_name)
elif(compression==1):
	compression1(dictionary,index_file_name)
elif(compression==2):
	compression2(dictionary,index_file_name)
elif(compression==3):
	compression3(dictionary,index_file_name)
