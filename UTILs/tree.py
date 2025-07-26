import os
import argparse

def tree(dir_path='.', prefix='', level=2):
    if level == 0:
        return
    try:
        files = os.listdir(dir_path)
    except PermissionError:
        print(prefix + '└── [Permission Denied]')
        return

    files.sort()
    for i, name in enumerate(files):
        path = os.path.join(dir_path, name)
        connector = '├── ' if i < len(files) - 1 else '└── '
        print(prefix + connector + name)
        if os.path.isdir(path):
            extension = '│   ' if i < len(files) - 1 else '    '
            tree(path, prefix + extension, level - 1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Imprimir árbol de carpetas.')
    parser.add_argument('path', nargs='?', default='.', help='Ruta de inicio (por defecto es el directorio actual)')
    parser.add_argument('--level', type=int, default=2, help='Nivel de profundidad (por defecto: 2)')
    args = parser.parse_args()

    tree(args.path, level=args.level)
