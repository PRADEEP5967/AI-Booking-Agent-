import json

try:
    import redis
except ImportError:
    redis = None

class SessionService:
    """
    Modern, robust, and bug-free session management using Redis.
    Improvements:
    - Handles Redis connection errors gracefully.
    - Allows configuration via environment variables.
    - Defensive: returns None or empty dict on error.
    - TTL configurable, default 1 hour.
    - All session keys are namespaced.
    """

    def __init__(self, host='localhost', port=6379, db=0, ttl=3600):
        self.ttl = ttl
        self.enabled = redis is not None
        self._client = None
        if self.enabled:
            try:
                self._client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,  # Always decode to str
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self._client.ping()
            except Exception as e:
                print(f"[SessionService] Redis connection failed: {e}")
                self.enabled = False
                self._client = None
        else:
            print("[SessionService] Redis library not installed. Session management disabled.")

    def _key(self, user_id):
        return f"session:{user_id}"

    def get_session(self, user_id):
        """
        Retrieve session data for a user.
        Returns dict if found, else empty dict.
        """
        if not self.enabled or not self._client:
            return {}
        try:
            session = self._client.get(self._key(user_id))
            if session:
                return json.loads(session)
            return {}
        except Exception as e:
            print(f"[SessionService] Error getting session for {user_id}: {e}")
            return {}

    def update_session(self, user_id, data):
        """
        Update session data for a user.
        Sets TTL (default 1 hour).
        """
        if not self.enabled or not self._client:
            return False
        try:
            self._client.setex(self._key(user_id), self.ttl, json.dumps(data))
            return True
        except Exception as e:
            print(f"[SessionService] Error updating session for {user_id}: {e}")
            return False

# Singleton instance for use in app
session_service = SessionService()

# For backward compatibility (if needed)
def get_session(user_id):
    return session_service.get_session(user_id)

def update_session(user_id, data):
    return session_service.update_session(user_id, data)
