

from collections import namedtuple, defaultdict
from itertools import zip_longest
import tweepy
from datetime import datetime
import re

from unidecode import unidecode
from unicodedata import normalize


#############################################################
#      Code related to dealing with UserRecords             #
#############################################################

# A user record named tuple to make it easier to get a bunch of data. Could
# be replaced with a class. 
UserRecord = namedtuple('UserRecord',['id','id_str','name','screen_name','location',
                                      'followers_count','friends_count','favourites_count',
                                      'description','geo_enabled','lang','statuses_count',
                                      'time_zone','created_at','verified','utc_offset',
                                      'contributors_enabled','listed_count','protected',
                                      'url'])

def build_user_record(json_obj) :
    
    ''' Takes in a json object from tweepy's lookup_users
        and returns a UserRecord made from the object.
    '''
    ret_val = UserRecord(json_obj['id'],
                         json_obj['id_str'],
                         json_obj['name'],
                         json_obj['screen_name'],                     
                         json_obj['location'],
                         json_obj['followers_count'],
                         json_obj['friends_count'],
                         json_obj['favourites_count'],
                         json_obj['description'],
                         json_obj['geo_enabled'],
                         json_obj['lang'],
                         json_obj['statuses_count'],
                         json_obj['time_zone'],
                         json_obj['created_at'],
                         json_obj['verified'],
                         json_obj['utc_offset'],
                         json_obj['contributors_enabled'],
                         json_obj['listed_count'],
                         json_obj['protected'],
                         json_obj['url'])

    return(ret_val)
                       
                     
def write_user_rec_headers(fhandle) :
    
    headers = ['screen_name','name','id','location',
               'followers_count','friends_count','description']
        
    fhandle.write("\t".join(headers) + "\n")


def write_user_rec(fhandle, the_rec) :
    oline = [the_rec.screen_name, the_rec.name, the_rec.id,
             the_rec.location, the_rec.followers_count, 
             the_rec.friends_count, the_rec.description]    

    fhandle.write("\t".join([parse_it(str(item)) for item in oline]) + "\n")

#############################################################
#              Helper functions                             #
#############################################################    
def grouper(n, iterable, padvalue=None):
    ''' Partitions an iterable into groups of size `n`. If there are empty
        spots in the final group they are padded with `padvalue`. It should be 
        clear, I just found this in the docs here: https://docs.python.org/3/library/itertools.html 
        
        "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')" '''
    args = [iter(iterable)] * n    
    return(zip_longest(*args, fillvalue=padvalue) )

    
#############################################################
#              Twitter functions                            #
#############################################################        
def initialize_twitter(auth) :
    consumer_key = auth['consumer_key']
    consumer_secret = auth['consumer_secret']
    access_token = auth['access_key']
    access_token_secret = auth['access_secret']
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return(tweepy.API(auth,
                     parser=tweepy.parsers.JSONParser(),
                     wait_on_rate_limit=True,
                     wait_on_rate_limit_notify=True))
 
 
def lookup_users_from_ids(api,ids) :
    ''' 
        Hydrates user records starting with IDs. Needs some tricky
        error handling because Twitter's `lookup_users` will fail
        on things like closed accounts. Since we process in a
        batch of 100, we have to do some work to figure out which
        one failed and get the others in that batch.
        
        Returns a dictionary with key of ID and value of UserRecord.
    '''
 
    print("Start lookup_users_from_ids on {} IDs.".format(len(ids)))
    ret_dict = defaultdict(UserRecord)

    total_processed = 0
    failures = 0
    
    # Begin by chunking the IDs into sets of 100
    chunks = grouper(100,ids) 

    for chunk in chunks :
        # Grouper pads with None by default, so drop those. 
        # TODO: only need to check last chunk...
        chunk = [a for a in chunk if a is not None]

        print(datetime.now().strftime("%Y%m%d-%H%M%S") +
            ": looking up user records for " + str(len(chunk)) + " IDs.")
        
        try:
            users_data = api.lookup_users(user_ids=chunk)
            total_processed += len(chunk)
            for this_user_data in users_data :
                ret_dict[this_user_data['id']] = build_user_record(this_user_data)            
        except:
            # if we end up here, we should step through the 
            # users one at a time.             
            for id in chunk :
                good_pull = False
                try :
                    this_user_data = api.lookup_users(user_ids=id)
                    total_processed += 1
                    good_pull = True
                except :
                    failures += 1
                
                if good_pull :
                    ret_dict[this_user_data['id']] = build_user_record(this_user_data)            
                
    print(datetime.now().strftime("%Y%m%d-%H%M%S") + ':  users pulled:  ' + str(total_processed))
    print('total failures: '+str(failures))
    return(ret_dict)
    

