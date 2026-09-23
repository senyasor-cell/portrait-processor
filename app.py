import os
import base64
import tempfile
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file, Response
from portrait_processor import PortraitProcessorJPG
from soap_service import SOAPService

# Инициализация Flask приложения
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Инициализация процессора
processor = PortraitProcessorJPG()

# ==================== Flask Routes ====================

@app.route('/')
def index():
    """Главная страница с веб-интерфейсом"""
    return render_template('index.html')

@app.route('/soap-client')
def soap_client():
    """Страница SOAP клиента"""
    return render_template('soap_client.html')

@app.route('/wsdl')
def get_wsdl():
    """Получение WSDL файла"""
    try:
        with open('templates/wsdl.xml', 'r', encoding='utf-8') as f:
            wsdl_content = f.read()
        
        # Заменяем переменные в WSDL
        host = request.host_url.rstrip('/')
        wsdl_content = wsdl_content.replace('{{HOST}}', host)
        
        return Response(wsdl_content, mimetype='application/xml')
    
    except Exception as e:
        return f"Ошибка загрузки WSDL: {str(e)}", 500

@app.route('/upload', methods=['POST'])
def upload_image():
    """Обработка загрузки изображения через веб-интерфейс"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Нет файла в запросе'}), 400
        
        file = request.files['image']
        use_background_removal = request.form.get('use_background_removal', 'true').lower() == 'true'
        
        if file.filename == '':
            return jsonify({'error': 'Не выбран файл'}), 400
        
        # Проверяем расширение файла
        allowed_extensions = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'error': 'Неподдерживаемый формат файла'}), 400
        
        # Читаем файл
        image_bytes = file.read()
        
        # Обрабатываем изображение
        processed_bytes = processor.process_image_bytes(
            image_bytes, 
            use_background_removal=use_background_removal
        )
        
        # Сохраняем временный файл для скачивания
        temp_dir = tempfile.gettempdir()
        output_filename = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        output_path = os.path.join(temp_dir, output_filename)
        
        with open(output_path, 'wb') as f:
            f.write(processed_bytes)
        
        # Конвертируем в base64 для отображения в браузере
        processed_base64 = base64.b64encode(processed_bytes).decode('utf-8')
        
        return jsonify({
            'success': True,
            'message': 'Изображение успешно обработано',
            'processed_image': f'data:image/jpeg;base64,{processed_base64}',
            'download_url': f'/download/{output_filename}',
            'filename': output_filename
        })
        
    except Exception as e:
        print(f"Ошибка при обработке изображения: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка обработки: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Скачивание обработанного файла"""
    try:
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Файл не найден'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"processed_portrait_{filename}",
            mimetype='image/jpeg'
        )
        
    except Exception as e:
        return jsonify({'error': f'Ошибка скачивания: {str(e)}'}), 500

@app.route('/soap', methods=['POST'])
def soap_service():
    """SOAP веб-сервис для обработки портретов"""
    try:
        print("=" * 60)
        print("SOAP запрос получен")
        print(f"Content-Type: {request.headers.get('Content-Type')}")
        print(f"Content-Length: {request.headers.get('Content-Length')}")
        print(f"SOAPAction: {request.headers.get('SOAPAction')}")
        
        # Получаем XML из запроса
        xml_data = request.data
        if not xml_data:
            return Response(SOAPService.create_soap_fault("Пустой SOAP запрос"), 
                          status=400, mimetype='text/xml')
        
        try:
            xml_string = xml_data.decode('utf-8')
        except UnicodeDecodeError:
            xml_string = xml_data.decode('latin-1')
        
        print(f"XML (первые 1000 символов): {xml_string[:1000]}")
        
        # Парсим SOAP запрос
        try:
            params = SOAPService.parse_soap_request(xml_string)
        except Exception as e:
            print(f"Ошибка парсинга SOAP: {str(e)}")
            return Response(SOAPService.create_soap_fault(f"Ошибка парсинга SOAP: {str(e)}"), 
                          status=400, mimetype='text/xml')
        
        print(f"Извлечены параметры: use_background_removal={params['use_background_removal']}")
        print(f"Длина base64: {len(params['image_base64'])}")
        
        # Декодируем base64 изображение
        try:
            image_bytes = base64.b64decode(params['image_base64'])
            print(f"Длина декодированных байтов: {len(image_bytes)}")
        except Exception as e:
            print(f"Ошибка декодирования base64: {str(e)}")
            return Response(SOAPService.create_soap_fault(f"Ошибка декодирования base64: {str(e)}"), 
                          status=400, mimetype='text/xml')
        
        # Обрабатываем изображение
        try:
            processed_bytes = processor.process_image_bytes(
                image_bytes, 
                use_background_removal=params['use_background_removal']
            )
            print(f"Длина обработанных байтов: {len(processed_bytes)}")
        except Exception as e:
            print(f"Ошибка обработки изображения: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(SOAPService.create_soap_fault(f"Ошибка обработки изображения: {str(e)}"), 
                          status=500, mimetype='text/xml')
        
        # Кодируем результат в base64
        processed_base64 = base64.b64encode(processed_bytes).decode('utf-8')
        
        # Создаем SOAP ответ
        soap_response = SOAPService.create_soap_response(processed_base64)
        
        print("SOAP ответ успешно сгенерирован")
        print("=" * 60)
        
        return Response(soap_response, mimetype='text/xml')
        
    except Exception as e:
        print(f"Необработанная ошибка в SOAP сервисе: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(SOAPService.create_soap_fault(f"Внутренняя ошибка сервера: {str(e)}"), 
                      status=500, mimetype='text/xml')

@app.route('/health')
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'healthy',
        'service': 'Portrait Processor SOAP Service',
        'timestamp': datetime.now().isoformat(),
        'rembg_available': processor.rembg_available,
        'endpoints': {
            'web_interface': '/',
            'soap_service': '/soap',
            'wsdl': '/wsdl',
            'soap_client': '/soap-client',
            'health_check': '/health'
        }
    })

# ==================== Main Entry Point ====================

if __name__ == '__main__':
    print("=" * 60)
    print("SOAP Portrait Processor Service")
    print("=" * 60)
    print(f"SOAP endpoint: http://localhost:5000/soap")
    print(f"WSDL: http://localhost:5000/wsdl")
    print(f"Web interface: http://localhost:5000/")
    print(f"SOAP client: http://localhost:5000/soap-client")
    print(f"Health check: http://localhost:5000/health")
    print("=" * 60)
    
    # Создаем необходимые папки
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Используем waitress для продакшн-сервера
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)