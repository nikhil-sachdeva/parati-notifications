from pyfcm import FCMNotification
import mysql.connector
import datetime


def getDB():
	return mysql.connector.connect(host="35.238.153.230",    # your host, usually localhost
										 user="root",         # your username
										 passwd="pass",  # your password
										 database="paratidb")        # name of the data base

def send_notif(fcm_token,title, message):
  push_service = FCMNotification(api_key="api-key")
  registration_id = fcm_token
  message_title = title
  message_body = message
  result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body)
  print(result)

def feedback_empty(user_id):
	db = getDB()
	cur = db.cursor()
	cur.execute("select * from userapi_userfeedback where user_id = " + str(user_id))
	if(len(cur.fetchall()) == 0):
		db.close()
		return True
	db.close()
	return False

def wardrobe_empty(user_id):
	db=getDB()
	cur = db.cursor()
	cur.execute("select * from userapi_userwardrobe where user_id = " + str(user_id))
	if(len(cur.fetchall()) == 0):
		db.close()
		return True
	db.close()
	return False

def wardrobe_product(user_id, product_id):
	db=getDB()
	cur = db.cursor()
	cur.execute("select * from userapi_userwardrobe where user_id = " + str(user_id) + " and product_id = " + str(product_id))
	if(len(cur.fetchall()) == 0):
		db.close()
		return True
	else:
		db.close()
		return False

def check_frequency(type, user_id, hours):
	db = getDB()
	cur = db.cursor()
	cur.execute("select updated_at from userapi_notification_frequency where notification_type = '"+ type + "' and user_id = "+ str(user_id))
	rows = cur.fetchall()
	if(len(rows) == 0):
		return True
	else:
		for row in rows:
			print(row)
			now = datetime.datetime.now()
			diff = now-row[0]
			if(diff.seconds > hours * 60 * 60):
				return True
			else:
				print(str(diff.seconds) + "Not yet")
				return False

def update_frequency(type,user_id):
	db = getDB()
	cur = db.cursor(buffered=True)
	cur.execute("select updated_at from userapi_notification_frequency where notification_type = '" + type + "' and user_id = "+ str(user_id))
	cur1 = db.cursor(buffered=True)
	now = datetime.datetime.now()
	if(len(cur.fetchall()) == 0):
		cur1.execute("insert into userapi_notification_frequency (user_id, notification_type, updated_at) values(%s, %s, %s )" ,(str(user_id), type , now.strftime('%Y-%m-%d %H:%M:%S')))
	else:
		cur1.execute("update userapi_notification_frequency set updated_at = '"+ now.strftime('%Y-%m-%d %H:%M:%S') + "' where user_id = " + str(user_id))
	db.commit()
	db.close()



def start_browsing_notif():
	db = getDB()
	cur = db.cursor()
	cur.execute("select user_id, fcm_token, first_name, updated_at from userapi_user, userapi_userprofile where userapi_user.id = userapi_userprofile.user_id"
			 )
	users = []

	for row in cur.fetchall():
		hours = 3
		now = datetime.datetime.now()
		c = now-row[3]
		if(c.seconds > (hours * 60 * 60) and feedback_empty(row[0]) and check_frequency("start_browsing", row[0], 48)):
				print (row)
				users.append(row)

	print("Scheduling Start Browsing notif for : " )
	db.close()
	if(len(users) > 0):
		for row in users:
			print(row)
			if(row[1]!='temp'):
				send_notif(row[1],"Start swiping!", "Hi " + row[2] + ", browse through your personalized product recommendations.")
				update_frequency("start_browsing", row[0])



def start_wishlist_notif():
	db = getDB()
	cur = db.cursor()
	cur.execute("select a.user_id, a.fcm_token, b.updated_at, b.product_id from userapi_userprofile a inner join (select user_id, product_id, updated_at from userapi_userwishlist) b on a.user_id = b.user_id"
			 )
	users = []
	user_ids = []

	for row in cur.fetchall():
		#registration_ids.append(row[2])
		days = 2
		hours = days * 24
		now = datetime.datetime.now()
		c = now-row[2]
		#if 2 days have passed, product is not in wardrobe and 72 hours have not passed since last notif
		if(c.seconds > (hours * 60 * 60) and wardrobe_product(row[0], row[3]) and check_frequency("wishlist_notif", row[0], 72)):
				if(row[0] not in user_ids):
					print(row)
					user_ids.append(row[0])
					users.append(row)
	db.close()
	print("Scheduling Wishlist notif for : " )
	if(len(users) > 0):
		for row in users:
			print(row)
			if(row[1]!='temp'):
				send_notif(row[1],"Clear up your Wishlist", "Hi, your wishlist feels abandoned. Wishes are meant to be fulfilled! Empty your wishlist before it runs out.")
				update_frequency("wishlist_notif", row[0])
	else:
		print("NA")


def start_order_trigger_notification():
	db = getDB()
	cur = db.cursor()
	cur.execute("select a.user_id, a.fcm_token, b.updated_at from userapi_userprofile a inner join ( select MAX(updated_at) updated_at, user_id from userapi_userwardrobe) b on a.user_id = b.user_id")
	users=[]
	for row in cur.fetchall():
		print(row)
		days = 10
		hours = days * 24
		now = datetime.datetime.now()
		c = now - row[2]
		if(c.seconds > hours * 60 * 60 and check_frequency("order_trigger", row[0], 48)):
			users.append(row)
	db.close()
	print("Scheduling Order Trigger notif for : " )
	if(len(users) > 0):
		for row in users:
			print(row)
			if(row[1]!='temp'):
				send_notif(row[1],"Just checking in", "We will love to see you back ! \nEnjoy your curated products which are only bound to get better.")
				update_frequency("order_trigger", row[0])
	else:
		print("NA")


def start_product_purchase_notification():
	db = getDB()
	cur = db.cursor()
	cur.execute("select a.user_id, a.fcm_token, b.updated_at from userapi_userprofile a inner join (select user_id, MIN(updated_at) updated_at from userapi_userfeedback group by user_id) b on a.user_id = b.user_id;")
	users=[]
	for row in cur.fetchall():
		print(row)
		days = 2
		hours = days * 24
		now = datetime.datetime.now()
		c = now - row[2]
		print(c.seconds)
		if(c.seconds > hours * 60 * 60 and wardrobe_empty(row[0]) and check_frequency("product_purchase", row[0], 48)):
			users.append(row)
	db.close()
	print("Scheduling Product Purchase notif for : " )
	if(len(users) > 0):
		for row in users:
			print(row)
			if(row[1]!='temp'):
				send_notif(row[1],"Found the perfect outfit yet?", "Keep browsing to find the perfect outfit. Click on the cart icon to buy it on the retailer's website.")
				update_frequency("product_purchase", row[0])
	else:
		print("NA")
	
def main():
	start_browsing_notif()
	start_wishlist_notif()
	start_order_trigger_notification()
	start_product_purchase_notification()

# fUIlX2P_w3E:APA91bEu7HFmp6Eqfe8HKrOAILA2c2sNN58t6Zw6NY5kmZiaPqd8Iec825GoQnwFLQ7sTLr2nXi9vLmYU_wFcfJtsbuw5aRo7pYXo7orMJHteekfB0L7PeFsfYGBOl3yDbM4ZiQAmpDE

if __name__=="__main__":
	main()