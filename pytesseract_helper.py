import pytesseract
from PIL import Image

from pytomation import android


def process_image(path):
    """
    Processes image in OCR and returns its text elements as a list of dictionaries.
    :param path: Path to the image.
    :return: List of image elements.
    """
    raw_data = pytesseract.image_to_boxes(Image.open(path))
    return _raw_data_to_elements(raw_data)


def _raw_data_to_elements(raw_data):
    split_by_char = list(filter(lambda x: x, raw_data.split('\n')))
    elements = list(map(_line_to_element, split_by_char))
    y_axis_size = android.display_height()
    return list(map(lambda x: _fix_element_y_coordinates(x, y_axis_size), elements))


def _line_to_element(line):
    line_split = line.split(' ')
    return {
        'char': line_split[0],
        'bottom-left': (
            int(line_split[1]), int(line_split[2])
        ),
        'top-right': (
            int(line_split[3]), int(line_split[4])
        )
    }


# Y coordinates are inverted in relation to how Android SDK sees them (Y 0 is Y max for PyTesseract)
def _fix_element_y_coordinates(element, max_y):
    for entry in ['bottom-left', 'top-right']:
        cur = element[entry]
        x = cur[0]
        y = max_y - cur[1]
        element[entry] = (x, y)
    return element


def click_coordinates_for_char(elements, char):
    """
    Returns click coordinates for the specified character (first appearance).
    :param elements: Image elements as returned by process_image()
    :param char: Character to look for.
    :return: Click coordinates as a tuple (x, y).
    """
    element = find_character(elements, char)
    assert element is not None
    x1 = element['top-right'][0]
    y1 = element['top-right'][1]
    x2 = element['bottom-left'][0]
    y2 = element['bottom-left'][1]
    x = x2 + (x1 - x2) / 2
    y = y1 + (y2 - y1) / 2
    return x, y


def find_character(elements, char):
    """
    Returns first element dictionary with the specified character.
    :param elements: Image elements as returned by process image()
    :param char: Character to look for.
    :return: Element dictionary of the first element with that character.
    """
    return next((entry for entry in elements if entry['char'] == char), None)
