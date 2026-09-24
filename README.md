# Portrait Processor SOAP Web Service
&emsp;Сервис для автоматической обработки портретных фотографий с возможностью удаления фона, кадрирования и улучшения качества. Предоставляет SOAP API и веб-интерфейс для ручной загрузки.<br>
&emsp;Проект предназначен в первую очередь для ускорения фотографирования с помощью веб камер посетителей в таких подразделениях как бюро пропусков, отделы кадров, учебные отделы и получения однообразного результата без необходимости ручной обработки изображений.<br>
![Input](screenshots/Брюс.jpg)<br>
![Output](screenshots/Брюс+.jpg)<br>
# 📋 Содержание
Возможности<br>
Технологии<br>
Установка<br>
Запуск<br>
Использование<br>
Веб-интерфейс<br>
SOAP API<br>
SOAP клиент<br>
Структура проекта<br>
Описание алгоритма обработки<br>
Решение проблем<br>
Автор<br>
Лицензия<br>
# ✨ Возможности
Автоматическая обработка портретов:<br>
Детекция лица и определение положения кончика носа<br>
Удаление фона (с помощью rembg) с сохранением одежды<br>
Кадрирование по правилам:<br>
Кончик носа всегда в центре по горизонтали<br>
Лицо занимает ~50% высоты кадра<br>
Соотношение сторон 4:3 (если не выходит за границы)<br>
При выходе за границы – симметричная обрезка или сдвиг<br>
Изменение размера до 600×800 пикселей с сохранением пропорций<br>
Улучшение качества (резкость, контраст, насыщенность)<br>
SOAP API с ручной обработкой XML и автоматической генерацией WSDL<br>
Веб-интерфейс для загрузки, просмотра и сохранения результата<br>
SOAP клиент для тестирования сервиса прямо из браузера<br>
Полная совместимость с Python 3.12 (не используется Spyne)<br>
# 🛠 Технологии
Python 3.12+<br>
Flask – веб-фреймворк<br>
lxml – обработка XML для SOAP<br>
OpenCV – детекция лиц<br>
Pillow – обработка изображений<br>
rembg – удаление фона (опционально)<br>
waitress – продакшн-сервер<br>
# 📦 Установка
Клонируйте репозиторий или создайте структуру папок вручную:<br>
mkdir portrait_processor_soap<br>
cd portrait_processor_soap<br>
mkdir templates static<br>
Создайте виртуальное окружение и активируйте его:<br>
python -m venv venv<br>
source venv/bin/activate      # Linux/Mac<br>
venv\Scripts\activate         # Windows<br>
Установите зависимости:<br>
pip install -r requirements.txt<br>
requirements.txt:<br>
Flask==2.3.3<br>
lxml==4.9.3<br>
Pillow==10.0.0<br>
opencv-python==4.8.1.78<br>
numpy==1.24.3<br>
rembg==2.0.50<br>
waitress==2.1.2<br>
Поместите файлы проекта в соответствующие папки согласно структуре.<br>
# 🚀 Запуск<br>
python app.py<br>
Сервер запустится на http://localhost:5000.<br>
Доступные адреса:<br>
Веб-интерфейс: http://localhost:5000/<br>
SOAP-сервис: http://localhost:5000/soap<br>
WSDL: http://localhost:5000/wsdl<br>
SOAP-клиент: http://localhost:5000/soap-client<br>
Проверка здоровья: http://localhost:5000/health<br>
# 🖥 Использование
Веб-интерфейс
Откройте http://localhost:5000/<br>
Перетащите или выберите файл изображения (JPG, PNG, BMP, GIF, до 10 МБ)<br>
При необходимости снимите галочку «Удалить фон»<br>
Нажмите «Начать обработку»<br>
После завершения вы увидите результат и кнопку «Скачать обработанное изображение»<br>
SOAP API
Endpoint: POST http://localhost:5000/soap<br>
Заголовки:<br>
text
Content-Type: text/xml; charset=utf-8
SOAPAction: http://portrait-processor-service.ru/ProcessPortrait
Пример запроса:<br>
xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:por="http://portrait-processor-service.ru">
   <soapenv:Header/>
   <soapenv:Body>
      <por:ProcessPortrait>
         <por:image_base64>BASE64_ENCODED_IMAGE</por:image_base64>
         <por:use_background_removal>true</por:use_background_removal>
      </por:ProcessPortrait>
   </soapenv:Body>
