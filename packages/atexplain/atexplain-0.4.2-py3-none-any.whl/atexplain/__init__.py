from .engine import explain_code

def ask_explanation(filename: str):
    """
    Спрашивает пользователя, хочет ли он получить объяснение кода.
    Если ответ да — выводит объяснение, иначе — только соцсети.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"⚠️ Файл '{filename}' не найден!")
        return

    answer = input("Нужно объяснение работы кода? (да/нет): ").strip().lower()
    if answer == "да" or answer == "yes":
        explanation = explain_code(code)
        print("\n📘 Объяснение:\n")
        print(explanation)

    # соцсети всегда показываются
    print("\n🌐 Наши соцсети:")
    print("VK: vk.com/club234635039")
    print("TG: t.me/AIPythonTeacher_bot")


