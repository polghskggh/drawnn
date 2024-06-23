from dataclasses import dataclass, field

import svgwrite

ymax = 1000
cnt = 0


@dataclass
class Specification:
    height: float
    width: float
    x: float = 0
    y: float = ymax
    change_x: float = 15
    change_y: float = 15
    arrow_size: float = 8
    temp: dict = field(default_factory=lambda: {})


def __type_color(layer_type):
    if layer_type == "conv":
        return "blue"
    elif layer_type == "deconv":
        return "red"
    elif layer_type == "dense":
        return "orange"
    else:
        raise ValueError("not correct type")


def __add_to_temp(specification, key, value):
    if key in specification.temp:
        specification.temp[key].append(value)
    else:
        specification.temp[key] = [value]
    return specification


def __draw_arrow(drawing, specification, arrow_start, arrow_end):
    arrow_height, arrow_width = specification.arrow_size, specification.arrow_size / 2

    if (arrow_start[0] != arrow_end[0]):
        drawing.add(drawing.line(start=arrow_start, end=(arrow_end[0], arrow_start[1]),
                                 stroke=svgwrite.rgb(0, 0, 0, '%')))
        arrow_start = (arrow_end[0], arrow_start[1])

    arrow = drawing.add(drawing.line(start=arrow_start, end=arrow_end, stroke=svgwrite.rgb(0, 0, 0, '%')))
    arrow_marker = drawing.marker(insert=(arrow_height, arrow_width), size=(arrow_height, arrow_height), orient="auto")
    arrow_marker.add(drawing.path(d=f"M0,0 L{arrow_height},{arrow_width} L0,{arrow_height} z", fill="black"))
    drawing.defs.add(arrow_marker)
    arrow['marker-end'] = arrow_marker.get_funciri()
    return drawing


def __group(specification, group: str, align: str = "right"):
    x = specification.x if align == "right" else specification.x + specification.width

    return __add_to_temp(specification, group, Specification(specification.height, specification.width, x,
                                                             specification.y, temp={"align": align}))


def __ungroup(drawing, specification, group: str):
    vals = specification.temp[group]
    for val in vals:
        if val.temp["align"] == "left":
            targ_x = specification.x
            sign = 1
        else:
            targ_x = specification.x + specification.width
            sign = -1

        targ_x += sign * specification.change_x / 4
        arrow_start = (
            val.x + specification.change_x / 4, val.y)
        arrow_end = (targ_x, specification.y - specification.height)
        __draw_arrow(drawing, specification, arrow_start, arrow_end)


def __get_start_end(specification):
    arrow_start = (
        specification.x + specification.width / 2, specification.y - specification.height + specification.change_y)
    arrow_end = (specification.x + specification.width / 2, specification.y - specification.height)
    return arrow_start, arrow_end


def __draw_text(drawing, specification, text):
    text = drawing.text(text, insert=(specification.x + specification.width / 2, specification.height / 2),
                        text_anchor="middle")
    drawing.add(text)
    return drawing


def __draw_layer(drawing, specification, layer_type):
    rectangle = drawing.rect(insert=(specification.x, specification.y),
                             size=(specification.width, specification.height),
                             fill=__type_color(layer_type), stroke='black')
    drawing.add(rectangle)
    drawing = __draw_text(drawing, specification, layer_type)

    # Add arrow to the next rectangle (if not the last rectangle)

    drawing = __draw_arrow(drawing, specification, *__get_start_end(specification))
    return drawing


def __eval_skip(drawing, specification, scale):
    if scale == "down":
        specification = __add_to_temp(specification, "skip_stack", specification.y)
    elif scale == "up":
        arrow_start = (
            specification.x + specification.change_x / 4, specification.temp['skip_stack'].pop(len(specification.temp['skip_stack']) - 1))
        arrow_end = (specification.x + specification.change_x / 4, specification.y - specification.height)
        __draw_arrow(drawing, specification, arrow_start, arrow_end)
    return specification


def draw_conv(drawing, specification, scale: str = "same", skip: bool = False):
    if scale == "down":
        specification.width -= specification.change_x * 2
        specification.x += specification.change_x
    elif scale == "up":
        specification.width += specification.change_x * 2
        specification.x -= specification.change_x

    if skip:
        specification = __eval_skip(drawing, specification, scale)

    specification.y -= 2 * specification.change_y
    drawing = __draw_layer(drawing, specification, "deconv" if scale == "up" else "conv")
    return drawing, specification


def draw_dense(drawing, specification):
    specification.y -= 2 * specification.change_y

    drawing = __draw_layer(drawing, specification, "dense")
    return drawing, specification


def draw_simple():
    drawing = svgwrite.Drawing("simple.svg", profile='Full')
    specification = Specification(height=15, width=200)

    drawing, specification = draw_dense(drawing, specification)
    for i in range(6):
        drawing, specification = draw_conv(drawing, specification, "down", skip=True)
    specification = __group(specification, "latent")
    for i in range(2):
        drawing, specification = draw_conv(drawing, specification, "same")
    for i in range(6):
        drawing, specification = draw_conv(drawing, specification, "up", skip=True)
    __ungroup(drawing, specification,"latent")
    drawing, specification = draw_dense(drawing, specification)

    drawing.save()


if __name__ == "__main__":
    draw_simple()
