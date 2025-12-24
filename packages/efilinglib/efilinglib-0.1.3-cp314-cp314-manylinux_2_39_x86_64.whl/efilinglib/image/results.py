import xml.etree.ElementTree as ET


def get_results_as_xml(convert_results):
    root = ET.Element('images')
    for result in convert_results:
        elem = ET.Element('image', result)
        root.append(elem)
    ET.indent(root, space='  ')
    return ET.ElementTree(root)
