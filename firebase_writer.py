import threading, time
import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_CREDENTIAL_PATH, FIREBASE_COLLECTION

class FirebaseWriter(threading.Thread):
    def __init__(self, write_queue):
        super().__init__(daemon=True)
        self.queue = write_queue
        firebase_admin.initialize_app(credentials.Certificate(FIREBASE_CREDENTIAL_PATH))
        self.db = firestore.client()

    def run(self):
        while True:
            event = self.queue.get()
            for attempt in range(5):
                try:
                    self.db.collection(FIREBASE_COLLECTION).document(event["name"]).update({
                        "isHome":      event["isHome"],
                        "lastUpdated": firestore.SERVER_TIMESTAMP,
                    })
                    break
                except Exception as e:
                    time.sleep(2 ** attempt)
                    print(f"Firebase write failed ({attempt+1}/5): {e}")