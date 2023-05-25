from xml.dom import minidom
from builder import builder
import sys
import os

# COMMON TAGS GENERATOR
def gen_process_tag(root: minidom.Document, structure_name: str) -> minidom.Element:
    processTag = root.createElement("process")
    processTag.setAttribute("name", "BPELProcess1")
    processTag.setAttribute("targetNamespace", "http://xmlns.oracle.com/bpel_process/{structure_name}_bpel/BPELProcess1".format(structure_name=structure_name))
    processTag.setAttribute("xmlns", "http://docs.oasis-open.org/wsbpel/2.0/process/executable")
    processTag.setAttribute("xmlns:client", "http://xmlns.oracle.com/bpel_process/{structure_name}_bpel/BPELProcess1".format(structure_name=structure_name))
    processTag.setAttribute("xmlns:ora", "http://schemas.oracle.com/xpath/extension")
    processTag.setAttribute("xmlns:ui", "http://xmlns.oracle.com/soa/designer")
    processTag.setAttribute("xmlns:bpelx", "http://schemas.oracle.com/bpel/extension")
    processTag.setAttribute("xmlns:bpel", "http://docs.oasis-open.org/wsbpel/2.0/process/executable")
    return processTag

def gen_import_tag(root: minidom.Document, structure_name: str) -> minidom.Element:
    importTag = root.createElement("import")
    importTag.setAttribute("ui:processWSDL", "true")
    importTag.setAttribute("namespace", "http://xmlns.oracle.com/bpel_process/{structure_name}_bpel/BPELProcess1".format(structure_name=structure_name))
    importTag.setAttribute("location", "../WSDLs/BPELProcess1.wsdl")
    importTag.setAttribute("importType", "http://schemas.xmlsoap.org/wsdl/")
    return importTag

def gen_partnerLinks_tag(root: minidom.Document, structure_name: str) -> minidom.Element:
    partnerLinksTag = root.createElement("partnerLinks")
    partnerLinkTag = root.createElement("partnerLink")
    partnerLinkTag.setAttribute("name", "bpelprocess1_client")
    partnerLinkTag.setAttribute("partnerLinkType", "client:BPELProcess1")
    partnerLinkTag.setAttribute("myRole", "BPELProcess1Provider")
    partnerLinksTag.appendChild(partnerLinkTag)
    return partnerLinksTag

def gen_variables_tag(root: minidom.Document, structure_name: str) -> minidom.Element:
    variablesTag = root.createElement("variables")
    input_variableTag = root.createElement("variable")
    input_variableTag.setAttribute("name", "inputVariable")
    input_variableTag.setAttribute("messageType", "client:BPELProcess1RequestMessage")
    output_variableTag = root.createElement("variable")
    output_variableTag.setAttribute("name", "outputVariable")
    output_variableTag.setAttribute("messageType", "client:BPELProcess1ResponseMessage")
    variablesTag.appendChild(input_variableTag)
    variablesTag.appendChild(output_variableTag)
    return variablesTag

def gen_receive_tag(root: minidom.Document, structure_name: str) -> minidom.Element:
    receiveTag = root.createElement("receive")
    receiveTag.setAttribute("name", "receiveInput")
    receiveTag.setAttribute("partnerLink", "bpelprocess1_client")
    receiveTag.setAttribute("portType", "client:BPELProcess1")
    receiveTag.setAttribute("operation", "process")
    receiveTag.setAttribute("variable", "inputVariable")
    receiveTag.setAttribute("createInstance", "yes")
    return receiveTag

def gen_reply_tag(root: minidom.Document, structure_name: str) -> minidom.Element:
    replyTag = root.createElement("reply")
    replyTag.setAttribute("name", "replyOutput")
    replyTag.setAttribute("partnerLink", "bpelprocess1_client")
    replyTag.setAttribute("portType", "client:BPELProcess1")
    replyTag.setAttribute("operation", "process")
    replyTag.setAttribute("variable", "outputVariable")
    return replyTag

# MAIN GENERATOR
def main_gen(structure_name: str, file_path: str) -> str:
    if structure_name not in ['flow', 'if', 'pick', 'repeatUntil', 'repeatWhile', 'sequence', 'while']:
        raise Exception('structure name is not a well-structured')
    
    root = minidom.Document()

    # init process tag and set attributes
    processTag = gen_process_tag(root, structure_name)
    root.appendChild(processTag)

    # init import tag and set attributes
    importTag = gen_import_tag(root, structure_name)
    processTag.appendChild(importTag)

    # init partnerLinks tag and set attributes
    partnerLinksTag = gen_partnerLinks_tag(root, structure_name)
    processTag.appendChild(partnerLinksTag)

    # init variables tag and set attributes
    variablesTag = gen_variables_tag(root, structure_name)
    processTag.appendChild(variablesTag)

    # init sequence tag
    sequenceTag = root.createElement("sequence")
    sequenceTag.setAttribute("name", "main")
    builder(file_path, root, sequenceTag)
    
    ## append to process tag
    processTag.appendChild(sequenceTag)

    ## write to result file
    if not os.path.exists("./result"):
        os.mkdir("./result")
    filename = file_path.split("/")[-1]
    filename = filename.split(".")[0]
    resultFile = "./result/" + filename + ".bpel"
    f = open(resultFile, "w", encoding="utf-8")
    f.write(processTag.toprettyxml(indent="\t"))
    f.close()

    return resultFile

if __name__ == '__main__':
    filepath = sys.argv[1]
    output_file = main_gen("sequence", filepath)
    print("Output file name", output_file)