from flask import redirect, request
from flask_appbuilder.security.views import AuthDBView
from flask_appbuilder.security.views import expose
from flask_login import login_user
from airflow.www.security import FabAirflowSecurityManagerOverride
from dataflow.dataflow import Dataflow
import logging, os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

dataflow = Dataflow()

class DataflowAuthDBView(AuthDBView):    
    @expose('/login/', methods=['GET', 'POST'])
    def login(self):

        """This method checks for a 'dataflow_session' cookie, retrieves user details from Dataflow,
        and logs in or creates the user in Airflow accordingly. 
        If the cookie is not present, it falls back to the standard login process.
        
        Overrides the default login method to integrate with Dataflow authentication.
        """

        try:
            session_id = request.cookies.get('dataflow_session')
            if not session_id:
                logger.info("No session cookie found, falling back to standard login.")
                return super().login()
            
            user_details = dataflow.auth(session_id)
            logger.info(f"User details retrieved for: {user_details['user_name']}")
            user = self.appbuilder.sm.find_user(username=user_details['user_name'])
            if user:
                logger.info(f"User found: {user}")
                login_user(user, remember=False)
            else:
                user = self.appbuilder.sm.add_user(
                    username=user_details['user_name'], 
                    first_name=user_details.get("first_name", ""),
                    last_name=user_details.get("last_name", ""), 
                    email=user_details.get("email", ""), 
                    role=self.appbuilder.sm.find_role(user_details.get("base_role", "user").title())
                )
                logger.info(f"New user created: {user}")
                if user:
                    login_user(user, remember=False)
            
            return redirect(self.appbuilder.get_url_for_index)

        except Exception as e:
            logger.critical(f"Login failed: {e}", exc_info=True, extra={"status_code": 500, "user": os.getenv("HOSTNAME", "unknown"), "organization": os.getenv("ORGANIZATION", "unknown"), "slug": os.getenv("SLUG", "unknown"), "runtime": os.getenv("RUNTIME", "unknown")})
            return super().login()

class DataflowAirflowAuthenticator(FabAirflowSecurityManagerOverride):
    
    """Custom Security Manager to integrate Airflow authentication with Dataflow."""
    
    authdbview = DataflowAuthDBView
    
    def __init__(self, appbuilder):
        super().__init__(appbuilder)
