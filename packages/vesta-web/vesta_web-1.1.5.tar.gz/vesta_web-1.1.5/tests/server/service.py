import threading
import requests
from os.path import abspath, dirname
import time


from vesta.http import baseServer as server
from vesta import HTTPError, HTTPRedirect


TEST_PORT = 9999
TEST_HOST = '127.0.0.1'


class TestServer(server.BaseServer):
    features = {}

    @server.BaseServer.expose
    def index(self):
        """root Endpoint"""
        return "<h1>Test OK</h1>"

    @server.BaseServer.expose
    def api_ping(self):
        """simple test Endpoint"""
        return "pong"

    @server.BaseServer.expose
    def api_echo(self, message=""):
        """message return Endpoint"""
        return f"echo: {message}"

    @server.BaseServer.expose
    def api_json(self):
        """Endpoint that return JSON"""
        self.response.type = "json"
        self.response.headers = [('Content-Type', 'application/json; charset=utf-8')]
        return '{"status": "ok", "message": "test"}'

    @server.BaseServer.expose
    def api_params(self, name="", age="0", city=""):
        """Endpoint with multiple parameters"""
        return f"name={name}, age={age}, city={city}"

    @server.BaseServer.expose
    def api_error(self):
        """Endpoint that raises an error"""
        raise ValueError("This is a test error")

    @server.BaseServer.expose
    def api_redirect(self):
        """Endpoint that redirects"""
        raise HTTPRedirect(self.response, "/")

    @server.BaseServer.expose
    def api_http_error(self):
        """Endpoint that raises an HTTP error"""
        raise HTTPError(self.response, 403, "Forbidden")

    @server.BaseServer.expose
    def api_custom_headers(self):
        """Endpoint with custom headers"""
        self.response.headers = [
            ('X-Custom-Header', 'test-value'),
            ('Content-Type', 'text/plain; charset=utf-8')
        ]
        return "Custom headers response"

    @server.BaseServer.expose
    def api_empty(self):
        """Endpoint that returns nothing"""
        return ""

    @server.BaseServer.expose
    def api_html(self):
        """Endpoint that returns HTML"""
        self.response.type = "html"
        self.response.headers = [('Content-Type', 'text/html; charset=utf-8')]
        return "<html><body><h1>HTML Response</h1></body></html>"

    @server.BaseServer.expose
    def api_cookies(self):
        """Endpoint that reads cookies"""
        cookies = self.response.cookies
        if cookies:
            return f"cookies: {str(cookies)}"
        return "no cookies"

    @server.BaseServer.expose
    def api_post_json(self, data="", value=""):
        """Endpoint that receives JSON POST data"""
        return f"received: data={data}, value={value}"

    @server.BaseServer.expose
    def api_delete(self):
        """Endpoint for DELETE method"""
        return "deleted"

    @server.BaseServer.expose
    def api_special_chars(self, text=""):
        """Endpoint that handles special characters"""
        print(f"[DEBUG api_special_chars] Received text param: {repr(text)}")
        return f"text: {text}"

    @server.BaseServer.expose
    def api_multiple_query(self, param1="", param2="", param3=""):
        """Endpoint with many query parameters"""
        return f"p1={param1}, p2={param2}, p3={param3}"

    @server.BaseServer.expose
    def api_numeric(self, number="0"):
        """Endpoint that handles numeric parameters"""
        try:
            num = int(number)
            return f"number squared: {num * num}"
        except ValueError:
            return "invalid number"

    @server.BaseServer.expose
    def api_long_response(self):
        """Endpoint that returns a long response"""
        return "x" * 10000

    @server.BaseServer.expose
    def api_unicode(self, text=""):
        """Endpoint that handles unicode characters"""
        return f"unicode: {text}"

    @server.BaseServer.expose
    def api_query_array(self, items=""):
        """Endpoint that handles array-like query parameters"""
        return f"items: {items}"

    @server.BaseServer.expose
    def api_set_cookie(self):
        """Endpoint that sets a cookie"""
        self.response.headers = [
            ('Set-Cookie', 'test_cookie=test_value; Path=/'),
            ('Content-Type', 'text/plain; charset=utf-8')
        ]
        return "cookie set"

    @server.BaseServer.expose
    def api_case_sensitive(self):
        """Endpoint to test case sensitivity"""
        return "case_sensitive_ok"

    @server.BaseServer.expose
    def api_mixed_params(self, id="", name="", active="false"):
        """Endpoint with mixed parameter types"""
        return f"id={id}, name={name}, active={active}"

    @server.BaseServer.expose
    def api_boolean(self, enabled=""):
        """Endpoint with boolean-like parameters"""
        return f"enabled={enabled}"

    @server.BaseServer.expose
    def api_nested_path_like(self):
        """Endpoint with underscore simulating nested path"""
        return "nested_ok"

    @server.BaseServer.expose
    def api_upload_file(self):
        """Endpoint that handles file upload"""
        try:
            # Simuler un upload de fichier en recevant du contenu base64
            import multipart as mp
            from io import BytesIO

            # On va recevoir le fichier dans la requête
            return "file_upload_endpoint_ready"
        except Exception as e:
            return f"error: {str(e)}"

    @server.BaseServer.expose
    def api_save_file(self, file_data="", filename="", ext=""):
        """Endpoint that saves an uploaded file using saveFile method"""
        try:
            if not file_data:
                return "error: no file data"

            # Utiliser la méthode saveFile du serveur
            saved_path = self.saveFile(content=file_data, name=filename, ext=ext)
            return f"saved: {saved_path}"
        except Exception as e:
            return f"error: {str(e)}"

    @server.BaseServer.expose
    def api_cookies_multiple(self):
        """Endpoint that reads multiple cookies"""
        cookies = self.response.cookies
        if not cookies:
            return "no cookies"

        # Retourner tous les cookies sous forme de string
        cookie_list = [f"{k}={v}" for k, v in cookies.items()]
        return f"cookies: {', '.join(cookie_list)}"

    @server.BaseServer.expose
    def api_cookies_specific(self, cookie_name=""):
        """Endpoint that reads a specific cookie by name"""
        cookies = self.response.cookies
        if not cookies:
            return "no cookies"

        if cookie_name in cookies:
            return f"cookie {cookie_name}={cookies[cookie_name]}"
        else:
            return f"cookie {cookie_name} not found"

    @server.BaseServer.expose
    def api_set_multiple_cookies(self):
        """Endpoint that sets multiple cookies"""
        self.response.headers = [
            ('Set-Cookie', 'cookie1=value1; Path=/'),
            ('Set-Cookie', 'cookie2=value2; Path=/'),
            ('Set-Cookie', 'cookie3=value3; Path=/; HttpOnly'),
            ('Content-Type', 'text/plain; charset=utf-8')
        ]
        return "multiple cookies set"

    @server.BaseServer.expose
    def api_upload_validate(self, file_data="", expected_ext=""):
        """Endpoint that validates file extension"""
        try:
            if not file_data:
                return "error: no file data"

            # Extraire l'extension du header base64
            header = file_data.split(",")[0]
            mime_type = header.split("/")[1].split(";")[0]

            if expected_ext and mime_type != expected_ext:
                return f"error: extension mismatch, expected {expected_ext}, got {mime_type}"

            return f"valid: {mime_type}"
        except Exception as e:
            return f"error: {str(e)}"

    @server.BaseServer.expose
    def api_sanitize_filename(self, filename=""):
        """Endpoint that sanitizes a filename"""
        try:
            sanitized = self._sanitize_filename(filename)
            return f"sanitized: {sanitized}"
        except Exception as e:
            return f"error: {str(e)}"


