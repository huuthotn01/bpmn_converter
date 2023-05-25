from xml.dom import minidom
import utils

def read_bpmn_code(file_path: str) -> minidom.Element:
    document = minidom.parse(file=file_path)
    definitionsTag = document.getElementsByTagName("definitions")
    processTag = definitionsTag[0].getElementsByTagName("process")
    return processTag[1] 

def builder_main(structure: minidom.Element, root: minidom.Document, sequenceTag: minidom.Element):
    mapIdToNext, mapIdToContent, startEvent = utils.map_id_to_next_element(structure)
    currEvent = startEvent # init current tag as startEvent
    recursive_builder(sequenceTag, mapIdToContent[currEvent], root, mapIdToNext, mapIdToContent, list())

visitedNodes = []
    
def recursive_builder(parent_node: minidom.Element, current_node: minidom.Element, root: minidom.Document,
                      mapIdToNext: dict(), mapIdToContent: dict(), visited: list(), inExclusive="", prevParent: minidom.Element = None):
    global visitedNodes
    if current_node.getAttribute("id") in visitedNodes: return
    visitedNodes += [current_node.getAttribute("id")]
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
                    closeGate = recursive_builder(branchTag, thisElement, root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], prevParent=parent_node)
                return
            for next in mapIdToNext[current_node.getAttribute("id")]:
                n = mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]]
                recursive_builder(prevParent, mapIdToContent[n.getAttribute("id")], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")])
            return
        case "exclusiveGateway":
            if current_node.getAttribute("gatewayDirection") == "Diverging" and inExclusive == "":
                print("If")
                ifTag = root.createElement("if")
                conditionTag = root.createElement("condition")
                ifTag.appendChild(conditionTag)
                ifSequenceTag = root.createElement("sequence")
                ifTag.appendChild(ifSequenceTag)
                parent_node.appendChild(ifTag)
                ifBranches = mapIdToNext[current_node.getAttribute("id")]
                recursive_builder(ifSequenceTag, mapIdToContent[ifBranches[0]], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], "if", prevParent=parent_node)
                ifBranches = ifBranches[1:]
                if len(ifBranches) == 0: return
                while len(ifBranches) > 1:
                    elseIfTag = root.createElement("elseif")
                    elifConditionTag = root.createElement("condition")
                    elseIfTag.appendChild(elifConditionTag)
                    elifSequenceTag = root.createElement("sequence")
                    elseIfTag.appendChild(elifSequenceTag)
                    ifTag.appendChild(elseIfTag)
                    recursive_builder(elifSequenceTag, mapIdToContent[ifBranches[0]], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], "if", prevParent=parent_node)
                    ifBranches = ifBranches[1:]
                elseTag = root.createElement("else")
                elseSequenceTag = root.createElement("sequence")
                elseTag.appendChild(elseSequenceTag)
                ifTag.appendChild(elseTag)
                recursive_builder(elseSequenceTag, mapIdToContent[ifBranches[0]], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], "if", prevParent=parent_node)
                return
            elif current_node.getAttribute("gatewayDirection") == "Converging":
                n = mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]]
                if inExclusive == "if":
                    print("IF")
                    recursive_builder(prevParent, mapIdToContent[n.getAttribute("id")], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], "")
                elif n.tagName == "exclusiveGateway" and n.getAttribute("gatewayDirection") == "Diverging":
                    print("While")
                    whileTag = root.createElement("while")
                    parent_node.appendChild(whileTag)
                    closeTagNext = mapIdToNext[n.getAttribute("id")]
                    for next in closeTagNext:
                        if mapIdToContent[next].tagName == "endEvent":
                            recursive_builder(parent_node, mapIdToContent[next], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id"), n.getAttribute("id")], "")
                        else:
                            recursive_builder(whileTag, mapIdToContent[next], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id"), n.getAttribute("id")], "while")
                elif mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]].tagName != "endEvent" and inExclusive == "":
                    isRepeatUntil = False
                    ingoing = current_node.getElementsByTagName("incoming")
                    ingoingOne = mapIdToContent[utils.get_text(ingoing[0].childNodes)].getAttribute("sourceRef")
                    ingoingTwo = mapIdToContent[utils.get_text(ingoing[1].childNodes)].getAttribute("sourceRef")
                    if mapIdToContent[ingoingOne].tagName == "exclusiveGateway" and mapIdToContent[ingoingOne].getAttribute("gatewayDirection") == "Diverging":
                        isRepeatUntil = True
                    else:
                        isRepeatUntil = mapIdToContent[ingoingTwo].tagName == "exclusiveGateway" and mapIdToContent[ingoingTwo].getAttribute("gatewayDirection") == "Diverging"              
                    if isRepeatUntil:
                        print("RepeatUntil")
                        repeatUntilTag = root.createElement("repeatUntil")
                        repeatUntilSequenceTag = root.createElement("sequence")
                        repeatUntilTag.appendChild(repeatUntilSequenceTag)
                        parent_node.appendChild(repeatUntilTag)
                        recursive_builder(repeatUntilSequenceTag, mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]],
                        root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], inExclusive="repeatUntil", prevParent=parent_node)
                        return
                    print("RepeatWhile")
                    repeatBranchSequence = root.createElement("sequence")
                    parent_node.appendChild(repeatBranchSequence)
                    recursive_builder(repeatBranchSequence, mapIdToContent[mapIdToNext[current_node.getAttribute("id")][0]],
                        root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], inExclusive="repeatWhile", prevParent=parent_node)
                elif utils.get_text(current_node.getElementsByTagName("ingoing")):
                    pass

            elif inExclusive == "repeatUntil":
                print("REPEAT UNTIL")
                next = mapIdToNext[current_node.getAttribute("id")]
                nextOne = mapIdToContent[next[0]]
                nextTwo = mapIdToContent[next[1]]
                recursive_builder(prevParent, nextOne, root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], "")
                recursive_builder(prevParent, nextTwo, root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], "")
            elif inExclusive == "while":
                print("WHILE")
                whileSequenceTag = root.createElement("sequence")
                parent_node.appendChild(whileSequenceTag)
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
                        recursive_builder(prevParent, mapIdToContent[n], root, mapIdToNext, mapIdToContent, visited + [current_node.getAttribute("id")], "")
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

def builder(file_path: str, root: minidom.Document, sequenceTag: minidom.Element) -> minidom.Element:
    trimmed_bpmn = read_bpmn_code(file_path)
    builder_main(trimmed_bpmn, root, sequenceTag)

# print(builder("bpmn_code/If.bpmn"))
# Done sequence, flow, pick, while, repeatWhile, If, Repeat-Until