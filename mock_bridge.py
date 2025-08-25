#!/usr/bin/env python3
"""
Mock WhatsApp bridge server for testing MCP
"""

from flask import Flask, jsonify, request
import qrcode
import io
import base64
from datetime import datetime

app = Flask(__name__)

# Global state
connected = False
qr_code_data = "2@AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB,CCCCCCCCCCCCCCCC"

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return '', 200

@app.route('/api/status', methods=['GET'])
def status():
    """Get connection status"""
    return jsonify({
        'connected': connected,
        'phone_number': '+1234567890' if connected else None
    })

@app.route('/api/qr', methods=['GET'])
def get_qr():
    """Get QR code for authentication"""
    if connected:
        return jsonify({
            'error': 'Already connected'
        }), 400
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_code_data)
    qr.make(fit=True)
    
    # ASCII version
    ascii_qr = qr.get_matrix()
    ascii_str = ""
    for row in ascii_qr:
        for cell in row:
            ascii_str += "██" if cell else "  "
        ascii_str += "\n"
    
    # Image version
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return jsonify({
        'qr_string': qr_code_data,
        'qr_ascii': ascii_str,
        'qr_base64': f"data:image/png;base64,{img_base64}"
    })

@app.route('/api/send', methods=['POST'])
def send_message():
    """Send a message"""
    data = request.json
    if not connected:
        return jsonify({
            'success': False,
            'message': 'WhatsApp not connected'
        }), 400
    
    return jsonify({
        'success': True,
        'message': f"Message sent to {data.get('recipient')}"
    })

@app.route('/api/connect', methods=['POST'])
def connect():
    """Simulate connection (for testing)"""
    global connected
    connected = True
    return jsonify({'success': True})

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Simulate disconnection (for testing)"""
    global connected
    connected = False
    return jsonify({'success': True})

if __name__ == '__main__':
    print("Starting mock WhatsApp bridge on port 8080...")
    print("Endpoints:")
    print("  GET  /health - Health check")
    print("  GET  /api/status - Connection status")
    print("  GET  /api/qr - Get QR code")
    print("  POST /api/send - Send message")
    print("  POST /api/connect - Simulate connection")
    print("  POST /api/disconnect - Simulate disconnection")
    print("-" * 50)
    app.run(port=8080, debug=False)