#run a server for testing in a separate thread
TEST_SERVER_URL = f'http://{TEST_HOST}:{TEST_PORT}'

def start_test_server():
    PATH = dirname(abspath(__file__))

    # Start the test server in a separate thread but output its logs to the main thread
    server_thread = threading.Thread(target=lambda: TestServer(path=PATH, configFile="/../server.ini"))
    server_thread.setDaemon(True)
    server_thread.start()


def run():
    print("Starting test server...")
    start_test_server()
    time.sleep(1)  # Give the server a moment to start
    print("Running tests...")

    resList = []
    resList.append(test_server_starts())
    resList.append(test_index_endpoint())
    resList.append(test_ping_endpoint())
    resList.append(test_echo_endpoint())
    resList.append(test_json_endpoint())
    resList.append(test_404_endpoint())
    resList.append(test_params_endpoint())
    resList.append(test_params_partial_endpoint())
    resList.append(test_error_endpoint())
    resList.append(test_redirect_endpoint())
    resList.append(test_http_error_endpoint())
    resList.append(test_custom_headers_endpoint())
    resList.append(test_empty_endpoint())
    resList.append(test_html_endpoint())
    resList.append(test_method_post())
    resList.append(test_method_put())
    resList.append(test_method_delete())
    resList.append(test_cookies_endpoint())
    resList.append(test_post_json_endpoint())
    resList.append(test_special_chars_endpoint())
    resList.append(test_multiple_query_params())
    resList.append(test_numeric_endpoint())
    resList.append(test_numeric_invalid_endpoint())
    resList.append(test_echo_empty_message())
    resList.append(test_redirect_followed())
    resList.append(test_long_response())
    resList.append(test_unicode_endpoint())
    resList.append(test_set_cookie_endpoint())
    resList.append(test_case_sensitive_endpoint())
    resList.append(test_mixed_params_endpoint())
    resList.append(test_boolean_endpoint())
    resList.append(test_nested_path_like())
    resList.append(test_concurrent_requests())
    resList.append(test_zero_params())
    resList.append(test_negative_number())

    # Tests pour les cookies
    resList.append(test_cookies_multiple())
    resList.append(test_cookies_specific())
    resList.append(test_set_multiple_cookies())
    resList.append(test_cookies_with_special_chars())

    # Tests pour l'upload de fichiers
    resList.append(test_upload_file_endpoint())
    resList.append(test_save_file_png())
    resList.append(test_save_file_with_custom_name())
    resList.append(test_upload_validate_extension())
    resList.append(test_sanitize_filename())
    resList.append(test_sanitize_filename_dangerous())

    return resList


