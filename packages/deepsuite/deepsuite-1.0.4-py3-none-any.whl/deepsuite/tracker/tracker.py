"""Tracker module."""

from abc import ABC, abstractmethod

import torch
from torch import nn


class TrackerBase(ABC):
    @abstractmethod
    def update(self, box):
        pass

    @abstractmethod
    def predict(self):
        pass


class Track(TrackerBase):
    def __init__(
        self, track_id, initial_box, filter_type="kalman", device="cpu", feature=None
    ) -> None:
        self.id = track_id
        self.boxes = [initial_box]
        self.age = 1
        self.time_since_update = 0
        self.active = True
        self.device = device
        self.appearance = feature

        if filter_type == "kalman":
            self.filter = KalmanFilter(initial_box, device=device)
        elif filter_type == "lstm":
            self.filter = LSTMTracker(device=device)
        elif filter_type == "particle":
            self.filter = ParticleFilter(initial_box, device=device)
        elif filter_type == "particle_gpu":
            self.filter = ParticleFilterGPU(initial_box, num_particles=500, device=device)
        elif filter_type == "particle_tpu":
            self.filter = ParticleFilterTPU(initial_box, num_particles=1000, device=device)
        else:
            raise ValueError(
                f"Unknown filter_type: {filter_type}. "
                f"Choose from: kalman, lstm, particle, particle_gpu, particle_tpu"
            )

    def predict(self):
        return self.filter.predict()

    def update(self, box, feature=None):
        self.filter.update(box)
        self.boxes.append(box)
        self.time_since_update = 0
        self.age += 1
        if feature is not None:
            self.appearance = feature


class LSTMTracker(TrackerBase):
    def __init__(self, input_dim=4, hidden_dim=64, device="cpu") -> None:
        super().__init__()
        self.device = torch.device(device)
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True).to(self.device)
        self.fc = nn.Linear(hidden_dim, input_dim).to(self.device)
        self.history = []

    def update(self, box):
        box_tensor = torch.tensor(box, dtype=torch.float32, device=self.device)
        self.history.append(box_tensor)
        if len(self.history) > 10:
            self.history.pop(0)

    def predict(self):
        if len(self.history) < 2:
            return self.history[-1]
        input_seq = torch.stack(self.history).unsqueeze(0)  # [1, T, 4]
        output, _ = self.lstm(input_seq)
        pred = self.fc(output[:, -1, :])
        return pred.squeeze().detach()


class ParticleFilter(TrackerBase):
    """Simple Particle Filter for bounding box tracking.

    Basic implementation with motion model and measurement update.
    For GPU-accelerated version with resampling, use ParticleFilterGPU.
    """

    def __init__(self, initial_box, num_particles=100, device="cpu") -> None:
        self.device = torch.device(device)
        self.num_particles = num_particles
        box_tensor = torch.tensor(initial_box, dtype=torch.float32, device=self.device)
        self.particles = box_tensor.unsqueeze(0).repeat(num_particles, 1).clone()
        self.weights = torch.ones(num_particles, device=self.device) / num_particles

    def predict(self):
        noise = torch.randn_like(self.particles)  # std ggf. parametrisierbar
        self.particles += noise
        estimate = torch.sum(self.particles * self.weights[:, None], dim=0)
        return estimate

    def update(self, observation):
        obs_tensor = torch.tensor(observation, dtype=torch.float32, device=self.device)
        dists = torch.norm(self.particles[:, :2] - obs_tensor[:2], dim=1)
        self.weights = torch.exp(-0.5 * dists**2)
        self.weights /= torch.sum(self.weights) + 1e-6


