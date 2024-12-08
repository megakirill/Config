import os
import tarfile
import csv

class Shell_emulator:
    def __init__(self, config):
        self.load_config(config)
        self.load_virtual_fs_tar()
        self.cwd = '/'
        self.history = []
        self.output = []
        self.log_actions = []


    def load_virtual_fs_tar(self):
        # Открываем tar-архив для чтения
        self.tar_file = tarfile.open(self.zip_path, 'r')

        # Получаем список всех файлов и директорий из архива
        self.files = list(set(member.name for member in self.tar_file.getmembers()))
        print(self.files)

    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            reader = csv.reader(f)
            config = {row[0]: row[1] for row in reader}  # Преобразуем CSV в словарь

            # Присваиваем значения соответствующим атрибутам
            self.computer_name = config.get('computer.name', '')
            self.zip_path = config.get('filesystem.path', '')
            self.startup_script = config.get('startup.script', '')
            self.log_path = config.get('logging.path', '')

    def cd(self, path):
        current = self.cwd
        if path == '..':
            self.cwd = os.path.dirname(self.cwd.rstrip('/'))
            if not self.cwd:
                self.cwd = '/'
        else:
            new_path = os.path.join(self.cwd.rstrip('/'), path).replace('\\', '/')
            if any(file.startswith('./' + new_path) or file == new_path for file in self.files):
                self.cwd = new_path
                print(f"Changed directory to {self.cwd}")
            else:
                print(new_path)
                print(f"Directory '{path}' not found")
        print(self.cwd)

    def ls(self):
        if self.cwd == '/':
            cwd_with_slash = './'
        else:
            cwd_with_slash = './' + self.cwd + '/'
        items = set()
        for file in self.files:
            if file.startswith(cwd_with_slash) and cwd_with_slash != file:
                relative_path = file[len(cwd_with_slash):].split('/')[0]
                items.add(relative_path)
        print(items)

    def rev(self, file):
        full_path = os.path.join(self.cwd.rstrip('/'), file).replace('\\', '/').lstrip('/')
        if './' + full_path in self.files:
            try:
                member = self.tar_file.getmember('./' + full_path)
                # Убедимся, что это файл, а не директория
                if member.isfile():
                    with self.tar_file.extractfile(member) as f:
                        a = f.readlines()
                        text = map(lambda x: x.decode('utf-8').strip()[::-1], a)
                        print(list(text))
                else:
                    print('is not a file')
            except KeyError:
                print('Не найден в архиве')
        else:
            print(f'file {file} is not in directory')


a = Shell_emulator('config.csv')
a.ls()
a.rev('startup_script.txt')



