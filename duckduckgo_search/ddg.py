from bs4 import BeautifulSoup

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from time import sleep

from .utils import SESSION, _do_output, _download_file, _get_vqd, _normalize

logger = logging.getLogger(__name__)


def ddg(
    keywords,
    region="wt-wt",
    safesearch="moderate",
    time=None,
    max_results=None,
    page=1,
    output=None,
    download=False,
):
    """DuckDuckGo text search. Query params: https://duckduckgo.com/params

    Args:
        keywords (str): keywords for query.
        region (str, optional): wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".
        safesearch (str, optional): on, moderate, off. Defaults to "moderate".
        time (Optional[str], optional): d, w, m, y. Defaults to None.
        max_results (Optional[int], optional): maximum number of results, max=200. Defaults to None.
            if max_results is set, then the parameter page is not taken into account.
        page (int, optional): page for pagination. Defaults to 1.
        output (Optional[str], optional): csv, json. Defaults to None.
        download (bool, optional): if True, download and save dociments to 'keywords' folder.
            Defaults to False.

    Returns:
        Optional[List[dict]]: DuckDuckGo text search results.
    """

    def get_ddg_page(page):
        payload["s"] = max(PAGINATION_STEP * (page - 1), 0)
        page_data = None
        try:
            resp = SESSION.get("https://links.duckduckgo.com/d.js", params=payload)
            resp.raise_for_status()
            page_data = resp.json().get("results", None)
        except Exception:
            logger.exception("")
        page_results = []
        if page_data:
            for row in page_data:
                if "n" not in row and row["u"] not in cache:
                    cache.add(row["u"])
                    body = _normalize(row["a"])
                    if body:
                        page_results.append(
                            {
                                "title": _normalize(row["t"]),
                                "href": row["u"],
                                "body": body,
                            }
                        )
        return page_results

    if not keywords:
        return None

    # get vqd
    vqd = _get_vqd(keywords)
    if not vqd:
        return None

    PAGINATION_STEP, MAX_API_RESULTS = 25, 200

    # prepare payload
    safesearch_base = {"On": 1, "Moderate": -1, "Off": -2}
    payload = {
        "q": keywords,
        "l": region,
        "t": "D",
        "p": safesearch_base[safesearch.capitalize()],
        "s": 0,
        "df": time,
        "o": "json",
        "vqd": vqd,
    }

    # get results
    cache = set()
    if max_results:
        results, page = [], 1
        max_results = min(abs(max_results), MAX_API_RESULTS)
        iterations = (max_results - 1) // PAGINATION_STEP + 1  # == math.ceil()
        with ThreadPoolExecutor(min(iterations, 4)) as executor:
            fs = []
            for page in range(1, iterations + 1):
                fs.append(executor.submit(get_ddg_page, page))
                sleep(min(iterations / 17, 0.3))  # sleep to prevent blocking
            for r in as_completed(fs):
                if r.result():
                    results.extend(r.result())

    else:
        results = get_ddg_page(page)

    results = results[:max_results]
    keywords = keywords.replace(" filetype:", "_")

    # save to csv or json file
    if output:
        _do_output("ddg", keywords, output, results)

    # download documents
    if download:
        print("Downloading documents. Wait...")
        keywords = keywords.replace('"', "'")
        path = f"ddg_{keywords}_{datetime.now():%Y%m%d_%H%M%S}"
        os.makedirs(path, exist_ok=True)
        futures = []
        with ThreadPoolExecutor(30) as executor:
            for i, res in enumerate(results, start=1):
                filename = res["href"].split("/")[-1].split("?")[0]
                future = executor.submit(
                    _download_file, res["href"], path, f"{i}_{filename}"
                )
                futures.append(future)
            for i, future in enumerate(as_completed(futures), start=1):
                logger.info("%s/%s", i, len(results))
                print(f"{i}/{len(results)}")
        print("Done.")

    return results


""" using html method
    payload = {
        'q': keywords,
        'l': region,
        'p': safesearch_base[safesearch],
        'df': time
        }
    results = []
    while True:
        res = SESSION.post('https://html.duckduckgo.com/html', data=payload, **kwargs)
        tree = html.fromstring(res.text)
        if tree.xpath('//div[@class="no-results"]/text()'):
            return results
        for element in tree.xpath('//div[contains(@class, "results_links")]'):
            results.append({
                'title': element.xpath('.//a[contains(@class, "result__a")]/text()')[0],
                'href': element.xpath('.//a[contains(@class, "result__a")]/@href')[0],
                'body': ''.join(element.xpath('.//a[contains(@class, "result__snippet")]//text()')),
            })
        if len(results) >= max_results:
            return results
        next_page = tree.xpath('.//div[@class="nav-link"]')[-1]
        names = next_page.xpath('.//input[@type="hidden"]/@name')
        values = next_page.xpath('.//input[@type="hidden"]/@value')
        payload = {n: v for n, v in zip(names, values)}
        sleep(2)
"""



final_results = {"info": {"query": "", "next": bool(True)}, "results": []}
page = 1

def ddg_n(keyword, region="wt-wt", safesearch="moderate", time=None, max_results=25, group=1, final=final_results, page=page):

    if final["info"]["query"] == keyword:
        pass
    else:
        final["results"] = []
        final["info"]["query"] = keyword
        page = 1
    #get vqd
    vqd = _get_vqd(keyword)
    if not vqd:
        return None
    
    #set parameters
    safesearch_base = {"On": 1, "Moderate": -1, "Off": -2}
    payload = {"q": keyword, "l": region, "t": "D", "p": safesearch_base[safesearch.capitalize()], "s": 0, "df": time, "o": "json", "vqd": vqd}

    #get results
    while True:
        resp = SESSION.get("https://html.duckduckgo.com/html", params=payload)
        soup = BeautifulSoup(resp.content, 'lxml')
        urls = soup.find_all("a", {"class": "result__url"})
        titles = soup.find_all("a", {"class": "result__a"})
        bodies = soup.find_all("a", {"class": "result__snippet"})

        for i in range(len(urls)):
            result = {"url": str(urls[i].text), "title": str(titles[i].text), "body": str(bodies[i].text)}
            final["results"].append((result))
        if len(final["results"]) < (max_results * group):
            payload["s"] = len(final["results"])
            page += 1
            continue
        else: break
    try:
        wanted_results = final["results"][(max_results * group) - max_results:(max_results * group)]
        return {"info": final["info"], "results": wanted_results}
    except:
        wanted_results = final["results"][(max_results* group) - max_results:]
        final["info"]["next"] = False
        return {"info": final["info"], "results": wanted_results}