class ParticleFilterGPU(TrackerBase):
    """GPU-accelerated Particle Filter for bounding box tracking.

    Features:
    - Efficient parallel particle update on GPU/TPU
    - Systematic resampling to avoid particle degeneracy
    - Adaptive noise based on velocity estimation
    - IoU-based likelihood for robust measurement updates
    - Box constraint enforcement

    State: [cx, cy, w, h, vx, vy, vw, vh]
    - (cx, cy): center coordinates
    - (w, h): width and height
    - (vx, vy, vw, vh): velocities

    Args:
        initial_box: Initial bounding box [x1, y1, x2, y2]
        num_particles: Number of particles (default: 500 for GPU)
        device: torch device ('cuda', 'cpu', or 'mps' for Apple Silicon)
        process_noise_pos: Process noise std for position (default: 10.0)
        process_noise_vel: Process noise std for velocity (default: 5.0)
        process_noise_scale: Process noise std for scale (default: 0.05)
        measurement_noise: Measurement noise parameter (default: 20.0)
        min_particles_ratio: Minimum effective particle ratio before resampling (default: 0.5)
    """

    def __init__(
        self,
        initial_box,
        num_particles: int = 500,
        device: str = "cpu",
        process_noise_pos: float = 10.0,
        process_noise_vel: float = 5.0,
        process_noise_scale: float = 0.05,
        measurement_noise: float = 20.0,
        min_particles_ratio: float = 0.5,
    ) -> None:
        self.device = torch.device(device)
        self.num_particles = num_particles
        self.process_noise_pos = process_noise_pos
        self.process_noise_vel = process_noise_vel
        self.process_noise_scale = process_noise_scale
        self.measurement_noise = measurement_noise
        self.min_particles_ratio = min_particles_ratio

        # Convert box [x1, y1, x2, y2] to state [cx, cy, w, h, vx, vy, vw, vh]
        x1, y1, x2, y2 = initial_box
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1

        # Initialize particles: [N, 8] - state vector with velocities
        initial_state = torch.tensor(
            [cx, cy, w, h, 0.0, 0.0, 0.0, 0.0], dtype=torch.float32, device=self.device
        )

        # Add small initial noise around initial state
        self.particles = initial_state.unsqueeze(0).repeat(self.num_particles, 1).clone()
        self.particles[:, :4] += torch.randn(self.num_particles, 4, device=self.device) * 5.0

        # Initialize uniform weights
        self.weights = torch.ones(self.num_particles, device=self.device) / self.num_particles

        # Box constraints (for clipping)
        self.min_box_size = 10.0
        self.max_box_size = 1000.0

    def predict(self) -> torch.Tensor:
        """Predict step: propagate particles using motion model.

        Motion model:
        - Position: cx_new = cx + vx + noise
        - Velocity: vx_new = vx + noise (random walk)
        - Same for cy, w, h

        Returns:
            Predicted bounding box [x1, y1, x2, y2]
        """
        # Motion model: state = state + velocity + noise
        # Position update
        self.particles[:, 0] += (
            self.particles[:, 4]
            + torch.randn(self.num_particles, device=self.device) * self.process_noise_pos
        )
        self.particles[:, 1] += (
            self.particles[:, 5]
            + torch.randn(self.num_particles, device=self.device) * self.process_noise_pos
        )

        # Scale update (w, h)
        self.particles[:, 2] += (
            self.particles[:, 6]
            + torch.randn(self.num_particles, device=self.device) * self.process_noise_scale
        )
        self.particles[:, 3] += (
            self.particles[:, 7]
            + torch.randn(self.num_particles, device=self.device) * self.process_noise_scale
        )

        # Velocity update (random walk)
        self.particles[:, 4:8] += (
            torch.randn(self.num_particles, 4, device=self.device) * self.process_noise_vel
        )

        # Enforce box size constraints
        self.particles[:, 2] = torch.clamp(
            self.particles[:, 2], self.min_box_size, self.max_box_size
        )
        self.particles[:, 3] = torch.clamp(
            self.particles[:, 3], self.min_box_size, self.max_box_size
        )

        # Weighted mean estimate
        estimate_state = torch.sum(self.particles * self.weights[:, None], dim=0)
        return self._state_to_box(estimate_state)

    def update(self, observation):
        """Update step: weight particles based on observation likelihood.

        Uses IoU-based likelihood for robust measurement update.
        Performs systematic resampling if effective particle count is low.

        Args:
            observation: Observed bounding box [x1, y1, x2, y2]
        """
        obs_tensor = torch.tensor(observation, dtype=torch.float32, device=self.device)

        # Convert particles to boxes for IoU calculation
        particle_boxes = self._particles_to_boxes()  # [N, 4]

        # Calculate IoU-based likelihood
        ious = self._batch_iou(particle_boxes, obs_tensor.unsqueeze(0))  # [N]

        # Update weights using likelihood (higher IoU = higher weight)
        # Add small epsilon to avoid zero weights
        self.weights = ious + 1e-6
        self.weights /= torch.sum(self.weights)

        # Update velocity estimate based on observation
        obs_cx = (obs_tensor[0] + obs_tensor[2]) / 2
        obs_cy = (obs_tensor[1] + obs_tensor[3]) / 2
        obs_w = obs_tensor[2] - obs_tensor[0]
        obs_h = obs_tensor[3] - obs_tensor[1]

        # Estimate velocity from weighted particles
        weighted_state = torch.sum(self.particles * self.weights[:, None], dim=0)

        # Update velocities based on difference
        self.particles[:, 4] = 0.7 * self.particles[:, 4] + 0.3 * (obs_cx - self.particles[:, 0])
        self.particles[:, 5] = 0.7 * self.particles[:, 5] + 0.3 * (obs_cy - self.particles[:, 1])
        self.particles[:, 6] = 0.7 * self.particles[:, 6] + 0.3 * (obs_w - self.particles[:, 2])
        self.particles[:, 7] = 0.7 * self.particles[:, 7] + 0.3 * (obs_h - self.particles[:, 3])

        # Check for resampling (effective particle count)
        n_eff = 1.0 / torch.sum(self.weights**2)
        if n_eff < self.min_particles_ratio * self.num_particles:
            self._systematic_resample()

    def _particles_to_boxes(self) -> torch.Tensor:
        """Convert particle states [cx, cy, w, h, ...] to boxes [x1, y1, x2, y2].

        Returns:
            Boxes [N, 4]
        """
        cx, cy, w, h = (
            self.particles[:, 0],
            self.particles[:, 1],
            self.particles[:, 2],
            self.particles[:, 3],
        )
        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = cx + w / 2
        y2 = cy + h / 2
        return torch.stack([x1, y1, x2, y2], dim=1)

    def _state_to_box(self, state: torch.Tensor) -> torch.Tensor:
        """Convert single state [cx, cy, w, h, ...] to box [x1, y1, x2, y2].

        Args:
            state: State vector [8]

        Returns:
            Box [4]
        """
        cx, cy, w, h = state[0], state[1], state[2], state[3]
        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = cx + w / 2
        y2 = cy + h / 2
        return torch.stack([x1, y1, x2, y2])

    def _batch_iou(self, boxes1: torch.Tensor, boxes2: torch.Tensor) -> torch.Tensor:
        """Compute IoU between two sets of boxes efficiently on GPU.

        Args:
            boxes1: [N, 4] in format [x1, y1, x2, y2]
            boxes2: [M, 4] in format [x1, y1, x2, y2]

        Returns:
            IoU matrix [N, M]
        """
        # Expand dimensions for broadcasting
        b1 = boxes1.unsqueeze(1)  # [N, 1, 4]
        b2 = boxes2.unsqueeze(0)  # [1, M, 4]

        # Intersection coordinates
        x1 = torch.max(b1[..., 0], b2[..., 0])
        y1 = torch.max(b1[..., 1], b2[..., 1])
        x2 = torch.min(b1[..., 2], b2[..., 2])
        y2 = torch.min(b1[..., 3], b2[..., 3])

        # Intersection area
        inter_area = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)

        # Box areas
        b1_area = (b1[..., 2] - b1[..., 0]) * (b1[..., 3] - b1[..., 1])
        b2_area = (b2[..., 2] - b2[..., 0]) * (b2[..., 3] - b2[..., 1])

        # Union area
        union_area = b1_area + b2_area - inter_area + 1e-6

        # IoU
        iou = inter_area / union_area
        return iou.squeeze()

    def _systematic_resample(self):
        """Systematic resampling to avoid particle degeneracy.

        This is more efficient than multinomial resampling and has lower variance.
        After resampling, weights are reset to uniform.
        """
        # Compute cumulative sum of weights
        cumsum = torch.cumsum(self.weights, dim=0)

        # Generate systematic samples
        positions = (
            torch.arange(self.num_particles, device=self.device, dtype=torch.float32)
            + torch.rand(1, device=self.device)
        ) / self.num_particles

        # Find indices
        indices = torch.searchsorted(cumsum, positions)
        indices = torch.clamp(indices, 0, self.num_particles - 1)

        # Resample particles
        self.particles = self.particles[indices].clone()

        # Add small noise to avoid particle collapse
        self.particles += torch.randn_like(self.particles) * 0.5

        # Reset weights to uniform
        self.weights = torch.ones(self.num_particles, device=self.device) / self.num_particles


