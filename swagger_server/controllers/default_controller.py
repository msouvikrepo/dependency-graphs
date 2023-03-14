import connexion
import six
from swagger_server import util
import os
import glob
import sys
from cube.api import Cube
import stanfordnlp
import re
import subprocess
import requests
import json
import spacy
from textacy.export import doc_to_conll
from collections import OrderedDict
from spacy import displacy

#Initializing model engines
spacy_nlp = spacy.load("de_core_news_md")
cube=Cube(verbose=True)
cube.load("de")
stanford_nlp = stanfordnlp.Pipeline(lang = 'de')

#SpaCy
def spacy_de(parse_text):
    print("Parsing with SpaCy")
    doc = spacy_nlp(parse_text)
    conllu_string = doc_to_conll(doc)

    output = ""
    conllu_string_list = conllu_string.split("\n")
    for sentence in conllu_string_list:
        if not(sentence.startswith('#')):
            output += sentence + "\n"


    return output.strip()

#DisplaCy_from_SpaCy
def displacy_render(sentence):
    doc = spacy_nlp(sentence)
    svg = displacy.render(doc, style="dep", jupyter=False)
    return svg

#ParZu
def ParZu(parse_text):

    print("Parsing with ParZu")
    data = {"text" : parse_text}
    headers = {'Content-Type': 'application/json'}
    req = requests.post('http://localhost:5003/parse/', data = json.dumps(data), headers = headers)
    output = req.text
    return output.strip()

#Stanford
def stanford(parse_text):
    print("Parsing with Stanford")
    
    #Text to parse
    doc = stanford_nlp(parse_text)

    #CoNLLoutput
    output = doc.conll_file.conll_as_string().strip()
    return output

#Adobe NPCube
def nlpcube(parse_text):
    print("Parsing with NLPCube")
    
    sentences=cube(parse_text)

    #CoNLL format output
    output = ""
    for sentence in sentences:
        for entry in sentence:
            output += str(entry.index)+"\t"+entry.word+"\t"+entry.lemma+"\t"+entry.upos+"\t"+entry.xpos+"\t"+entry.attrs+"\t"+str(entry.head)+"\t"+str(entry.label)+ "\t" + entry.deps + "\t" + entry.space_after+"\n"
        output += "\n"
    return output.strip()

#IMS HotCoref DE
def ims_hotcoref_de(parse_text):
    """ #Create input.txt
    print("Parsing with IMS HotCoref DE")
    file = open("/usr/src/app/conversion2conll12/input.txt","w+")
    file.write(parse_text)
    file.close()

    #Run shell script
    cwd = os.getcwd()
    os.chdir("/usr/src/app/conversion2conll12/")
    os.system("sh /usr/src/app/conversion2conll12/PreprocessingAndCoreference.sh /usr/src/app/conversion2conll12/input.txt /usr/src/app/conversion2conll12/output.txt")
    os.chdir(cwd)

    #Send back contents of file
    file = open("/usr/src/app/conversion2conll12/output.txt", "r")
    output = file.read()
    return output.strip() """

#CorZu
def CorZu(parse_text):

    print("Parsing with CorZu")
    corZu_input = """ {"text": " """ + parse_text + """ "} """
    #Create input file
    file = open("/usr/src/app/swagger_server/controllers/CorZu_v2.0/input.json","w+")
    file.write(corZu_input)
    file.close()
    

    #Run CorZu over text
    cwd = os.getcwd()
    os.chdir("/usr/src/app/swagger_server/controllers/CorZu_v2.0")
    os.system("./corzu.sh input.json")  
    os.chdir(cwd)
    

    #Capture contents of output file
    file = open("/usr/src/app/swagger_server/controllers/CorZu_v2.0/input.json.coref", "r")
    output = file.read()
    file.close()

    #Delete all operational files
    # get a recursive list of file paths that matches pattern input.*
    fileList = glob.glob('/usr/src/app/swagger_server/controllers/CorZu_v2.0/input.*', recursive=True)
 
    # Iterate over the list of filepaths & remove each file.
    for filePath in fileList:
        try:
            os.remove(filePath)
        except OSError:
            print("Error while deleting file")

    return output.strip()


