import os

def tree(dir_path='.', prefix='', level=2):
    if level == 0:
        return
    files = os.listdir(dir_path)
    files.sort()
    for i, name in enumerate(files):
        path = os.path.join(dir_path, name)
        connector = '├── ' if i < len(files) - 1 else '└── '
        print(prefix + connector + name)
        if os.path.isdir(path):
            extension = '│   ' if i < len(files) - 1 else '    '
            tree(path, prefix + extension, level - 1)

tree('.', level=2)