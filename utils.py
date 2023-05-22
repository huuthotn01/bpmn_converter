from xml.dom import minidom

def map_id_to_activity_type(inp: minidom.Element) -> tuple[dict(), dict()]:
    mapIdToActivityType = dict()
    mapActivityTypeToId = dict()
    for tag in inp.childNodes:
        if type(tag) is not minidom.Element: continue
        if tag.tagName == "documentation" or tag.tagName == "laneSet": continue
        mapIdToActivityType[tag.getAttribute("id")] = tag
        mapActivityTypeToId[tag.tagName] = [tag.getAttribute("id")] if tag.tagName not in list(mapActivityTypeToId.keys()) else mapActivityTypeToId[tag.tagName] + [tag.getAttribute("id")]
    return (mapIdToActivityType, mapActivityTypeToId)

def map_id_to_in_out(activities: minidom.Element, transitions: minidom.Element) -> tuple[dict(), dict()]:
    mapIdToIn = dict()
    mapIdToOut = dict()
    return (mapIdToIn, mapIdToOut)