import os

metadatafile = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../', 'metadata.txt')

def get_version():
    with open(metadatafile) as f:
        for line in f:
            if line.startswith('version'):
                return line.split("=")[1]
    return 'unknown'


if __name__ == '__main__':
    print(get_version())