#Check and remove anomalities in conll-u before displacy parsing
def check_tables_anomaly_in_conllu(conllu):
    #Multiple Table anomaly
    conllu = conllu.strip()
    conllu_output_string = ""
    conll_u_lines = [line for line in conllu.split("\n")]

    if('' in conll_u_lines):
        for line in conll_u_lines:
            if(line!=''):
                conllu_output_string += line + "\n"
            else:
                break
        
        return conllu_output_string.strip()
    else:
        return conllu

def check_index_anomaly_in_conllu(conllu):
    conllu = conllu.strip()
    conllu_output_string = ""
    conll_u_lines = [line for line in conllu.split("\n")]
    #Shared index anomaly
    for line in conll_u_lines:
        if(line.split("\t")[0].isnumeric()):
            conllu_output_string += line + "\n"
    return conllu_output_string.strip()


def set_arrow_direction(word_line):
    """
    Sets the orientation of the arrow that notes the directon of the dependency
    between the two units.

    """
    if int(word_line["id"]) > int(word_line["head"]):
        word_line["dir"] = "right"
    elif int(word_line["id"]) < int(word_line["head"]):
        word_line["dir"] = "left"
    return word_line

def convert2zero_based_numbering(word_line_field):
    "CONLL-U numbering starts at 1, displaCy's at 0..."
    word_line_field = str(int(word_line_field) - 1)
    return word_line_field

def get_start_and_end(word_line):
    """
    Displacy's 'start' value is the lowest value amongst the ID and HEAD values,
    and the 'end' is always the highest. 'Start' and 'End' have nothing to do
    with dependency which is indicated by the arrow direction, not the line
    direction.
    """
    word_line["start"] = min([int(word_line["id"]), int(word_line["head"])])
    word_line["end"] = max([int(word_line["id"]), int(word_line["head"])])
    return word_line
                           
#Source https://github.com/explosion/spaCy/issues/1215
def conll_u_string2displacy_json(conll_u_sent_string): 
    """
    Converts a single CONLL-U formatted sentence to the displaCy json format.
    CONLL-U specification: http://universaldependencies.org/format.html
    """
    
    
    conll_u_lines = [line for line in conll_u_sent_string.split("\n") \
                     if line[0].isnumeric()]

    displacy_json = {"arcs": [], "words": []}
    for tabbed_line in conll_u_lines:
        word_line = OrderedDict()
        word_line["id"], word_line["form"], word_line["lemma"], \
        word_line["upostag"], word_line["xpostag"], word_line["feats"], \
        word_line["head"], word_line["deprel"], word_line["deps"], \
        word_line["misc"] = tabbed_line.split("\t")

        word_line["id"] = convert2zero_based_numbering(word_line["id"])
        if word_line["head"] != "_":
            word_line["head"] = convert2zero_based_numbering(word_line["head"])       
        
        if word_line["deprel"] != "root" and word_line["head"] != "_":
            word_line = get_start_and_end(word_line)
            word_line = set_arrow_direction(word_line)
            displacy_json["arcs"].append({"dir": word_line["dir"],
                                          "end": word_line["end"],
                                          "label": word_line["deprel"],
                                          "start": word_line["start"]})
            
        displacy_json["words"].append({"tag": word_line["upostag"],
                                       "text": word_line["form"]})

    displacy_json = (json.dumps(displacy_json, indent=4))
    return displacy_json



#Render parse tree from CoNLL-U
def generate_dependency_from_conllu(conllu):

    #Check tables
    conllu = check_tables_anomaly_in_conllu(conllu)
    #Check shared indexes
    conllu = check_index_anomaly_in_conllu(conllu)
    
    displacy_dict = json.loads(conll_u_string2displacy_json(conllu))
    parse_tree = displacy.render(displacy_dict, style="dep", manual=True)

    return parse_tree


