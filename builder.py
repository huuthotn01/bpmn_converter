from xml.dom import minidom
import utils

def read_bpmn_code(file_path: str) -> minidom.Element:
    document = minidom.parse(file=file_path)
    definitionsTag = document.getElementsByTagName("definitions")
    processTag = definitionsTag[0].getElementsByTagName("process")
    return processTag[1] 

def builder_main(structure: minidom.Element) -> str:
    mapIdToNext, mapIdToContent, startEvent = utils.map_id_to_next_element(structure)
    currEvent = startEvent # init current tag as startEvent
    ## JUST MOCK
    root = minidom.Document()
    sequenceTag = root.createElement("sequence")
    sequenceTag.setAttribute("name", "main")
    recursive_builder(sequenceTag, mapIdToContent[currEvent], root, mapIdToNext, mapIdToContent, list())
    return sequenceTag.toprettyxml(indent="\t")
    
def recursive_builder(parent_node: minidom.Element, current_node: minidom.Element, root: minidom.Document, mapIdToNext: dict(), mapIdToContent: dict(), visited: list()):
    generatedNode = None
    match current_node.tagName:
        case "endEvent":
            generatedNode = root.createElement("reply")
            generatedNode.setAttribute("name", current_node.getAttribute("name"))
            parent_node.appendChild(generatedNode)
            return
        case "startEvent":
            generatedNode = root.createElement("receive")
        case "task":
            generatedNode = root.createElement("invoke")
        case "intermediateCatchEvent":
            checkIfTimer = current_node.getElementsByTagName("timerEventDefinition")
            if len(checkIfTimer) > 0:
                generatedNode = root.createElement("wait")
            else: generatedNode = root.createElement("receive")
        case "intermediateThrowEvent":
            generatedNode = root.createElement("invoke")
        case "parallelGateway" | "eventBasedGateway":
            tagName = current_node.tagName
            if current_node.getAttribute("gatewayDirection") == "Diverging":
                if tagName == "parallelGateway":
                    generatedNode = root.createElement("flow")
                elif tagName == "eventBasedGateway":
                    generatedNode = root.createElement("pick")
                generatedNode.setAttribute("name", current_node.getAttribute("name"))
                parent_node.appendChild(generatedNode)
                for next in mapIdToNext[current_node.getAttribute("id")]:
                    if next in visited: continue
                    thisElement = mapIdToContent[next]
                    if tagName == "parallelGateway":
                        branchTag = root.createElement("sequence")
                        generatedNode.appendChild(branchTag)
                    elif tagName == "eventBasedGateway":
                        onMsgTag = root.createElement("onMessage")
                        branchTag = root.createElement("sequence")
                        onMsgTag.appendChild(branchTag)
                        generatedNode.appendChild(onMsgTag)
                    closeGate = recursive_builder(branchTag, thisElement, root, mapIdToNext, mapIdToContent, visited + [current_node.tagName])
                if closeGate.tagName == tagName and closeGate.getAttribute("gatewayDirection") == "Converging":
                    for next in mapIdToNext[closeGate.getAttribute("id")]:
                        if next in visited: continue
                        thisElement = mapIdToContent[next]
                        recursive_builder(parent_node, thisElement, root, mapIdToNext, mapIdToContent, visited + [closeGate.tagName])
                return
            for next in mapIdToNext[current_node.getAttribute("id")]:
                if next in visited: continue
                return current_node
            return
            
    generatedNode.setAttribute("name", current_node.getAttribute("name"))
    parent_node.appendChild(generatedNode)
    for next in mapIdToNext[current_node.getAttribute("id")]:
        if next in visited: continue
        thisElement = mapIdToContent[next]
        return recursive_builder(parent_node, thisElement, root, mapIdToNext, mapIdToContent, visited + [current_node.tagName])

def builder(file_path: str) -> str:
    trimmed_bpmn = read_bpmn_code(file_path)
    structure_name = builder_main(trimmed_bpmn)
    return structure_name

print(builder("bpmn_code/Pick.bpmn"))