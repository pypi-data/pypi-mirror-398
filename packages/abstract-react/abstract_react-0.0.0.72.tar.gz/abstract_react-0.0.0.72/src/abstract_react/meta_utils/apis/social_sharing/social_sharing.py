from ...imports import *
#from abstract_webserver import create_post_url,get_alias_params
api_data_bp = Blueprint('api_data_bp', __name__)
logger = get_logFile('api_data_bp')

@api_data_bp.route('/api/get-tweet', methods=['GET', 'POST'])
def renderTweet():
    data = get_request_data(request)
    # Update the in-memory store.
    try:
        keywords = data.get('keywords')
        pageTitle = data.get('pageTitle')
        description = data.get('description')
        title = data.get('title')
        path = data.get('path')
        link_address = data.get('link_address')
        
        tweet_content = prepare_tweet(
            keyWords,
            pageTitle,
            description,
            title,
            path,
            link_address
            )
        if tweet_content:
            return jsonify({"result": tweet_content}), 200
        return jsonify({"error": "image not found"}), 400
    except IndexError:
        return jsonify({"error": "Index out of range"}), 500


@api_data_bp.route('/api/get-post-url', methods=['GET', 'POST'])
def renderPostUrl():
    data = get_request_data(request)
    # Update the in-memory store.
    try:
        platform = data.get('platform')
        
        text = get_post_text(data)
        
        url = get_data_from_alias(data,'url')
        
        via = get_data_from_alias(data,'via')
        
        hashtags = get_data_from_alias(data,'hashtags')
        
        post_url = create_post_url(platform,text=text,url=url,via=via,hashtags=hashtags)
        
        if post_url:
            return jsonify({"result": post_url}), 200
        return jsonify({"error": "post url not found"}), 400
    except Exception as e:
        return jsonify({"error": f"{e}"}), 500

