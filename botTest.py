import os, json
import praw, pymongo
import keys
import time
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

client = pymongo.MongoClient('mongodb+srv://dbUser:'+keys.password+'@redditcontext-yp9rl.mongodb.net/test?retryWrites=true&w=majority')

reddit = praw.Reddit('contextBot')

subreddits = ["pythonforengineers"]#,"publicFreakout", "instantKarma"]

'''
THINGS YOU CAN PULL FROM READ QUERIES

post comes in as a POST ID

['approve', # Cant See (unless mod ?)
'approved_by',  | same as approve (?) Idk, comes back None type
'author',       
 
'domain', # Website it's posted on (youtube, v.reddit, imgur, etc)
'downs', # comes in as int
'downvote', # type method which acts on post with certain ID
'edit', # method which acts on post with certain ID
'edited', # bool value
 
'saved',
 
'score',
'secure_media',
'secure_media_embed',
'selftext',
'selftext_html',
 
'title', # in as string
 
'ups',
'upvote',
'url',
'user_reports', #Mod stuff
'visited', #bool
'vote']
'''



def get_posts_replied_to():
    global posts_replied_to
    if not os.path.isfile("posts_replied_to.json"):
        print("FILE PATH NOT FOUND")
        posts_replied_to = {}
    else:
        with open("posts_replied_to.json", "r") as f:
            posts_replied_to = json.load(f)
            
    

def addContext(post, comment):
    #Default context
    context = "Context bot can't find context for this"

    context = comment.body.split()
    context = ' '.join(context[1:])
    print("Post join context: " + context)
    
    if "://" in context or "www." in context: #is link
        print("Content contains reddit link")
        if "reddit.com" in context: #is reddit link
            print("context contains reddit link")
            for i in posts_replied_to:
                if posts_replied_to[i]['url'] == context:
                    context = posts_replied_to[i]['context'] #transfer context
                    break
            print("CONTEXT reddit: " + context)
            posts_replied_to[post.id]["context"] = context #set new link to new reddit
            print("POST CONTEXT reddit: " + posts_replied_to[post.id]["context"])
        else:
            print("CONTEXT link: " + context)
            posts_replied_to[post.id]["context"] = context #set link + txt
            print("POST CONTEXT link: " + posts_replied_to[post.id]["context"])  
    else:
        print("Content contains no link")
        posts_replied_to[post.id]["context"] = context
        print("Context added to database: " + context) #server side log
        comment.reply("Context is now: " + context + " \n\nThanks for helping out!\n\n ^(*This action was performed by a bot beep boop*)") #user side validation

def replyComment(post, comment):
    if post.id not in posts_replied_to:
        print("Post not in list")
        posts_replied_to[post.id] = {
                        "post_title": post.title,
                        "post_subreddit": str(post.subreddit),
                        "post_id": post.id,
                        "post_text": str(post.selftext),
                        "url" : str(post.url),
                        "context": ""
                    }
    if len(comment.body.split()) > 1: 
        addContext(post, comment)
    else:
        if len(posts_replied_to[post.id]["context"]) > 1:
            print("Context exists")
            comment.reply("Context for this post is: " + posts_replied_to[post.id]["context"])
            print("Replied context \n")
        else:
            print("Context doesn't exist")
            comment.reply("Context doesn't exist yet. If you'd like to add some, you can do a few things:\n\n1. You can link to a post that also has context using the format *u/addContext_bot <link>*\n\nOR\n\n2. you can make your own with news articles using the same format\n\n ^(*This action was performed by a bot beep boop*)")
            print("Replied context")
    with open("posts_replied_to.json", "w") as f:
        json.dump(posts_replied_to, f, indent=4)



def send_to_db(data):
    print("\n\nSENDING TO DATABASE")
    try:
        client.postData.posts.delete_many(data)
    except Exception as e:
        print(e)
    collection = client.postData.posts
    try:
        
        collection.insert(data)
    except Exception as e:
        pass

#Delete count of posts -- if you need a clean slate
def purge(count = 1000):
    mee = reddit.user.me()
    i = 1
    for c in mee.comments.new(limit=count):
        c.edit("#")
        c.delete()
        print("Deleted " + str(i))
        i += 1

#get if people mention
def getMentions():
    
    for item in reddit.inbox.unread(limit=None):
        if isinstance(item, praw.models.Comment) and "u/addContext_bot":
            mention=item
            print("MENTION: " + str(mention))
            print("MENTION TEXT: " + str(mention.body))
            post = mention.submission
            replyComment(post, mention)
        item.mark_read()    

get_posts_replied_to()
getMentions()

send_to_db(posts_replied_to)

# purge()