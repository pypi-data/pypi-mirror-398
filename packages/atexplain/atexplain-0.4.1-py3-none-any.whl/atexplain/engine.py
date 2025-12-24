import builtins

def ask_explanation(filename: str):
    user_input = input("Нужно объяснение работы кода? (да/нет): ").strip().lower()
    
    show_explanation = user_input in ("да", "yes", "y")
    
    if show_explanation:
        print("\n📘 Объяснение:")
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line_strip = line.strip()
                if line_strip.startswith("import atexplain"):
                    continue
                print(f"{i}. {line_strip} -> выполняется как Python инструкция")
                
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
    
    # В любом случае показываем соцсети
    print("\n🔗 Подписывайтесь на наши соцсети:")
    print("VK: vk.com/club234635039")
    print("Telegram: t.me/AIPythonTeacher_bot")
