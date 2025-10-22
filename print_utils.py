def rainbow_print(string):
    colors = [
        Colors.red,
        Colors.orange,
        Colors.yellow,
        Colors.green,
        Colors.blue,
        Colors.purple,
        None,
    ]

    color_count = len(colors)

    output = ""
    for i in range(len(string)):
        output += color(string[i], colors[i % color_count])

    print(output)


def color(text, rgb):
    if rgb is None:
        return text
    else:
        return "\033[38;2;{};{};{}m{}\033[0m".format(
            str(rgb[0]), str(rgb[1]), str(rgb[2]), text
        )


class Colors:
    red = (245, 90, 66)
    orange = (245, 170, 66)
    yellow = (245, 252, 71)
    green = (92, 252, 71)
    blue = (71, 177, 252)
    purple = (189, 71, 252)
    white = (255, 255, 255)
