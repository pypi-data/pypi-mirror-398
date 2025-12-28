def is_collection(variable):
    return isinstance(variable, (list, tuple))

def is_primitive(variable):
    return isinstance(variable, (int, str, bool, float))

def is_dumpable(variable):
    return isinstance(variable, DumpBase)

def are_all_primitive(collection):
    return all([is_primitive(a) for a in collection])

class DumpBase(object):

    @classmethod
    def _dump_item(cls, indent_level, list_decorator, key_name, value):
        #todo: Dodac przypadek ze wartosc elementu jest None

        if is_dumpable(value):
            for key_name, item in value.__dict__.items():

                if is_dumpable(item):
                    cls._print_line(indent_level, list_decorator, key_name, element="")
                    cls._dump_item(indent_level + 1, list_decorator, key_name, item)
                else:
                    cls._dump_item(indent_level + 0, list_decorator, key_name, item)
                list_decorator = False
            return

        if not is_collection(value):
            cls._print_line(indent_level, list_decorator, key_name, element=value)
            return


        if is_collection(value):
            if are_all_primitive(value):
                cls._print_line(indent_level, list_decorator, key_name, element=value)
                return

            cls._print_line(indent_level, list_decorator, key_name, element=None)
            for sub_value in value:
                cls._dump_item(indent_level + 1, True, None, sub_value)
            return

        raise Exception("Flow")



    @staticmethod
    def _print_line(indent_level, list_decorator, key_name, element=None):
        indent_level = indent_level * 2
        list_mark = ""

        if list_decorator:
            list_mark = "• "
            indent_level = indent_level - 2

        sp = f"{' ' * indent_level}{list_mark}"

        if element is None:
            key_name = f"{key_name:<25}: " if key_name else ""
            print(f"{sp}{key_name}↓")
            return

        key_name = f"{key_name:<25}: " if key_name else ""
        print(f"{sp}{key_name}{element}")



    def dump(self):
        self._dump_item(0, False, None, self)