def test_server_starts():
    """Test que le serveur démarre correctement"""
    response = requests.get(TEST_SERVER_URL)
    return ("test server starts", response.status_code == 200)


def test_index_endpoint():
    """Test de l'endpoint racine"""
    response = requests.get(f'{TEST_SERVER_URL}/')
    if not response.status_code == 200:
        return ("test index endpoint: bad status code", False)
    if not 'Test OK' in response.text:
        return ("test index endpoint: bad content", False)
    return ("test index endpoint", True)


def test_ping_endpoint():
    """Test de l'endpoint /api_ping"""
    response = requests.get(f'{TEST_SERVER_URL}/api_ping')
    if not response.status_code == 200:
        return ("test ping endpoint: bad status code", False)
    if not 'pong' == response.text:
        return ("test ping endpoint: bad content", False)
    return ("test ping endpoint", True)


def test_echo_endpoint():
    """Test de l'endpoint /api_echo avec paramètre"""
    message = "Hello World"
    response = requests.get(f'{TEST_SERVER_URL}/api_echo?message={message}')
    if not response.status_code == 200:
        return ("test echo endpoint: bad status code", False)
    if not f'echo: {message}' == response.text:
        return ("test echo endpoint: bad content", False)
    return ("test echo endpoint", True)



def test_json_endpoint():
    """Test de l'endpoint qui retourne du JSON"""
    response = requests.get(f'{TEST_SERVER_URL}/api_json')

    if not response.status_code == 200:
        return ("test json endpoint: bad status code", False)
    if not 'application/json' in response.headers.get('Content-Type', ''):
        return ("test json endpoint: bad content type", False)
    data = response.json()
    if not data['status'] == 'ok' or not data['message'] == 'test':
        return ("test json endpoint: bad json content", False)
    return ("test json endpoint", True)



def test_404_endpoint():
    """Test qu'un endpoint inexistant retourne 404"""
    response = requests.get(f'{TEST_SERVER_URL}/nonexistent')
    if not response.status_code == 404:
        return ("test 404 endpoint: bad status code", False)
    return ("test 404 endpoint", True)


