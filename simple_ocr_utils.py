import cv2
import numpy as np


def find_and_create_card_img(img_path: str, card_img_path: str = "card_inside.png"):
    """
    Ищет на скрине из игры выделенную жёлтым цветом карточку с предметом.
    Сохраняет её в файл `card_img_path`
    """
    # === Загрузка изображения ===
    image = cv2.imread(img_path)

    # === Перевод в HSV ===
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # === Диапазон "жёлтого свечения" в HSV ===
    lower_yellow = np.array([20, 100, 200])  # можно варьировать
    upper_yellow = np.array([40, 255, 255])

    # === Маска по цвету ===
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # === Морфология: убрать шум ===
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.erode(mask, kernel, iterations=1)

    # === Поиск контуров ===
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # === Фильтрация по площади и форме ===
    target_rect = None
    max_area = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 1000:  # минимальная разумная площадь
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) == 4:  # ищем именно прямоугольник
                if area > max_area:
                    max_area = area
                    target_rect = approx

    if target_rect is not None:
        # Получим ограничивающий прямоугольник
        x, y, w, h = cv2.boundingRect(target_rect)
        roi = image[y:y + h, x:x + w]  # Вырезаем изображение внутри рамки

        # Для отладки: рисуем прямоугольник и сохраняем ROI
        debug_img = image.copy()
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # cv2.imwrite("debug_found_card.png", debug_img)

        cv2.imwrite(card_img_path, roi)

        return card_img_path
    else:
        return None


def find_template_coordinates(image_path: str, template_path: str, threshold: float = 0.9):
    # Загружаем изображения в оттенках серого — быстрее и не требует цветовой обработки
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    if image is None or template is None:
        raise FileNotFoundError("Изображение или шаблон не найдены.")

    # Получаем размеры шаблона
    template_h, template_w = template.shape

    # Сопоставление шаблона
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Проверка на уверенность
    if max_val < threshold:
        raise ValueError(f"Шаблон не найден. Максимальное совпадение: {max_val:.3f} ниже порога {threshold}.")

    top_left = tuple(max_loc)
    bottom_right = (top_left[0] + template_w, top_left[1] + template_h)

    return {
        "top_left": top_left,
        "bottom_right": bottom_right,
        "confidence": max_val
    }


def detect_dominant_color(img, region: tuple) -> str | None:
    """
    Определяет, преобладает ли красный или ярко-фиолетовый цвет или жёлтый в прямоугольной области изображения.

    :param image_path: Путь к исходному изображению
    :param region: Координаты прямоугольника (top_left_x, top_left_y, bottom_right_x, bottom_right_y)
    :return: 'red', 'violet', 'yellow' или None
    """

    if img is None:
        raise FileNotFoundError("Изображение не найдено.")

    x1, y1, x2, y2 = region
    roi = img[y1:y2, x1:x2]

    # Переводим в HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Маски для красного
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    # Маска для ярко-фиолетового
    lower_violet = np.array([135, 50, 30])
    upper_violet = np.array([150, 255, 255])
    violet_mask = cv2.inRange(hsv, lower_violet, upper_violet)

    lower_yellow_ = np.array([20, 100, 100])
    upper_yellow_ = np.array([35, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow_, upper_yellow_)

    red_pixels = np.count_nonzero(red_mask)
    violet_pixels = np.count_nonzero(violet_mask)
    yellow_pixels = np.count_nonzero(yellow_mask)

    total_pixels = roi.shape[0] * roi.shape[1]

    red_ratio = red_pixels / total_pixels
    violet_ratio = violet_pixels / total_pixels
    yellow_ratio = yellow_pixels / total_pixels

    if red_ratio > 0.2 and red_ratio > violet_ratio:
        return 'red'
    elif violet_ratio > 0.2 and violet_ratio > red_ratio:
        return 'violet'
    elif yellow_ratio > 0.2 and yellow_ratio > red_ratio:
        return 'yellow'
    else:
        return None

if __name__ == '__main__':
    # for test

    img_path = find_and_create_card_img("images/left_yellow_T6.png")
    img = cv2.imread(img_path)
    left_card_color = detect_dominant_color(img, (55, 45, 94, 62))

    coords = find_template_coordinates(img_path, "template_images/fate_attrs_template.png")
    left_ = coords["top_left"]
    right_ = coords["bottom_right"]
    left_ = right_[0] + 5, left_[1]
    right_ = right_[0] + 35, right_[1]
    fate = detect_dominant_color(img, left_ + right_)
    print(fate)

    coords = find_template_coordinates(img_path, "template_images/talante_attrs_template.png")
    left_ = coords["top_left"]
    right_ = coords["bottom_right"]
    left_ = right_[0] + 5, left_[1]
    right_ = right_[0] + 35, right_[1]
    talante = detect_dominant_color(img, left_ + right_)
    print(talante)