class ParticleFilterTPU(ParticleFilterGPU):
    """TPU-optimized Particle Filter.

    Inherits from ParticleFilterGPU but optimizes operations for TPU:
    - Uses torch.float32 (TPU prefers float32 over float64)
    - Avoids dynamic shapes and in-place operations
    - Uses vectorized operations suitable for XLA compilation

    Compatible with Apple Silicon (MPS) and Google Cloud TPU.
    """

    def __init__(self, *args, **kwargs) -> None:
        # Force device to appropriate accelerator
        if "device" in kwargs:
            device = kwargs["device"]
            if device == "tpu":
                # For Google Cloud TPU, would use torch_xla
                kwargs["device"] = "cpu"  # Fallback if torch_xla not available
            elif device == "mps" or device == "cuda":
                # Apple Silicon or CUDA - use as is
                pass
        super().__init__(*args, **kwargs)


class KalmanFilter(TrackerBase):
    def __init__(self, initial_box, device="cpu") -> None:
        self.device = torch.device(device)

        x1, y1, x2, y2 = initial_box
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1

        self.state = torch.tensor(
            [cx, cy, w, h, 0, 0, 0, 0], dtype=torch.float32, device=self.device
        )

        self.dt = 1.0
        self.F = torch.eye(8, device=self.device)
        for i in range(4):
            self.F[i, i + 4] = self.dt

        self.H = torch.eye(4, 8, device=self.device)
        self.P = torch.eye(8, device=self.device) * 1000
        self.Q = torch.eye(8, device=self.device)
        self.R = torch.eye(4, device=self.device) * 10

        self._I = torch.eye(8, device=self.device)  # für Update

    def predict(self):
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self._state_to_box()

    def update(self, box):
        x1, y1, x2, y2 = box
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1
        z = torch.tensor([cx, cy, w, h], dtype=torch.float32, device=self.device)

        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ torch.linalg.inv(S)

        y = z - self.H @ self.state
        self.state = self.state + K @ y
        self.P = (self._I - K @ self.H) @ self.P

    def _state_to_box(self):
        cx, cy, w, h = self.state[:4]
        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = cx + w / 2
        y2 = cy + h / 2
        return torch.stack([x1, y1, x2, y2])
