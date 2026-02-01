from flask import Flask

def create_app():
    app = Flask(__name__)

    app.secret_key="sourav"
    # Import blueprints
    from app.routes.home import home_bp,document_bp
    from app.routes.file_upload import file_page
    from app.routes.file_upload import eda
    
    # later:
    # from app.routes.upload import upload_bp
    # from app.routes.eda import eda_bp

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(file_page)
    app.register_blueprint(eda)
    # app.register_blueprint(upload_bp)
    # app.register_blueprint(eda_bp)

    return app
