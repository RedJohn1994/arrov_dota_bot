import ctypes
import time
from datetime import datetime, timedelta

import cv2
import pyautogui

from screen_grabber import Grabber
from simple_ocr_utils import find_and_create_card_img, detect_dominant_color, find_template_coordinates

ATTRIBUTE_COLORS_TO_CHOOSE = ["red", "violet"]

# Глобальные настройки надежности
pyautogui.PAUSE = 0.15
pyautogui.FAILSAFE = True

# Константы для низкоуровневых событий мыши
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

# Координаты для выбора предметов
ITEM_POSITIONS = [
    (1030, 700),  # Точка 1
    (1777, 700),  # Точка 2
    (2152, 295)  # Точка закрытия
]

# регион для определения цвета предмета карточки
CARD_COLOR_REGION = (55, 45, 94, 62)

grabber = Grabber()

def send_mouse_event(x, y, dwFlags, button='left'):
    """Отправляет низкоуровневое событие мыши"""
    ctypes.windll.user32.SetCursorPos(x, y)
    if button == 'left':
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == 'right':
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


def robust_click(x, y, button='left', duration=0.5, retries=5, delay_before=0.5, delay_after=0.5):
    """Надежный клик с использованием низкоуровневых функций"""
    for attempt in range(1, retries + 1):
        try:
            time.sleep(delay_before)

            # Плавное перемещение
            pyautogui.moveTo(x, y, duration=duration)
            time.sleep(0.1)

            # Низкоуровневый клик
            send_mouse_event(x, y, 0, button)

            # Задержка после клика
            time.sleep(delay_after)

            print(f"✅ Клик на ({x}, {y}) [попытка {attempt}/{retries}]")
            return True

        except Exception as e:
            print(f"Ошибка при клике ({x}, {y}): {str(e)}")
            time.sleep(0.5)

    print(f"🛑 Критическая ошибка: не удалось выполнить клик на ({x}, {y})")
    return False


def is_target_color(rgb):
    """
    Проверяет, является ли пиксель красным или желтым.
    Возвращает 'red', 'yellow' или None.
    """
    r, g, b = rgb

    # Улучшенное распознавание красного
    if r > 160 and g < 100 and b < 100:
        return 'red'

    # Улучшенное распознавание желтого
    if r > 180 and g > 160 and b < 120:
        # Проверяем что это именно желтый, а не зеленый
        if r - g < 50 and g - b > 60:
            return 'yellow'

    return None


def analyze_color_with_delay(x, y, delay=5):
    """Анализирует цвет пикселя с задержкой"""
    print(f"Анализ цвета на ({x}, {y}) в течение {delay} секунд...")
    start_time = time.time()
    detected_colors = []

    while time.time() - start_time < delay:
        try:
            color = pyautogui.pixel(x, y)
            color_type = is_target_color(color)
            if color_type:
                detected_colors.append(color_type)
            time.sleep(0.5)  # Проверяем каждые 0.5 секунды
        except Exception:
            time.sleep(0.5)

    # Определяем преобладающий цвет
    if detected_colors:
        from collections import Counter
        color_counter = Counter(detected_colors)
        predominant_color = color_counter.most_common(1)[0][0]
        print(f"Преобладающий цвет: {predominant_color} (всего обнаружений: {len(detected_colors)})")
        return predominant_color
    return None


def move_mouse_to(x, y, duration=0.5, delay_after=0.5):
    pyautogui.moveTo(x, y, duration=duration)
    time.sleep(delay_after)


def get_red_card_attribute_colors(image_path: str, img):
    coords = find_template_coordinates(image_path, "template_images/fate_attrs_template.png")
    left_ = coords["top_left"]
    right_ = coords["bottom_right"]
    left_ = right_[0] + 5, left_[1]
    right_ = right_[0] + 35, right_[1]
    fate = detect_dominant_color(img, left_ + right_)
    if fate not in ATTRIBUTE_COLORS_TO_CHOOSE:
        fate = None

    coords = find_template_coordinates(image_path, "template_images/talante_attrs_template.png")
    left_ = coords["top_left"]
    right_ = coords["bottom_right"]
    left_ = right_[0] + 5, left_[1]
    right_ = right_[0] + 35, right_[1]
    talante = detect_dominant_color(img, left_ + right_)
    if talante not in ATTRIBUTE_COLORS_TO_CHOOSE:
        talante = None

    return fate, talante

