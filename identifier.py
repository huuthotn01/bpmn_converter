from xml.dom import minidom
import utils

def get_text(nodelist) -> str:
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def read_bpmn_code(file_path: str) -> minidom.Element:
    document = minidom.parse(file=file_path)
    definitionsTag = document.getElementsByTagName("definitions")
    processTag = definitionsTag[0].getElementsByTagName("process")
    return processTag[1] 

def identify_structure(structure: minidom.Element) -> str:
    mapIdToActivityType, mapActivityTypeToId = utils.map_id_to_activity_type(structure)
    startEvent = structure.getElementsByTagName("startEvent")[0]
    endEvent = structure.getElementsByTagName("endEvent")[0]
    startEventOutFlow = get_text(startEvent.getElementsByTagName("outgoing")[0].childNodes)
    endEventInFlow = get_text(endEvent.getElementsByTagName("incoming")[0].childNodes)
    afterStartEventNodeId = mapIdToActivityType[startEventOutFlow].getAttribute("targetRef")
    beforeEndEventNodeId = mapIdToActivityType[endEventInFlow].getAttribute("sourceRef")
    # Identify Flow structure
    ## only structure having parallel gateway after startEvent and before endEvent
    if mapIdToActivityType[afterStartEventNodeId].tagName == "parallelGateway" and mapIdToActivityType[beforeEndEventNodeId].tagName == "parallelGateway":
        return "flow"
    # Identify Pick structure
    ## only structure having event based gateway after startEvent and before endEvent
    if mapIdToActivityType[afterStartEventNodeId].tagName == "eventBasedGateway" and mapIdToActivityType[beforeEndEventNodeId].tagName == "eventBasedGateway":
        return "pick"
    # Identify Sequence structure
    ## only structure having no gateway
    listEventType = list(mapActivityTypeToId.keys())
    if "eventBasedGateway" not in listEventType and "exclusiveGateway" not in listEventType and "parallelGateway" not in listEventType:
        return "sequence"
    return ""
    # Remain structure has exclusive gateway.
    

def identifier(file_path: str) -> str:
    trimmed_bpmn = read_bpmn_code(file_path)
    structure_name = identify_structure(trimmed_bpmn)
    return structure_name

print(identifier("bpmn_code/Flow.bpmn"))