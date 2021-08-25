import sys
import os

def decode0(file):

	dictionary_keys_len = int.from_bytes(file.read(4),byteorder='big')
	stopping_dic = {}

	for key in range(dictionary_keys_len):

		list_len = int.from_bytes(file.read(4),byteorder='big')
		stopping_dic[key] = []

		for idx in range(list_len):
			document_id = int.from_bytes(file.read(4),byteorder='big')
			stopping_dic[key].append(document_id)

	for index in range(5):
		print(stopping_dic[index])
		print('\n')

	file.close()

def decode1_next(file):

	byte_int = int.from_bytes(file.read(1),byteorder='big')
	number = byte_int & 127

	while(byte_int>=128):
		byte_int = int.from_bytes(file.read(1),byteorder='big')
		number = (number<<7) + (byte_int & 127)

	return number

def decode1(file):

	dictionary_keys_len = decode1_next(file)
	stopping_dic = {}
	
	for key in range(dictionary_keys_len):

		list_len = decode1_next(file)
		stopping_dic[key] = []

		previous = 0
		for idx in range(list_len):
			document_id = decode1_next(file) + previous
			stopping_dic[key].append(document_id)
			previous = document_id
	
	#for index in range(5):
	#	print(stopping_dic[index])
	#	print('\n')

	#print(file.read(1))
	#print(file.read(1))
	#print(file.read(1))
	#print(file.read(1))

	file.close()

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


def decode2(file):

	dictionary_keys_len,new_first = decode2_next(file,"")

	stopping_dic = {}

	for key in range(dictionary_keys_len):
		list_len,new_first = decode2_next(file,new_first)
		stopping_dic[key] = []

		previous = 0
		for idx in range(list_len):
			document_id,new_first = decode2_next(file,new_first) 
			document_id += previous
			stopping_dic[key].append(document_id)
			previous = document_id

	for index in range(5):
		print(stopping_dic[index])
		print('\n')

	print(file.read(1))
	print(file.read(1))
	print(file.read(1))
	print(file.read(1))

def decode3(file):
	dictionary_keys_len = int.from_bytes(file.read(4),byteorder='big')
	stopping_dic = {}

	for key in range(dictionary_keys_len):

		list_len = int.from_bytes(file.read(4),byteorder='big')
		stopping_dic[key] = []

		previous = 0
		for idx in range(list_len):
			document_id = int.from_bytes(file.read(4),byteorder='big') + previous
			stopping_dic[key].append(document_id)
			previous = document_id

	for index in range(5):
		print(stopping_dic[index])
		print('\n')

	#print(file.read(1))
	#print(file.read(1))
	#print(file.read(1))
	#print(file.read(1))

	file.close()


num_arguments = len(sys.argv)

queryfile_name = sys.argv[1]
resultfile_name = sys.argv[2]
indexfile_name = sys.argv[3]
dictfile_name = sys.argv[4]

file = open(indexfile_name,"rb")
comp_type = int.from_bytes(file.read(1),byteorder='big')
print(comp_type)

if(comp_type==0):
	decode0(file)
elif(comp_type==1):
	decode1(file)
elif(comp_type==2):
	decode2(file)
else:
	file.close()
	os.system("python -m snappy -d "+indexfile_name+" "+indexfile_name+"_temp")

	file = open(indexfile_name+"_temp","rb")
	file.read(1)

	decode3(file)
	os.remove(indexfile_name+"_temp")



	
