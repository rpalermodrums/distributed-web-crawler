import cssutils
import csv

def parse_css(file_name):
    properties = ['color', 'border', 'border-radius', 'font', 'margin', 'padding']
    chunks = {prop: [] for prop in properties}

    sheet = cssutils.parseFile(file_name)
    for rule in sheet:
        if isinstance(rule, cssutils.css.CSSStyleRule):
            for prop in properties:
                if rule.style.getProperty(prop):
                    chunks[prop].append(rule.style.getPropertyValue(prop))

    return chunks

def write_csv(file_name, chunks):
    with open(file_name, 'w', newline='') as file:
        writer = csv.writer(file)
        for prop, values in chunks.items():
            for value in values:
                writer.writerow([prop, value])

chunks = parse_css('full.css')
write_csv('css_properties.csv', chunks)
