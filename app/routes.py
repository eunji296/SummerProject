import random
from datetime import timedelta
from flask import Blueprint, jsonify, request, abort
from tasks.klang_api import upload_to_klang, download_xml
from app.models import db, User, MusicSheet, Video
from app.redis import access_token, refresh_token, verify_refresh_token, verify_access_token, delete_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from tasks.stage import *
from tasks.mysql import save_to_database
from tasks.cleanup import cleanup_file
from tasks.video import save_video
from flask_cors import CORS
import os

api = Blueprint('api', __name__)

# CORS 설정 (모든 API에 적용)
CORS(api, resources={r"/*": {"origins": ["https://notanova.vercel.app"]}}, supports_credentials=True)

@api.route('/')
def index():
    return "Hello, Flask!"

# 회원가입
@api.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')
    nickname = data.get('nickname')

    if not user_id or not password or not nickname:
        return jsonify({"error": "User ID, password, and nickname are required"}), 400

    # 중복 확인
    if User.query.filter_by(user_id=user_id).first() or User.query.filter_by(nickname=nickname).first():
        return jsonify({"error": "User ID or nickname already exists"}), 400

    # 비밀번호 해싱 및 사용자 저장
    hashed_password = generate_password_hash(password)
    new_user = User(user_id=user_id, password=hashed_password, nickname=nickname)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# 로그인
@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')

    if not user_id or not password:
        return jsonify({"error": "User ID and password are required"}), 400

    # 사용자 인증
    user = User.query.filter_by(user_id=user_id).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # 토큰 생성
    access_token_value = access_token(user_id)
    refresh_token_value = refresh_token(user_id)

    print(f"Access Token: {access_token_value}")  # 로그 추가
    print(f"Refresh Token: {refresh_token_value}")  # 로그 추가

    # 응답에 Refresh Token을 HTTP-only 쿠키로 설정
    response = jsonify({
        "user_id": user_id,
        "nickname": user.nickname,
        "message": "Login successful",
        "access_token": access_token_value
    })

    # refresh_token을 HTTP-only 쿠키에 저장
    response.set_cookie(
        'refresh_token',
        refresh_token_value,
        samesite='None',
        secure=True,
        path='/',
        httponly=True
    )
    print(f"Set cookies: {response.headers.get('Set-Cookie')}")  # 쿠키 설정 로그 추가

    return response, 200

# 새 Access Token 발급
@api.route('/refresh', methods=['POST'])
def refresh_access_token():
    # 클라이언트에서 Refresh Token을 받아옴
    get_refresh_token = request.cookies.get('refresh_token')
    print(f"Received cookies: {request.cookies}")  # 모든 쿠키 로그 출력
    print(f"Extracted refresh_token: {get_refresh_token}")  # 특정 토큰 로그 출력

    # Refresh Token 검증
    user_id = verify_refresh_token(get_refresh_token)
    if not user_id:
        print("Invalid or expired refresh token")
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    # 새 Access Token 생성
    new_access_token = access_token(user_id)
    return jsonify({"access_token": new_access_token}), 200

# 로그아웃
@api.route('/logout', methods=['POST'])
def logout():
    refresh_token_value = request.cookies.get('refresh_token')

    if not refresh_token_value:
        return jsonify({"error": "Refresh token is required"}), 400

    user_id = verify_refresh_token(refresh_token_value)
    if not user_id:
        return jsonify({"error": "Invalid or expired token"}), 401

    # Redis에서 Refresh Token 삭제
    delete_refresh_token(user_id)

    # 쿠키에서 refresh_token 삭제
    response = jsonify({"message": "Logout successful"})
    response.delete_cookie('refresh_token', path='/')

    return response, 200
