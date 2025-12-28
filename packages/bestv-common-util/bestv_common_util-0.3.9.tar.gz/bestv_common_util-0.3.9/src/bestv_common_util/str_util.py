
def concat(s, n, sep=","):
    result = ''
    for i in range(n - 1):
        result = result + s + sep
    return result + s


def extract_bucket(path):
    if path and len(path) > 6:
        start = path.find('//') + 2
        end = path.find('/', 6)
        return path[start:end]


def extract_object_key(path):
    if path and len(path) > 6:
        start = path.find('/', 6) + 1
        return path[start:]


def extract_object_name(path):
    if path and len(path) > 6:
        return path.split('/')[-1]
