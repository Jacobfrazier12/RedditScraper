# What is this software? 

This software is designed to read the top posts from r/worldnews. It scans the post flairs to see which ones appear most often. If a post does not have one, this software uses Natural Language Processing to find potential flairs. If none are found, the row is discarded. BE AWARE that this software only works with worldnews. Using any other subreddit may or will result in software failure.  

# License
 **This software is free to copy, use, monetize, or redistribute, whether the reproduction of this software is open-source or not, without the consent of the author. However, the author offers no warranty or support for this software outside of any fixes or modifications made by the author, at their discretion. By using this software, you agree that the author bares no responsibility for any issues or damages received by using this software.**

## Visualization of the results, through Tableau Public

[Top posts Dashboard link](https://public.tableau.com/views/rworldnewstoppostflairs/worldnews?:language=en-US&:display_count=n&:origin=viz_share_link)
## DISCLAIMER 

You MUST supply your own API keys and credentials. 



## How to run

- Run `pip3 install -r "requirements.txt"` to install the required external packages. 
Run `python3 -m spacy download en_core_web_sm` to install the needed model.

- On line 9, you will find multiple variables, which are client_id, client_secret, and user_agent. Set each one's value to your appropriate credentials. If running on a production server, I highly recommend storing them as environment variables, encrypting them, and accessing them via os.environ. This software does not include encryption or decryption for that purpose. You will need to do that yourself. 

- On line 11, you will find a variable called "file_path_for_dumping_posts." Set this string to the path for where you want to store the posts. Note: It must be a CSV file.

- On line 13, you will find a variable called "top_flairs_dump_path." Set this string to the path for where you want to store the flairs and their number of occurrences.

- Finally, run `python3 scraper.py`, in your terminal. 

# Automate the initialization process and running the script
**If you have GNU Make installed on your system, run `make init` to install the dependencies and `make run` to run the scraper.**