def test_params_endpoint():
    """Test de l'endpoint avec multiples paramètres"""
    response = requests.get(f'{TEST_SERVER_URL}/api_params?name=John&age=30&city=Paris')
    if not response.status_code == 200:
        return ("test params endpoint: bad status code", False)
    expected = "name=John, age=30, city=Paris"
    if not expected == response.text:
        return ("test params endpoint: bad content", False)
    return ("test params endpoint", True)


def test_params_partial_endpoint():
    """Test de l'endpoint avec seulement certains paramètres"""
    response = requests.get(f'{TEST_SERVER_URL}/api_params?name=Alice')
    if not response.status_code == 200:
        return ("test params partial endpoint: bad status code", False)
    expected = "name=Alice, age=0, city="
    if not expected == response.text:
        return ("test params partial endpoint: bad content", False)
    return ("test params partial endpoint", True)


def test_error_endpoint():
    """Test de l'endpoint qui lève une erreur"""
    response = requests.get(f'{TEST_SERVER_URL}/api_error')
    if not response.status_code == 500:
        return ("test error endpoint: bad status code", False)
    if not 'This is a test error' in response.text:
        return ("test error endpoint: error message not found", False)
    return ("test error endpoint", True)


def test_redirect_endpoint():
    """Test de l'endpoint qui redirige"""
    response = requests.get(f'{TEST_SERVER_URL}/api_redirect', allow_redirects=False)
    if not response.status_code == 302:
        return ("test redirect endpoint: bad status code", False)
    if not response.headers.get('Location') == '/':
        return ("test redirect endpoint: bad location", False)
    return ("test redirect endpoint", True)


def test_http_error_endpoint():
    """Test de l'endpoint qui retourne une erreur HTTP 403"""
    response = requests.get(f'{TEST_SERVER_URL}/api_http_error')
    if not response.status_code == 403:
        return ("test http error endpoint: bad status code", False)
    return ("test http error endpoint", True)


def test_custom_headers_endpoint():
    """Test de l'endpoint avec headers personnalisés"""
    response = requests.get(f'{TEST_SERVER_URL}/api_custom_headers')
    if not response.status_code == 200:
        return ("test custom headers endpoint: bad status code", False)
    if not response.headers.get('X-Custom-Header') == 'test-value':
        return ("test custom headers endpoint: custom header not found", False)
    if not 'Custom headers response' == response.text:
        return ("test custom headers endpoint: bad content", False)
    return ("test custom headers endpoint", True)


def test_empty_endpoint():
    """Test de l'endpoint qui retourne une réponse vide"""
    response = requests.get(f'{TEST_SERVER_URL}/api_empty')
    if not response.status_code == 200:
        return ("test empty endpoint: bad status code", False)
    if not '' == response.text:
        return ("test empty endpoint: should be empty", False)
    return ("test empty endpoint", True)


def test_html_endpoint():
    """Test de l'endpoint qui retourne du HTML"""
    response = requests.get(f'{TEST_SERVER_URL}/api_html')
    if not response.status_code == 200:
        return ("test html endpoint: bad status code", False)
    if not 'text/html' in response.headers.get('Content-Type', ''):
        return ("test html endpoint: bad content type", False)
    if not '<h1>HTML Response</h1>' in response.text:
        return ("test html endpoint: bad html content", False)
    return ("test html endpoint", True)


def test_method_post():
    """Test d'une requête POST"""
    response = requests.post(f'{TEST_SERVER_URL}/api_ping')
    if not response.status_code == 200:
        return ("test method post: bad status code", False)
    if not 'pong' == response.text:
        return ("test method post: bad content", False)
    return ("test method post", True)


def test_method_put():
    """Test d'une requête PUT"""
    response = requests.put(f'{TEST_SERVER_URL}/api_ping')
    if not response.status_code == 200:
        return ("test method put: bad status code", False)
    if not 'pong' == response.text:
        return ("test method put: bad content", False)
    return ("test method put", True)


