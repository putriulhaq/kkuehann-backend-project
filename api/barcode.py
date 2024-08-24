# from fastapi import FastAPI, HTTPException
# from fastapi.responses import JSONResponse
# import uvicorn
from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app, Blueprint
import psycopg2 
from flask_restx import Namespace, Resource
# from .db import pool
import qrcode
import time
from datetime import datetime
import jwt
# import requests
import uuid
from werkzeug.exceptions import HTTPException
# from fastapi.responses import FileResponse

secret_key = 'isthisabsenceforstudent'
algorithm = 'HS256'

barcode = Namespace('barcode', description='Barcode Namespace')


# @barcode = Namespace('users', description='User Namespace').get("/hello-world")
# def hello_world():
#     return {"message": jadwal}

# Endpoint untuk memulai sesi absensi
@barcode.route('/start-session')
class Session(Resource):
    def get():
        session_id = str(uuid.uuid4())  # Generate a unique session ID
        start_time = time.time()  # Timestamp saat sesi dimulai

        # Simpan session_id ke database atau memori di sini
        print(session_id)

        return {"session_id": session_id, "start_time": start_time}
# <int:menu_id>
@barcode.route('/generate-code/<session_id>')
class GenerateBarcode(Resource):
    def get(session_id):
    # 8b6c17fc-bee6-4eaa-8636-a946bf851999
        jadwal = {
            "nama_matkul":"Pencitraan",
            "dosen_matkul":"Winang",
            "ruang_matkul":"2AB",
            "datetime": datetime.now().isoformat()
        }
        payload = {
                    "session_id": session_id,
                    "jadwal" :jadwal,
                    "exp": time.time() + 30
                }
        
        barcode_token = jwt.encode(payload, secret_key, algorithm="HS256")
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(barcode_token)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        filename = f"./data/qrcode/qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img.save(filename)
        return jsonify(content={
            "filename": filename,
            "token": barcode_token
        })

@barcode.route("/validate-barcode/<token>")
class ValidateBarcode(Resource):
    def get(token):
        try:
            # Decode the JWT token
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            jadwal = payload.get("jadwal")
            exp = payload.get("exp")

            # Cek apakah token sudah kedaluwarsa
            if exp < time.time():
                raise HTTPException(status_code=400, detail="Barcode expired")

            # Jika valid, kembalikan session_id atau informasi lainnya
            return {"message": "Barcode is valid", "jadwal": jadwal}

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="Barcode expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=400, detail="Invalid barcode")