from xml.dom import minidom

def get_text(nodelist) -> str:
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
    mapIdToActivityType = dict()
    mapActivityTypeToId = dict()
    for tag in inp.childNodes:
        if type(tag) is not minidom.Element: continue
        if tag.tagName == "documentation" or tag.tagName == "laneSet": continue
        mapIdToActivityType[tag.getAttribute("id")] = tag
        mapActivityTypeToId[tag.tagName] = [tag.getAttribute("id")] if tag.tagName not in list(mapActivityTypeToId.keys()) else mapActivityTypeToId[tag.tagName] + [tag.getAttribute("id")]
    return (mapIdToActivityType, mapActivityTypeToId)

def map_id_to_next_element(inp: minidom.Element) -> tuple[dict(), dict(), str]:
    """
        Input: linear main content of the BPMN. It includes elements' tags and sequenceFlow tags indicating connections between elements.
        This function returns:
        - Dict 1: Map one element's id to next elements' ids. Next elements' ids are placed in a list.
        - Dict 2: Map element's id to its content - the whole tag of that element.
        - String: Start event tag's id.
    """
    mapIdToNextElements = dict()
    mapIdToContent = dict()
    startEventId = ""
    for tag in inp.childNodes:
        if type(tag) is not minidom.Element: continue
        if tag.tagName == "documentation" or tag.tagName == "laneSet": continue
        if tag.tagName == "startEvent": startEventId = tag.getAttribute("id")
        mapIdToContent[tag.getAttribute("id")] = tag
        mapIdToNextElements[tag.getAttribute("id")] = list()
    currentTag = mapIdToContent[startEventId].getAttribute("id")
    recursive_map_id_to_next_element(currentTag, mapIdToContent, mapIdToNextElements)
    return (mapIdToNextElements, mapIdToContent, startEventId)

def recursive_map_id_to_next_element(currentTag: str, mapIdToContent: dict(), mapIdToNextElements: dict()):
    if mapIdToContent[currentTag].tagName == "endEvent": return # terminate when meeting end event

    currTag = mapIdToContent[currentTag]
    outgoingTags = currTag.getElementsByTagName("outgoing")
    for outTag in outgoingTags:
        outId = get_text(outTag.childNodes)
        targetRef = mapIdToContent[outId].getAttribute("targetRef")
        if currTag.tagName in ["parallelGateway", "eventBasedGateway"] and currTag.getAttribute("gatewayDirection") == "Converging": mapIdToNextElements[currentTag] = [targetRef]
        else: mapIdToNextElements[currentTag] += [targetRef]
        recursive_map_id_to_next_element(targetRef, mapIdToContent, mapIdToNextElements)