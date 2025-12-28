import json
from typing import Optional, Union
from playwright.sync_api import Page

from .fun_base import log, send_exception
from .time_utils import get_current_datetime

import inspect

def debug_shein_signature(page: Page) -> dict:
    """
    调试函数：检测 _SHEIN_CALC_SIGNATURE_ 函数的加载状态。
    用于排查签名函数未加载的问题。
    
    :param page: Playwright 的 Page 对象
    :return: 包含调试信息的字典
    """
    try:
        result = page.evaluate("""
            () => {
                const info = {
                    has_signature_func: typeof window._SHEIN_CALC_SIGNATURE_ === 'function',
                    page_url: window.location.href,
                    ready_state: document.readyState,
                    window_keys_with_shein: Object.keys(window).filter(k => k.toLowerCase().includes('shein')),
                    timestamp: new Date().toISOString()
                };
                
                // 检查常见的签名/安全相关全局变量
                const securityVars = ['_SHEIN_CALC_SIGNATURE_', '__INITIAL_STATE__', '__NUXT__', 'Vue', 'React'];
                info.global_vars = {};
                securityVars.forEach(v => {
                    info.global_vars[v] = typeof window[v];
                });
                
                return info;
            }
        """)
        log("希音签名调试信息:", result)
        return result
    except Exception as e:
        return {"error": str(e)}


# 希音签名脚本的 URL（可能需要根据版本更新）
SHEIN_SIGNATURE_SCRIPT_URL = 'https://assets.dotfashion.cn/webassets/sig_bundle/D58CJi06nV8d45rPGs7SrW2nvz6Dn4/1.0.7/1/main.js'

def ensure_shein_signature(page: Page, timeout: int = 15000) -> bool:
    """
    确保希音签名函数可用。
    
    该函数会检测页面是否存在 window._SHEIN_CALC_SIGNATURE_ 函数，
    如果不存在，则尝试直接注入签名脚本。
    
    :param page: Playwright 的 Page 对象
    :param timeout: 等待超时时间（毫秒），默认 15 秒
    :return: True 如果签名函数可用，False 如果失败
    """
    try:
        # 首先检查函数是否已存在
        has_func = page.evaluate("typeof window._SHEIN_CALC_SIGNATURE_ === 'function'")
        if has_func:
            log("希音签名函数已存在")
            return True
        
        log("希音签名函数不存在，尝试注入签名脚本...")
        
        # 方法1：尝试直接注入签名脚本
        try:
            page.add_script_tag(url=SHEIN_SIGNATURE_SCRIPT_URL)
            # 等待函数可用
            page.wait_for_function(
                "typeof window._SHEIN_CALC_SIGNATURE_ === 'function'",
                timeout=timeout
            )
            log("签名脚本注入成功，签名函数已可用")
            return True
        except Exception as e:
            log(f"直接注入签名脚本失败: {e}")
        
        # 方法2：尝试触发页面加载签名脚本（通过等待）
        import time
        start_time = time.time()
        max_wait_sec = timeout / 1000
        
        while (time.time() - start_time) < max_wait_sec:
            has_func = page.evaluate("typeof window._SHEIN_CALC_SIGNATURE_ === 'function'")
            if has_func:
                log(f"希音签名函数已加载，耗时 {time.time() - start_time:.2f} 秒")
                return True
            time.sleep(0.5)
        
        log(f"等待希音签名函数超时（{timeout/1000}秒）")
        return False
        
    except Exception as e:
        log(f"确保签名函数可用时出错: {e}")
        return False

def fetch(page: Page, url: str, params: Optional[Union[dict, list, str]] = None, headers: Optional[dict] = None, config:
Optional[dict] = None) -> dict:
    """
    发送 HTTP POST 请求，支持自定义 headers 和重定向处理。

    :param page: Playwright 的 Page 对象
    :param url: 请求地址
    :param params: 请求参数（dict、list、str 或 None）
    :param headers: 自定义 headers 字典
    :param config: 请求配置字典
    :return: 服务器返回的 JSON 响应（dict）
    """
    if params is not None and not isinstance(params, (dict, list, str)):
        raise ValueError("params 参数必须是 dict、list、str 或 None")
    if headers is not None and not isinstance(headers, dict):
        raise ValueError("headers 参数必须是 dict 或 None")

    try:
        page.wait_for_load_state('load')
        response = page.evaluate("""
            async ({ url, params, extraHeaders, config }) => {
                try {
                    const defaultHeaders = {
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
                        'x-requested-with': 'XMLHttpRequest',
                    };

                    const headers = Object.assign({}, defaultHeaders, extraHeaders || {});
                    const options = {
                        method: 'POST',
                        credentials: 'include',
                        redirect: 'follow',  // 明确设置跟随重定向
                        headers: headers
                    };

                    // 应用额外配置
                    if (config) {
                        Object.assign(options, config);
                    }

                    if (params !== null) {
                        if (typeof params === 'string') {
                            options.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
                            options.body = params;
                        } else {
                            options.headers['Content-Type'] = 'application/json';
                            options.body = JSON.stringify(params);
                        }
                    }

                    const response = await fetch(url, options);
                    
                    // 处理重定向
                    if (response.redirected) {
                        console.log(`请求被重定向到: ${response.url}`);
                    }
                    
                    if (!response.ok) {
                        // 如果是重定向相关的状态码，尝试获取响应内容
                        if (response.status >= 300 && response.status < 400) {
                            const text = await response.text();
                            return { 
                                "error": "redirect_error", 
                                "message": `HTTP ${response.status} - ${response.statusText}`,
                                "redirect_url": response.url,
                                "response_text": text,
                                "status": response.status
                            };
                        }
                        throw new Error(`HTTP ${response.status} - ${response.statusText}`);
                    }
                    
                    // 尝试解析 JSON，如果失败则返回文本内容
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return await response.json();
                    } else {
                        const text = await response.text();
                        return { "content": text, "content_type": contentType, "final_url": response.url };
                    }
                } catch (error) {
                    return { "error": "fetch_failed", "message": error.message };
                }
            }
        """, {"url": url, "params": params, "extraHeaders": headers, "config": config})

        return response
    except Exception as e:
        raise send_exception()
        # return {"error": "fetch error", "message": str(e)}

