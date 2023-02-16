from duckduckgo_search import ddg_n

def search_web(query, region='wt-wt', time=None, group=1):
    if query != '' and query != None and query.startswith('!') != True:
        results = ddg_n(keyword=query, region=region, safesearch="On", time=time, group=group)
        print(results)
    else: results = []
    return results