def get_yellow_card_attribute_colors(image_path: str, img):
    coords = find_template_coordinates(image_path, "template_images/fate_attrs_template.png")
    left_ = coords["top_left"]
    right_ = coords["bottom_right"]
    left_ = right_[0] + 5, left_[1]
    right_ = right_[0] + 35, right_[1]
    fate = detect_dominant_color(img, left_ + right_)
    return fate

def select_items():
    """Выбирает красные или желтые предметы"""
    target_items_selected = 0
    round_count = 0
    start_time = datetime.now()
    timeout = timedelta(seconds=300)  # 5 минут таймаут

    print("\n--- Начало выбора предметов ---")
    print(f"Таймаут установлен: {timeout}")

    # images = [
    #     "images/1_left_yellow.png",
    #     "images/2_right_yellow.png",
    #     "images/left_red_1.png",
    #     "images/right_red_2.png",
    # ]
    # images = itertools.cycle(images)

    while datetime.now() - start_time < timeout:
        time.sleep(1)

        msg = ""
        try:
            left_fate_color, left_talantes_color, right_fate_color, right_talantes_color = [None] * 4
            left_card_priority_points, right_card_priority_points = 0, 0

            move_mouse_to(1030, 700) # left card
            img_path = find_and_create_card_img(grabber.screenshot())
            if not img_path:
                continue

            round_count += 1
            time_remaining = timeout - (datetime.now() - start_time)
            print(f"\n--- Раунд {round_count} (осталось: {time_remaining}) ---")

            img = cv2.imread(img_path)
            left_card_color = detect_dominant_color(img, CARD_COLOR_REGION)
            if left_card_color == "red":
                msg = "Слева красный предмет"
                left_fate_color, left_talantes_color = get_red_card_attribute_colors(img_path, img)
            elif left_card_color == "yellow":
                msg = "Слева жёлтый предмет"
                left_fate_color = get_yellow_card_attribute_colors(img_path, img)
            else:
                pass

            if left_fate_color == "violet":
                left_card_priority_points += 2
                print("Слева violet судьба")
            elif left_fate_color == "red":
                left_card_priority_points += 1
                print("Слева red судьба")

            if left_talantes_color == "violet":
                left_card_priority_points += 2
                print("Слева violet таланты")
            elif left_talantes_color == "red":
                left_card_priority_points += 1
                print("Слева red таланты")

            move_mouse_to(1777, 700) # right card
            img_path = find_and_create_card_img(grabber.screenshot())
            # img_path = find_and_create_card_img(next(images))
            img = cv2.imread(img_path)
            right_card_color = detect_dominant_color(img, CARD_COLOR_REGION)
            if right_card_color == "red":
                msg += ", Справа красный предмет"
                right_fate_color, right_talantes_color = get_red_card_attribute_colors(img_path, img)
            elif right_card_color == "yellow":
                msg += ", Справа жёлтый предмет"
                right_fate_color = get_yellow_card_attribute_colors(img_path, img)
            else:
                pass

            if right_fate_color == "violet":
                right_card_priority_points += 2
                print("Справа violet судьба")
            elif right_fate_color == "red":
                right_card_priority_points += 1
                print("Справа red судьба")

            if right_talantes_color == "violet":
                right_card_priority_points += 2
                print("Справа violet таланты")
            elif right_talantes_color == "red":
                print("Справа red таланты")

            print(msg if msg else "Фигня слева и справа")

            print(f"Приоритет лево/право: {left_card_priority_points}/{right_card_priority_points}")
            if left_card_priority_points == 0 and right_card_priority_points == 0:
                print("Фигня, закрываем")
                robust_click(ITEM_POSITIONS[2][0], ITEM_POSITIONS[2][1], button='left')
            elif left_card_priority_points == right_card_priority_points:
                print(f"Рейтинг одинаков, берём левую")
                robust_click(ITEM_POSITIONS[0][0], ITEM_POSITIONS[0][1], button='left')
                target_items_selected += 1
            elif left_card_priority_points > right_card_priority_points:
                print("Берём левую")
                robust_click(ITEM_POSITIONS[0][0], ITEM_POSITIONS[0][1], button='left')
                target_items_selected += 1
            else:
                print("Берём правую")
                robust_click(ITEM_POSITIONS[1][0], ITEM_POSITIONS[1][1], button='left')
                target_items_selected += 1

            # # Анализ цветов с задержкой 5 секунд на точку
            # print("\nАнализ точки 1:")
            # point1_color_type = analyze_color_with_delay(ITEM_POSITIONS[0][0], ITEM_POSITIONS[0][1], 5)
            #
            # print("\nАнализ точки 2:")
            # point2_color_type = analyze_color_with_delay(ITEM_POSITIONS[1][0], ITEM_POSITIONS[1][1], 5)
            #
            # print(f"\nРезультаты анализа: Точка1={point1_color_type}, Точка2={point2_color_type}")
            #
            # # Логика выбора на основе анализа цвета
            # if point1_color_type and point2_color_type:
            #     # Если обе точки имеют целевой цвет - выбираем первую
            #     robust_click(ITEM_POSITIONS[0][0], ITEM_POSITIONS[0][1], button='left')
            #     target_items_selected += 1
            #     print(f"Выбрана точка 1 (оба целевые) - выбрано предметов: {target_items_selected}")
            # elif point1_color_type:
            #     # Если целевой цвет только в первой точке
            #     robust_click(ITEM_POSITIONS[0][0], ITEM_POSITIONS[0][1], button='left')
            #     target_items_selected += 1
            #     print(f"Выбрана точка 1 - выбрано предметов: {target_items_selected}")
            # elif point2_color_type:
            #     # Если целевой цвет только во второй точке
            #     robust_click(ITEM_POSITIONS[1][0], ITEM_POSITIONS[1][1], button='left')
            #     target_items_selected += 1
            #     print(f"Выбрана точка 2 - выбрано предметов: {target_items_selected}")
            # else:
            #     # Если нет целевых цветов - закрываем выбор
            #     robust_click(ITEM_POSITIONS[2][0], ITEM_POSITIONS[2][1], button='left')
            #     print("Целевые цвета не найдены, закрываем выбор")

        except Exception as e:
            print(f"Ошибка при анализе цвета: {str(e)}")
            # В случае ошибки просто закрываем выбор
            robust_click(ITEM_POSITIONS[2][0], ITEM_POSITIONS[2][1], button='left')
            print("Ошибка анализа, закрываем выбор")

    # Проверка причины завершения
    if target_items_selected >= 4:
        print(f"✅ Успешно выбрано {target_items_selected} предметов!")
    else:
        print(f"🛑 Таймаут! Выбрано только {target_items_selected} из 4 предметов")

    return target_items_selected


