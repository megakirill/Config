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
                details = f"Changed directory to {self.cwd}"
                self.log_action('cd', details)
            else:
                details = f"Directory '{path}' not found"
                self.log_action('cd', details)


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
        self.log_action('ls', f'ls')


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
                        self.log_action('rev', f'file:{file}')
                else:
                    self.log_action('rev', f'failed.file:{file}')
            except KeyError:
                self.log_action('rev', f'failed.file:{file}')
        else:
            self.log_action('rev', f'failed.file:{file}')

    def log_action(self, action_type, details, user=0):
        if user == 0:
            user = self.computer_name
        """Добавить действие в лог."""
        action = {
            "type": action_type,
            "details": details,
            "cwd": self.cwd,
            "user": user
        }
        self.log_actions.append(action)

        # Проверяем, существует ли CSV-файл; если нет, создаем его с заголовком
        file_exists = os.path.exists(self.log_path)

        # Сохранить логи в CSV файл
        with open(self.log_path, 'a', newline='') as log_file:
            writer = csv.DictWriter(log_file, fieldnames=["type", "details", "cwd", "user"])
            if not file_exists:
                writer.writeheader()  # Записываем заголовки, если файл создается впервые
            writer.writerow(action)  # Добавляем запись

    def chown(self, file_name, owner, group=None):
        """Изменить владельца и группу для файла."""
        full_path = os.path.join(self.cwd.rstrip('/'), file_name).replace('\\', '/').lstrip('/')
        if not full_path.startswith('./'):
            full_path = './' + full_path

        if full_path in self.files:
            try:
                # Получаем член архива
                member = self.tar_file.getmember(full_path)
                # Проверяем, что это файл, а не директория
                if member.isfile() or member.isdir():
                    # Инициализируем структуру для хранения владельца и группы
                    if not hasattr(self, 'file_ownership'):
                        self.file_ownership = {}

                    # Обновляем или добавляем запись о владельце и группе
                    self.file_ownership[full_path] = {
                        'owner': owner,
                        'group': group
                    }

                    # Логируем действие
                    details = f"Changed owner to {owner}" + (f", group to {group}" if group else "")
                    self.log_action("chown", details, owner)

                else:
                    details = f"'{file_name}' is not a valid file or directory."
                    self.log_action("chown", details)
            except KeyError:
                details = f"File '{file_name}' not found in the archive."
                self.log_action("chown", details)
        else:
            details = f"File '{file_name}' not found in the current directory '{self.cwd}'."
            self.log_action("chown", details)


a = Shell_emulator('config.csv')
a.ls()
a.cd('another_directory')
a.rev('test_file2.txt')
a.chown('test_file2.txt', 'Alice')



