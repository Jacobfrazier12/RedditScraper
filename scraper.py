import praw as pr
import pandas as pd
import spacy
from os import getcwd
from os import environ, path
from time import time
from datetime import date
from datetime import datetime
from difflib import SequenceMatcher
client_id, client_secret, user_agent = environ.get("REDDIT_CLIENT_ID"), environ.get("REDDIT_SECRET"), "AnalyticalScraper"
#Specifies the path for where to dump received data from Reddit 
file_path_for_dumping_posts = path.join(getcwd(),"RedditData.csv")
#Specifies the path for where to dump top flairs and the number of posts that contain them.
file_path_for_dumping_top_flairs = path.join(getcwd(),"TopPosts.csv")
#Generates a similarity score for two strings.
def similar(str1: str,  str2: str):
   return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def cleanup_similar_flairs(posts_df: pd.DataFrame):
   #Gathers the number of occurrences for each post unique post flair, adds these values to a dictionary, and coverts it to a Dataframe. 
   seen_dict = {"Flair": [], "Count": []}
   for flair, count in zip(posts_df["Post Flair"].value_counts().keys().tolist(), posts_df["Post Flair"].value_counts().tolist()):
      seen_dict["Flair"].append(flair)
      seen_dict["Count"].append(count)
   seen_df = pd.DataFrame(seen_dict)
   #Loops through each post and checks its Post Flair similarity to an existing one. If they are similar, the post flair with the higher number of occurrences in other posts will be used.
   # This cleans up any flairs generated by the NLP algorithm that are similar to a popular topic.
   # for example, since Russia/Ukraine/NATO is similar to Russia/Ukraine, we get a more accurate value count if we update Russia/Ukraine/NATO to Russia/Ukraine.  
   for post_index in range(len(posts_df)):
      for seen_index in range(len(seen_df)):
         if similar(posts_df.iloc[post_index, 3], seen_df.iloc[seen_index, 0]) > 0.95:
           seen_value_from_post_index = seen_df[seen_df["Flair"] == posts_df.iloc[post_index, 3]].index.to_list()[0]
           #Checks which flair occurs more often.
           if seen_df.iloc[seen_value_from_post_index, 1] < seen_df.iloc[seen_index, 1]:
            posts_df.iloc[post_index,3] = seen_df.iloc[seen_index, 0]
   #Removes and returns rows which have flairs that aren't talked about that much on that day. 
   return posts_df.groupby("Post Flair").filter(lambda x: len(x) >= 5)      

def get_top_posts_flairs_and_counts_per_year(top_posts_group):
   #This function takes a Dataframe grouped object, which is grouped by the year posted, to get the number of times a post flair appears.
   temp_top_posts_dict = {"Year": [], "Flair": [], "Number of Posts": []}
   #This loop goes through each group and passes to the inner loop.
   for index, group in top_posts_group:
      #This loop goes through a list or iterator of tuples and adds each value to the appropriate list in the dictionary. Each tuple contains the flair name (Key) and number of occurrences(value_counts).
      for flair, count in zip(group["Post Flair"].value_counts().keys(), group["Post Flair"].value_counts()):
         temp_top_posts_dict["Year"].append(index)
         temp_top_posts_dict["Flair"].append(flair)
         temp_top_posts_dict["Number of Posts"].append(count)
         #This section filters out flairs which only appear between 1 and 10 times and returns a Dataframe containing the filtered data. 
         unfiltered_top_posts = pd.DataFrame(temp_top_posts_dict)
         filtered_top_posts = unfiltered_top_posts[unfiltered_top_posts["Number of Posts"] > 10]
   return filtered_top_posts

def analyze_title(title, flair):
   #This function uses Natural Language Processing to scan posts without a flair to determine the potential flair. 
   list_of_potential_topics = []
   if flair == None or flair == "Behind Soft Paywall" or flair == "Covered by other articles":
      nlp = spacy.load("en_core_web_sm")
      doc = nlp(title)
      for ent in doc.ents:
         if ent.label_ == "PERSON" or ent.label_=="ORG" or ent.label_=="GPE" or ent.label_ =="PRODUCT" or ent.label_=="NORP" or ent.label_=="LOC" or ent.label_=="FAC" or ent.label_=="EVENT" or ent.label_=="WORK_OF_ART" or ent.label_=="LANGUAGE" or ent.label_=="Money" :
            list_of_potential_topics.append(ent.text)
   #This section combines each flair together and separates them with a "/." Otherwise, if the list is empty, the original flair is returned.
   if list_of_potential_topics:
      return "/".join(list_of_potential_topics)
   else: return flair

