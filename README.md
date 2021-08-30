# Boolean Retrieval System
This program is an implementation of the boolean retrieval system in python. It allows user to test 4 types of compression of the index_list, remove stopwords, stem the terms and query both single and multi-keywords retrieval, over a collection of xml documents. You can find complete problem statement here in `AssignmentDescription.pdf` and my report on the results in `2019CS50661.pdf` here
 

## Libraries Needed
* BeautifulSoup4, install via `pip install beautifulsoup4`
* snappy library, install via `pip install python-snappy`
* Python 3.7 is recommended

## Instructions
1) `invidx.sh [coll-path] [indexfile] [stopwordfile] {0|1|2|3|4} [xml-tags-info]` will create 2 files named `indexfile.idx` which contains compressed version of encoded posting lists in binary and `indexfile.dict` which contains dictionary saved in json.
* `coll_path` specifies the directory containing sample xml documents.
* `stopwordfile` contains list of stopwords seprated by newline that need not be tokenised
* 0 denotes no compression and 1,2,3,4 denote various compressions as explained in `2019CS50661.pdf` in the repo
* `xml-tags-info` deonte only those xml tags seperated by newline that need to be parsed  
  
2) `boolsearch.sh [queryfile] [resultfile] [indexfile] [dictfile]` will be used to get the results of queries separated by newline in `queryfile` to `resultfile`
* `indexfile` will be the `indexfile.idx` saved using the previous commands to get the posting lists
* `dictfile` will be the `indexfile.dict` saved before to get the dictionary 
* For multi-search retrievals your queries should be seperated by whitespace in the same line



