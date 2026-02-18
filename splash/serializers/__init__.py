from splash.env import APP_SECRET
from itsdangerous import URLSafeSerializer

previous_url_serializer = URLSafeSerializer(APP_SECRET, 'previous_url')
user_session_serializer = URLSafeSerializer(APP_SECRET, 'user_session')
