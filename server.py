from dotenv import load_dotenv
from flask import Flask, jsonify
from flask.typing import ResponseReturnValue
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from bin.blueprints import api_blueprint, img_assets_blueprint, react_blueprint
from modules.account.rest_api.account_rest_api_server import AccountRestApiServer
from modules.application.application_service import ApplicationService
from modules.application.errors import AppError, WorkerClientConnectionError
from modules.application.workers.health_check_worker import HealthCheckWorker
from modules.authentication.rest_api.authentication_rest_api_server import AuthenticationRestApiServer
from modules.config.config_service import ConfigService
from modules.logger.logger import Logger
from modules.logger.logger_manager import LoggerManager

# Try to import notification components, but don't fail if they're missing
try:
    from modules.notification.rest_api.notification_rest_api_server import NotificationRestApiServer
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    Logger.warn(message="Notification module not available, skipping notification features")

load_dotenv()

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# Mount deps
LoggerManager.mount_logger()

# Connect to Temporal Server
try:
    ApplicationService.connect_temporal_server()

    # Start the health check worker
    # In production, it is optional to run this worker
    ApplicationService.schedule_worker_as_cron(cls=HealthCheckWorker, cron_schedule="*/10 * * * *")
    
    # Only start notification workers if notification module is available
    if NOTIFICATION_AVAILABLE:
        try:
            from modules.notification.workers.notification_worker import (
                NotificationCleanupWorker,
                NotificationSchedulerWorker,
            )
            
            # Start notification workers
            # Process scheduled notifications every 5 minutes
            ApplicationService.schedule_worker_as_cron(
                cls=NotificationSchedulerWorker, 
                cron_schedule="*/5 * * * *"
            )
            
            # Clean up old notifications daily at 2 AM
            ApplicationService.schedule_worker_as_cron(
                cls=NotificationCleanupWorker, 
                cron_schedule="0 2 * * *"
            )
            Logger.info(message="Notification workers started successfully")
        except ImportError:
            Logger.warn(message="Notification workers not available, skipping")

except WorkerClientConnectionError as e:
    Logger.critical(message=e.message)


# Apply ProxyFix to interpret `X-Forwarded` headers if enabled in configuration
# Visit: https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/ for more information
if ConfigService.has_value("is_server_running_behind_proxy") and ConfigService[bool].get_value(
    "is_server_running_behind_proxy"
):
    app.wsgi_app = ProxyFix(app.wsgi_app)  # type: ignore

# Register authentication apis
authentication_blueprint = AuthenticationRestApiServer.create()
api_blueprint.register_blueprint(authentication_blueprint)

# Register accounts apis
account_blueprint = AccountRestApiServer.create()
api_blueprint.register_blueprint(account_blueprint)

# Register notification apis only if available
if NOTIFICATION_AVAILABLE:
    try:
        notification_blueprint = NotificationRestApiServer.create()
        api_blueprint.register_blueprint(notification_blueprint)
        Logger.info(message="Notification REST API registered successfully")
    except Exception as e:
        Logger.error(message=f"Failed to register notification REST API: {str(e)}")

app.register_blueprint(api_blueprint)

# Register frontend elements
app.register_blueprint(img_assets_blueprint)
app.register_blueprint(react_blueprint)


@app.errorhandler(AppError)
def handle_error(exc: AppError) -> ResponseReturnValue:
    return jsonify({"message": exc.message, "code": exc.code}), exc.http_code or 500