"""
Quick test suite for RibbitXDB v1.0.6
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import ribbitxdb
import time

def test_basic_operations():
    """Test basic CRUD operations"""
    print("Testing basic operations...")
    
    conn = ribbitxdb.connect('test_basic.rbx')
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER
        )
    """)
    
    # Insert
    cursor.execute("INSERT INTO users VALUES (1, 'Alice', 30)")
    cursor.execute("INSERT INTO users VALUES (2, 'Bob', 25)")
    conn.commit()
    
    # Select
    cursor.execute("SELECT * FROM users WHERE age > 20")
    results = cursor.fetchall()
    assert len(results) == 2, f"Expected 2 rows, got {len(results)}"
    
    # Update
    cursor.execute("UPDATE users SET age = 31 WHERE name = 'Alice'")
    conn.commit()
    
    # Delete
    cursor.execute("DELETE FROM users WHERE name = 'Bob'")
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()
    
    conn.close()
    os.remove('test_basic.rbx')
    
    print("✓ Basic operations passed")

def test_advanced_sql():
    """Test advanced SQL features"""
    print("Testing advanced SQL...")
    
    conn = ribbitxdb.connect('test_advanced.rbx')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price INTEGER,
            category TEXT
        )
    """)
    
    # Insert test data
    for i in range(10):
        cursor.execute(
            "INSERT INTO products VALUES (?, ?, ?, ?)",
            (i, f"Product{i}", (i+1)*10, 'A' if i % 2 == 0 else 'B')
        )
    conn.commit()
    
    # Test aggregates
    cursor.execute("SELECT COUNT(*), AVG(price), MAX(price) FROM products")
    result = cursor.fetchone()
    assert result['count_*'] == 10
    
    # Test GROUP BY
    cursor.execute("SELECT category, COUNT(*) as cnt FROM products GROUP BY category")
    results = cursor.fetchall()
    assert len(results) == 2
    
    # Test ORDER BY + LIMIT
    cursor.execute("SELECT * FROM products ORDER BY price DESC LIMIT 3")
    results = cursor.fetchall()
    assert len(results) == 3
    
    # Test LIKE
    cursor.execute("SELECT * FROM products WHERE name LIKE 'Product%'")
    results = cursor.fetchall()
    assert len(results) == 10
    
    conn.close()
    os.remove('test_advanced.rbx')
    
    print("✓ Advanced SQL passed")

def test_network_components():
    """Test network components (without actual server)"""
    print("Testing network components...")
    
    # Test protocol
    from ribbitxdb.server.protocol import Message, MessageType
    
    msg = Message.create_json(MessageType.CONNECT, {'version': 1})
    serialized = msg.serialize()
    deserialized = Message.deserialize(serialized)
    
    assert deserialized.msg_type == MessageType.CONNECT
    assert deserialized.get_json()['version'] == 1
    
    # Test user manager
    from ribbitxdb.auth import UserManager
    
    if os.path.exists('test_users.rbx'):
        os.remove('test_users.rbx')
    
    um = UserManager('test_users.rbx')
    um.create_user('testuser', 'password123')
    
    user = um.get_user('testuser')
    assert user is not None
    assert user.username == 'testuser'
    
    # Test authentication
    from ribbitxdb.auth import Authenticator
    auth = Authenticator(um)
    assert auth.authenticate('testuser', 'password123')
    assert not auth.authenticate('testuser', 'wrongpassword')
    
    os.remove('test_users.rbx')
    
    print("✓ Network components passed")

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("RibbitXDB v1.0.6 Test Suite")
    print("="*60)
    print()
    
    try:
        test_basic_operations()
        test_advanced_sql()
        test_network_components()
        
        print()
        print("="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        return True
    except Exception as e:
        print()
        print("="*60)
        print(f"✗ TEST FAILED: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
