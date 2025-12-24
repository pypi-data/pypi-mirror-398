import math
import threading
import queue
import time
import numpy as np

"""
def worker(obs, horizon):
    
    obs: 任意观测
    return: np.array with shape (horizon, 14)
    


example usage:
rtc = RealtimeChunking(
    worker=vla_worker,
    horizon=32,
    overlap=8,
)

while True:
    obs = get_obs()
    action = rtc.step(obs)
    send_action(action)

"""


class ActionChunk:
    def __init__(self, actions):
        self.actions = np.array(actions)

    def __len__(self):
        return len(self.actions)


class RealtimeChunkingSoft:
    """
    A simple realtime chunking implementation which can wraps any VLA model.
    for REAL RTC as pi does, we need model supports action prefix.
    """

    def __init__(
        self,
        worker,
        horizon,
        overlap,
        blend_mode="cosine",  # "linear" | "cosine" | "minjerk"
        blend_grippers=False,
        gripper_indices=[6, 13],
    ):
        assert overlap > 0
        assert overlap < horizon

        self.worker = worker
        self.horizon = horizon
        self.overlap = overlap
        self.blend_mode = blend_mode
        self.blend_grippers = blend_grippers
        self.gripper_indices = gripper_indices

        self.current_chunk = None
        self.step_idx = 0

        self.infer_thread = None
        self.infer_queue = queue.Queue(maxsize=1)

    def _infer_async(self, obs):
        def _run():
            actions = self.worker(obs, self.horizon)
            self.infer_queue.put(actions)

        self.infer_thread = threading.Thread(target=_run, daemon=True)
        self.infer_thread.start()

    def _should_start_inference(self):
        return (
            self.infer_thread is None and self.step_idx >= self.horizon - self.overlap
        )

    def _alpha(self, i):
        s = (i + 1) / self.overlap

        if self.blend_mode == "linear":
            return s

        if self.blend_mode == "cosine":
            return 0.5 * (1.0 - math.cos(math.pi * s))

        if self.blend_mode == "minjerk":
            return 10 * s**3 - 15 * s**4 + 6 * s**5

        raise ValueError(f"Unknown blend_mode: {self.blend_mode}")

    def _blend(self, old_tail, new_head):
        blended = np.zeros_like(old_tail)

        for i in range(self.overlap):
            a = self._alpha(i)
            blended[i] = (1.0 - a) * old_tail[i] + a * new_head[i]

        if not self.blend_grippers:
            blended[:, self.gripper_indices] = new_head[:, self.gripper_indices]

        return blended

    def _try_commit_next_chunk(self):
        if self.step_idx < self.horizon:
            return
        if self.infer_queue.empty():
            return

        new_actions = self.infer_queue.get()

        old_tail = self.current_chunk.actions[
            self.horizon - self.overlap : self.horizon
        ]
        new_head = new_actions[: self.overlap]

        blended = self._blend(old_tail, new_head)
        merged = np.concatenate((blended, new_actions[self.overlap :]), axis=0)

        self.current_chunk = ActionChunk(merged)
        self.step_idx = 0
        self.infer_thread = None

    def reset(self):
        self.current_chunk = None
        self.step_idx = 0
        self.infer_thread = None
        while not self.infer_queue.empty():
            self.infer_queue.get()

    def step(self, obs):
        if self.current_chunk is None:
            actions = self.worker(obs, self.horizon)
            self.current_chunk = ActionChunk(actions)
            self.step_idx = 0

        action = self.current_chunk.actions[self.step_idx]
        self.step_idx += 1

        if self._should_start_inference():
            self._infer_async(obs)

        self._try_commit_next_chunk()

        return action
