# -*- coding: utf-8 -*-
import asyncio
import base64
import hashlib
import json
import random
import re
import time
import traceback
from typing import Dict, List, Any
from urllib.parse import urlparse

import primp

from loguru import logger

async def get_akamai_ck(proxy) -> dict:
    akamai_url = f"http://45.207.195.220:5001/akamai/v3?token={token}"
    json_data = {
        "target_url": "https://www.jetstar.com/hk/zh/home?adults=1&flight-type=2&origin=PVG",
        "proxy": proxy,
        "site_key": "jetstar",
    }
    async with primp.AsyncClient(timeout=70) as client:
        response = await client.post(url=akamai_url, json=json_data)
    print(response.status_code, response.text)
    if response.json()["code"] == 1:
        return response.json()["data"]
    return None
    # akm = AKmV3Crack(index_url=json_data["target_url"], proxy=proxy, device_index=0, country="HK", site_key="jetstar")
    # result = await akm.crack(alogo_num=3)
    # return result


def solve_challenge(sec_cpt: str, pow_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    批量求解 PoW，返回 answers 数组（即多次命中的 pV 列表）。
    """

    def sha256(kV: str) -> bytes:
        return hashlib.sha256(kV.encode("utf-8")).digest()

    def Nj(digest: bytes, difficulty: int) -> int:
        return int.from_bytes(digest, "big", signed=False) % difficulty

    def js_math_random_hex():
        return f'0.{format(random.getrandbits(53), "013x").lstrip("0")}'

    difficulty = pow_dict["difficulty"]
    count = int(pow_dict.get("count", 1))
    timestamp = pow_dict["timestamp"]
    nonce = pow_dict["nonce"]
    IV = f'{str(sec_cpt).split("~")[0]}{timestamp}{nonce}'
    dur = pow_dict.get("chlg_duration") or pow_dict.get("duration") or 5
    try:
        ttl_ms = int(float(dur) * 1000)
    except Exception:
        ttl_ms = 5000
    guard_ms = 100  # 余量，避免临界提交时超时
    answers: List[str] = []
    t0 = time.perf_counter()

    while len(answers) < count:
        # 超时保护：在循环内频繁检查，避免无谓计算
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        if elapsed_ms >= (ttl_ms - guard_ms):
            # 解算时间已逼近/超过 TTL，直接退出，由上层重新拉 challenge
            raise Exception("PoW 计算超过挑战窗口/已过期，需要重新获取 challenge")
        pV = str(js_math_random_hex())
        kV = f"{IV}{difficulty}{pV}"
        mV = sha256(kV)
        if Nj(mV, difficulty) == 0:
            answers.append(pV)
    return {
        "token": pow_dict["token"],
        "answers": answers,
    }


async def sec_verify(
        ua: str,
        pow_dict: dict,
        client,
        retries: int = 5,
) -> Dict[str, str]:
    headers = {
        'accept': '*/*',
        'content-type': 'text/plain;charset=UTF-8',
        'origin': 'https://booking.jetstar.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'user-agent': ua,
        'referer': 'https://booking.jetstar.com/captcha/adaptivecheck.html',
        'sec-fetch-dest': 'empty',
        'accept-language': 'zh-CN,zh-Hans;q=0.9',
        'priority': 'u=3, i',
        'accept-encoding': 'gzip, deflate, br',
    }
    url = "https://booking.jetstar.com/_sec/verify"
    params = {
        "provider": "adaptive"
    }
    for attempt in range(1, retries + 1):
        sec_cpt = client.get_cookies(f"{urlparse(url).scheme}://{urlparse(url).netloc}").get("sec_cpt")
        try:
            json_data = solve_challenge(sec_cpt=sec_cpt, pow_dict=pow_dict)
        except Exception as e:
            raise Exception(str(e))

        resp = await client.post(url, headers=headers, params=params, json=json_data)
        txt = resp.text
        logger.debug(f"pow verify (attempt {attempt}/{retries}): {txt}")

        if resp.status_code == 403:
            raise Exception("pow验证被拒绝403")

        # 解析响应
        try:
            data = resp.json()
        except Exception:
            if attempt == retries:
                raise Exception(f"pow验证失败：非 JSON 响应 {txt[:200]}")
            continue

        if data.get("success"):
            # ✅ 成功且无 token => 通过
            if not data.get("token"):
                # 合并服务端下发的新 cookie（如果有）
                logger.info("✅️ pow验证成功，更新cookie")
                return resp.cookies
        # 成功但给了 token => 站点需要继续 cp_challenge/verify
        if data.get("token") and data.get("nonce") and data.get("timestamp"):
            logger.warning("pow验证成功但返回 token，需继续 cp_challenge/verify")
            pow_dict = data
            continue
        logger.warning("❌️ pow验证失败（无新挑战参数），需要重新获取challenge")
        raise Exception("pow验证失败（无新挑战参数），需要重新获取challenge")
    raise Exception("pow验证失败，达到最大重试次数")


async def verify(ua: str, client):
    headers = {
        'sec-fetch-dest': 'empty',
        'user-agent': ua,
        'accept': '*/*',
        'referer': 'https://booking.jetstar.com/hk/zh/booking/select-flights',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'accept-language': 'zh-CN,zh-Hans;q=0.9',
        'priority': 'u=3, i',
        'accept-encoding': 'gzip, deflate, br',
    }
    url = "https://booking.jetstar.com/_sec/cp_challenge/verify"
    response = await client.get(url, headers=headers)
    if response.json()["success"]:
        logger.success(f"✅️ pow最终验证成功，更新cookie")
        return response.cookies
    else:
        logger.error(f"❌️ pow失败")
        return None


async def crack_pow(ua, pow_dict: dict, client) -> dict:
    await sec_verify(ua, pow_dict, client=client)
    await asyncio.sleep(1)
    sec_cookies = await verify(ua, client)
    return sec_cookies


async def get_jetstar_search():
    proxy = get_proxy()
    akamai_result = await get_akamai_ck(proxy)
    logger.debug(f"获取akamai: {akamai_result}")
    cookies = akamai_result["ck"]
    headers = {
        'sec-fetch-dest': 'document',
        'user-agent': akamai_result["ua"],
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'referer': 'https://www.jetstar.com/',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'navigate',
        'accept-language': 'zh-CN,zh-Hans;q=0.9',
        'priority': 'u=0, i',
        'accept-encoding': 'gzip, deflate, br',
    }
    url = "https://booking.jetstar.com/hk/zh/booking/search-flights"
    params = {
        "origin1": "PVG",
        "destination1": "CNS",
        "departuredate1": "2025-12-26",
        "adults": "1",
        "children": "0",
        "infants": "0",
        "dotcomFCPricesHidden": "false",
        "dotcomFCOutboundCorrelationId": "54dd4743-f27e-4a5a-afd7-487a3dc005c3",
        "dotcomFCOutboundIncludeMember": "False",
        "dotcomFCOutboundPriceShown": "false",
        "pid": "destinations-flights-widget"
    }
    start_time = time.time()
    # primp
    for i in range(10):
        async with primp.AsyncClient(proxy=proxy, impersonate="safari_26.1", impersonate_os="macos", http2_only=False) as client:
            client.set_cookies(f"{urlparse(url).scheme}://{urlparse(url).netloc}", cookies)
            # for key, value in cookies.items():
            #     client.set_cookie(key, value)
            response = await client.get(url, headers=headers, params=params)
        if 'bundle-data-v2' in response.text:
            logger.success(f"✅ [耗时 {time.time() - start_time:.2f}s] 搜索成功\t{response.status_code}")
            return response.text
        elif "请稍候片刻" in response.text:
            logger.warning(f"⚠️ [耗时 {time.time() - start_time:.2f}s] 触发速率限制，等待10秒后重试...")
            # await asyncio.sleep(10)
        else:
            logger.warning(
                f"⚠️ [耗时 {time.time() - start_time:.2f}s] 搜索失败: {response.status_code}\t{response.text}")
            if "challenge=" in response.text:
                logger.warning(f"触发pow挑战页面...")
                challenge = re.findall(r'challenge="(.*?)"', response.text)[0]
                pow_dict = json.loads(base64.b64decode(challenge).decode("utf-8"))
                logger.info(f"pow_dict: {pow_dict}")
                sec_cookies = await crack_pow(akamai_result["ua"], pow_dict, client=client)
                logger.info(f"更新后的cookie: {sec_cookies}")
                cookies.update(sec_cookies)
    raise Exception(f"搜索失败，达到最大重试次数")


async def main():
    """
    降低并发，添加任务间延迟，避免触发速率限制和 HTTP/2 stream error
    """
    semaphore = asyncio.Semaphore(10)

    total_count = 0
    success_count = 0
    error_count = 0

    async def submit_task(task_id):
        nonlocal total_count, success_count, error_count
        async with semaphore:
            try:
                result = await get_jetstar_search()
                success_count += 1
                total_count += 1
                logger.info(
                    f"[任务 {task_id}] ✅ 成功率: {success_count / total_count * 100:.2f}% (总成功: {success_count} / 总计: {total_count})")
                return result
            except Exception as e:
                error_count += 1
                total_count += 1
                logger.error(f"[任务 {task_id}] ❌ 失败: {e} (总失败: {error_count})")

    # 🔧 减少任务数：从 1000 -> 100（测试用）
    tasks = [submit_task(i) for i in range(10000)]
    await asyncio.gather(*tasks)

    logger.info(f"\n📊 最终统计: 成功 {success_count}, 失败 {error_count}")


def get_proxy():
    proxy = f"http://chivalry_jy-country-HK:EG3JGXL-UUD7ZOC-JVUH4JJ-26QXCIR-LE9YQI7-TMBLUU8-A4ZQWEN@unmetered.residential.proxyrack.net:{random.randint(10000, 10999)}"
    # proxy = f"https://chivalry_jy-country-AU:EG3JGXL-UUD7ZOC-JVUH4JJ-26QXCIR-LE9YQI7-TMBLUU8-A4ZQWEN@unmetered.residential.proxyrack.net:9001"
    # proxy = "http://127.0.0.1:7890"
    # proxy = "http://juluser1-country-hk:juluser1@private-eu-v2.proxyventure.io:7777"
    proxy = f"http://B_62370_HK_3865_66511_5_FuVeGMkf:zhu123@gate2.ipweb.cc:7778"
    # data = primp.get("http://asapi.lumidaili.com:9988/iplist?passageId=12959&secret=hbe6DS&num=1&protocol=http&format=2&split=1&region=hk").json()
    # ip = data["data"][0]["ip"]
    # port = data["data"][0]["port"]
    # proxy = f"http://{ip}:{port}"
    return proxy


if __name__ == '__main__':
    # proxy = f"https://chivalry_jy-country-jp:EG3JGXL-UUD7ZOC-JVUH4JJ-26QXCIR-LE9YQI7-TMBLUU8-A4ZQWEN@unmetered.residential.proxyrack.net:10001"
    token = "3240273cffc4a9b7af8e3c11bff6a881"
    for i in range(1):
        try:
            asyncio.run(get_jetstar_search())
        except Exception as e:
            logger.error(traceback.format_exc())
    exit()
    asyncio.run(main())