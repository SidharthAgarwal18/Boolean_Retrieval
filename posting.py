import sys
import os
from bs4 import BeautifulSoup
import re

def return_stoplist(stoplist_path):
	file = open(stoplist_path,"r")
	lines = file.readlines()
	return lines

num_arguments = len(sys.argv)
collection_path = sys.argv[1]


xml_tags = ["HEAD","TEXT"]
stopwords_list = return_stoplist(sys.argv[3]) if num_arguments>=4 else []


tags_terms_list = []
document_index = 0
document_hash = {}
dictionary = {}


collection = os.listdir(collection_path)

for file_name in collection:

	file = open(collection_path+file_name,"r")
	file_string = file.read()
	contents = BeautifulSoup(file_string,'xml')

	document_names = contents.find_all("DOCNO")

	for tag in xml_tags:
		tags_terms_list.append(contents.find_all(tag))

	for index in range(len(document_names)):
		document_hash[document_index] = document_names[index].get_text()
		document_index += 1

		for tag in range(len(tags_terms_list)):
			terms_string = tags_terms_list[tag][index].get_text()
			terms_list = re.split(' ',terms_string)

			for term in terms_list:
				if(term not in stopwords_list):

					if(term not in dictionary):
						dictionary[term] = [document_index]

					elif(dictionary[term][-1]!=document_index):
						dictionary[term].append(document_index)
	file.close()
	tags_terms_list = []

