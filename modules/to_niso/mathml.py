import re
import latex2mathml.converter


def generate_math_ml(text, idx):
    match = re.findall('(?<=math:::)(.+?)(?=end:::)', text)
    if match:
        for latex in match:
            idx += 1
            try:
                formula = latex2mathml.converter.convert(latex)
                formula = re.sub("xmlns", f"xmlns:mml", formula)
                formula = re.sub("<math", f"<math id='mml_m{idx}'", formula)
                formula = re.sub('<m', '<mml:m', formula)
                formula = re.sub('</m', '</mml:m', formula)
                text = text.replace(f'math:::{latex}end:::', f"<inline-formula>{str(formula)}</inline-formula>", 1)
            except:
                text = text.replace(f'math:::{latex}end:::', "", 1)
            #print(text)
        return text, idx
    return text, idx