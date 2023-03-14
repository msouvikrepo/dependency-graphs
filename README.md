# Dependency Graph API

## Overview
Web services to perform three steps on german text, namely :
1. Generate CONLL-U from text
2. Generate Dependency parse tree from CONLL-U
3. Generate Dependency parse tree from a sentence

The main working script is swagger_server/controllers/default_controller.py

## Requirements
Tested for Ubuntu 18.04
```
apt-get update && apt-get -y install \
    python2.7 \
    python3-pip \
    python-pexpect \
    python-flask \
    docker
```

## Usage

### Create and activate virtualenv
```
pip3 install virtualenv
virtualenv venv
source venv/bin/activate
```

### Install required packages
```
pip3 install -r requirements.txt
python3 -m spacy download de_core_news_md
```

### Running the server

To run the server, please execute the following from the root directory:

Run [ParZu](https://github.com/rsennrich/ParZu)
```
docker run -p 5003:5003 rsennrich/parzu
```

Run swagger-server :

```
python3 -m swagger_server
```

Runs on port 8080

## API endpoints

GET requests:
1. Text to CoNLL-U: /text_to_conll   
    Parameters : text - The text to parse   
                 tool - The NLP tool to use    
    Available tools : spacy, nlpcube, stanford, parzu, corzu    
    Example request URL : http://localhost:8080/text_to_conll?text=Harald, du hast mich angurefen  das du deine karte verloren hast&tool=corzu   
     
2. CONLL-U to Dependency graph : /conll_to_dependency    
    Parameter : conllu - The CoNLL-U string with preserved tabs and newlines
    Example request URL : http://localhost:8080/conll_to_dependency?conllu=1	Harald	Harald	N	NE	Masc|_|Sg	4	vok	_	-    
2	,	,	$,	$,	_	0	root	_	-    
3	du	du	PRO	PPER	2|Sg|_|Nom	4	subj	_	(0)    
4	hast	haben	V	VAFIN	2|Sg|Pres|Ind	0	root	_	-    
5	mich	ich	PRO	PPER	1|Sg|_|Acc	4	obja	_	-    
6	angurefen	angurefen	V	VVFIN	_	0	root	_	-    
7	das	die	ART	ART	Def|Neut|_|Sg	0	root	_	-    
8	du	du	PRO	PPER	2|Sg|_|Nom	0	root	_	(0)    
9	deine	deine	ART	PPOSAT	_|_|_	0	root	_	(0)    
10	karte	karten	V	VVFIN	_|Sg|Pres|_	0	root	_	-    
11	verloren	verloren	ADV	ADJD	Pos|	12	adv	_	-    
12	hast	haben	V	VAFIN	2|Sg|Pres|Ind	0	root	_	-    

3. Sentence to Dependency Graph : /sentence_to_dependency    
    Parameters : sentence - Sentence to generate dependency graph from    
                 tool - NLP tool to use for dependency parsing    
    Available tools : spacy, nlpcube, stanford, parzu    
    Example request URL : http://localhost:8080/sentence_to_dependency?sentence=Das ist ein test&tool=stanford    

#### Known Issues
1. POST requests to same API endpoints not available
2. Tool for IMS HotCoref DE causes internal issues
