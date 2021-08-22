import sys
import os
from bs4 import BeautifulSoup
import re

def return_stoplist(stoplist_path):
	file = open(stoplist_path,"r")
	lines = file.readlines()
	return lines


num_arguments = len(sys.argv)
collection_path = sys.argv[1]				# 0th index argument is .py filename

xml_tags = ["HEAD","TEXT"]
stopwords_list = return_stoplist(sys.argv[3]) if num_arguments>=4 else []

document_index = 0
document_hash = {}
dictionary = {}


collection = os.listdir(collection_path)

for file_name in collection:
	
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
				tag_term_list = re.split(' ',tag_string)

				document_terms_list = document_terms_list + tag_term_list

		for term in document_terms_list:

			if(term not in stopwords_list):

				if(term not in dictionary):
					dictionary[term] = [document_index]

				elif(dictionary[term][-1]!=document_index):
					dictionary[term].append(document_index)

		document_index += 1

	file.close()

