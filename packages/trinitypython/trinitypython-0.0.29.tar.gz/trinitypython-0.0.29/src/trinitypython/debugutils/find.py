import inspect

nm_done = set()
functions = []
classes = []

def get_all_functions(objout):
    for name, obj in inspect.getmembers(objout):
        if not hasattr(obj, "__qualname__"):
            continue
        nm = obj.__qualname__
        if nm not in nm_done and not name.startswith("_"):
            nm_done.add(nm)
            if inspect.isfunction(obj):
                functions.append(nm)
            elif inspect.isclass(obj):
                classes.append(nm)
                get_all_functions(obj)


def search_function(obj, search_term):
    get_all_functions(obj)
    l_term = search_term.lower()
    print(" --> Functions <-- ")
    print("\n".join([x for x in functions if l_term in x.lower()]))
    print(" --> Classes <-- ")
    print("\n".join([x for x in classes if l_term in x.lower()]))

def list_elements(obj, search_term, showdoc):
    l_term = search_term.lower()
    for name, obj in inspect.getmembers(obj):
        if not name.startswith("_") and l_term in name.lower():
            if showdoc:
                print(name, "-->", inspect.getdoc(obj))
                print("="*20)
            else:
                print(name)