def fetch_shein(page: Page, url: str, params: Optional[Union[dict, list, str]] = None, headers: Optional[dict] = None, config:
Optional[dict] = None) -> dict:
    """
    发送 HTTP POST 请求，专门用于希音接口，自动处理 x-gw-auth 签名。
    
    该函数会先确保签名函数可用（通过注入脚本），然后自动生成签名并添加到请求头中。

    :param page: Playwright 的 Page 对象
    :param url: 请求地址（完整 URL 或相对路径，如 /sbn/common/get_update_time）
    :param params: 请求参数（dict、list、str 或 None）
    :param headers: 自定义 headers 字典
    :param config: 请求配置字典
    :return: 服务器返回的 JSON 响应（dict）
    """
    if params is not None and not isinstance(params, (dict, list, str)):
        raise ValueError("params 参数必须是 dict、list、str 或 None")
    if headers is not None and not isinstance(headers, dict):
        raise ValueError("headers 参数必须是 dict 或 None")

    try:
        page.wait_for_load_state('load')
        
        # 在 Python 端确保签名函数可用（注入脚本）
        ensure_shein_signature(page)
        
        response = page.evaluate("""
            async ({ url, params, extraHeaders, config }) => {
                try {
                    const defaultHeaders = {
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                        'x-requested-with': 'XMLHttpRequest',
                        'Origin-Url': window.location.href,
                    };

                    const headers = Object.assign({}, defaultHeaders, extraHeaders || {});
                    
                    // 提取相对路径用于签名
                    let signPath = url;
                    if (url.startsWith('http')) {
                        try {
                            const urlObj = new URL(url);
                            signPath = urlObj.pathname;
                        } catch (e) {
                            // 解析失败使用原 url
                        }
                    }
                    
                    // 生成希音签名（Python 端已确保函数可用）
                    if (typeof window._SHEIN_CALC_SIGNATURE_ === 'function') {
                        try {
                            const signature = await window._SHEIN_CALC_SIGNATURE_(signPath);
                            if (signature) {
                                headers['x-gw-auth'] = signature;
                                console.log('希音签名生成成功');
                            }
                        } catch (signError) {
                            console.warn('生成希音签名失败:', signError.message);
                        }
                    } else {
                        console.warn('签名函数不存在，将不带签名发送请求');
                    }

                    const options = {
                        method: 'POST',
                        credentials: 'include',
                        redirect: 'follow',
                        headers: headers
                    };

                    // 应用额外配置
                    if (config) {
                        Object.assign(options, config);
                    }

                    if (params !== null) {
                        if (typeof params === 'string') {
                            options.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
                            options.body = params;
                        } else {
                            options.headers['Content-Type'] = 'application/json';
                            options.body = JSON.stringify(params);
                        }
                    }

                    const response = await fetch(url, options);
                    
                    // 处理重定向
                    if (response.redirected) {
                        console.log(`请求被重定向到: ${response.url}`);
                    }
                    
                    if (!response.ok) {
                        // 如果是重定向相关的状态码，尝试获取响应内容
                        if (response.status >= 300 && response.status < 400) {
                            const text = await response.text();
                            return { 
                                "error": "redirect_error", 
                                "message": `HTTP ${response.status} - ${response.statusText}`,
                                "redirect_url": response.url,
                                "response_text": text,
                                "status": response.status
                            };
                        }
                        throw new Error(`HTTP ${response.status} - ${response.statusText}`);
                    }
                    
                    // 尝试解析 JSON，如果失败则返回文本内容
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return await response.json();
                    } else {
                        const text = await response.text();
                        return { "content": text, "content_type": contentType, "final_url": response.url };
                    }
                } catch (error) {
                    return { "error": "fetch_failed", "message": error.message };
                }
            }
        """, {"url": url, "params": params, "extraHeaders": headers, "config": config})

        return response
    except Exception as e:
        raise send_exception()
        # return {"error": "fetch error", "message": str(e)}

