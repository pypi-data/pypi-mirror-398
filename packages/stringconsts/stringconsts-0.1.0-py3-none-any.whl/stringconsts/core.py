from typing import Dict, Any, Callable, Final

# Special constant used to mark attributes for automatic string generation
init_str: Final = None

class CStrConsts_Meta(type):
    """Metaclass for automatically creating dictionaries of string constants."""
    def __call__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} cannot be instantiated; use class attributes instead")

    def __init__(cls, name, bases, dct):
        cls._items : Dict[str, str] = {}
                
        # Get the external handler if defined, otherwise use identity
        handler : Callable[[str], str] = getattr(cls, "__handler__", lambda name: name.rstrip("_") if name.endswith("_") else name)
        # Get the external filter if defined, otherwise exclude dunder attributes
        filter_func : Callable[[str, Any], bool] = getattr(cls, "__filter__", lambda name, val: not name.startswith("__"))

        # skip processing for the base class itself
        if cls.__name__ == "StrConsts":
            return
        
        for attr_name, attr_val in dct.items():
            # Skip attributes that are filtered out
            if not filter_func(attr_name, attr_val):
                continue

            val = attr_val
            if val is init_str:
                # Apply the handler to generate the value
                val = handler(attr_name)

                setattr(cls, attr_name, val)

            # Store in internal dictionary
            cls._items[attr_name] = getattr(cls, attr_name)

        cls.bInited = True

    def __setattr__(cls, *args):
        # Prevent reassignment after initialization
        if getattr(cls, "bInited", False):
            raise AttributeError("Cannot reassign members.")
        super().__setattr__(*args)

    def __contains__(cls, key):
        """Check if a key exists in the constants."""
        return key in cls._items

    def __iter__(cls):
        """Iterate over attribute names"""
        return iter(cls._items)

    def keys(cls):
        """Return a dictionary keys"""
        return cls._items.keys()

    def values(cls):
        """Return a dictionary values"""
        return cls._items.values()

    def items(cls):
        """Return a dictionary items"""
        return cls._items.items()
    
    def __len__(cls):
        return len(cls._items)

    def as_dict(cls):
        """Return a dictionary of all constants: {attribute_name: value}"""
        return dict(cls._items)
    
class StrConsts(metaclass=CStrConsts_Meta):
    """
    Base class for creating string constants.

    Example usage:

    ```python
    # Simple example
    class Colors(StrConsts):
        red = init_str
        green = init_str
        blue = init_str
        class_ = init_str
        fixed = "not touched"
    c = Colors

    print(c.red) # red
    print(c.green) # green
    print(c.blue) # blue
    print(c.class_) # class
    print(c.fixed) # not touched
    print(c.as_dict()) # {'red': 'red', 'green': 'green', 'blue': 'blue', 'class_': 'class'}
    print(c.as_dict().keys()) # dict_keys(['red', 'green', 'blue', 'class_'])
    print(c.as_dict().values()) # dict_values(['red', 'green', 'blue', 'class'])
    print(c.as_dict().items()) # dict_items([('red', 'red'), ('green', 'green'), ('blue', 'blue'), ('class_', 'class')])
    print(c.keys()) # dict_keys(['red', 'green', 'blue', 'class_']) - the same c.as_dict().keys() - the same c.as_dict().keys()
    print(c.values()) # dict_values(['red', 'green', 'blue', 'class']) - the same c.as_dict().values() - the same c.as_dict().values()
    print(c.items()) # dict_items([('red', 'red'), ('green', 'green'), ('blue', 'blue'), ('class_', 'class')]) - the same c.as_dict().items()

    # iteration by keys
    for i in c:
        print(i, type(i))
    # red <class 'str'>
    # green <class 'str'>
    # blue <class 'str'>
    # class_ <class 'str'>
    # fixed <class 'str'>    

    # check value in Str
    print("red" in c) # True
    print("magenta" in c) # False


    # Example explain default handler's
    class JSWords(StrConsts):
        class_= init_str
        display = init_str
        style = init_str
        __test__ = init_str

    print(JSWords.display) # display
    print(JSWords.style) # style
    print(JSWords.class_) # class - default handler remove last underscore
    print(JSWords.__test__) # None (original value preserved, attribute excluded from constants). init_str is None, this key removed by filter.
    print(JSWords.as_dict()) # {'class_': 'class', 'display': 'display', 'style': 'style'} - no dunder
    for i in JSWords:
        print(i)
    # class_
    # display
    # style


    # Example explain custom handler and filter
    def colonize(name: str) -> str:
        return name.rstrip("_") if name.endswith("_") else name.replace("_", ":")

    # Default filter excludes dunder attributes automatically.
    # User-defined __filter__ can fully control filtering, including dunders.
    class Fields(StrConsts):
        __handler__ = colonize
        __filter__ = lambda name, val: not name.startswith("internal_") and not name.startswith("__")  # exclude internal attributes and dunders

        some_attr = init_str           # automatically generated
        other_attr = init_str          # automatically generated
        class_ = init_str              # automatically generated - the standard behavior of removing the last underscore is preserved, since we added this to our custom handler.
        internal_attr = init_str       # filtered out
        fixed_value = "fixed_string"   # user-defined fixed value

    print(Fields.some_attr)       # "some:attr"
    print(Fields.other_attr)      # "other:attr"
    print(Fields.class_)          # "class"
    print(Fields.fixed_value)     # "fixed_string"
    print(list(Fields))           # ['some_attr', 'other_attr', 'class_', 'fixed_value']
    print(Fields.as_dict())       # {'some_attr': 'some:attr', 'other_attr': 'other:attr', 'class_': 'class', 'fixed_value': 'fixed_string'}    ```
    """
    pass
