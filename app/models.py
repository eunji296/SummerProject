from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.String(80), primary_key=True, unique=True, nullable=False) # nunique는 유일성 보장, 기본키 설정
    password = db.Column(db.String(255), nullable=False)  # 비밀번호는 해싱하여 저장
    nickname = db.Column(db.String(20), unique=True, nullable=False)

class MusicSheet(db.Model):
    __tablename__ = 'musicsheets'

    sheet_id = db.Column(db.Integer, primary_key=True)  # 기본 키로 설정
    user_id = db.Column(db.String(80), db.ForeignKey('users.user_id'), nullable=False)  # 외래 키
    pdf_url = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    composer = db.Column(db.String(20), nullable=False)
    instruments = db.Column(db.String(20), nullable=False)
    stages = db.Column(db.String(20), nullable=False)

    # 관계 설정
    user = db.relationship('User', backref='musicsheets', lazy=True)

    def to_dict_search_all(self):
        return {
            "title": self.title,
            "sheet_id": self.sheet_id
        }

    def to_dict_search_one(self):
        return {
            "instrument": self.instruments,
            "stage": self.stages,
            "pdf_url": self.pdf_url
        }

class Video(db.Model):
    __tablename__ = 'video'

    video_id = db.Column(db.Integer, primary_key=True)  # 기본 키로 설정
    sheet_id = db.Column(db.Integer, db.ForeignKey('musicsheets.sheet_id'), nullable=False)  # 외래 키
    user_id = db.Column(db.String(80), db.ForeignKey('users.user_id'), nullable=False)  # 외래 키
    video_path = db.Column(db.String(255), nullable=True)

    # 관계 설정
    music_sheet = db.relationship('MusicSheet', backref='videos', lazy=True)
    user = db.relationship('User', backref='videos', lazy=True)

    def to_dict_video(self):
        return {
            "video_path": self.video_path
        }