def fetch_via_iframe(page: Page, target_domain: str, url: str, params: Optional[Union[dict, list, str]] = None, config:
Optional[dict] = None) -> dict:
    """
    方案 2：在 iframe 内部执行 fetch 请求，绕过 CORS 限制

    :param page: Playwright 的 Page 对象
    :param url: 目标请求的 URL
    :param target_domain: 目标 iframe 所在的域名（用于匹配 iframe）
    :param params: 请求参数（dict、list、str 或 None）
    :return: 服务器返回的 JSON 响应（dict）
    """
    if params is not None and not isinstance(params, (dict, list, str)):
        raise ValueError("params 参数必须是 dict、list、str 或 None")
    response = None
    try:
        # 获取所有 iframe，查找目标域名的 iframe
        frames = page.frames
        target_frame = None
        for frame in frames:
            if target_domain in frame.url:
                target_frame = frame
                break

        if not target_frame:
            return {"error": "iframe_not_found", "message": f"未找到包含 {target_domain} 的 iframe"}

        response = target_frame.evaluate("""
            async ({ url, params }) => {
                try {
                    const options = {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
                            'x-requested-with': 'XMLHttpRequest',
                        }
                    };

                    if (params !== null) {
                        if (typeof params === 'string') {
                            options.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
                            options.body = params;
                        } else {
                            options.headers['Content-Type'] = 'application/json';
                            options.body = JSON.stringify(params);
                        }
                    }

                    const response = await fetch(url, options);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status} - ${response.statusText}`);
                    }
                    return await response.json();
                } catch (error) {
                    return { "error": "iframe_fetch_failed", "message": error.message };
                }
            }
        """, {"url": url, "params": params})

        return response
    except Exception as e:
        raise send_exception()
        # return {"error": "iframe_exception", "message": str(e)}

# 找到一个页面里面所有的iframe
def find_all_iframe(page: Page):
    frames = page.frames
    for frame in frames:
        log("找到 iframe:", frame.url)
    return [frame.url for frame in frames]

# 全屏幕截图
def full_screen_shot(web_page: Page, config):
    # 设置页面的视口大小为一个较大的值，确保截图高清
    web_page.set_viewport_size({"width": 1920, "height": 1080})
    # 截取全页面的高清截图
    full_screenshot_image_path = f'{config.auto_dir}/screenshot/{get_current_datetime()}.png'
    web_page.screenshot(path=full_screenshot_image_path, full_page=True)
    return full_screenshot_image_path

def fetch_get(page: Page, url: str, headers: Optional[dict] = None, config: Optional[dict] = None) -> dict:
    """
    发送 HTTP GET 请求，支持自定义 headers 和配置，支持重定向处理。
    
    :param page: Playwright 的 Page 对象
    :param url: 请求地址
    :param headers: 自定义 headers 字典
    :param config: 请求配置字典，可包含 credentials, mode, referrer, referrerPolicy 等
    :return: 服务器返回的 JSON 响应（dict）
    """
    if headers is not None and not isinstance(headers, dict):
        raise ValueError("headers 参数必须是 dict 或 None")
    if config is not None and not isinstance(config, dict):
        raise ValueError("config 参数必须是 dict 或 None")

    try:
        page.wait_for_load_state('load')
        response = page.evaluate("""
            async ({ url, extraHeaders, config }) => {
                try {
                    const defaultHeaders = {
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                    };

                    const defaultConfig = {
                        method: 'GET',
                        credentials: 'include',
                        mode: 'cors',
                        redirect: 'follow'  // 明确设置跟随重定向
                    };

                    const headers = Object.assign({}, defaultHeaders, extraHeaders || {});
                    const options = Object.assign({}, defaultConfig, config || {}, { headers: headers });

                    const response = await fetch(url, options);
                    
                    // 处理重定向
                    if (response.redirected) {
                        console.log(`请求被重定向到: ${response.url}`);
                    }
                    
                    if (!response.ok) {
                        // 如果是重定向相关的状态码，尝试获取响应内容
                        if (response.status >= 300 && response.status < 400) {
                            const text = await response.text();
                            return { 
                                "error": "redirect_error", 
                                "message": `HTTP ${response.status} - ${response.statusText}`,
                                "redirect_url": response.url,
                                "response_text": text,
                                "status": response.status
                            };
                        }
                        throw new Error(`HTTP ${response.status} - ${response.statusText}`);
                    }
                    
                    // 尝试解析 JSON，如果失败则返回文本内容
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return await response.json();
                    } else {
                        const text = await response.text();
                        return { "content": text, "content_type": contentType, "final_url": response.url };
                    }
                } catch (error) {
                    return { "error": "fetch_failed", "message": error.message };
                }
            }
        """, {"url": url, "extraHeaders": headers, "config": config})

        return response
    except Exception as e:
        raise send_exception()

def safe_goto(page, url, **kwargs):
    caller = inspect.stack()[1]
    log(f"[DEBUG] goto called from {caller.filename}:{caller.lineno} url={url}")
    return page.goto(url, **kwargs)
