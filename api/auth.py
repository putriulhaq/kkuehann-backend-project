from flask import Flask, request, jsonify, current_app, Blueprint
from flask_restx import Namespace, Resource, fields
import psycopg2
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from .db import pool
import jwt
import os
import datetime


auth = Namespace("auth", description= "auth's APIS Namespace")


user_model = auth.model('User', {
    'username': fields.String(required=True, description='User username'),
    'password': fields.String(required=True, description='User password'),
    'email': fields.String(required=True, description='User email')
})

# Model for user login
login_model = auth.model('Login', {
    'username': fields.String(required=True, description='User username'),
    'password': fields.String(required=True, description='User password')
})

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]
        
        if not token:
            return {'message': 'Token is missing.'}, 401

        try:
            # Here you would typically decode and verify the token
            # For simplicity, we're just checking if it's not None
            if token is None:
                raise ValueError('Invalid token')
        except:
            return {'message': 'Token is invalid.'}, 401

        return f(*args, **kwargs)
    return decorated

@auth.route("/register")
class Register(Resource):
    @auth.expect(user_model)
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not username or not password or not email:
            return {"message": "Missing required fields"}, 400

        hashed_password = generate_password_hash(password)
        print(hashed_password)

        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        try:
            cur.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                        (username, hashed_password, email))
            conn.commit()
            return {"message": "User registered successfully"}, 201
        except psycopg2.IntegrityError:
            conn.rollback()
            return {"message": "Username or email already exists"}, 409
        finally:
            cur.close()
            conn.close()

@auth.route('/login')
class Login(Resource):
    @auth.expect(login_model)
    def post (self):
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {"message": "Missing username or password"}, 400
        
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        try: 
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            payload = {
                "user_id": user['user_id'],
                "username": user['username'],
                "exp": datetime.timedelta(minutes=30)
            }
            
            if user and check_password_hash(user["password"], password):
                token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm="HS256")
                return {"message": "login succesfull", "token": token}, 201
            else:
                return {"message": "invalid name or username"}
        finally:
            cur.close()
            conn.close()


@auth.route("/logout")
class Logout(Resource):
    @token_required
    def post(self):
        # Here you would typically invalidate the token
        # For simplicity, we're just returning a success message
        return {"message": "Logged out successfully"}, 200

@auth.route("/protected")
class ProtectedResource(Resource):
    @token_required
    def get(self):
        return {"message": "This is a protected resource"}, 200
        