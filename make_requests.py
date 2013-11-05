import random
import requests
import time
import time
import pdb
from pymongo import MongoClient
import newsubs

requests_count = 0

def make_users(n, file_name):
	'''
	creates a list of n random ids and writes them to a file
	only ever use this ONCE!
	'''
	ids = random.sample(range(30000000), n)
	to_mod = "tomod" + file_name
	original = file(file_name,'w')
	copy = file(to_mod, 'w')
	for user_id in ids:
		original.write("%s\n" % user_id)
		copy.write("%s\n" % user_id)
	original.close()
	copy.close()



def user_list(file_name, remove = False):
	'''
	opens user file and builds a python list containing all
	user therin
	'''
	f = file(file_name, 'r')
	ids = f.read().splitlines()
	f.close()
	if remove:
		f = file(file_name, 'w')
		for u_id in ids[1:]:
			f.write("%s\n" % u_id)
		f.close()
		return
	return ids



def too_many(call):
	''' 
	function to look at global count of requests
	waits if count is too high and updates count to zero
	if count is small enough, will increment count and coninue
	'''
	global requests_count
	if requests_count >= 5:
		print 'stopped on ' + call + ' to take a break'
		time.sleep(1.2)
		requests_count = 0
	else:
		requests_count += 1

def get(user_id):
	'''
	takes an user_id and returns the relevent information for that user
	'''
	# list of api calls to make
	api_calls = ['user.getinfo','user.getrecenttracks','user.getfriends',
	'user.gettopartists', 'user.getevents','user.getTopTags']
	# initialize dictionary of results with the user id as _id for mongo
	results = {}
	results['_id'] = user_id
	# make the api calls
	for call in api_calls:
		# customize url with payload
		payload = {'user': 
		(user_id),'method':call, 
		'api_key':'872d9492f0b60d20c8f230faef15cc00', 'format':'json'}
		if call in ['user.gettopartists','user.getTopTags']:
			payload['limit'] = '5'
		try:
			# get user info
			too_many(call)
			info = requests.get('http://ws.audioscrobbler.com/2.0/', params = payload)
		except (requests.exceptions):
			results = None
			# if there was an error in the request, 
			# break out of calls and return none
			break
		try:
			info.json()
		except(ValueError):
			results = "something strange happened"
		# skip if user_id was invalid
		if call == 'user.getinfo':
			if 'error' in info.json().keys():
				# if there was an error from last.fm
				# break out of calls and return none
				results = None
				break
			else:
				new_id = info.json()['user']['name'] 
		elif call == 'user.gettopartists':
			# if the call was get top artists, iterate through the top artists
			# and get the first top tag
			payload['limit'] = '1'
			payload['method'] = 'artist.gettoptags'
			# remove the user from the payload as it's irrelevant
			payload.pop('user', None)
			tags = []
			try:
				# get the artist info
				info_list = info.json()['topartists']['artist']
				if isinstance(info_list, dict):
					# if the artist info only contains one artist, turn it into
					# an interable
					info_list = [info_list]
				# iterate through the artist info
				for artist_info in info_list:
					payload['artist'] = artist_info['name']
					# try to get the tag for the artist
					try:
						too_many(call)
						tag_info = requests.get('http://ws.audioscrobbler.com/2.0/',
							params = payload)
						tags.append(tag_info.json()['toptags']['tag'][0]['name'])
					except(requests.exceptions):
						# if the request for artist tags failed, continue to next artist
						pass
				results['top_tags'] = tags
				results['top_artists'] = info.json()
			except(KeyError):
				print 'no top artists'
				results['top_tags'] = tags
				results['top_artists'] = []
		else:
			results[call.split('.')[1]] = info.json()
	return results

def write_to_db(user_info):
	'''
	write the user's info to the database
	'''
	client = MongoClient()
	db = client.test
	collection = db.test
	collection.insert(user_info) 
	
def main():
	# create a list of ids to iterate through
	timeout = time.time() + 60*5
	while True:
		newsubs.main()
		ids = user_list('tomodusers.txt')
		for i in range(len(ids)):
			if time.time() > timeout:
				break
			user_id = ids[i]
			print "getting info for " + str(user_id) + ' on iteration ' + str(i) + ' ' + str(float(i)/len(ids)*100) + '%'
			f = file('log_file', 'a')
			too_many('user_id lookup')
			f.write('looking up user ' + str(user_id))
			f.write('\n')
			info = get(user_id = user_id)
			if info:
				if isinstance(info, str):
					f.write('something went wrong')
					f.write('\n')
				else:
					f.write('writing info to database')
					f.write('\n')
					write_to_db(user_info = info)
			else:
				f.write('not added due to error in user info')
				f.write('\n')
			# remove the user from the file
			user_list('tomodusers.txt', remove = True)
			f.close()

if __name__ == "__main__":
	main()




			

