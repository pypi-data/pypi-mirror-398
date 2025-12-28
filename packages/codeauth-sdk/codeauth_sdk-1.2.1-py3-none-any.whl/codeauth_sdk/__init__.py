import time
import requests
from types import SimpleNamespace

class CodeAuth:
    # Private static state container
    # We use a SimpleNamespace here to hold the variables just like the JS static private fields
    _Endpoint=None
    _ProjectID=None
    _UseCache=False
    _CacheDuration=0
    _CacheExpiration=0
    _HasInitialized=False
    _CacheSession={} # Python Dictionary acts as the Map
    

    @staticmethod
    def Initialize(project_endpoint, project_id, use_cache=True, cache_duration=30):
        """
        Initialize the CodeAuth SDK

        
        :param project_endpoint: The endpoint of your project. This can be found inside your project settings.
        :param project_id: Your project ID. This can be found inside your project settings.
        :param use_cache: Whether to use cache or not. Using cache can help speed up response time and mitigate some rate limits. This will automatically cache new session token (from '/signin/emailverify', 'signin/socialverify', 'session/info', 'session/refresh') and automatically delete cache when it is invalidated (from 'session/refresh', 'session/invalidate').
        :param cache_duration: How long the cache should last. At least 15 seconds required to effectively mitigate most rate limits. Check docs for more info.
        """
        if CodeAuth._HasInitialized:
            raise Exception('CodeAuth has already been Initialized.')
        
        CodeAuth._HasInitialized = True
        CodeAuth._Endpoint = project_endpoint
        CodeAuth._ProjectID = project_id
        CodeAuth._UseCache = use_cache
        CodeAuth._CacheDuration = cache_duration * 1000 # Convert to milliseconds
        CodeAuth._CacheSession = {}
        # Python time.time() is seconds, convert to ms to match JS logic
        CodeAuth._CacheExpiration = (time.time() * 1000) + CodeAuth._CacheDuration

    # -------
    # Makes sure cache hasn't expired, if it did, delete the whole dictionary
    # -------
    @staticmethod
    def _EnsureCache():
        # make sure caching is enabled
        if not CodeAuth._UseCache:
            return

        current_time = time.time() * 1000
        
        # delete cache if cache expired
        if CodeAuth._CacheExpiration < current_time:
            # set next expiration time
            CodeAuth._CacheExpiration = current_time + CodeAuth._CacheDuration
            CodeAuth._CacheSession.clear()

    # -------
    # Makes sure that the CodeAuth SDK has been initialized
    # -------
    @staticmethod
    def _EnsureInitialized():
        if not CodeAuth._HasInitialized:
            raise Exception('CodeAuth has not been initialized.')

    # -------
    # Create api request and call server
    # -------
    @staticmethod
    def _CallApiRequest(path, body):
        try:
            # Construct URL
            base = CodeAuth._Endpoint.rstrip('/')
            clean_path = path if path.startswith('/') else f'/{path}'
            url = f"https://{base}{clean_path}"

            headers = {
                "Content-Type": "application/json"
            }

            # Call HTTP
            response = requests.post(url, json=body, headers=headers)
            
            try:
                data = response.json()
                # mimic JS logic: set .error json to 'no_error' for OK (200) response
                if response.status_code == 200:
                    data['error'] = "no_error"
                
                # Convert to SimpleNamespace for dot notation access
                return SimpleNamespace(**data)
            except ValueError:
                return SimpleNamespace(**{'error':"connection_error"})
                
        except requests.exceptions.RequestException:
            return SimpleNamespace(**{'error':"connection_error"})

    @staticmethod
    def SignInEmail(email):
        """
        Begins the sign in or register flow by sending the user a one time code via email.
        
        :param email: The email of the user you are trying to sign in/up. Email must be between 1 and 64 characters long. The email must also only contain letter, number, dot (not first, last, or consecutive), underscore(not first or last) and/or hyphen(not first or last).
        :return: A success response will return error = 'no_error'
        """
        CodeAuth._EnsureInitialized()
        CodeAuth._EnsureCache()

        return CodeAuth._CallApiRequest(
            "/signin/email",
            {
                "project_id": CodeAuth._ProjectID,
                "email": email,
            }
        )

    @staticmethod
    def SignInEmailVerify(email, code):
        """
        Checks if the one time code matches in order to create a session token.

        :param email: The email of the user you are trying to sign in/up. Email must be between 1 and 64 characters long. The email must also only contain letter, number, dot (not first, last, or consecutive), underscore(not first or last) and/or hyphen(not first or last).
        :param code: The one time code that was sent to the email.
        :return: { session_token, email, expiration, refresh_left } 
        """
        CodeAuth._EnsureInitialized()
        CodeAuth._EnsureCache()

        result = CodeAuth._CallApiRequest(
            "/signin/emailverify",
            {
                "project_id": CodeAuth._ProjectID,
                "email": email,
                "code": code
            }
        )

        # save to cache if enabled
        # We use getattr/dot notation because result is a SimpleNamespace
        if CodeAuth._UseCache and getattr(result, 'error', None) == "no_error":
            CodeAuth._CacheSession[result.session_token] = result

        return result

    @staticmethod
    def SignInSocial(social_type):
        """
        Begins the sign in or register flow by allowing users to sign in through a social OAuth2 link.
        
        :param social_type: The type of social OAuth2 url you are trying to create. Possible social types: "google", "microsoft", "apple"
        :return: { signin_url }
        """
        CodeAuth._EnsureInitialized()
        CodeAuth._EnsureCache()

        return CodeAuth._CallApiRequest(
            "/signin/social",
            {
                "project_id": CodeAuth._ProjectID,
                "social_type": social_type
            }
        )

    @staticmethod
    def SignInSocialVerify(social_type, code):
        """
        Checks the authorization code given by the social media company in order to create a session token.

        :param social_type: The type of social OAuth2 url you are trying to verify. Possible social types: "google", "microsoft", "apple"
        :param code: The authorization code given by the social. Check the docs for more info.
        :return: { session_token, email, expiration, refresh_left }
        """
        CodeAuth._EnsureInitialized()
        CodeAuth._EnsureCache()

        result = CodeAuth._CallApiRequest(
            "/signin/socialverify",
            {
                "project_id": CodeAuth._ProjectID,
                "social_type": social_type,
                "code": code
            }
        )

        if CodeAuth._UseCache and getattr(result, 'error', None) == "no_error":
            CodeAuth._CacheSession[result.session_token] = result

        return result

    @staticmethod
    def SessionInfo(session_token):
        """
        Gets the information associated with a session token.

        :param session_token: The session token you are trying to get information on.
        :return: { email, expiration, refresh_left }
        """
        CodeAuth._EnsureInitialized()
        CodeAuth._EnsureCache()

        current_time = time.time() * 1000

        # return the cached info if it is enabled, not expired and exist
        if CodeAuth._UseCache and CodeAuth._CacheExpiration > current_time:
            cache = CodeAuth._CacheSession.get(session_token)
            if cache:
                return cache

        result = CodeAuth._CallApiRequest(
            "/session/info",
            {
                "project_id": CodeAuth._ProjectID,
                "session_token": session_token
            }
        )

        if CodeAuth._UseCache and getattr(result, 'error', None) == "no_error":
            CodeAuth._CacheSession[session_token] = result

        return result

    @staticmethod
    def SessionRefresh(session_token):
        """
        Create a new session token using existing session token.
        
        :param session_token: The session token you are trying to use to create a new token.
        :return: { session_token:<string>, email:<string>, expiration:<int>, refresh_left:<int> }
        """
        CodeAuth._EnsureInitialized()
        CodeAuth._EnsureCache()

        result = CodeAuth._CallApiRequest(
            "/session/refresh",
            {
                "project_id": CodeAuth._ProjectID,
                "session_token": session_token
            }
        )

        # if cache is enabled, delete old session token cache and set the new one
        if CodeAuth._UseCache and getattr(result, 'error', None) == "no_error":
            # Delete old (if exists)
            if session_token in CodeAuth._CacheSession:
                del CodeAuth._CacheSession[session_token]
            
            # Set new
            CodeAuth._CacheSession[result.session_token] = result

        return result

    @staticmethod
    def SessionInvalidate(session_token, invalidate_type):
        """
        Invalidate a session token.

        :param session_token: The session token you are trying to use to invalidate.
        :param invalidate_type: How to use the session token to invalidate. Possible invalidate types: 'only_this', 'all', 'all_but_this'
        :return: {}
        """
        CodeAuth._EnsureInitialized()
        CodeAuth._EnsureCache()

        result = CodeAuth._CallApiRequest(
            "/session/invalidate",
            {
                "project_id": CodeAuth._ProjectID,
                "session_token": session_token,
                "invalidate_type": invalidate_type
            }
        )

        # if cache is enabled, delete the session token cache
        if CodeAuth._UseCache and getattr(result, 'error', None) == "no_error":
            if session_token in CodeAuth._CacheSession:
                del CodeAuth._CacheSession[session_token]

        return result