def test_method_delete():
    """Test d'une requête DELETE"""
    response = requests.delete(f'{TEST_SERVER_URL}/api_delete')
    if not response.status_code == 200:
        return ("test method delete: bad status code", False)
    if not 'deleted' == response.text:
        return ("test method delete: bad content", False)
    return ("test method delete", True)


def test_cookies_endpoint():
    """Test de l'endpoint qui lit les cookies"""
    # Test sans cookies
    response = requests.get(f'{TEST_SERVER_URL}/api_cookies')
    if not response.status_code == 200:
        return ("test cookies endpoint: bad status code", False)
    if not 'no cookies' == response.text:
        return ("test cookies endpoint: should say no cookies", False)

    # Test avec cookies
    cookies = {'test_cookie': 'test_value', 'another': 'cookie'}
    response = requests.get(f'{TEST_SERVER_URL}/api_cookies', cookies=cookies)
    if not response.status_code == 200:
        return ("test cookies endpoint with cookies: bad status code", False)
    if not 'cookies:' in response.text:
        return ("test cookies endpoint with cookies: should contain cookies", False)
    return ("test cookies endpoint", True)


def test_post_json_endpoint():
    """Test de l'endpoint qui reçoit des données JSON en POST"""
    json_data = {"data": "test_data", "value": "123"}
    response = requests.post(f'{TEST_SERVER_URL}/api_post_json', json=json_data)
    if not response.status_code == 200:
        return ("test post json endpoint: bad status code", False)
    expected = "received: data=test_data, value=123"
    if not expected == response.text:
        return ("test post json endpoint: bad content", False)
    return ("test post json endpoint", True)


def test_special_chars_endpoint():
    """Test de l'endpoint qui gère les caractères spéciaux"""
    special_text = "Hello & World! @#$%"
    # Utiliser params au lieu d'encoder manuellement
    response = requests.get(f'{TEST_SERVER_URL}/api_special_chars', params={'text': special_text})
    if not response.status_code == 200:
        return ("test special chars endpoint: bad status code", False)

    # Forcer l'encodage UTF-8
    if response.encoding is None or response.encoding.lower() != 'utf-8':
        response.encoding = 'utf-8'


    if not special_text in response.text:
        return (f"test special chars endpoint: special chars not preserved (got: {response.text})", False)
    return ("test special chars endpoint", True)


def test_multiple_query_params():
    """Test de l'endpoint avec plusieurs paramètres query"""
    response = requests.get(f'{TEST_SERVER_URL}/api_multiple_query?param1=value1&param2=value2&param3=value3')
    if not response.status_code == 200:
        return ("test multiple query params: bad status code", False)
    expected = "p1=value1, p2=value2, p3=value3"
    if not expected == response.text:
        return ("test multiple query params: bad content", False)
    return ("test multiple query params", True)


def test_numeric_endpoint():
    """Test de l'endpoint qui traite des nombres"""
    response = requests.get(f'{TEST_SERVER_URL}/api_numeric?number=5')
    if not response.status_code == 200:
        return ("test numeric endpoint: bad status code", False)
    expected = "number squared: 25"
    if not expected == response.text:
        return ("test numeric endpoint: bad calculation", False)
    return ("test numeric endpoint", True)


def test_numeric_invalid_endpoint():
    """Test de l'endpoint avec un nombre invalide"""
    response = requests.get(f'{TEST_SERVER_URL}/api_numeric?number=notanumber')
    if not response.status_code == 200:
        return ("test numeric invalid endpoint: bad status code", False)
    expected = "invalid number"
    if not expected == response.text:
        return ("test numeric invalid endpoint: should return error message", False)
    return ("test numeric invalid endpoint", True)


def test_echo_empty_message():
    """Test de l'endpoint echo avec un message vide"""
    response = requests.get(f'{TEST_SERVER_URL}/api_echo')
    if not response.status_code == 200:
        return ("test echo empty: bad status code", False)
    expected = "echo: "
    if not expected == response.text:
        return ("test echo empty: bad content", False)
    return ("test echo empty", True)


def test_redirect_followed():
    """Test de la redirection avec suivi automatique"""
    response = requests.get(f'{TEST_SERVER_URL}/api_redirect', allow_redirects=True)
    if not response.status_code == 200:
        return ("test redirect followed: bad status code", False)
    if not 'Test OK' in response.text:
        return ("test redirect followed: should redirect to index", False)
    return ("test redirect followed", True)


