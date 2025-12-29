from importlib import resources

def read_file(filename):
    with resources.files('testoli').joinpath(filename).open('r') as f:
        content=f.readlines()
        return content

def funcfoo():
    print("The chickens come home to roost")