</soapenv:Envelope>
Пример успешного ответа:<br>
xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:por="http://portrait-processor-service.ru">
   <soapenv:Body>
      <por:ProcessPortraitResponse>
         <por:result>success</por:result>
         <por:message>Изображение успешно обработано</por:message>
         <por:processed_image_base64>BASE64_ENCODED_RESULT</por:processed_image_base64>
         <por:timestamp>2024-01-01T12:00:00</por:timestamp>
      </por:ProcessPortraitResponse>
   </soapenv:Body>
</soapenv:Envelope>
Пример ответа с ошибкой:<br>
xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
      <soapenv:Fault>
         <faultcode>soapenv:Server</faultcode>
         <faultstring>Ошибка обработки: ...</faultstring>
      </soapenv:Fault>
   </soapenv:Body>
</soapenv:Envelope>
WSDL: доступен по адресу http://localhost:5000/wsdl<br>
SOAP клиент
Откройте http://localhost:5000/soap-client<br>
Загрузите изображение (до 2 МБ)<br>
При необходимости измените настройки<br>
Нажмите «Отправить SOAP запрос»<br>
Результат появится ниже, его можно скачать<br>
# 📁 Структура проекта<br>
portrait_processor_soap/<br>
├── app.py                  # Основное Flask-приложение и маршруты<br>
├── portrait_processor.py   # Логика обработки изображений<br>
├── soap_service.py         # Парсинг и генерация SOAP-сообщений<br>
├── requirements.txt        # Зависимости<br>
├── README.md               # Документация<br>
├── templates/<br>
│   ├── index.html          # Веб-интерфейс<br>
│   ├── soap_client.html    # SOAP-клиент<br>
│   └── wsdl.xml            # Шаблон WSDL<br>
└── static/<br>
    └── style.css           # Стили для веб-интерфейса
# 🧠 Описание алгоритма обработки
Загрузка изображения – из файла или base64.<br>
Детекция лица – каскады Хаара (frontal + profile). При неудаче используется центральная область.<br>
Определение кончика носа – оценка: центр лица по горизонтали, 65% высоты лица от верхней границы.<br>
Расчёт области кадрирования:<br>
Высота кадра = 2 × высота лица (лицо ~50% высоты).<br>
Ширина = высота × 0.75 (соотношение 4:3).<br>
Центрирование по кончику носа.<br>
Корректировка при выходе за границы:<br>
сверху/снизу – сдвиг к границе;<br>
слева/справа – симметричная обрезка.<br>
Добавление отступа сверху для волос (5% высоты лица).<br>
Удаление фона – с помощью rembg, если доступно.<br>
Кадрирование – вырезается рассчитанная область.<br>
Изменение размера – до 600×800 с сохранением пропорций.<br>
Улучшение качества – фильтрация, повышение резкости, контраста, насыщенности, яркости.<br>
Сохранение – в формате JPEG с высоким качеством.<br>
# ❗ Решение проблем
Ошибка 500 при отправке SOAP запроса
Проверьте логи сервера – там будут подробные сообщения об ошибках.<br>
Убедитесь, что изображение не слишком большое (для SOAP клиента ограничение 2 МБ).<br>
Проверьте, что rembg установлен корректно (если используется удаление фона).<br>
Попробуйте отправить запрос через встроенный SOAP-клиент – он выводит отладочную информацию.<br>
Убедитесь, что в soap_service.py правильно обрабатываются пространства имён.<br>
Не удаляется фон
Убедитесь, что библиотека rembg установлена: pip install rembg.<br>
При первом запуске rembg может загружать модель – это занимает время.<br>
Если rembg недоступен, фон не удаляется, но остальная обработка выполняется.<br>
Долгая обработка
Обработка может занимать 5–15 секунд в зависимости от размера изображения и наличия rembg.<br>
Для ускорения можно отключить удаление фона.<br>
Ошибки при установке rembg
rembg требует дополнительных зависимостей. Если возникают проблемы, можно временно отключить удаление фона (установите use_background_removal=False).<br>
Альтернативно используйте pip install rembg[gpu] для GPU-ускорения.<br>

# © Автор
Сорокин Александр (СПбГУ)<br>
# 📄 Лицензия
MIT License. Свободное использование, модификация и распространение.<br>
Примечание: Проект протестирован на Python 3.12. При использовании других версий возможны незначительные отличия.