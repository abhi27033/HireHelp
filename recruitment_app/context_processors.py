from django.db import connection

def get_notification(request):
    user_id = request.session.get('user_id')
    noti=[]
    if user_id is not None:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id,message,created_at from notifications where user_id=%s AND is_read=FALSE",[user_id])
                noti_fetched = list(cursor.fetchall())
            for i in noti_fetched:
                noti_dict={
                    'Notification_ID':i[0],
                    'Message':i[1],
                    'Date':i[2]
                }
                noti.append(noti_dict)
            print("Notifications ",noti)
        except:
            print("Notifications ",noti)
            noti = []
    return {'fetched_notifications':noti}