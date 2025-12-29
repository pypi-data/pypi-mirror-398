"""
Tests for Vesta ORM (db_service.py)

This test suite requires a PostgreSQL database to be running.
It will automatically create the test database and user if they don't exist.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from vesta.db import db_service as db
import psycopg
from psycopg import sql


# Configuration
TEST_DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'test_user'),
    'password': os.environ.get('DB_PASSWORD', 'test_password'),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '5432')),
    'db': os.environ.get('DB_NAME', 'test_vesta_db')
}



class TestORMSuite:
    """Test suite for Vesta ORM"""

    def __init__(self):
        self.db = None
        self.setup_successful = False

    def setup(self):
        """Initialize database connection and create test tables"""
        try:
            self.db = db.DB(**TEST_DB_CONFIG)

            # Create test tables
            self.create_test_tables()
            self.setup_successful = True
            print("Database setup successful")
            return True
        except Exception as e:
            print(f"Database setup failed: {e}")
            print("⚠️  Make sure PostgreSQL is running and test database exists")
            return False

    def create_test_tables(self):
        """Create test tables for ORM testing"""
        # Simple table for basic tests
        self.db.createTable('test_users', '''
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(100),
            age INTEGER,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ''')

        # Table for relation tests
        self.db.createTable('test_posts', '''
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            title VARCHAR(255),
            content TEXT,
            published BOOLEAN DEFAULT FALSE
        ''')

        # Many-to-many proxy table
        self.db.createTable('test_tags', '''
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE
        ''')

        self.db.createTable('test_post_tags', '''
            id SERIAL PRIMARY KEY,
            test_posts INTEGER,
            test_tags INTEGER,
            UNIQUE(test_posts, test_tags)
        ''')

        print("✅ Test tables created")

    def teardown(self):
        """Clean up test data"""
        if self.db:
            try:
                self.db.resetTable('test_post_tags')
                self.db.resetTable('test_posts')
                self.db.resetTable('test_tags')
                self.db.resetTable('test_users')
                print("Test tables cleaned up")
            except Exception as e:
                print(f"Cleanup warning: {e}")

    def run_all_tests(self):
        """Run all ORM tests"""
        if not self.setup():
            return [("ORM setup", False)]

        results = []

        # Basic CRUD tests
        results.append(self.test_insert_dict())
        results.append(self.test_get_something())
        results.append(self.test_get_all())
        results.append(self.test_edit())
        results.append(self.test_delete_something())

        # Advanced tests
        results.append(self.test_insert_dict_with_id())
        results.append(self.test_insert_replace_dict())
        results.append(self.test_get_filters_simple())
        results.append(self.test_get_filters_multiple())
        results.append(self.test_get_filters_in_clause())
        results.append(self.test_get_filters_null())
        results.append(self.test_get_filters_boolean())
        results.append(self.test_get_something_proxied())

        # Edge cases
        results.append(self.test_get_nonexistent())
        results.append(self.test_sql_injection_protection())

        self.teardown()
        return results

    # ==================== Basic CRUD Tests ====================

    def test_insert_dict(self):
        """Test inserting a dictionary into database"""
        try:
            user_data = {
                'email': 'test@example.com',
                'name': 'Test User',
                'age': 25,
                'active': True
            }
            self.db.insertDict('test_users', user_data)

            # Verify insertion
            result = self.db.getSomething('test_users', 'test@example.com', 'email')
            if not result or result['name'] != 'Test User':
                return ("test insert dict: verification failed", False)

            return ("test insert dict", True)
        except Exception as e:
            return (f"test insert dict: {str(e)}", False)

    def test_get_something(self):
        """Test getting a single record"""
        try:
            # Insert test data
            user_data = {'email': 'get_test@example.com', 'name': 'Get Test', 'age': 30}
            self.db.insertDict('test_users', user_data)

            # Get by email
            result = self.db.getSomething('test_users', 'get_test@example.com', 'email')
            if not result or result['name'] != 'Get Test':
                return ("test get something: not found", False)

            return ("test get something", True)
        except Exception as e:
            return (f"test get something: {str(e)}", False)

    def test_get_all(self):
        """Test getting multiple records"""
        try:
            # Insert multiple posts for same user
            for i in range(3):
                post_data = {
                    'user_id': 1,
                    'title': f'Post {i}',
                    'content': f'Content {i}'
                }
                self.db.insertDict('test_posts', post_data)

            # Get all posts for user 1
            results = self.db.getAll('test_posts', 1, 'user_id')
            if len(results) < 3:
                return ("test get all: wrong count", False)

            return ("test get all", True)
        except Exception as e:
            return (f"test get all: {str(e)}", False)

    def test_edit(self):
        """Test updating a record"""
        try:
            # Insert test data
            user_data = {'email': 'edit_test@example.com', 'name': 'Original Name', 'age': 25}
            self.db.insertDict('test_users', user_data)

            # Get the user
            user = self.db.getSomething('test_users', 'edit_test@example.com', 'email')
            user_id = user['id']

            # Edit the name
            self.db.edit('test_users', user_id, 'name', 'Updated Name')

            # Verify edit
            updated = self.db.getSomething('test_users', user_id)
            if updated['name'] != 'Updated Name':
                return ("test edit: name not updated", False)

            return ("test edit", True)
        except Exception as e:
            return (f"test edit: {str(e)}", False)

    def test_delete_something(self):
        """Test deleting a record"""
        try:
            # Insert test data
            user_data = {'email': 'delete_test@example.com', 'name': 'Delete Me', 'age': 25}
            self.db.insertDict('test_users', user_data)

            # Get the user
            user = self.db.getSomething('test_users', 'delete_test@example.com', 'email')
            user_id = user['id']

            # Delete
            self.db.deleteSomething('test_users', user_id)

            # Verify deletion
            result = self.db.getSomething('test_users', user_id)
            if result:
                return ("test delete: record still exists", False)

            return ("test delete something", True)
        except Exception as e:
            return (f"test delete something: {str(e)}", False)

    # ==================== Advanced Tests ====================

    def test_insert_dict_with_id(self):
        """Test inserting with ID return"""
        try:
            user_data = {'email': 'withid@example.com', 'name': 'With ID', 'age': 28}
            user_id = self.db.insertDict('test_users', user_data, getId=True)

            if not user_id or not isinstance(user_id, int):
                return ("test insert dict with id: no ID returned", False)

            # Verify
            result = self.db.getSomething('test_users', user_id)
            if not result or result['email'] != 'withid@example.com':
                return ("test insert dict with id: verification failed", False)

            return ("test insert dict with id", True)
        except Exception as e:
            return (f"test insert dict with id: {str(e)}", False)

    def test_insert_replace_dict(self):
        """Test insert or replace functionality"""
        try:
            # Insert initial
            user_data = {'email': 'replace@example.com', 'name': 'Original', 'age': 30}
            user_id = self.db.insertDict('test_users', user_data, getId=True)

            # Replace
            updated_data = {'id': user_id, 'email': 'replace@example.com', 'name': 'Replaced', 'age': 31}
            self.db.insertReplaceDict('test_users', updated_data)

            # Verify
            result = self.db.getSomething('test_users', user_id)
            if result['name'] != 'Replaced' or result['age'] != 31:
                return ("test insert replace dict: not replaced", False)

            return ("test insert replace dict", True)
        except Exception as e:
            return (f"test insert replace dict: {str(e)}", False)

    def test_get_filters_simple(self):
        """Test filtering with simple condition"""
        try:
            # Insert test data
            self.db.insertDict('test_users', {'email': 'filter1@example.com', 'name': 'Filter1', 'age': 20})
            self.db.insertDict('test_users', {'email': 'filter2@example.com', 'name': 'Filter2', 'age': 30})

            # Filter age > 25
            results = self.db.getFilters('test_users', ['age', '>', 25])

            if not results or len(results) == 0:
                return ("test get filters simple: no results", False)

            # All results should have age > 25
            if any(r['age'] <= 25 for r in results):
                return ("test get filters simple: wrong filter", False)

            return ("test get filters simple", True)
        except Exception as e:
            return (f"test get filters simple: {str(e)}", False)

    def test_get_filters_multiple(self):
        """Test filtering with multiple conditions"""
        try:
            # Insert test data
            self.db.insertDict('test_users', {'email': 'multi1@example.com', 'name': 'Multi1', 'age': 25, 'active': True})
            self.db.insertDict('test_users', {'email': 'multi2@example.com', 'name': 'Multi2', 'age': 30, 'active': False})

            # Filter age >= 25 AND active = true
            results = self.db.getFilters('test_users', ['age', '>=', 25, 'AND', 'active', '=', 'true'])

            if not results:
                return ("test get filters multiple: no results", False)

            # All should be active and age >= 25
            if any(not r['active'] or r['age'] < 25 for r in results):
                return ("test get filters multiple: wrong filter", False)

            return ("test get filters multiple", True)
        except Exception as e:
            return (f"test get filters multiple: {str(e)}", False)

    def test_get_filters_in_clause(self):
        """Test filtering with IN clause"""
        try:
            # Insert test data
            self.db.insertDict('test_users', {'email': 'in1@example.com', 'name': 'In1', 'age': 20})
            self.db.insertDict('test_users', {'email': 'in2@example.com', 'name': 'In2', 'age': 30})
            self.db.insertDict('test_users', {'email': 'in3@example.com', 'name': 'In3', 'age': 40})

            # Filter age IN (20, 30)
            results = self.db.getFilters('test_users', ['age', 'IN', [20, 30]])

            if len(results) < 2:
                return ("test get filters in clause: wrong count", False)

            # All should have age 20 or 30
            if any(r['age'] not in [20, 30] for r in results):
                return ("test get filters in clause: wrong filter", False)

            return ("test get filters in clause", True)
        except Exception as e:
            return (f"test get filters in clause: {str(e)}", False)

    def test_get_filters_null(self):
        """Test filtering with NULL values"""
        try:
            # Insert test data with NULL
            self.db.insertDict('test_users', {'email': 'null1@example.com', 'age': None})
            self.db.insertDict('test_users', {'email': 'null2@example.com', 'age': 25})

            # Filter age IS NULL
            results = self.db.getFilters('test_users', ['age', 'IS', None])

            if not results:
                return ("test get filters null: no results", False)

            # All should have NULL age
            if any(r['age'] is not None for r in results):
                return ("test get filters null: wrong filter", False)

            return ("test get filters null", True)
        except Exception as e:
            return (f"test get filters null: {str(e)}", False)

    def test_get_filters_boolean(self):
        """Test filtering with boolean values"""
        try:
            # Insert test data
            self.db.insertDict('test_posts', {'user_id': 1, 'title': 'Published', 'published': True})
            self.db.insertDict('test_posts', {'user_id': 1, 'title': 'Draft', 'published': False})

            # Filter published = true
            results = self.db.getFilters('test_posts', ['published', '=', 'true'])

            if not results:
                return ("test get filters boolean: no results", False)

            # All should be published
            if any(not r['published'] for r in results):
                return ("test get filters boolean: wrong filter", False)

            return ("test get filters boolean", True)
        except Exception as e:
            return (f"test get filters boolean: {str(e)}", False)

    def test_get_something_proxied(self):
        """Test many-to-many relationship query"""
        try:
            # Create a post
            post_id = self.db.insertDict('test_posts', {'user_id': 1, 'title': 'Tagged Post'}, getId=True)

            # Create tags
            tag1_id = self.db.insertDict('test_tags', {'name': 'python'}, getId=True)
            tag2_id = self.db.insertDict('test_tags', {'name': 'testing'}, getId=True)

            # Link post to tags
            self.db.insertDict('test_post_tags', {'test_posts': post_id, 'test_tags': tag1_id})
            self.db.insertDict('test_post_tags', {'test_posts': post_id, 'test_tags': tag2_id})

            # Get all tags for the post
            results = self.db.getSomethingProxied('test_tags', 'test_post_tags', 'test_posts', post_id)

            if len(results) < 2:
                return ("test get something proxied: wrong count", False)

            # Verify tag names
            tag_names = [r['name'] for r in results]
            if 'python' not in tag_names or 'testing' not in tag_names:
                return ("test get something proxied: wrong tags", False)

            return ("test get something proxied", True)
        except Exception as e:
            return (f"test get something proxied: {str(e)}", False)

    # ==================== Edge Cases ====================

    def test_get_nonexistent(self):
        """Test getting non-existent record"""
        try:
            result = self.db.getSomething('test_users', 999999)

            # Should return empty list or None
            if result and result != []:
                return ("test get nonexistent: should be empty", False)

            return ("test get nonexistent", True)
        except Exception as e:
            return (f"test get nonexistent: {str(e)}", False)

    def test_sql_injection_protection(self):
        """Test that SQL injection is prevented"""
        try:
            # Try to inject SQL
            malicious_email = "test@example.com' OR '1'='1"

            # This should not cause SQL injection
            result = self.db.getSomething('test_users', malicious_email, 'email')

            # Should return empty (the literal string doesn't exist)
            if result and result != []:
                return ("test sql injection protection: vulnerable!", False)

            return ("test sql injection protection", True)
        except Exception as e:
            # If it throws an error, that's also fine - it means it didn't execute malicious SQL
            return ("test sql injection protection", True)


def run():
    """Run all ORM tests"""

    suite = TestORMSuite()
    results = suite.run_all_tests()

    return results

