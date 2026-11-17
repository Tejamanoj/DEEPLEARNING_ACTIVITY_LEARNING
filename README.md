# 3D Weather-Adaptive Autonomous Sidewalk Delivery Robot Simulator
## Deep Learning Experiential Learning Activity (ELA)

An interactive, real-time 3D simulation application built with **Python**, **Ursina Engine**, **OpenCV**, and **PyTorch/YOLOv8** to demonstrate autonomous sidewalk navigation, AI perception, safety rule enforcement, and collision avoidance under diverse real-world conditions.

Optimized for 60 FPS performance on Windows 11 with integrated **Intel Iris Xe Graphics**.

---

## 🚀 Key Implemented Features

### 1. Cyber Humanoid Android Robot & Wheeled Rover ([humanoid_robot.py](file:///c:/Users/tejam/OneDrive/Desktop/3d_walk/robot/humanoid_robot.py)):
- **Aesthetic**: Spherical ceramic white head, glossy black visor screen, dual glowing cyan circular camera eyes (`O O`), glowing chest arc reactor, cyber boots with glowing LED soles, and rear delivery payload backpack.
- **Kinematics**: Bipedal walking stride animation (swinging legs and arms), idle bobbing, and **active head gaze tracking** (smoothly turns its head to look directly at detected pedestrians and obstacles).
- **Chassis Toggle (`[T]`)**: Switch instantly between the **Humanoid Android** and the **Wheeled Delivery Rover**.

### 2. Upgraded Camera System & Mouse Zoom ([camera_controller.py](file:///c:/Users/tejam/OneDrive/Desktop/3d_walk/camera_controller.py)):
- **Mouse Wheel**: Smooth real-time **Zoom In / Zoom Out** across all external camera views.
- **RMB / LMB Drag**: Free 360° orbital pan with pitch/yaw adjustment.
- **5 Camera Presets (`[C]`)**:
  1. `CINEMATIC_CHASE`: Over-the-shoulder framing focusing ahead of the robot.
  2. `FREE_ORBIT`: Complete 360° mouse-controlled exploration.
  3. `ISOMETRIC_ADAS`: 45° tactical highway/sidewalk overview.
  4. `ROBOT_POV`: Direct first-person view from inside the robot's glowing cyan eyes.
  5. `TOP_DOWN`: Direct vertical bird's-eye map view.

### 3. Directional Forward Collision Avoidance & Emergency Stop:
- Real-time forward corridor projection: Monitors only actors directly ahead in the robot's driving path (`lateral_dist < 1.05m`, `forward_dist < 8.0m`).
- **Side traffic is ignored**: Cars in road lanes do not trigger unnecessary stopping.
- **Emergency Stop**: When an obstacle or pedestrian is within `< 2.8m` directly in front, the robot executes an **immediate emergency stop** (`0.0 m/s`), turns on brake indicators, and waits until the path is clear before smoothly resuming!

### 4. Safety Rules Engine & Roadway Intrusion Protection ([safety_rules.py](file:///c:/Users/tejam/OneDrive/Desktop/3d_walk/decision/safety_rules.py)):
- **Sidewalk vs Roadway Boundaries**: Curb line at `x = 6.35m`.
- **Roadway Intrusion Alert**: If the robot enters the vehicle roadway outside the authorized zebra crossing:
  - Triggers a **flashing red alert banner** on HUD: `⚠️ ROADWAY INTRUSION ALERT! VEHICLE COLLISION RISK - RETURNING TO SIDEWALK ⚠️`
  - **Automated Safety Intervention**: Autonomous safety supervisor overrides driving, steers the robot back to the safe sidewalk corridor (`x = 8.75m`), and restores safe operation.
- **Live Rule Compliance Badges on HUD**:
  - `RULE 1: SIDEWALK BOUNDS`
  - `RULE 2: PEDESTRIAN BUFFER`
  - `RULE 3: FORWARD PATH CLEARANCE`
  - `RULE 4: SPEED COMPLIANCE`

### 5. Omnidirectional Movement (Manual & Auto):
- In Manual Mode (`[M]`): Full directional control:
  - `[W]` : Forward throttle
  - `[S]` : Reverse gear / backwards driving
  - `[A]` : Turn Left
  - `[D]` : Turn Right
  - Can steer in reverse and pivot on the spot!

---

## 🕹️ Interactive Controls

| Input | Action | Description |
|---|---|---|
| **`[SPACE]`** | **Start / Pause Nav** | Starts or pauses autonomous route navigation along the sidewalk. |
| **`[M]`** | **Toggle Auto / Manual** | Switch to full manual driving or autonomous path following. |
| **`[W, A, S, D]`** | **Omnidirectional Drive** | Forward throttle, full reverse gear, and left/right steering (in Manual Mode). |
| **`[T]`** | **Toggle Robot Model** | Switches between the Humanoid Android and Wheeled Rover. |
| **`[C]`** | **Cycle Camera Angles** | Cinematic Chase, Free Orbit, Isometric ADAS, Robot POV, Top-Down. |
| **Mouse Wheel** | **Zoom In / Out** | Smoothly zooms the camera closer or further from the robot. |
| **RMB / LMB Drag** | **Orbit Pan** | Smooth 360° mouse camera rotation around the robot. |
| **`[B]`** | **Targeting Lasers** | Toggles 3D lock-on laser beams and bounding boxes. |
| **`[L]`** | **360° LiDAR Arc** | Toggles rotating LiDAR fan and ground range rings. |
| **`[F]`** | **Vision Frustum** | Toggles optical camera perception pyramid. |
| **`[W]`** | **Weather Presets** | Cycles Clear, Fog, Night, Rain, Snow. |
| **`[R]`** | **Reset** | Resets the robot back to the Start Depot. |
| **`[H]`** | **Toggle Help** | Toggles on-screen keyboard controls overlay. |

---

## 🛠️ How to Run

Launch the simulator:
```powershell
python main.py
```

Run automated verification:
```powershell
python test_safety_and_movement.py
```
