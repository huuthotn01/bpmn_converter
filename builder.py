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
    
def recursive_builder(parent_node: minidom.Element, current_node: minidom.Element, root: minidom.Document,
                      mapIdToNext: dict(), mapIdToContent: dict(), visited: list(), inExclusive="", prevParent: minidom.Element = None):
    if current_node.getAttribute("id") in visited: return
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
                    closeGate = recursive_builder(branchTag, thisElement, root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")])
                if closeGate.tagName == tagName and closeGate.getAttribute("gatewayDirection") == "Converging":
                    for next in mapIdToNext[closeGate.getAttribute("id")]:
                        if next in visited: continue
                        thisElement = mapIdToContent[next]
                        recursive_builder(parent_node, thisElement, root, mapIdToNext, mapIdToContent, visited + [closeGate.getAttribute("id")])
                return
            for next in mapIdToNext[current_node.getAttribute("id")]:
                if next in visited: continue
                return current_node
            return
        case "exclusiveGateway":
            if current_node.getAttribute("gatewayDirection") == "Diverging" and inExclusive == "":
                for n in mapIdToNext[current_node.getAttribute("id")]:
                    cont = mapIdToContent[n]
                    if cont.tagName == "exclusiveGateway" and cont.getAttribute("gatewayDirection") == "Converging":
                        # repeatUntil
                        print("Haha")
                        repeatUntilTag = root.createElement("repeatUntil")
                        parent_node.appendChild(repeatUntilTag)
                        recursive_builder(repeatUntilTag, mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]],
                        root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], inExclusive="repeatUntil", prevParent=parent_node)
            elif current_node.getAttribute("gatewayDirection") == "Converging":
                n = mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]]
                if n.tagName == "exclusiveGateway" and n.getAttribute("gatewayDirection") == "Diverging":
                    print("While")
                    whileTag = root.createElement("while")
                    parent_node.appendChild(whileTag)
                    closeTagNext = mapIdToNext[n.getAttribute("id")]
                    for next in closeTagNext:
                        if mapIdToContent[next].tagName == "endEvent":
                            recursive_builder(parent_node, mapIdToContent[next], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id"), n.getAttribute("id")], "while")
                        else:
                            recursive_builder(whileTag, mapIdToContent[next], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id"), n.getAttribute("id")], "while")
                elif mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]].tagName == "endEvent":
                    print("If")
                    ifTag = root.createElement("if")
                    parent_node.appendChild(ifTag)
                elif mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]].tagName != "endEvent" and inExclusive == "":
                    # repeatWhile
                    print("RepeatWhile")
                    repeatBranchSequence = root.createElement("sequence")
                    parent_node.appendChild(repeatBranchSequence)
                    recursive_builder(repeatBranchSequence, mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]],
                        root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], inExclusive="repeatWhile", prevParent=parent_node)
                elif utils.get_text(current_node.getElementsByTagName("ingoing")):
                    pass

            elif inExclusive == "repeatUntil":
                print("REPEAT UNTIL")
            elif inExclusive == "while":
                print("WHILE")
                whileSequenceTag = root.createElement("sequence")
                parent_node.appendChild(whileSequenceTag)
            elif inExclusive == "if":
                print("IF")
            elif inExclusive == "repeatWhile":
                print("REPEAT WHILE")
                whileBranchTag = root.createElement("while")
                whileBranchSequenceTag = root.createElement("sequence")
                whileBranchTag.appendChild(whileBranchSequenceTag)
                prevParent.appendChild(whileBranchTag)
                next = mapIdToNext[current_node.getAttribute("id")]
                for n in next:
                    if mapIdToContent[n].tagName != "endEvent":
                        recursive_builder(whileBranchSequenceTag, mapIdToContent[n], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], inExclusive)
                    else:
                        recursive_builder(prevParent, mapIdToContent[n], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], inExclusive)
                additionalTags = prevParent.getElementsByTagName("sequence")[0].childNodes
                for tag in additionalTags:
                    tmpTag = root.createElement(tag.tagName)
                    tmpTag.setAttribute("name", tag.getAttribute("name"))
                    whileBranchSequenceTag.appendChild(tmpTag)
            return
            
    generatedNode.setAttribute("name", current_node.getAttribute("name"))
    parent_node.appendChild(generatedNode)
    for next in mapIdToNext[current_node.getAttribute("id")]:
        if next in visited: continue
        thisElement = mapIdToContent[next]
        return recursive_builder(parent_node, thisElement, root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], inExclusive=inExclusive, prevParent=prevParent)

def builder(file_path: str) -> str:
    trimmed_bpmn = read_bpmn_code(file_path)
    structure_name = builder_main(trimmed_bpmn)
    return structure_name

print(builder("bpmn_code/If.bpmn"))