def test_long_response():
    """Test d'une réponse très longue"""
    response = requests.get(f'{TEST_SERVER_URL}/api_long_response')
    if not response.status_code == 200:
        return ("test long response: bad status code", False)
    if not len(response.text) == 10000:
        return ("test long response: incorrect length", False)
    return ("test long response", True)


def test_unicode_endpoint():
    """Test de l'endpoint avec des caractères unicode"""
    unicode_text = "Hello 世界 🌍 café"
    # Utiliser params au lieu d'encoder manuellement l'URL
    response = requests.get(f'{TEST_SERVER_URL}/api_unicode', params={'text': unicode_text})
    if not response.status_code == 200:
        return ("test unicode endpoint: bad status code", False)

    # Forcer l'encodage UTF-8 si requests ne le détecte pas correctement
    if response.encoding is None or response.encoding.lower() != 'utf-8':
        response.encoding = 'utf-8'

    if not unicode_text in response.text:
        return (f"test unicode endpoint: unicode not preserved (got: {response.text})", False)
    return ("test unicode endpoint", True)


def test_set_cookie_endpoint():
    """Test de l'endpoint qui définit un cookie"""
    response = requests.get(f'{TEST_SERVER_URL}/api_set_cookie')
    if not response.status_code == 200:
        return ("test set cookie endpoint: bad status code", False)
    if not 'Set-Cookie' in response.headers or not 'test_cookie' in response.headers.get('Set-Cookie', ''):
        return ("test set cookie endpoint: cookie not set", False)
    if not 'cookie set' == response.text:
        return ("test set cookie endpoint: bad content", False)
    return ("test set cookie endpoint", True)


def test_case_sensitive_endpoint():
    """Test de la sensibilité à la casse des endpoints"""
    response = requests.get(f'{TEST_SERVER_URL}/api_case_sensitive')
    if not response.status_code == 200:
        return ("test case sensitive endpoint: bad status code", False)
    if not 'case_sensitive_ok' == response.text:
        return ("test case sensitive endpoint: bad content", False)
    return ("test case sensitive endpoint", True)


def test_mixed_params_endpoint():
    """Test de l'endpoint avec différents types de paramètres"""
    response = requests.get(f'{TEST_SERVER_URL}/api_mixed_params?id=123&name=Test&active=true')
    if not response.status_code == 200:
        return ("test mixed params endpoint: bad status code", False)
    expected = "id=123, name=Test, active=true"
    if not expected == response.text:
        return ("test mixed params endpoint: bad content", False)
    return ("test mixed params endpoint", True)


def test_boolean_endpoint():
    """Test de l'endpoint avec paramètre booléen"""
    response = requests.get(f'{TEST_SERVER_URL}/api_boolean?enabled=true')
    if not response.status_code == 200:
        return ("test boolean endpoint: bad status code", False)
    if not 'enabled=true' == response.text:
        return ("test boolean endpoint: bad content", False)
    return ("test boolean endpoint", True)


def test_nested_path_like():
    """Test de l'endpoint avec chemin simulé"""
    response = requests.get(f'{TEST_SERVER_URL}/api_nested_path_like')
    if not response.status_code == 200:
        return ("test nested path like: bad status code", False)
    if not 'nested_ok' == response.text:
        return ("test nested path like: bad content", False)
    return ("test nested path like", True)


def test_concurrent_requests():
    """Test de requêtes concurrentes"""
    import concurrent.futures

    def make_request():
        response = requests.get(f'{TEST_SERVER_URL}/api_ping')
        return response.status_code == 200 and response.text == 'pong'

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    if not all(results):
        return ("test concurrent requests: some requests failed", False)
    return ("test concurrent requests", True)


def test_zero_params():
    """Test avec paramètre à zéro"""
    response = requests.get(f'{TEST_SERVER_URL}/api_numeric?number=0')
    if not response.status_code == 200:
        return ("test zero params: bad status code", False)
    expected = "number squared: 0"
    if not expected == response.text:
        return ("test zero params: bad calculation", False)
    return ("test zero params", True)