def format_post_created_date(post):
   #Reddit sends a timestamp based on the Unix timestamp, which is not human readable.
   #This function returns the year that corresponds to the timestamp.
   return datetime.fromtimestamp(post.created_utc).strftime("%Y")

def get_reddit_posts(client_id, client_secret, user_agent, number_of_posts):
   #This section creates a read-only instance to access the reddit API. This section also creates a dictionary to hold the data, and sends a request to Reddit for all of r/worldnews' top posts.
   REDDIT_READ_ONLY = pr.Reddit(client_id = client_id, client_secret = client_secret, user_agent = user_agent)
   SUB_REDDIT = REDDIT_READ_ONLY.subreddit(display_name = "worldnews")
   post_temp_dict = {"Year Created": [], "Title": [], "Post Flair": [], "Post URL": [], "Number of Upvotes": []}
   top_posts = SUB_REDDIT.top(limit = number_of_posts)
   #
   # This section takes the received post data and adds them to a dictionary, which is used to populate a Dataframe.
   for post in top_posts:
      post_temp_dict["Year Created"].append(format_post_created_date(post = post))
      post_temp_dict["Title"].append(post.title)
      post_temp_dict["Post Flair"].append(post.link_flair_text)
      post_temp_dict["Post URL"].append(post.url)
      post_temp_dict["Number of Upvotes"].append(post.score)
   #Coverts the dictionary to a Dataframe.
   top_posts_temp_df = pd.DataFrame(post_temp_dict)
   #Returns the Dataframe.
   return top_posts_temp_df


def is_file_older_than_x_days(file_path, days=1):
   #Checks if the CSV file is older than 34 hours. If so, the CSV file is updated.
   #Otherwise, the data is just read from the CSV file. This will speed things up and be courteous to Reddit, by not frequently using their API. 
   file_time = path.getmtime(file_path)
   return ((time()-file_time)/3600>24*days)


top_posts_df = None
#This section checks if the CSV file, containing the reddit data, exists or if its outdated. If it is, this script will grab post data, using Praw to use the Reddit API.
#To be courteous to Reddit, This script will only check Reddit every 24 hours when executed. Outside of this window, this script will check the CSV file instead. 
if not path.exists(path = file_path_for_dumping_posts) or is_file_older_than_x_days(file_path = file_path_for_dumping_posts, days = 1):
   #Gets the top posts from Reddit.
   top_posts_df = get_reddit_posts(client_id = client_id, client_secret = client_secret,user_agent = user_agent, number_of_posts = 2000)
   top_posts_df["Post Flair"] = top_posts_df.apply(lambda x: analyze_title(x["Title"], x["Post Flair"]), axis = "columns") #This line uses the Dataframe apply function, which calls a function and takes the return value of the function and places it in the cell it is currently on during the current iteration. In this situation, the analyze title function needs access to data in other column values to execute successfully. By default, apply only passes a single column value to the function(e.g., The current post flair). By specifying index as the axis argument, both the title and the post flair can be passed as arguments to the analyze title function. 
   top_posts_df.dropna(axis = "index", inplace = True) #Drops rows with any null values, such as still missing flairs. 
   top_posts_df = cleanup_similar_flairs(top_posts_df) #Calls the cleanup_similar_flairs function to merge together similar titles.
   top_posts_df.drop_duplicates(keep = "first") #Drops duplicate rows while keeping the first encountered.
   top_posts_df.to_csv(path_or_buf = file_path_for_dumping_posts, mode = "a", index = False) #Appends the data to the CSV file. DOES NOT overwrite.
   print(f"Dumped results to {file_path_for_dumping_posts}")
   print("Calculating top flairs!")
   #This section rereads the cleaned CSV file and groups the data by the year created and passes it to the get_top_posts_flairs_and_counts_per_year function.
   reddit_data_group = pd.read_csv(file_path_for_dumping_posts).groupby("Year Created")
   top_flairs_by_year_df = get_top_posts_flairs_and_counts_per_year(top_posts_group = reddit_data_group)
   top_flairs_by_year_df.to_csv(path_or_buf = file_path_for_dumping_top_flairs, mode = "w", index = False) #Dumps the flair and counts to specified CSV file.
   print(f"Done! Dumped results to {file_path_for_dumping_top_flairs}")

   
   
   
else:
   
   top_flairs_by_year_df = pd.read_csv(filepath_or_buffer = file_path_for_dumping_top_flairs) #Reads the CSV file containing the flair counts. 
   print(top_flairs_by_year_df)
   
   
   
   
   

    
