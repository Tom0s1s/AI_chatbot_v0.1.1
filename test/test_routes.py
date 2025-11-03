import pytest

from application.app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    # Use a short secret key to allow sessions in tests if needed
    flask_app.secret_key = flask_app.secret_key or 'test-secret'
    with flask_app.test_client() as client:
        yield client


def test_index_page(client):
    r = client.get('/')
    assert r.status_code == 200
    # page should include site title or Kjell mention
    assert b'AI Chatbot' in r.data or b'Kjell' in r.data


def test_bot_and_info_pages(client):
    r = client.get('/bot')
    assert r.status_code == 200

    r2 = client.get('/info')
    assert r2.status_code == 200


def test_cookie_endpoints_set_and_clear(client):
    # accept cookies should redirect back to the index and set a consent cookie
    r = client.get('/accept_cookies', follow_redirects=False)
    assert r.status_code in (302, 301)
    # check Set-Cookie header contains consent
    set_cookie_headers = r.headers.get_all('Set-Cookie')
    assert any('consent=' in s for s in set_cookie_headers)

    # decline cookies should also redirect and set consent=false
    r2 = client.get('/decline_cookies', follow_redirects=False)
    assert r2.status_code in (302, 301)
    set_cookie_headers2 = r2.headers.get_all('Set-Cookie')
    assert any('consent=' in s for s in set_cookie_headers2)

    # clear cookies helper should redirect and not error
    r3 = client.get('/clear_cookies', follow_redirects=False)
    assert r3.status_code in (302, 301)


def test_admin_login_logout_flow(client):
    # GET login page
    r = client.get('/admin/login')
    assert r.status_code == 200

    # POST wrong password should return the login page (status 200)
    r2 = client.post('/admin/login', data={'password': 'wrong'}, follow_redirects=False)
    assert r2.status_code == 200

    # POST correct password should redirect to the admin panel
    r3 = client.post('/admin/login', data={'password': '123'}, follow_redirects=False)
    assert r3.status_code in (302, 301)

    # Logout should redirect back to index
    r4 = client.get('/admin/logout', follow_redirects=False)
    assert r4.status_code in (302, 301)
