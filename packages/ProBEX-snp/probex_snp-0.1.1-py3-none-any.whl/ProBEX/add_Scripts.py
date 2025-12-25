import os

root_dir = 'scripts'

for dirpath, dirnames, filenames in os.walk(root_dir):
    init_file = os.path.join(dirpath, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            pass
        print(f'Created: {init_file}')
    else:
        print(f'Exists: {init_file}')