def test_negative_number():
    """Test avec nombre négatif"""
    response = requests.get(f'{TEST_SERVER_URL}/api_numeric?number=-3')
    if not response.status_code == 200:
        return ("test negative number: bad status code", False)
    expected = "number squared: 9"
    if not expected == response.text:
        return ("test negative number: bad calculation", False)
    return ("test negative number", True)


# ============================================================================
# TESTS POUR LES COOKIES
# ============================================================================

def test_cookies_multiple():
    """Test de lecture de multiples cookies"""
    # Test sans cookies
    response = requests.get(f'{TEST_SERVER_URL}/api_cookies_multiple')
    if not response.status_code == 200:
        return ("test cookies multiple: bad status code (no cookies)", False)
    if not 'no cookies' == response.text:
        return ("test cookies multiple: should say no cookies", False)

    # Test avec plusieurs cookies
    cookies = {
        'session_id': 'abc123',
        'user_pref': 'dark_mode',
        'lang': 'fr'
    }
    response = requests.get(f'{TEST_SERVER_URL}/api_cookies_multiple', cookies=cookies)
    if not response.status_code == 200:
        return ("test cookies multiple: bad status code (with cookies)", False)
    if not 'cookies:' in response.text:
        return ("test cookies multiple: should contain 'cookies:'", False)
    # Vérifier que tous les cookies sont présents
    for key, value in cookies.items():
        if not f"{key}={value}" in response.text:
            return (f"test cookies multiple: cookie {key}={value} not found", False)
    return ("test cookies multiple", True)


def test_cookies_specific():
    """Test de lecture d'un cookie spécifique"""
    cookies = {
        'session_id': 'xyz789',
        'another_cookie': 'another_value'
    }

    # Test lecture d'un cookie existant
    response = requests.get(
        f'{TEST_SERVER_URL}/api_cookies_specific?cookie_name=session_id',
        cookies=cookies
    )
    if not response.status_code == 200:
        return ("test cookies specific: bad status code", False)
    expected = "cookie session_id=xyz789"
    if not expected == response.text:
        return (f"test cookies specific: expected '{expected}', got '{response.text}'", False)

    # Test lecture d'un cookie inexistant
    response = requests.get(
        f'{TEST_SERVER_URL}/api_cookies_specific?cookie_name=nonexistent',
        cookies=cookies
    )
    if not response.status_code == 200:
        return ("test cookies specific (not found): bad status code", False)
    if not 'not found' in response.text:
        return ("test cookies specific: should say 'not found'", False)

    return ("test cookies specific", True)


def test_set_multiple_cookies():
    """Test de définition de plusieurs cookies"""
    response = requests.get(f'{TEST_SERVER_URL}/api_set_multiple_cookies')
    if not response.status_code == 200:
        return ("test set multiple cookies: bad status code", False)

    # Vérifier la présence des Set-Cookie headers
    set_cookie_headers = response.headers.get('Set-Cookie', '')
    if not 'cookie1=value1' in set_cookie_headers:
        return ("test set multiple cookies: cookie1 not set", False)

    if not 'multiple cookies set' == response.text:
        return ("test set multiple cookies: bad content", False)

    return ("test set multiple cookies", True)


def test_cookies_with_special_chars():
    """Test des cookies avec caractères spéciaux"""
    cookies = {
        'token': 'abc-123_xyz.456',
        'data': 'test%20value'
    }
    response = requests.get(f'{TEST_SERVER_URL}/api_cookies_multiple', cookies=cookies)
    if not response.status_code == 200:
        return ("test cookies special chars: bad status code", False)
    if not 'cookies:' in response.text:
        return ("test cookies special chars: should contain cookies", False)
    return ("test cookies special chars", True)


# ============================================================================
# TESTS POUR L'UPLOAD DE FICHIERS
# ============================================================================

def test_upload_file_endpoint():
    """Test que l'endpoint d'upload est disponible"""
    response = requests.get(f'{TEST_SERVER_URL}/api_upload_file')
    if not response.status_code == 200:
        return ("test upload file endpoint: bad status code", False)
    if not 'file_upload_endpoint_ready' == response.text:
        return ("test upload file endpoint: bad content", False)
    return ("test upload file endpoint", True)


