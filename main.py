#!/usr/bin/env python3
"""
API Service - Quizizz Answers Bypass
Servicio web que recibe room code y devuelve respuestas usando IP rotation bypass
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import time
import logging
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)  # Permitir CORS para uso desde navegadores

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuizAnswersBypass:
    def __init__(self):
        self.base_url = "https://api.cheatnetwork.eu/quizizz"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
    def generate_random_ip(self):
        """Genera una IP privada aleatoria"""
        private_ranges = [
            lambda: f"192.168.{random.randint(1,255)}.{random.randint(1,254)}",
            lambda: f"10.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,254)}",
            lambda: f"172.{random.randint(16,31)}.{random.randint(1,255)}.{random.randint(1,254)}",
        ]
        return random.choice(private_ranges)()
    
    def make_bypass_request(self, room_code, ip_address):
        """Hace una petición con bypass de IP específica"""
        url = f"{self.base_url}/{room_code}/answers"
        headers = {
            'X-Forwarded-For': ip_address,
            'X-Request-ID': f'req_{int(time.time())}_{random.randint(1000,9999)}'
        }
        
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') == True and 'answers' in data:
                    return {
                        'success': True,
                        'data': data,
                        'ip_used': ip_address,
                        'answers_count': len(data.get('answers', [])),
                        'status_code': response.status_code
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('message', 'API returned false'),
                        'ip_used': ip_address,
                        'status_code': response.status_code,
                        'api_response': data
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'ip_used': ip_address,
                    'status_code': response.status_code,
                    'content': response.text[:200]
                }
                
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'ip_used': ip_address,
                'status_code': None
            }
    
    def get_answers(self, room_code, max_attempts=15):
        """Obtiene respuestas usando rotación de IP hasta encontrar una exitosa"""
        logger.info(f"Iniciando bypass para room code: {room_code}")
        
        for attempt in range(1, max_attempts + 1):
            ip_address = self.generate_random_ip()
            logger.info(f"Intento {attempt}/{max_attempts} con IP: {ip_address}")
            
            result = self.make_bypass_request(room_code, ip_address)
            
            if result['success']:
                logger.info(f"¡Éxito! IP {ip_address} obtuvo {result['answers_count']} respuestas")
                return {
                    'success': True,
                    'room_code': room_code,
                    'answers': result['data']['answers'],
                    'metadata': {
                        'ip_used': ip_address,
                        'attempts_needed': attempt,
                        'total_answers': result['answers_count'],
                        'room_hash': result['data'].get('roomHash'),
                        'game_state': result['data'].get('gameState'),
                        'game_type': result['data'].get('gameType'),
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                logger.warning(f"Fallo con IP {ip_address}: {result['error']}")
                if attempt < max_attempts:
                    time.sleep(1)  # Pausa entre intentos
        
        logger.error(f"No se pudo obtener respuestas después de {max_attempts} intentos")
        return {
            'success': False,
            'room_code': room_code,
            'error': f'Could not get answers after {max_attempts} IP attempts',
            'attempts_made': max_attempts,
            'timestamp': datetime.now().isoformat()
        }

# Instancia global del bypass service
bypass_service = QuizAnswersBypass()

@app.route('/')
def home():
    """Endpoint de información del servicio"""
    return jsonify({
        'service': 'Quizizz Answers API',
        'version': '1.0',
        'description': 'API service for retrieving quiz answers using IP bypass',
        'endpoints': {
            'GET /': 'Service information',
            'GET /answers/<room_code>': 'Get answers for room code',
            'POST /answers': 'Get answers via POST with room_code in body'
        },
        'usage': {
            'GET': '/answers/4656829',
            'POST': '{"room_code": "4656829"}'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/answers/<room_code>', methods=['GET'])
def get_answers_get(room_code):
    """GET endpoint - recibe room code como parámetro URL"""
    if not room_code or not room_code.strip():
        return jsonify({
            'success': False,
            'error': 'Room code is required',
            'timestamp': datetime.now().isoformat()
        }), 400
    
    room_code = room_code.strip()
    logger.info(f"GET request for room code: {room_code}")
    
    try:
        result = bypass_service.get_answers(room_code)
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error processing GET request: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'room_code': room_code,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/answers', methods=['POST'])
def get_answers_post():
    """POST endpoint - recibe room code en el body JSON"""
    try:
        data = request.get_json()
        
        if not data or 'room_code' not in data:
            return jsonify({
                'success': False,
                'error': 'room_code is required in request body',
                'example': {'room_code': '4656829'},
                'timestamp': datetime.now().isoformat()
            }), 400
        
        room_code = str(data['room_code']).strip()
        
        if not room_code:
            return jsonify({
                'success': False,
                'error': 'room_code cannot be empty',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        logger.info(f"POST request for room code: {room_code}")
        
        result = bypass_service.get_answers(room_code)
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error processing POST request: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Quizizz Answers API',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': ['/answers/<room_code>', '/answers (POST)', '/', '/health'],
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'timestamp': datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    import os
    print("🚀 Iniciando Quizizz Answers API Service")
    print("⚠️  Para uso en testing de seguridad autorizado")
    print("📡 Servicio web con bypass automático de IP")
    print()
    print("📋 Endpoints disponibles:")
    print("  GET  /                     - Información del servicio")
    print("  GET  /answers/<room_code>  - Obtener respuestas (GET)")
    print("  POST /answers              - Obtener respuestas (POST)")
    print("  GET  /health               - Health check")
    print()
    print("🔓 Servicio iniciando...")
    print("=" * 60)
    
    # Ejecutar servidor Flask (para desarrollo local)
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )
