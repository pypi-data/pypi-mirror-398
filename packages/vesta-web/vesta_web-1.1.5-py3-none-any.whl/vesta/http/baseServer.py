"""Vesta HTTP Server - Base server implementation with routing and request handling."""

import fastwsgi
import inspect

import os
import time
import json
import hashlib
import base64
import re
import urllib.parse
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from io import BytesIO

import multipart as mp
from configparser import ConfigParser

from vesta.http import response
from vesta.http import error
from vesta.http import redirect
from vesta.db import db_service as db

Response = response.Response
HTTPRedirect = redirect.HTTPRedirect
HTTPError = error.HTTPError

# Compile regex patterns once for performance
RE_URL = re.compile(r"[\&]")
RE_PARAM = re.compile(r"[\=]")

from colorama import Fore, Style
from colorama import init as colorama_init
colorama_init()

routes: Dict[str, Dict[str, Any]] = {}

class BaseServer:
    """Base HTTP server with routing, request parsing, and file handling capabilities."""

    def __init__(self, path: str, configFile: str, noStart: bool = False):
        """
        Initialize the Vesta server.

        Args:
            path: Base path for the server
            configFile: Path to configuration file
            noStart: If True, don't start the server (useful for testing)

        Raises:
            ValueError: If path is invalid
            FileNotFoundError: If config file doesn't exist
        """
        self.log("Starting Vesta server...")

        self.path = path

        # Instance-specific features
        self.features: Dict[str, Any] = {}

        self.importConf(configFile)

        if noStart:
            return

        self.start()


    #----------------------------HTTP SERVER------------------------------------
    def expose(func: Callable) -> Callable:
        """
        Decorator to expose a method as an HTTP route.

        Args:
            func: Function to expose as a route

        Returns:
            Wrapped function
        """
        def wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            self.response.ok()
            if res:
                return res.encode()
            else:
                return b""

        name = func.__name__
        if func.__name__ == "index":
            name = "/"
        elif func.__name__ == "default":
            name = "default"
        else:
            name = "/" + func.__name__

        routes[name] = {
            "params": inspect.signature(func).parameters,
            "target": wrapper
        }
        return wrapper


    def saveFile(self, content: str, name: str = "", ext: Optional[str] = None,
                 category: Optional[str] = None) -> str:
        """
        Save a base64-encoded file to the attachments' directory.

        Args:
            content: Base64-encoded file content with data URI prefix
            name: Optional filename (generated from hash if not provided)
            ext: Optional file extension override
            category: Optional subdirectory category

        Returns:
            Relative path to saved file

        Raises:
            ValueError: If content is invalid or file size exceeds limit
            IOError: If file cannot be saved
        """
        content = content.split(",")
        extension = content[0].split("/")[1].split(";")[0]
        content = base64.b64decode(content[1])

        if not name:
            hash_object = hashlib.sha256(content)
            hex_dig = hash_object.hexdigest()

            name = hex_dig
        else:
            name = self._sanitize_filename(name)

        prefix = self.path + "/static/attachments/"
        if category:
            name = category + "/"  + name
        if ext :
            name = name + "." + ext

        with open(prefix+name, 'wb') as f:
            f.write(content)
        return name


    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other security issues.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        # Remove path separators and dangerous characters
        filename = filename.replace('/', '').replace('\\', '').replace('..', '')
        # Keep only alphanumeric, dash, underscore
        filename = re.sub(r'[^a-zA-Z0-9_-]', '', filename)
        if not filename:
            raise ValueError("Invalid filename after sanitization")
        return filename


    def parseCookies(self, cookieStr: Optional[str]) -> Dict[str, str]:
        """
        Parse HTTP cookie header into a dictionary.

        Args:
            cookieStr: Raw cookie header string

        Returns:
            Dictionary of cookie name-value pairs
        """
        if not cookieStr:
            return {}

        cookies = {}
        try:
            for cookie in cookieStr.split(';'):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies[key.strip()] = value.strip()
        except Exception as e:
            self.logWarning(f"Error parsing cookies: {e}")

        return cookies



    def parseRequest(self, environ: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse HTTP request into a dictionary of parameters.

        Args:
            environ: WSGI environ dictionary

        Returns:
            Dictionary of request parameters

        Raises:
            ValueError: If content length exceeds maximum
        """
        self.response.cookies = self.parseCookies(environ.get('HTTP_COOKIE'))

        if environ.get('CONTENT_TYPE'):
            content_type = environ.get('CONTENT_TYPE').strip().split(";")
        else:
            content_type = ["text/html"]

        args = {}

        # Parse query string
        if environ.get('QUERY_STRING'):
            query = re.split(RE_URL, environ['QUERY_STRING'])
            for param in query:
                parts = re.split(RE_PARAM, param)
                if len(parts) == 2:
                    args[parts[0]] = urllib.parse.unquote_plus(parts[1], encoding='utf-8')

        content_length = int(environ.get('CONTENT_LENGTH', 0))
        # Parse multipart form data
        if content_type[0] == "multipart/form-data":
            try:
                body = environ['wsgi.input'].read(content_length)
                sep = content_type[1].split("=")[1]
                parser = mp.MultipartParser(BytesIO(body), sep.encode('utf-8'))
                for part in parser.parts():
                    args[part.name] = part.value
            except Exception as e:
                self.logError(f"Error parsing multipart data: {e}")
                raise ValueError("Invalid multipart data")

        # Parse JSON
        elif content_type[0] == "application/json" and content_length > 0:
            try:
                body = environ['wsgi.input'].read(content_length)
                data = json.loads(body)
                if isinstance(data, dict):
                    args.update(data)
            except json.JSONDecodeError as e:
                self.logError(f"Error parsing JSON: {e}")
                raise ValueError("Invalid JSON data")

        return args



    def tryDefault(self, environ: Dict[str, Any], target: str) -> bytes:
        """
        Try to handle request with default route.

        Args:
            environ: WSGI environ dictionary
            target: Request target path

        Returns:
            Response bytes
        """
        self.logInfo("Vesta - using default route")

        args = self.parseRequest(environ)
        args["target"] = target
        try:
            return routes["default"]["target"](self, **args)
        except (HTTPError, HTTPRedirect):
            return self.response.encode()
        except Exception as e:
            return self.handleUnexpected(e)


    def onrequest(self, environ: Dict[str, Any], start_response: Callable) -> bytes:
        """
        Handle incoming HTTP request.

        Args:
            environ: WSGI environ dictionary
            start_response: WSGI start_response callable

        Returns:
            Response bytes
        """
        self.response = Response(start_response=start_response)
        self.log(f"Vesta - request received: '{environ['PATH_INFO']}' with {environ.get('QUERY_STRING')}")
        target = environ['PATH_INFO']

        if routes.get(target):
            args = self.parseRequest(environ)

            try:
                if len(args) == 0:
                    return routes[target]["target"](self)
                return routes[target]["target"](self, **args)
            except (HTTPError, HTTPRedirect):
                return self.response.encode()
            except Exception as e:
                return self.handleUnexpected(e)
        else:
            if routes.get("default"):
                return self.tryDefault(environ, target)
            self.response.code = 404
            self.response.ok()
            return self.response.encode()

    def handleUnexpected(self, e: Exception) -> bytes:
        """
        Handle unexpected errors during request processing.

        Args:
            e: Exception that occurred

        Returns:
            Error response bytes
        """
        self.logError(f"Vesta - UNEXPECTED ERROR: {e}", exc_info=True)
        self.response.code = 500
        self.response.ok()

        # Only expose detailed errors in debug mode
        if self.config.getboolean("server", "DEBUG"):
            self.response.content = str(e) + "\n\n" + traceback.format_exc()
        else:
            self.response.content = "Internal Server Error"

        return self.response.encode()

    def onStart(self):
        pass

    #--------------------------GENERAL USE METHODS------------------------------

    def importConf(self, configFile: str):
        """
        Import configuration from file.

        Args:
            configFile: Path to configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        self.config = ConfigParser()
        config_path = self.path + configFile

        try:
            self.config.read(config_path)
            print(Fore.GREEN,"[INFO] Vesta - config at " + config_path + " loaded")
        except Exception:
            print(Fore.RED,"[ERROR] Vesta - Please create a config file")

    def start(self):
        """Start the HTTP server."""
        self.fileCache = {}

        if self.features.get("errors"):
            for code, page in self.features["errors"].items():
                Response.ERROR_PAGES[code] = self.path + page

        if self.features.get("orm"):
            try:
                self.db = db.DB(
                    user=self.config.get('DB', 'DB_USER'),
                    password=self.config.get('DB', 'DB_PASSWORD'),
                    host=self.config.get('DB', 'DB_HOST'),
                    port=int(self.config.get('DB', 'DB_PORT')),
                    db=self.config.get('DB', 'DB_NAME')
                )
            except Exception as e:
                self.logError(f"Failed to initialize database: {e}")
                raise

        self.onStart()

        fastwsgi.server.nowait = 1
        fastwsgi.server.hook_sigint = 1

        self.logInfo(f"Vesta - server running on PID: {os.getpid()} and port {self.config.get('server', 'PORT')}")
        fastwsgi.server.init(
            app=self.onrequest,
            host=self.config.get('server', 'IP'),
            port=int(self.config.get('server', 'PORT'))
        )

        while True:
            code = fastwsgi.server.run()
            if code != 0:
                break
            time.sleep(0)

        self.close()

    def close(self):
        """Shutdown the server gracefully."""

        self.logInfo("SIGTERM/SIGINT received")

        # Close database connection if it exists
        if hasattr(self, 'db'):
            try:
                self.db.close()
            except Exception as e:
                self.logError(f"Error closing database: {e}")

        fastwsgi.server.close()
        self.logInfo("SERVER STOPPED")


    def file(self, path: str, responseFile: bool = True) -> str:
        """
        Read a file with caching support.

        Args:
        path: Path to file (relative to server path or absolute)
        responseFile: If True, set response type to HTML

        Returns:
        File content as string

        Raises:
        ValueError: If path traversal is detected
        """
        file = self.fileCache.get(path)
        if file:
            return file
        else:
            # Validate path to prevent traversal
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = self.path / file_path

            file_path = file_path.resolve()

            # Ensure path is within server directory
            if not str(file_path).startswith(str(self.path.resolve())):
                raise ValueError("Invalid file path: path traversal attempt detected")

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            file = open(path)
            content = file.read()
            file.close()
            return content


    def start_ORM(self):
        """
        Start ORM connection (for manual initialization).

        Raises:
            Exception: If ORM is not enabled in features
        """
        if not self.features.get("orm"):
            raise Exception("ORM not enabled in server features")

        try:
            self.db = db.DB(
                user=self.config.get('DB', 'DB_USER'),
                password=self.config.get('DB', 'DB_PASSWORD'),
                host=self.config.get('DB', 'DB_HOST'),
                port=int(self.config.get('DB', 'DB_PORT')),
                db=self.config.get('DB', 'DB_NAME')
            )
            self.logInfo("Vesta - ORM database connection established")
        except Exception as e:
            self.logError(f"Failed to start ORM: {e}")
            raise

    def log(self, message):
        print(Fore.WHITE,"[LOG]", message, Style.RESET_ALL)

    def logInfo(self, message):
        print(Fore.GREEN,"[INFO]", message, Style.RESET_ALL)

    def logWarning(self, message):
        print(Fore.ORANGE,"[WARNING]", message, Style.RESET_ALL)

    def logError(self, message: str, exc_info: bool = False):
        """
        Log an error message.

        Args:
            message: Error message to log
            exc_info: If True, include exception traceback
        """
        print(Fore.RED, "[ERROR]", message, Style.RESET_ALL)
        if exc_info:
            print(Fore.RED, traceback.format_exc(), Style.RESET_ALL)