def lookup_users_from_handles(api,handles) :
    ''' 
        Hydrates user records starting with handles. Needs some tricky
        error handling because Twitter's `lookup_users` will fail
        on things like closed accounts. Since we process in a
        batch of 100, we have to do some work to figure out which
        one failed and get the others in that batch.
        
        Returns a dictionary with key of ID and value of UserRecord.
    '''
 
    print("Start lookup_users_from_ids on {} handles.".format(len(handles)))
    ret_dict = defaultdict(UserRecord)

    total_processed = 0
    failures = 0
    
    # Begin by chunking the handles into sets of 100
    chunks = grouper(100,handles) 

    for chunk in chunks :
        # Grouper pads with None by default, so drop those. 
        # TODO: only need to check last chunk...
        chunk = [a for a in chunk if a is not None]

        print(datetime.now().strftime("%Y%m%d-%H%M%S") + 
            ": looking up user records for " + str(len(chunk)) + " handles.")

        try:
            users_data = api.lookup_users(screen_names=chunk)
            total_processed += len(chunk)
            for this_user_data in users_data :
                ret_dict[this_user_data['id']] = build_user_record(this_user_data)            
        except:
            # if we end up here, we should step through the 
            # users one at a time.             
            for handle in chunk :
                good_pull = False
                try :
                    this_user_data = api.lookup_users(screen_names=handle)
                    total_processed += 1
                    good_pull = True
                except :
                    failures += 1
                
                if good_pull :
                    ret_dict[this_user_data['id']] = build_user_record(this_user_data)            
                
    print(datetime.now().strftime("%Y%m%d-%H%M%S") + ':  users pulled:  ' + str(total_processed))
    print('total failures: '+str(failures))
    return(ret_dict)

    
    
def gather_followers(api, ids, follower_limit = 10000, file_name=None) :
    ''' from a set of IDs, get all the followers of those ids up to follower
        limit. Returns a dictionary with key = id, value = follower_id list
    '''
    
    ret_dict = defaultdict(list)    
    
    for this_id in ids :
        print("Pulling followers for " + str(this_id))        
        pulled_followers = 0
        try :
            for page in tweepy.Cursor(api.followers_ids,user_id = this_id).pages() :
                pulled_followers += len(page['ids'])
                ret_dict[this_id].extend(page['ids'])
                print("Number pulled: " + str(pulled_followers))                
                
                if follower_limit and pulled_followers > follower_limit :
                    break

            if file_name is not None :
                with open(file_name,'a') as ofile :
                    for friend_id in ret_dict[this_id] :
                        ofile.write("\t".join([str(this_id),str(friend_id)]) + "\n")

        except tweepy.TweepError :
            print("Failed to run command on that user (probably protected or bad id). Skipping...")
            
    return(ret_dict)
    
    
def parse_it(tweetText):
    # parse text from user entered data:  tweets, descriptions and screen_names
    # Remove all commas, single quotes and double-quotes
    tweet_text = tweetText.translate(str.maketrans(',"','  '))
    tweet_text = tweetText.translate(str.maketrans("'",' '))
    # Remove new lines
    tweet_text = tweet_text.replace('\r', ' ').replace('\n', ' ').replace('\t',' ')
    #remove non-utf8 characters
    tweet_text.encode('utf-8','ignore')
    
    # I think this removes more than we need since we call unidecode
#    tweet_text = ''.join([i if ord(i) < 128 else ' ' for i in tweet_text])

    tweet_text = unidecode(tweet_text)
    tweet_text = normalize('NFD', tweet_text)
    return(tweet_text)
    
