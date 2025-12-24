import re
DEFINITIION_ALIAS = {
    "text":{"alias":["text","post","content","tweet","thread","body"],"description":"The main text."},
    "url":{"alias":["url","u","link","site","domain","intentUrl","link_address","address","canonical",'path'],"description":"A URL to include in the post."},
    "via":{"alias":["via","username","user","@","uploader","author"],"description":"A username to attribute the post to."},
    "hashtags":{"alias":["hashtags","hashtag","tag","tags"],"description":"Comma-separated hashtags (without the # symbol)."},
    "related":{"alias":["related","contributor","credit","cc","bcc"],"description":"Comma-separated related accounts."},
    "subject":{"alias":["title","subject","heading","header"],"description":"The email subject."},
    "body":{"alias":["text","post","content","tweet","thread","body"],"description":"The email body."},
    "cc":{"alias":["related","contributor","credit","cc","bcc"],"description":"Additional email addresses."},
    "bcc":{"alias":["related","contributor","credit","cc","bcc"],"description":"Additional email addresses."}
}
def get_alias_params(string):
    return DEFINITIION_ALIAS.get(string)
SOCIAL_SHARE_PARAMS={
    "x":{
        "url":"https://twitter.com/intent/tweet",
        "params":{
            "text":get_alias_params("text"),
            "url":get_alias_params("url"),
            "via":get_alias_params("via"),
            "hashtags":get_alias_params("hashtags"),
            "related":get_alias_params("related")
            },
        "characters":{"limit":280,"optimal":100,"mobile_cutoff":150,"url_len":30},
        "alias":["x","twitter","x.com","tweet","twitter.com"],
        "hash_symbol":False
        },
     "facebook":{
         "url":"http://facebook.com/sharer.php",
         "params":{
             "u":get_alias_params("url")
             },
         "characters":{"limit":63206,"optimal":50,"mobile_cutoff":150,"url_len":None},
         "alias":["facebook","fb","facebook.com","meta","meta.com"],
         "hash_symbol":True
         },
    
     "threads":{
         "url":"https://www.threads.net/intent/post",
         "params":{
             "text":get_alias_params("text")
             },
         "characters":{"limit":500,"optimal":150,"mobile_cutoff":150,"url_len":None},
         "alias":["threads","@","threads.com","@.com"],
         "hash_symbol":True
         },
    "mailto":{
        "url":"mailto:",
        "params":{
             "subject":get_alias_params("subject"),
             "body":get_alias_params("body"),
             "cc":get_alias_params("cc"),
             "bcc":get_alias_params("bcc")
             },
        "characters":{"limit":None,"optimal":None,"mobile_cutoff":None},
        "alias":["mailto","mail","email","email.com","mail.com"],
        "hash_symbol":True
        },
    "minds":{
        "url":"https://www.minds.com/newsfeed/subscriptions/latest",
        "params":{
            "intentUrl":get_alias_params("url")
            },
        "characters":{"limit":500,"optimal":125,"mobile_cutoff":150,"url_len":None},
        "alias":["minds","mindscollective","collective"],
        "hash_symbol":True
        }
             
    }

META_VARS = {
    "title": {"min": [20, 30], "max": [50,60]},
    "description": {"min": [70, 100], "max": [150, 160]},
    "alt": {"min": [10, 20], "max": [100, 125]},
    "context": {"min": [20, 30], "max": [70, 100]},
    "keywords": {"min": [10, 20], "max": [200, 250]}
}
ATTR_RE = re.compile(r'([a-zA-Z0-9:_-]+)\s*=\s*([\'"`])([^\'"`]+)\2')
TAG_OPEN_RE = re.compile(r'<\s*([a-zA-Z0-9:_-]+)')
TAG_CONTENT_RE = re.compile(r'<\s*([a-zA-Z0-9:_-]+)[^>]*>(.*?)</\s*\1\s*>', re.DOTALL)
