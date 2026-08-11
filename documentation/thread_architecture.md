# Thread Architecture
 
```
T1: Camera capture  ──────────────── frame_queue (maxsize 2)
                                           │
T2: Main loop  ←── frame_queue             │
    Motion detection  (cheap, every frame) │
    Door state        (cheap, every frame) │
    Event logic                            │
    If motion: push to face_queue ─────────┤
                                           │
T3: FaceWorker  ←── face_queue (maxsize 1)
    face_app.get() → ALL faces + embeddings  (one call, no double inference)
    tracker.update(detections)
    tracker.update([]) when no faces         (tracks age out correctly)
    Recognition: one face per unidentified track (claimed_tids prevents conflicts)
 
T4: Firebase writer  ←── write_queue
    Non-blocking Firestore writes with retry
```
 
---
 
## Thread Responsibilities
 
### T1 — Camera Capture
Continuously reads frames from the camera and pushes them onto `frame_queue`. Queue size 2 acts as a one-frame buffer; if the main loop falls behind, the oldest frame is dropped, keeping latency low.
 
### T2 — Main Loop
Consumes frames from `frame_queue` and runs two cheap per-frame checks:
 
| Check | Cost | Notes |
|---|---|---|
| Motion detection | Cheap | Background subtractor; gates whether T3 is fed |
| Door state | Cheap | Classifier on a small ROI; never blocked by face inference |
 
When motion is active, the current frame is forwarded to `face_queue` (non-blocking — dropped if T3 is busy). Event logic runs every frame regardless of motion.
 
### T3 — FaceWorker
Receives frames from `face_queue` (maxsize 1 — always processes the freshest frame).
 
- Calls `face_app.get()` **once per frame** — returns all face bounding boxes and ArcFace embeddings in a single inference pass.
- Calls `tracker.update([])` when no faces are detected so that track `disappeared` counts increment correctly — required for exit events to fire.
- A `claimed_tids` set prevents two faces from matching the same track within one pass.
 
### T4 — Firebase Writer
Consumes write events from `write_queue`. Writes are non-blocking relative to the main pipeline. Failed writes are retried with exponential back-off (up to 5 attempts).
 
---
 
## Queues
 
| Queue | Max size | Producer | Consumer | Drop policy |
|---|---|---|---|---|
| `frame_queue` | 2 | T1 | T2 | `put_nowait` — oldest frame dropped |
| `face_queue` | 1 | T2 | T3 | `put_nowait` — skipped if T3 busy |
| `write_queue` | 50 | T2 (EventLogic) | T4 | Blocks if full (events are rare) |
 