#Generates CoNLL-U
def generate_conllu_from_sentence(sentence, tool):
    output = ""
    if(tool == 'spacy'):
        output = spacy_de(sentence)
    elif(tool == 'parzu'):
        output = ParZu(sentence)
    elif(tool == 'stanford'):
        output = stanford(sentence)
    elif(tool == 'nlpcube'):
        output = nlpcube(sentence)
    elif(tool == 'ims'):
        output = ims_hotcoref_de(sentence)
    elif(tool == 'corzu'):
        output = CorZu(sentence)
    else:
        output = "Invalid Tool"

    return output

#Generates parse tree from sentence
def generate_dependency_from_sentence(sentence, tool):
    if(tool == "stanford"):
        conllu = stanford(sentence)
        parse_tree = generate_dependency_from_conllu(conllu)
    elif(tool == "parzu"):
        conllu = ParZu(sentence)
        parse_tree = generate_dependency_from_conllu(conllu)
    elif(tool == "nlpcube"):
        conllu = nlpcube(sentence)
        parse_tree = generate_dependency_from_conllu(conllu)
    elif(tool == "spacy"):
        parse_tree = displacy_render(sentence)
    else:
        parse_tree = "Invalid Tool"

    return parse_tree


def get_conllu_to_dependency(conllu):  # noqa: E501
    """Converts CoNLL-U to Dependency Graph

    By passing in the CoNLL-U string of a dependency parser, you can generate the Dependency parse Tree diagram  # noqa: E501

    :param conllu: pass a CoNLL-U to generate Dependency Parse Tree
    :type conllu: str

    :rtype: str
    """
    print(conllu)
    parse_tree = generate_dependency_from_conllu(conllu)
    return parse_tree


def get_sentence_to_dependency(sentence, tool):  # noqa: E501
    """Converts sentence to Dependency Graph

    By passing in the sentence, you can generate the Dependency parse Tree diagram  # noqa: E501

    :param sentence: pass a sentence to generate Dependency Parse Tree
    :type sentence: str
    :param tool: pass a tool generate Dependency Parse Tree
    :type tool: str

    :rtype: str
    """
    parse_tree = generate_dependency_from_sentence(sentence, tool)
    return parse_tree


def get_text_to_conllu(text, tool):  # noqa: E501
    """Converts plain text to CoNLL-U

    By passing in the text you can generate a CoNLL-U representation of the sentence  # noqa: E501

    :param text: pass a sentence to generate CoNLL-U
    :type text: str
    :param tool: pass a tool to use
    :type tool: str

    :rtype: str
    """
    conllu = generate_conllu_from_sentence(text, tool)
    return conllu


def post_conllu_to_dependency(body=None):  # noqa: E501
    """Converts CoNLL-U to Dependency Parse Tree

    pass a CoNLL-U to generate Dependency Parse Tree # noqa: E501

    :param body: CoNLL-U to Parse
    :type body: dict | bytes

    :rtype: str
    """
    if connexion.request.is_json:
        body = str.from_dict(connexion.request.get_json())  # noqa: E501
    print(body.decode())
    parse_tree = generate_dependency_from_conllu(body.decode())
    return parse_tree


def post_sentence_to_dependency(sentence=None, tool=None):  # noqa: E501
    """Converts sentence to Dependency Parse Tree

    pass a sentence to generate Dependency Parse Tree # noqa: E501

    :param sentence: 
    :type sentence: str
    :param tool: 
    :type tool: str

    :rtype: str
    """
    parse_tree = generate_dependency_from_sentence(sentence, tool)
    return parse_tree


def post_text_to_conllu(text=None, tool=None):  # noqa: E501
    """Converts plain text to CoNLL-U

    pass a sentence to generate CoNLL-U # noqa: E501

    :param text: 
    :type text: str
    :param tool: 
    :type tool: str

    :rtype: None
    """
    print("Text :", text)
    print("Tool :", tool)
    conllu = generate_conllu_from_sentence(text, tool)
    return conllu