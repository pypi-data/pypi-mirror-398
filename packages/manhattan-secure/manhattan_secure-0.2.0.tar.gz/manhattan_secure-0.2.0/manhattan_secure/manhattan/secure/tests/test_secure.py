import string

from manhattan import secure


def test_encrypt_password():
    """One-way encrypt a password and return the hash string"""

    password = 'abc123'
    password_salt = 'foobar'

    # Encrypting the password
    password_hash = secure.encrypt_password(password, password_salt)

    # Check the password hash is reproducable with the same details
    assert password_hash == secure.encrypt_password(password, password_salt)

    # Check that the password hash cannot be reproduced without the same salt
    assert password_hash != secure.encrypt_password(password, 'barfoo')

    # Encrypt the password using a different hash type
    password_hash = secure.encrypt_password(password, password_salt, \
            hash_name='md5')

    # Check the password hash is reproducable with the same details
    assert password_hash == secure.encrypt_password(password, password_salt, \
            hash_name='md5')

    # Check that the password hash cannot be reproduced without the same hash
    # type.
    assert password_hash != secure.encrypt_password(password, password_salt, \
            hash_name='sha1')

    # Encrypt the password using a different number of iterations
    password_hash = secure.encrypt_password(password, password_salt, \
            iterations=10)

    # Check the password hash is reproducable with the same details
    assert password_hash == secure.encrypt_password(password, password_salt, \
            iterations=10)

    # Check that the password hash cannot be reproduced without the same hash
    # type.
    assert password_hash != secure.encrypt_password(password, password_salt, \
            iterations=100)

def test_random_code():
    """Return a random code"""

    # Check we can generate a random code
    code = secure.random_code()
    assert len(code) == 8
    assert set(code).issubset('abcdefghkmnopqrstuvw23456789')

    # Check we can generate a random code of a custom length
    code = secure.random_code(length=4)
    assert len(code) == 4
    assert set(code).issubset('abcdefghkmnopqrstuvw23456789')

    # Check we can generate a random code with a custom charset
    code = secure.random_code(charset='abcd')
    assert len(code) == 8
    assert set(code).issubset('abcd')

def test_random_token():
    """Return a random token"""
    code = secure.random_token()
    assert len(code) == 32
    assert set(code).issubset(string.hexdigits)

def test_safe_redirect_url():
    """Return a URL that can safely be redirected to"""

    restricted_urls = ['/sign-out']

    # Check valid URLs are shortened to local paths
    safe_url = secure.safe_redirect_url(
            'http://www.example.com/some-path?some=query#some-fragment',
            restricted_urls
            )
    assert safe_url == '/some-path?some=query#some-fragment'

    # Check invalid URLs return None
    safe_url = secure.safe_redirect_url('www.badplace.com')
    assert safe_url == None

    # Check restricted URLs return None
    safe_url = secure.safe_redirect_url(
        'http://www.example.com/sign-out',
        restricted_urls
        )
    assert safe_url == None
