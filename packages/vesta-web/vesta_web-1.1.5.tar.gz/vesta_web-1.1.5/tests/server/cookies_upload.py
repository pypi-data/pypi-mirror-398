#!/usr/bin/env python3
"""
Tests unitaires pour les fonctions de cookies et upload de fichiers.
Ces tests peuvent être exécutés sans démarrer le serveur.
"""

import sys
import os
from os.path import dirname, abspath
import base64
import tempfile
import shutil

# Ajouter le path du projet
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from vesta.http import baseServer


class TestBaseServerUnit:
    """Tests unitaires pour BaseServer"""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.server = None
        self.setup()

    def setup(self):
        """Créer un serveur de test"""
        # Créer une structure de dossiers temporaire
        os.makedirs(os.path.join(self.temp_dir, 'static', 'attachments'), exist_ok=True)

        # Créer un fichier de config minimal
        config_content = """[server]
IP = 127.0.0.1
PORT = 9999

[DB]
DB_USER = test
DB_PASSWORD = test
DB_HOST = localhost
DB_PORT = 5432
DB_NAME = test
"""
        config_path = os.path.join(self.temp_dir, 'test.ini')
        with open(config_path, 'w') as f:
            f.write(config_content)

        # Créer le serveur sans le démarrer
        self.server = baseServer.BaseServer(
            path=self.temp_dir,
            configFile='/test.ini',
            noStart=True
        )

    def teardown(self):
        """Nettoyer les fichiers temporaires"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_sanitize_filename_valid(self):
        """Test de sanitization avec nom valide"""
        valid_names = [
            "myfile",
            "my_file",
            "my-file",
            "myfile123",
            "file_2024-01-01"
        ]

        for name in valid_names:
            try:
                result = self.server._sanitize_filename(name)
                if result != name:
                    return (f"test sanitize valid '{name}'", False, f"Expected {name}, got {result}")
            except Exception as e:
                return (f"test sanitize valid '{name}'", False, str(e))

        return ("test sanitize filename valid", True, "All valid filenames passed")

    def test_sanitize_filename_dangerous(self):
        """Test de sanitization avec noms dangereux"""
        dangerous_tests = [
            ("../../../etc/passwd", "etcpasswd"),
            ("..\\..\\windows\\system32", "windowssystem32"),
            ("test/../../dangerous", "testdangerous"),
            ("file space.txt", "filespacetxt"),
            ("file@#$%.txt", "filetxt"),
            ("COM1", "COM1"),  # Nom réservé Windows
        ]

        for dangerous, expected_safe in dangerous_tests:
            try:
                result = self.server._sanitize_filename(dangerous)
                # Vérifier qu'il ne contient pas de caractères dangereux
                if '/' in result or '\\' in result or '..' in result:
                    return (
                        f"test sanitize dangerous '{dangerous}'",
                        False,
                        f"Dangerous chars still present: {result}"
                    )
            except ValueError as e:
                # C'est acceptable de lever une exception pour les noms invalides
                if "Invalid filename" not in str(e):
                    return (f"test sanitize dangerous '{dangerous}'", False, str(e))
            except Exception as e:
                return (f"test sanitize dangerous '{dangerous}'", False, str(e))

        return ("test sanitize filename dangerous", True, "All dangerous filenames handled")

    def test_sanitize_filename_empty(self):
        """Test de sanitization avec nom vide ou invalide"""
        invalid_names = ["", "...", "///", "\\\\\\", "@#$%"]

        for name in invalid_names:
            try:
                result = self.server._sanitize_filename(name)
                # Si on arrive ici sans exception, le nom ne devrait pas être vide
                if not result:
                    return (
                        f"test sanitize empty '{name}'",
                        False,
                        "Should raise exception or return non-empty"
                    )
            except ValueError as e:
                # Exception attendue pour noms invalides
                if "Invalid filename" not in str(e):
                    return (f"test sanitize empty '{name}'", False, str(e))
            except Exception as e:
                return (f"test sanitize empty '{name}'", False, str(e))

        return ("test sanitize filename empty", True, "Empty filenames handled correctly")

    def test_parse_cookies_valid(self):
        """Test de parsing de cookies valides"""
        test_cases = [
            ("session_id=abc123", {"session_id": "abc123"}),
            ("user=john; token=xyz", {"user": "john", "token": "xyz"}),
            ("a=1; b=2; c=3", {"a": "1", "b": "2", "c": "3"}),
            ("empty=", {"empty": ""}),
        ]

        for cookie_str, expected in test_cases:
            result = self.server.parseCookies(cookie_str)
            if result != expected:
                return (
                    f"test parse cookies '{cookie_str}'",
                    False,
                    f"Expected {expected}, got {result}"
                )

        return ("test parse cookies valid", True, "All cookie strings parsed correctly")

    def test_parse_cookies_empty(self):
        """Test de parsing de cookies vides ou None"""
        test_cases = [None, "", "   "]

        for cookie_str in test_cases:
            result = self.server.parseCookies(cookie_str)
            if result != {}:
                return (
                    f"test parse cookies empty '{cookie_str}'",
                    False,
                    f"Expected empty dict, got {result}"
                )

        return ("test parse cookies empty", True, "Empty cookies handled correctly")

    def test_parse_cookies_malformed(self):
        """Test de parsing de cookies malformés"""
        # Ces cookies ne devraient pas crasher le serveur
        malformed = [
            "nocookie",
            "multiple===equals",
            ";;;;;",
            "=value_no_key",
        ]

        for cookie_str in malformed:
            try:
                result = self.server.parseCookies(cookie_str)
                # Ne devrait pas crasher, peut retourner un dict vide ou partiel
                if not isinstance(result, dict):
                    return (
                        f"test parse cookies malformed '{cookie_str}'",
                        False,
                        f"Should return dict, got {type(result)}"
                    )
            except Exception as e:
                return (f"test parse cookies malformed '{cookie_str}'", False, str(e))

        return ("test parse cookies malformed", True, "Malformed cookies handled gracefully")

    def test_save_file_base64_png(self):
        """Test de sauvegarde d'un fichier PNG"""
        # PNG 1x1 transparent
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        file_data = f"data:image/png;base64,{base64.b64encode(png_data).decode('utf-8')}"

        try:
            result = self.server.saveFile(content=file_data, name="test", ext="png")

            # Vérifier que le fichier a été créé
            file_path = os.path.join(self.temp_dir, 'static', 'attachments', result)
            if not os.path.exists(file_path):
                return ("test save file png", False, f"File not created at {file_path}")

            # Vérifier la taille
            if os.path.getsize(file_path) != len(png_data):
                return ("test save file png", False, "File size mismatch")

            return ("test save file png", True, f"File saved at {result}")
        except Exception as e:
            return ("test save file png", False, str(e))

    def test_save_file_auto_hash_name(self):
        """Test de génération automatique du nom par hash"""
        text_content = b"Hello, World!"
        text_b64 = base64.b64encode(text_content).decode('utf-8')
        file_data = f"data:text/plain;base64,{text_b64}"

        try:
            # Sans nom, devrait utiliser le hash
            result = self.server.saveFile(content=file_data, ext="txt")

            # Vérifier que le fichier existe
            file_path = os.path.join(self.temp_dir, 'static', 'attachments', result)
            if not os.path.exists(file_path):
                return ("test save file auto hash", False, "File not created")

            # Le nom devrait être un hash SHA256 (64 caractères hex)
            name_part = result.split('.')[0]
            if len(name_part) != 64:
                return ("test save file auto hash", False, f"Hash name length incorrect: {len(name_part)}")

            return ("test save file auto hash", True, f"File saved with hash name: {result}")
        except Exception as e:
            return ("test save file auto hash", False, str(e))


def run():

    tester = TestBaseServerUnit()
    results = []

    try:
        # Tests de sanitization
        results.append(tester.test_sanitize_filename_valid())
        results.append(tester.test_sanitize_filename_dangerous())
        results.append(tester.test_sanitize_filename_empty())

        # Tests de parsing de cookies
        results.append(tester.test_parse_cookies_valid())
        results.append(tester.test_parse_cookies_empty())
        results.append(tester.test_parse_cookies_malformed())

        # Tests de sauvegarde de fichiers
        results.append(tester.test_save_file_base64_png())
        results.append(tester.test_save_file_auto_hash_name())

    finally:
        tester.teardown()

    return results


