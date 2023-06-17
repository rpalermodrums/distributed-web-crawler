import pandas as pd
from matplotlib import colors
import colorsys

def hsl_to_rgb(h, s, l):
    return colorsys.hls_to_rgb(h/360, l/100, s/100)

def convert_to_hex(color):
    if color.startswith('#'):
        # Hex color, just return it
        return color
    elif color.startswith('rgba'):
        # Convert RGBA to hex
        r, g, b, a = map(float, color[5:-1].split(','))
        return colors.rgb2hex((r/255, g/255, b/255, a))
    elif color.startswith('hsl'):
        # Convert HSL to RGB to hex
        h, s, l = map(lambda x: float(x.strip('%'))/100 if '%' in x else float(x.strip()), color[4:-1].split(','))
        r, g, b = hsl_to_rgb(h, s, l)
        return colors.rgb2hex((r, g, b))
    else:
        # Convert named color to hex
        return colors.cnames.get(color, color)

def process_colors(input_file, output_file):
    df = pd.read_csv(input_file, header=None, names=['property', 'value'])

    # Filter color rows and convert to hex
    color_rows = df[df['property'] == 'color']
    color_rows['value'] = color_rows['value'].apply(convert_to_hex)

    # Filter non-color rows
    non_color_rows = df[df['property'] != 'color']

    # Concatenate color and non-color rows
    df = pd.concat([color_rows, non_color_rows])

    df.to_csv(output_file, index=False, header=False)

process_colors('css_properties.csv', 'css_properties_processed.csv')
