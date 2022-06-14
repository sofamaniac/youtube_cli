from parser.datastructures import functions_list, global_properties, Property


def add_primitive(name, function):
    functions_list.add_property(Property(name, function))


def quit():
    # TODO find a better way to handle exit
    exit(0)


add_primitive("quit", quit)
add_primitive("q", quit)
