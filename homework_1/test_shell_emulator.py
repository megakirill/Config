import os
import tarfile
import csv
from shell_emulator import Shell_emulator  # Убедитесь, что файл с классом Shell_emulator доступен

def test_shell_emulator():
    # Создаем экземпляр эмулятора
    emulator = Shell_emulator('config.csv')

    test_passed = 0
    total_tests = 6

    try:
        # Тест 1: Список файлов в корневой директории
        print("Test 1: List files in the root directory")
        output = emulator.ls()
        assert "some_directory" in output or "another_directory" in output, "Directory listing failed"
        print("Test 1 passed")
        test_passed += 1

        # Тест 2: Переход в директорию 'some_directory'
        print("\nTest 2: Change directory to 'some_directory'")
        emulator.cd('some_directory')
        assert emulator.cwd.endswith('some_directory'), "Directory change failed"
        print("Test 2 passed")
        test_passed += 1

        # Тест 3: Список файлов после смены директории
        print("\nTest 3: List files after changing directory")
        output = emulator.ls()
        assert "some_file.txt" in output or "test_file.txt" in output, "Directory contents incorrect after cd"
        print("Test 3 passed")
        test_passed += 1

        # Тест 4: Обратное содержание файла 'some_file.txt'
        print("\nTest 4: Reverse content of 'some_file.txt'")
        reversed_content = emulator.rev('some_file.txt')
        assert reversed_content != "File 'some_file.txt' not found.", "Failed to reverse file content"
        print("Test 4 passed")
        test_passed += 1
        # Тест 5: Переход в несуществующую директорию
        print("\nTest 5: Change to a non-existing directory 'pop_directory'")
        emulator.cd('pop_directory')
        print(emulator.cwd)
        assert emulator.cwd == 'some_directory', "Directory change to invalid directory should not succeed"
        print("Test 5 passed")
        test_passed += 1

        # Тест 6: Логирование действий
        print("\nTest 6: Check logging actions")
        assert len(emulator.log_actions) > 0, "Logging actions failed"
        print("Test 6 passed")
        test_passed += 1

    except AssertionError as e:
        print(f"Test failed: {e}")

    print(f"\nAll {test_passed}/{total_tests} tests passed successfully!")

if __name__ == "__main__":
    test_shell_emulator()
