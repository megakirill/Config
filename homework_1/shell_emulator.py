import os
import tarfile
import csv
import tkinter as tk
from tkinter import scrolledtext, messagebox
import sys


class Shell_emulator:
    def __init__(self, config):
        self.load_config(config)
        self.load_virtual_fs_tar()
        self.cwd = '/'
        self.history = []
        self.output = []
        self.log_actions = []
        self.file_ownership = {}

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
        return "\n".join(sorted(items))

    def rev(self, file):
        full_path = os.path.join(self.cwd.rstrip('/'), file).replace('\\', '/').lstrip('/')
        if './' + full_path in self.files:
            try:
                member = self.tar_file.getmember('./' + full_path)
                # Убедимся, что это файл, а не директория
                if member.isfile():
                    with self.tar_file.extractfile(member) as f:
                        a = f.readlines()
                        text = "\n".join(x.decode('utf-8').strip()[::-1] for x in a)
                        self.log_action('rev', f'file:{file}')
                        return text
                else:
                    self.log_action('rev', f'failed.file:{file}')
            except KeyError:
                self.log_action('rev', f'failed.file:{file}')
        else:
            self.log_action('rev', f'failed.file:{file}')
        return f"File '{file}' not found."

    def chown(self, file_name, owner, group=None):
        """Изменить владельца и группу для файла."""
        full_path = os.path.join(self.cwd.rstrip('/'), file_name).replace('\\', '/').lstrip('/')
        if not full_path.startswith('./'):
            full_path = './' + full_path

        if full_path in self.files:
            try:
                member = self.tar_file.getmember(full_path)
                # Проверяем, что это файл, а не директория
                if member.isfile() or member.isdir():
                    self.file_ownership[full_path] = {
                        'owner': owner,
                        'group': group
                    }
                    details = f"Changed owner to {owner}" + (f", group to {group}" if group else "")
                    self.log_action("chown", details, owner)
                    return f"Owner and group updated for {file_name}: owner={owner}, group={group}"
                else:
                    details = f"'{file_name}' is not a valid file or directory."
                    self.log_action("chown", details)
            except KeyError:
                details = f"File '{file_name}' not found in the archive."
                self.log_action("chown", details)
        else:
            details = f"File '{file_name}' not found in the current directory '{self.cwd}'."
            self.log_action("chown", details)
        return f"Failed to change owner for {file_name}."

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

        file_exists = os.path.exists(self.log_path)

        # Сохранить логи в CSV файл
        with open(self.log_path, 'a', newline='') as log_file:
            writer = csv.DictWriter(log_file, fieldnames=["type", "details", "cwd", "user"])
            if not file_exists:
                writer.writeheader()
            writer.writerow(action)

    def exit_shell(self):
        """Выход из консоли."""
        self.log_action("exit", "Exiting shell.")
        print("Exiting shell...")
        sys.exit(0)  # Завершаем выполнение программы


class ShellGUI:
    def __init__(self, root, shell):
        self.shell = shell

        # Вывод текущей директории
        self.cwd_label = tk.Label(root, text="Current Directory: /")
        self.cwd_label.pack(pady=5)

        # Область вывода
        self.output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', height=20, width=50)
        self.output_area.pack(pady=10)

        # Поле ввода
        self.command_input = tk.Entry(root, width=50)
        self.command_input.pack(pady=5)
        self.command_input.bind("<Return>", self.execute_command)

    def execute_command(self, event):
        command = self.command_input.get().strip()
        self.command_input.delete(0, tk.END)

        if not command:
            return

        parts = command.split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "ls":
            output = self.shell.ls()
        elif cmd == "cd" and args:
            self.shell.cd(args[0])
            output = f"Changed directory to {self.shell.cwd}"
        elif cmd == "rev" and args:
            output = self.shell.rev(args[0])
        elif cmd == "chown" and len(args) >= 2:
            output = self.shell.chown(args[0], args[1], args[2] if len(args) > 2 else None)
        elif cmd == "exit":
            self.shell.exit_shell()
            root.destroy()  # Завершение цикла Tkinter
        else:
            output = f"Unknown command: {command}"

        self.show_output(output)
        self.cwd_label.config(text=f"Current Directory: {self.shell.cwd}")

    def show_output(self, output):
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, output + "\n")
        self.output_area.configure(state='disabled')
        self.output_area.see(tk.END)


def main():
    global root  # Делаем root глобальным для доступа из других методов
    root = tk.Tk()
    root.title("Shell Emulator")

    shell = Shell_emulator('config.csv')
    gui = ShellGUI(root, shell)

    root.mainloop()



if __name__ == "__main__":
    main()