def test_save_file_png():
    """Test de sauvegarde d'un fichier PNG via base64"""
    import base64

    # Créer un petit fichier PNG (1x1 pixel transparent)
    # PNG signature + IHDR + IDAT + IEND
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    )

    # Encoder en base64 avec le préfixe data URI
    file_data = f"data:image/png;base64,{base64.b64encode(png_data).decode('utf-8')}"

    # Envoyer via POST JSON
    json_data = {
        "file_data": file_data,
        "filename": "test",
        "ext": "png"
    }
    response = requests.post(f'{TEST_SERVER_URL}/api_save_file', json=json_data)
    if not response.status_code == 200:
        return ("test save file png: bad status code", False)
    if not 'saved:' in response.text:
        return (f"test save file png: should contain 'saved:', got '{response.text}'", False)
    return ("test save file png", True)


def test_save_file_with_custom_name():
    """Test de sauvegarde avec nom personnalisé"""
    import base64

    # Fichier texte simple en base64
    text_content = "Hello, World!"
    text_b64 = base64.b64encode(text_content.encode()).decode('utf-8')
    file_data = f"data:text/plain;base64,{text_b64}"

    json_data = {
        "file_data": file_data,
        "filename": "customname",
        "ext": "txt"
    }
    response = requests.post(f'{TEST_SERVER_URL}/api_save_file', json=json_data)
    if not response.status_code == 200:
        return ("test save file custom name: bad status code", False)
    if not 'saved:' in response.text and not 'customname' in response.text:
        return (f"test save file custom name: should contain filename, got '{response.text}'", False)
    return ("test save file custom name", True)


def test_upload_validate_extension():
    """Test de validation de l'extension de fichier"""
    import base64

    # Créer un fichier JPEG
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    jpeg_b64 = base64.b64encode(jpeg_header).decode('utf-8')
    file_data = f"data:image/jpeg;base64,{jpeg_b64}"

    json_data = {
        "file_data": file_data,
        "expected_ext": "jpeg"
    }
    response = requests.post(f'{TEST_SERVER_URL}/api_upload_validate', json=json_data)
    if not response.status_code == 200:
        return ("test upload validate extension: bad status code", False)
    if not 'valid: jpeg' == response.text:
        return (f"test upload validate extension: expected 'valid: jpeg', got '{response.text}'", False)
    return ("test upload validate extension", True)


def test_sanitize_filename():
    """Test de sanitization de nom de fichier valide"""
    filename = "my_test_file-123"
    response = requests.get(f'{TEST_SERVER_URL}/api_sanitize_filename?filename={filename}')
    if not response.status_code == 200:
        return ("test sanitize filename: bad status code", False)
    expected = f"sanitized: {filename}"
    if not expected == response.text:
        return (f"test sanitize filename: expected '{expected}', got '{response.text}'", False)
    return ("test sanitize filename", True)


def test_sanitize_filename_dangerous():
    """Test de sanitization avec chemin dangereux"""
    dangerous_filenames = [
        "../../../etc/passwd",
        "..\\..\\windows\\system32",
        "test/../../dangerous",
        "file with spaces.txt"
    ]

    for dangerous in dangerous_filenames:
        response = requests.get(
            f'{TEST_SERVER_URL}/api_sanitize_filename',
            params={'filename': dangerous}
        )
        if not response.status_code == 200:
            return (f"test sanitize dangerous filename: bad status code for '{dangerous}'", False)

        # Vérifier que les caractères dangereux ont été supprimés
        if 'sanitized:' in response.text:
            sanitized = response.text.split('sanitized: ')[1]
            # Ne doit pas contenir /, \, ou ..
            if '/' in sanitized or '\\' in sanitized or '..' in sanitized:
                return (f"test sanitize dangerous filename: dangerous chars still present in '{sanitized}'", False)
        elif 'error:' not in response.text:
            return (f"test sanitize dangerous filename: unexpected response '{response.text}'", False)

    return ("test sanitize dangerous filename", True)


