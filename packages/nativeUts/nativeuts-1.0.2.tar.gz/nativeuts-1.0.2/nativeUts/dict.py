from forbiddenfruit import curse

def explodeDict(dic:dict,key=None):
    adjust = {}
    for k,v in dic.items():
        if isinstance(v,dict):
            v = explodeDict(v,key=k)
            adjust = {**adjust,**v}
        else:
            kk = k if not key else f"{key}_{k}"
            adjust[kk]=v
    return adjust

def explodeListDict(dic): #[{},{}]
    adjust = []
    for r in dic:
        if isinstance(r,dict):
            adjust.append(explodeDict(r))
    return adjust

def keys_to_lower(dic:dict):
    new = {}
    for k,v in dic.items():
        new[k.lower()] = v
    return new

def rename_key(key,new_key,dic:dict):
    v = dic.pop(key)
    dic[new_key] = v
    return dic

def filter_keys(dic:dict,keys):
    return {k:y for k,y in dic.items() if k in keys}


curse(dict, "explodeDict", explodeDict)
curse(dict, "keys_to_lower", keys_to_lower)
curse(dict, "rename_key", rename_key)
curse(dict, "filter_keys", filter_keys)