def run_game_session():
    """Запускает одну игровую сессию"""
    try:
        # Шаг 1: Начальные действия
        print("\n" + "=" * 50)
        print("НАЧАЛО НОВОЙ ИГРОВОЙ СЕССИИ")
        print("=" * 50 + "\n")
        print("Старт через 600 секунд...")
        time.sleep(600)

        # Шаг 1.2: Открываем магазин
        robust_click(2208, 1398, button='left', duration=0.5, delay_before=1)
        print("Шаг 1.2: Открываем магазин")

        # Шаг 1.3: Покупаем топор
        robust_click(2390, 449, button='right', duration=0.5, delay_before=1.2)
        print("Шаг 1.3: Покупаем топор")

        # Шаг 1.4: Закрываем магазин
        robust_click(2208, 1398, button='left', duration=0.5, delay_before=1.5)
        print("Шаг 1.4: Закрываем магазин")

        # Шаг 1.5: Клик по башне на мини-карте (особое внимание!)
        robust_click(80, 1207, button='left', duration=0.5, delay_before=3, retries=7)
        print("Шаг 1.5: Башня на мини карте")

        # Шаг 1.6: Атака башни
        robust_click(1906, 860, button='right', duration=0.5, delay_before=1.8)
        print("Шаг 1.6: Атака башни")

        # Шаг 2.1: Ожидание 15 минут
        print("Ожидание 5 минут...")
        time.sleep(300)

        # Шаг 2.2: Атака трона
        robust_click(1527, 785, button='right', duration=0.5, delay_before=1)
        print("Шаг 2.2: Атака трона")

        # Шаг 2.3: Ожидание 3 минуты
        print("Ожидание 1 минута...")
        time.sleep(60)

        # Шаг 2.4: Подтверждение игры
        robust_click(1337, 1090, button='left', duration=0.5, delay_before=1.5)
        print("Шаг 2.4: Подтверждение игры")

        # Шаг 3.1: Поиск арены (особое внимание!)
        robust_click(152, 1267, button='left', duration=0.6, delay_before=2, retries=7)
        print("Шаг 3.1: Левый клик на (152, 1267)")

        # Шаг 3.2: Координаты MPC Арены
        robust_click(1566, 767, button='left', duration=0.8, delay_before=1)
        print("Шаг 3.2: МПС Арены")

        # Шаг 3.3: Подтверждение входа
        robust_click(1824, 897, button='left', duration=0.3, delay_before=1)
        print("Шаг 3.3: Подтверждение входа")

        # Шаг 3.4-3.7: Интеллектуальный выбор предметов
        selected_count = select_items()
        print(f"--- Выбрано {selected_count} предметов ---")

        # Шаг 3.8: Выход из арены
        time.sleep(15)
        robust_click(1281, 414, button='left', duration=0.8)
        print("Шаг 3.8: Выход из арены")

        # Шаг 3.9: Подтверждение выхода
        time.sleep(15)
        robust_click(1088, 836, button='left', duration=0.7)
        print("Шаг 3.9: Подтвердить выход из арены")

        # Шаг 3.10: Поиск МПС рестарта
        time.sleep(15)
        robust_click(1454, 1214, button='left', duration=0.9)
        print("Шаг 3.10: Поиск МПС рестарта")

        # Шаг 3.11: Подтверждение выхода
        time.sleep(5)
        robust_click(1095, 842, button='left', duration=0.4)
        print("Шаг 3.11: Подтвердить выход")

        # Шаг 3.12: Выбор сложности
        time.sleep(5)
        robust_click(1435, 481, button='left', duration=0.4)
        print("Шаг 3.12: Выбор сложности")

        # Шаг 3.13: Подтверждение выхода
        time.sleep(5)
        robust_click(2301, 1292, button='left', duration=0.4)
        print("Шаг 3.13: Начать игру")

        print("✅ Игровая сессия выполнена успешно!")
        return True

    except pyautogui.FailSafeException:
        print("⛔ Аварийная остановка: курсор мыши в углу экрана")
        return False
    except Exception as e:
        print(f"⛔ Критическая ошибка в сессии: {str(e)}")
        return False


