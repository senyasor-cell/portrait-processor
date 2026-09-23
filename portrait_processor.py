import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import os
import base64
from io import BytesIO

class PortraitProcessorJPG:
    def __init__(self):
        # Используем OpenCV для детекции лиц
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Проверяем наличие rembg
        self.rembg_available = False
        try:
            from rembg import remove
            self.rembg_remove = remove
            self.rembg_available = True
            print("rembg доступен для удаления фона")
        except ImportError:
            print("rembg не установлен. Использую альтернативные методы.")
        
        # Дополнительный классификатор для профильных лиц
        self.profile_cascade = None
        try:
            self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        except:
            print("Профильный классификатор не найден, используем только фронтальный")
    
    def load_image_from_bytes(self, image_bytes):
        """Загрузка изображения из байтов"""
        try:
            image = Image.open(BytesIO(image_bytes)).convert('RGB')
            return image
        except Exception as e:
            raise ValueError(f"Неверный формат изображения: {e}")
    
    def load_image(self, image_path):
        """Загрузка изображения из файла"""
        if isinstance(image_path, str):
            image = Image.open(image_path).convert('RGB')
        elif isinstance(image_path, Image.Image):
            image = image_path.convert('RGB')
        else:
            raise ValueError("Неверный формат изображения")
        return image
    
    def image_to_bytes(self, image, format='JPEG'):
        """Конвертация PIL Image в байты"""
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=format, quality=95)
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()
    
    def image_to_base64(self, image, format='JPEG'):
        """Конвертация PIL Image в base64 строку"""
        img_bytes = self.image_to_bytes(image, format)
        return base64.b64encode(img_bytes).decode('utf-8')
    
    def base64_to_image(self, base64_string):
        """Конвертация base64 строки в PIL Image"""
        img_bytes = base64.b64decode(base64_string)
        return self.load_image_from_bytes(img_bytes)
    
    def enhance_image(self, image):
        """Улучшение качества изображения"""
        # 1. Уменьшение шума
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # 2. Повышение резкости
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)
        
        # 3. Улучшение контраста
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        
        # 4. Небольшое повышение насыщенности
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.05)
        
        # 5. Легкая коррекция яркости
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.02)
        
        return image
    
    def detect_face_and_nose(self, image):
        """Детекция лица и носа с помощью OpenCV"""
        # Конвертируем PIL в numpy для OpenCV
        image_np = np.array(image)
        
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        
        # Улучшаем контраст для лучшей детекции
        gray = cv2.equalizeHist(gray)
        
        # Детекция фронтальных лиц
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Если не найдены фронтальные лица, пробуем профильные
        if len(faces) == 0 and self.profile_cascade is not None:
            faces = self.profile_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50)
            )
        
        if len(faces) == 0:
            # Пробуем более чувствительные параметры
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,
                minNeighbors=3,
                minSize=(30, 30)
            )
        
        if len(faces) == 0:
            raise ValueError("Лицо не обнаружено на изображении.")
        
        # Выбираем самое крупное лицо
        faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
        x, y, w, h = faces[0]
        
        # Оцениваем положение кончика носа
        nose_tip_x = x + w // 2
        nose_tip_y = y + int(h * 0.65)
        
        return {
            'bbox': (int(x), int(y), int(x + w), int(y + h)),
            'face_width': w,
            'face_height': h,
            'center_x': x + w // 2,
            'center_y': y + h // 2,
            'nose_tip_x': nose_tip_x,
            'nose_tip_y': nose_tip_y
        }
    
    def extract_person_with_white_bg(self, image, use_rembg=True):
        """Извлечение человека с белым фоном"""
        if use_rembg and self.rembg_available:
            try:
                # Используем rembg для удаления фона
                from rembg import remove
                
                # Конвертируем в RGBA для rembg
                if image.mode != 'RGBA':
                    image_rgba = image.convert('RGBA')
                else:
                    image_rgba = image
                
                # Получаем изображение с удаленным фоном
                no_bg = remove(image_rgba)
                
                # Конвертируем в numpy для обработки
                no_bg_np = np.array(no_bg)
                
                # Создаем белый фон
                white_bg = np.ones((no_bg_np.shape[0], no_bg_np.shape[1], 3), dtype=np.uint8) * 255
                
                # Получаем альфа-канал как маску
                if no_bg_np.shape[2] == 4:
                    alpha = no_bg_np[:, :, 3] / 255.0
                    alpha = alpha[:, :, np.newaxis]
                    
                    # Наложение на белый фон
                    result = (no_bg_np[:, :, :3] * alpha + white_bg * (1 - alpha)).astype(np.uint8)
                else:
                    result = no_bg_np
                
                return Image.fromarray(result)
                
            except Exception as e:
                print(f"   Ошибка при использовании rembg: {e}")
                return image
        
        return image
    
    def add_white_background(self, image):
        """Добавление белого фона к изображению"""
        if image.mode == 'RGBA':
            # Создаем белый фон
            white_bg = Image.new('RGB', image.size, (255, 255, 255))
            
            # Разделяем на RGB и альфа-канал
            r, g, b, a = image.split()
            
            # Наложение с учетом альфа-канала
            white_bg.paste(image, mask=a)
            return white_bg
        else:
            return image.convert('RGB')
    
    def calculate_crop_region(self, image_size, face_info):
        """Расчет области кадрирования с учетом кончика носа в центре по горизонтали"""
        img_width, img_height = image_size
        
        # Получаем координаты кончика носа
        nose_tip_x = face_info.get('nose_tip_x', face_info['center_x'])
        nose_tip_y = face_info.get('nose_tip_y', face_info['center_y'])
        
        # 1. Высота кадра = 2 * высота лица
        crop_height = face_info['face_height'] * 2.0
        
        # 2. Пропорция 4:3 → ширина = высота * 3/4
        crop_width = crop_height * 0.75
        
        # 3. Центрируем по кончику носа
        crop_left = nose_tip_x - crop_width / 2
        crop_right = nose_tip_x + crop_width / 2
        crop_top = nose_tip_y - crop_height / 2
        crop_bottom = nose_tip_y + crop_height / 2
        
        # 4. Корректируем вертикальное положение
        if crop_top < 0:
            crop_top = 0
            crop_bottom = min(img_height, crop_height)
        elif crop_bottom > img_height:
            crop_bottom = img_height
            crop_top = max(0, img_height - crop_height)
        
        # 5. Корректируем горизонтальное положение (симметричная обрезка)
        if crop_left < 0 or crop_right > img_width:
            if crop_left < 0:
                excess_left = abs(crop_left)
                if crop_right + excess_left > img_width:
                    excess_right = crop_right + excess_left - img_width
                    crop_width = crop_width - (excess_left + excess_right)
                    crop_left = 0
                    crop_right = crop_width
                else:
                    crop_width = crop_width - excess_left
                    crop_left = 0
                    crop_right = crop_width
            elif crop_right > img_width:
                excess_right = crop_right - img_width
                if crop_left - excess_right < 0:
                    excess_left = excess_right - crop_left
                    crop_width = crop_width - (excess_right + excess_left)
                    crop_left = img_width - crop_width
                    crop_right = img_width
                else:
                    crop_width = crop_width - excess_right
                    crop_left = img_width - crop_width
                    crop_right = img_width
        
        # 6. Убедимся, что кончик носа остается в центре по горизонтали
        final_crop_width = crop_right - crop_left
        if abs(nose_tip_x - (crop_left + final_crop_width / 2)) > 1:
            crop_left = nose_tip_x - final_crop_width / 2
            crop_right = nose_tip_x + final_crop_width / 2
            
            if crop_left < 0:
                crop_right -= crop_left
                crop_left = 0
            elif crop_right > img_width:
                crop_left -= (crop_right - img_width)
                crop_right = img_width
        
        # 7. Добавляем отступ сверху для волос
        hair_padding = face_info['face_height'] * 0.05
        new_crop_top = max(0, crop_top - hair_padding)
        
        if new_crop_top == 0:
            if crop_bottom + hair_padding <= img_height:
                crop_bottom += hair_padding
        else:
            crop_top = new_crop_top
        
        return (
            int(max(0, crop_left)),
            int(max(0, crop_top)),
            int(min(img_width, crop_right)),
            int(min(img_height, crop_bottom))
        )
    
    def resize_to_target(self, image, max_width=600, max_height=800):
        """Изменение размера до целевого с сохранением пропорций"""
        width, height = image.size
        
        if width <= max_width and height <= max_height:
            return image
        
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def process_image_bytes(self, image_bytes, use_background_removal=True):
        """Обработка изображения из байтов"""
        # 1. Загрузка изображения
        original_image = self.load_image_from_bytes(image_bytes)
        
        # 2. Детекция лица и носа
        try:
            face_info = self.detect_face_and_nose(original_image)
        except ValueError:
            width, height = original_image.size
            face_size = min(width, height) // 3
            face_info = {
                'bbox': (width//2 - face_size//2, height//2 - face_size//2,
                        width//2 + face_size//2, height//2 + face_size//2),
                'face_width': face_size,
                'face_height': face_size,
                'center_x': width // 2,
                'center_y': height // 2,
                'nose_tip_x': width // 2,
                'nose_tip_y': height // 2 + face_size // 4
            }
        
        # 3. Расчет области кадрирования
        crop_box = self.calculate_crop_region(original_image.size, face_info)
        
        # 4. Удаление фона
        if use_background_removal and self.rembg_available:
            bg_removed = self.extract_person_with_white_bg(original_image, use_rembg=True)
        else:
            bg_removed = original_image
        
        # 5. Кадрирование
        try:
            cropped = bg_removed.crop(crop_box)
        except Exception:
            width, height = bg_removed.size
            crop_size = min(width, height * 4 // 3)
            crop_box = (
                (width - crop_size) // 2,
                (height - crop_size * 3 // 4) // 2,
                (width + crop_size) // 2,
                (height + crop_size * 3 // 4) // 2
            )
            cropped = bg_removed.crop(crop_box)
        
        # 6. Изменение размера
        resized = self.resize_to_target(cropped, max_width=600, max_height=800)
        
        # 7. Улучшение качества
        enhanced = self.enhance_image(resized)
        
        # 8. Установка белого фона
        final_image = self.add_white_background(enhanced)
        
        # 9. Конвертация в байты
        return self.image_to_bytes(final_image)