#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巨潮资讯网公告检索与 PDF 下载工具（ESG 报告 / 制度公告采集）

用法:
    python3 cninfo_searcher.py 宁德时代
    python3 cninfo_searcher.py 300750 --kws "ESG" "可持续发展" "社会责任"
    python3 cninfo_searcher.py 宁德时代 --out ./downloads --download

说明:
- 巨潮全文检索接口的 stock 过滤参数已失效，本脚本改用「公司简称/代码 + 关键词」标题检索，
  并自动尝试多个关键词变体后合并去重（报告标题措辞不统一：ESG报告 / 可持续发展报告 / 社会责任报告）。
- 沪深 A 股代码↔简称映射来自巨潮官方 szse_stock.json；港股等无映射时直接用输入词检索。
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

import requests

SEARCH_URL = "https://www.cninfo.com.cn/new/fulltextSearch/full"
STOCK_MAP_URL = "https://www.cninfo.com.cn/new/data/szse_stock.json"
DOWNLOAD_BASE = "https://static.cninfo.com.cn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.cninfo.com.cn/",
}
# 全局会话：巨潮接口依赖首次响应种下的 Cookie，散装请求会漏结果
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
DEFAULT_KEYWORDS = ("ESG", "可持续发展", "环境、社会", "社会责任")
# 巨潮接口连续请求会被限频导致漏结果：关键词之间留间隔，空结果重试
QUERY_INTERVAL_SEC = 1.5
EMPTY_RETRY = 2
EMPTY_RETRY_WAIT_SEC = 2


def load_stock_map():
    """拉取沪深 A 股代码映射。返回 {code: (简称, orgId)}；失败返回空 dict。"""
    try:
        r = SESSION.get(STOCK_MAP_URL, timeout=20)
        r.raise_for_status()
        return {x["code"]: (x.get("zwjc", ""), x.get("orgId", ""))
                for x in r.json().get("stockList", [])}
    except Exception as e:
        print(f"代码映射获取失败（改用输入词直接检索）: {e}", file=sys.stderr)
        return {}


def resolve_company(query, stock_map):
    """输入代码或简称，返回 (代码, 检索用简称)；非上市公司返回 (None, query)。"""
    q = query.strip()
    if q in stock_map:
        name, _ = stock_map[q]
        return q, name
    for code, (name, _) in stock_map.items():
        if name and (name == q or q in name):
            return code, name
    return None, q


def search_once(searchkey, date_from, date_to, page_size=20):
    """单次标题检索（空结果自动重试）。返回 [{title, date, url, id}]"""
    data = {
        "searchkey": searchkey,
        "sdate": date_from, "edate": date_to,
        "isfulltext": "false",
        "sortName": "pubdate", "sortType": "desc",
        "pageNum": 1, "pageSize": page_size,
    }
    for attempt in range(EMPTY_RETRY + 1):
        try:
            r = SESSION.post(SEARCH_URL, data=data, timeout=15)
            r.raise_for_status()
            out = []
            for ann in (r.json().get("announcements") or []):
                title = re.sub(r"<[^>]+>", "", ann.get("announcementTitle", ""))
                adjunct = ann.get("adjunctUrl", "")
                if title and adjunct:
                    dm = re.search(r"finalpage/(\d{4}-\d{2}-\d{2})", adjunct)
                    out.append({
                        "title": title,
                        "date": ann.get("announcementDate") or (dm.group(1) if dm else ""),
                        "url": f"{DOWNLOAD_BASE}/{adjunct}",
                        "id": ann.get("announcementId", ""),
                    })
            if out or attempt == EMPTY_RETRY:
                return out
            time.sleep(EMPTY_RETRY_WAIT_SEC)
        except Exception as e:
            if attempt == EMPTY_RETRY:
                print(f"检索失败（{searchkey}）: {e}", file=sys.stderr)
                return []
            time.sleep(EMPTY_RETRY_WAIT_SEC)
    return []


def search_company(query, keywords=None, date_from="2018-01-01", date_to="", page_size=20):
    """多关键词变体检索并合并去重。返回 [{title, date, url, id}]，按日期倒序。"""
    keywords = keywords or DEFAULT_KEYWORDS
    date_to = date_to or datetime.now().strftime("%Y-%m-%d")
    _, name = resolve_company(query, load_stock_map())
    seen, results = set(), []
    for i, kw in enumerate(keywords):
        if i:
            time.sleep(QUERY_INTERVAL_SEC)
        for item in search_once(f"{name} {kw}", date_from, date_to, page_size):
            if item["id"] and item["id"] not in seen:
                seen.add(item["id"])
                results.append(item)
    results.sort(key=lambda x: x["date"], reverse=True)
    return results


def download_pdf(pdf_url, output_dir=".", filename=None):
    """下载公告 PDF。成功返回文件路径，失败返回 None。"""
    os.makedirs(output_dir, exist_ok=True)
    if not filename:
        filename = pdf_url.rsplit("/", 1)[-1]
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
    try:
        r = SESSION.get(pdf_url, timeout=30)
        if r.status_code == 200 and len(r.content) > 5000:
            fp = os.path.join(output_dir, filename)
            with open(fp, "wb") as f:
                f.write(r.content)
            return fp
        print(f"下载失败（状态码: {r.status_code}）", file=sys.stderr)
        return None
    except Exception as e:
        print(f"下载出错: {e}", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser(description="巨潮资讯网公告检索与 PDF 下载")
    ap.add_argument("company", help="公司简称或股票代码")
    ap.add_argument("--kws", nargs="*", default=list(DEFAULT_KEYWORDS),
                    help="关键词变体（默认 ESG/可持续发展/社会责任/环境、社会）")
    ap.add_argument("--from", dest="date_from", default="2018-01-01")
    ap.add_argument("--to", dest="date_to", default="")
    ap.add_argument("--limit", type=int, default=30, help="每个关键词的最大结果数")
    ap.add_argument("--out", default=".", help="下载目录")
    ap.add_argument("--download", action="store_true", help="下载全部结果 PDF")
    args = ap.parse_args()

    results = search_company(args.company, args.kws, args.date_from, args.date_to, args.limit)
    if not results:
        print("未找到相关公告（可尝试更换关键词变体或扩大日期范围）")
        sys.exit(1)
    for item in results:
        print(f"[{item['date']}] {item['title']}")
        print(f"  {item['url']}")
    print(f"\n共 {len(results)} 条")
    if args.download:
        for item in results:
            fp = download_pdf(item["url"], args.out)
            print(("已下载: " + fp) if fp else ("下载失败: " + item["url"]))


if __name__ == "__main__":
    main()