def main(retry_game = 30):
    """Основная функция с поддержкой повторных запусков"""
    session_count = 0
    successful_sessions = 0

    # Проверка прав администратора
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        print("⚠️ Запустите скрипт от имени администратора для максимальной надежности!")
        print("⚠️ Скрипт будет работать без прав администратора, но возможны сбои.")

    while session_count < retry_game:
        session_count += 1
        print(f"\n{'=' * 50}")
        print(f"ЗАПУСК СЕССИИ {session_count}/{retry_game}")
        print(f"{'=' * 50}\n")

        # Запуск игровой сессии
        success = run_game_session()
        if success:
            successful_sessions += 1

        # Если это не последняя сессия - ждем 10 секунд перед повторным запуском
        if session_count < retry_game:
            print(f"\n⏱️ Ожидание 10 секунд перед следующей сессией ({session_count + 1}/{retry_game})...")
            time.sleep(10)

    # Итоговый отчет
    print(f"\n{'=' * 50}")
    print(f"ВСЕ СЕССИИ ЗАВЕРШЕНЫ")
    print(f"Успешных сессий: {successful_sessions}/{retry_game}")
    print(f"Неудачных сессий: {retry_game - successful_sessions}/{retry_game}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    # Установите нужное количество повторений (по умолчанию 5)
    main(retry_game=30)