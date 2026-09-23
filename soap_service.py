import xml.etree.ElementTree as ET
from datetime import datetime
import base64
import re

class SOAPService:
    """Класс для обработки SOAP запросов и ответов"""
    
    SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
    SERVICE_NS = "http://portrait-processor-service.ru"
    
    @staticmethod
    def create_soap_response(processed_image_base64, message="Изображение успешно обработано"):
        """Создание SOAP ответа"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Создаем XML
            envelope = ET.Element(f"{{{SOAPService.SOAP_NS}}}Envelope")
            envelope.set(f"xmlns:soapenv", SOAPService.SOAP_NS)
            envelope.set(f"xmlns:por", SOAPService.SERVICE_NS)
            
            body = ET.SubElement(envelope, f"{{{SOAPService.SOAP_NS}}}Body")
            
            response = ET.SubElement(body, f"{{{SOAPService.SERVICE_NS}}}ProcessPortraitResponse")
            
            result = ET.SubElement(response, f"{{{SOAPService.SERVICE_NS}}}result")
            result.text = "success"
            
            msg = ET.SubElement(response, f"{{{SOAPService.SERVICE_NS}}}message")
            msg.text = message
            
            image = ET.SubElement(response, f"{{{SOAPService.SERVICE_NS}}}processed_image_base64")
            image.text = processed_image_base64
            
            ts = ET.SubElement(response, f"{{{SOAPService.SERVICE_NS}}}timestamp")
            ts.text = timestamp
            
            xml_str = ET.tostring(envelope, encoding='utf-8', method='xml')
            return xml_str
        except Exception as e:
            print(f"Ошибка создания SOAP ответа: {str(e)}")
            raise
    
    @staticmethod
    def create_soap_fault(error_message):
        """Создание SOAP Fault ответа"""
        try:
            envelope = ET.Element(f"{{{SOAPService.SOAP_NS}}}Envelope")
            envelope.set(f"xmlns:soapenv", SOAPService.SOAP_NS)
            
            body = ET.SubElement(envelope, f"{{{SOAPService.SOAP_NS}}}Body")
            fault = ET.SubElement(body, f"{{{SOAPService.SOAP_NS}}}Fault")
            
            faultcode = ET.SubElement(fault, "faultcode")
            faultcode.text = "soapenv:Server"
            
            faultstring = ET.SubElement(fault, "faultstring")
            faultstring.text = str(error_message)
            
            detail = ET.SubElement(fault, "detail")
            detail.text = f"Ошибка обработки SOAP запроса: {error_message}"
            
            xml_str = ET.tostring(envelope, encoding='utf-8', method='xml')
            return xml_str
        except Exception as e:
            print(f"Ошибка создания SOAP Fault: {str(e)}")
            # Возвращаем простой текст в случае ошибки
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="{SOAPService.SOAP_NS}">
    <soapenv:Body>
        <soapenv:Fault>
            <faultcode>soapenv:Server</faultcode>
            <faultstring>Ошибка: {str(e)}</faultstring>
        </soapenv:Fault>
    </soapenv:Body>
</soapenv:Envelope>"""
    
    @staticmethod
    def parse_soap_request(xml_string):
        """Парсинг SOAP запроса и извлечение параметров"""
        try:
            print(f"Парсинг SOAP запроса, длина: {len(xml_string)}")
            
            # Удаляем возможные пробелы и переносы строк в начале/конце
            xml_string = xml_string.strip()
            
            # Парсим XML
            try:
                root = ET.fromstring(xml_string)
            except ET.ParseError as e:
                print(f"ParseError: {str(e)}")
                # Попробуем исправить возможные проблемы с XML
                xml_string = re.sub(r'xmlns:por="[^"]+"', f'xmlns:por="{SOAPService.SERVICE_NS}"', xml_string)
                xml_string = re.sub(r'xmlns:soapenv="[^"]+"', f'xmlns:soapenv="{SOAPService.SOAP_NS}"', xml_string)
                root = ET.fromstring(xml_string)
            
            # Регистрируем namespace для поиска
            namespaces = {
                'soapenv': SOAPService.SOAP_NS,
                'por': SOAPService.SERVICE_NS
            }
            
            # Извлекаем параметры
            image_base64 = None
            use_background_removal = True
            
            # Пытаемся найти с namespace
            for elem in root.iter():
                # Ищем image_base64
                if image_base64 is None:
                    if elem.tag.endswith('image_base64') or 'image_base64' in elem.tag:
                        if elem.text and elem.text.strip():
                            image_base64 = elem.text.strip()
                            print(f"Найден image_base64 (с namespace), длина: {len(image_base64)}")
                
                # Ищем use_background_removal
                if elem.tag.endswith('use_background_removal') or 'use_background_removal' in elem.tag:
                    if elem.text:
                        text = elem.text.strip().lower()
                        use_background_removal = text == 'true'
                        print(f"Найден use_background_removal: {use_background_removal}")
            
            # Если не нашли с namespace, пробуем без
            if not image_base64:
                # Ищем любой элемент с текстом, который похож на base64
                for elem in root.iter():
                    if elem.text and len(elem.text) > 100:  # Base64 обычно длинный
                        # Проверяем, похоже ли на base64
                        text = elem.text.strip()
                        if (len(text) % 4 == 0 and 
                            re.match(r'^[A-Za-z0-9+/]+={0,2}$', text)):
                            image_base64 = text
                            print(f"Найден возможный base64 (без namespace), длина: {len(image_base64)}")
                            break
            
            if not image_base64:
                # Для отладки выведем структуру XML
                print("Структура XML:")
                for elem in root.iter():
                    print(f"  Тег: {elem.tag}, Текст: {elem.text[:50] if elem.text else 'None'}")
                raise ValueError("Не найден параметр image_base64 в SOAP запросе")
            
            return {
                'image_base64': image_base64,
                'use_background_removal': use_background_removal
            }
            
        except Exception as e:
            print(f"Ошибка парсинга SOAP запроса: {str(e)}")
            raise ValueError(f"Ошибка обработки SOAP запроса: {str(e)}")