from enum import IntEnum
from typing import List, Optional, Dict, Any
import numpy as np
import copy
import json
import array

from bam_gym.ros_types.bam_msgs import RequestHeader, ResponseHeader, GymAction, GymFeedback, ErrorType

class RequestType(IntEnum):
    NONE = 0
    STEP = 1
    RESET = 2
    CLOSE = 3

class GymAPI_Request:
    def __init__(self):
        self.header = RequestHeader()
        self.seed: int = 0
        self.env_name = ""
        self.action: List[GymAction] = []

    def to_dict(self):
        return {
            "header": self.header.to_dict(),
            "seed": self.seed,
            "env_name": self.env_name,
            "action": [a.to_dict() for a in self.action],
        }

class GymAPI_Response:
    def __init__(self):
        self.header = ResponseHeader()
        self.feedback: List[GymFeedback] = []

    @classmethod
    def from_dict(cls, d: dict):
        obj = cls()
        obj.header = ResponseHeader.from_dict(d.get("header", {}))
        obj.feedback = [GymFeedback.from_dict(f) for f in d.get("feedback", [])]
        return obj
    
    def to_dict(self):
        return {
            "header": self.header.to_dict(),
            "feedback": [f.to_dict() for f in self.feedback],
        }
    
    def to_step_tuple(self):
        """Unpack all responses into separate lists."""
        observations = [] # sequence
        rewards = []
        terminated = []
        truncated = []
        infos = {} # keep infos dict to add top level info like 'header'

        for idx, f in enumerate(self.feedback):
            obs, reward, term, trunc, info = f.to_step_tuple()
            observations.append(obs)
            rewards.append(reward)
            terminated.append(term) 
            truncated.append(trunc)
            infos[idx] = info

        infos['header'] = self.header.to_dict()

        return (
            observations,                # (N, obs_dim)
            rewards,    # (N,)
            terminated,        # (N,)
            truncated,        # (N,)
            infos    
        )

    def to_reset_tuple(self):
        """Unpack reset responses into separate lists."""
        observations = []
        infos = {}

        for idx, f in enumerate(self.feedback):
            obs, info = f.to_reset_tuple()
            observations.append(obs)
            infos[idx] = info

        infos['header'] = self.header.to_dict()

        return (
            observations,  # shape (N, obs_dim)
            infos          # list of dicts
        )
    

    def __str__(self):

        display_response = copy.deepcopy(self.to_dict())

        # Handle header.error_code nicely
        error_value = display_response["header"]["error_code"].get("value")
        display_response["header"]["error_code"]["value"] = ErrorType(error_value).name
        

        # Handle feedback images nicely
        for f in display_response.get("feedback"):
            color_img = f.get("color_img")
            if isinstance(color_img, np.ndarray):
                f["color_img"] = f"np.ndarray{color_img.shape}"

            depth_img = f.get("depth_img")
            if isinstance(depth_img, np.ndarray):
                f["depth_img"] = f"np.ndarray{depth_img.shape}"

            observation = f.get("observation")
            print(type(observation))
            if isinstance(observation, np.ndarray):
                f["observation"] = observation.tolist()
            elif isinstance(observation, array.array):
                f["observation"] = list(observation)
        return json.dumps(display_response, indent=2)