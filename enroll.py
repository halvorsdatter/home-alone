import cv2, json, os, numpy as np
from insightface.app import FaceAnalysis
from camera import create_camera
from config import CAPTURE_WIDTH, CAPTURE_HEIGHT, INSIGHTFACE_MODEL

app = FaceAnalysis(name=INSIGHTFACE_MODEL, providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(CAPTURE_WIDTH, CAPTURE_HEIGHT))

def enroll(name, n_frames=80):
    cam = create_camera(CAPTURE_WIDTH, CAPTURE_HEIGHT)
    print(f"Enrolling {name}. Stand 1–2m from camera. Press SPACE to start.")
    while True:
        frame_bgr = cam.capture_bgr()
        cv2.imshow("enroll", frame_bgr)
        if cv2.waitKey(1) & 0xFF == ord(' '): break

    embeddings = []
    while len(embeddings) < n_frames:
        frame_bgr = cam.capture_bgr()
        faces = app.get(frame_bgr)   # expects BGR
        if faces:
            emb = faces[0].embedding  # 512D ArcFace, L2-normalised
            embeddings.append(emb.tolist())
            print(f"  {len(embeddings)}/{n_frames}", end="\r")
        cv2.imshow("enroll", frame_bgr)
        cv2.waitKey(1)

    cam.stop(); cv2.destroyAllWindows()
    anchor_mean = np.mean(embeddings, axis=0)
    anchor_mean /= np.linalg.norm(anchor_mean) + 1e-8
    db_path = "data/enrollments.json"
    db = json.load(open(db_path)) if os.path.exists(db_path) else {}
    db[name] = {"anchors": embeddings, "prototype": anchor_mean.tolist()}
    json.dump(db, open(db_path, "w"))
    print(f"\nSaved {len(embeddings)} anchors for {name}.")

if __name__ == "__main__":
    enroll(input("Name: ").strip())