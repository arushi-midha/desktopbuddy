# Productivity Metrics & Behavioral Insights Proposal

This document outlines proposed metrics to enhance DeskBuddy's analytical capabilities. These metrics focus on behavioral patterns, focus quality, and wellness indicators.

## 1. Keystroke Dynamics

**Current State:** Captures `typing_speed` and `key_count` every second. Aggregated logs are stored.
**Issue:** `DataProcessor` currently attempts to calculate error rates from stored data, but raw key events (like "Backspace") are not stored in the database for privacy/efficiency reasons.

### Proposed Metrics
1.  **Error Rate (Backspace Ratio)**
    *   *Definition:* Percentage of `Backspace` or `Delete` keys pressed relative to total keystrokes.
    *   *Insight:* High error rates often indicate stress, fatigue, or cognitive overload.
    *   *Implementation:* Calculate `error_count` in `KeystrokeLogger` memory buffer and save this integer to the DB row every second, rather than saving raw keys.

2.  **Typing Burstiness**
    *   *Definition:* Variance in inter-key intervals (or typing speed variance within a minute).
    *   *Insight:* "Flow" states often show consistent, rhythmic typing. High burstiness (erratic typing) might indicate distraction or "stop-and-go" thinking.
    *   *Implementation:* Calculate standard deviation of intervals in `KeystrokeLogger` before aggregation.

3.  **Idle Time Ratio**
    *   *Definition:* Percentage of "active" session time spent with 0 keystrokes.
    *   *Insight:* Distinguishes between "writer's block" (staring at screen) vs. "browsing" (using mouse).

## 2. Window & Application Usage

**Current State:** Captures `app_name`, `window_title`, `category`, and `duration`.

### Proposed Metrics
1.  **Context Switching Cost (Switch Rate)**
    *   *Definition:* Number of window/app switches per hour.
    *   *Insight:* High switching rates destroy focus. "Multitasking" is often just rapid context switching, which reduces cognitive capacity.
    *   *Implementation:* Summary metric calculated in `DataProcessor` from `window_activity` log rows.

2.  **Average Dwell Time**
    *   *Definition:* Average duration spent on a single window before switching.
    *   *Insight:* Short dwell times (<15s) generally indicate fragmentation. Long dwell times (>5m) indicate deep work.

3.  **"Doomscrolling" Index (Scroll Velocity)**
    *   *Definition:* Detecting rapid, continuous content consumption in specific apps (Social/Browsers).
    *   *Insight:* Identifying non-productive "zombie" browsing states.
    *   *Implementation:* Requires Mouse Wheel listener (currently not implemented). *Feasibility: Medium.*

## 3. Webcam & Attention (Wellness)

**Current State:** Captures `attention_score`, `blink_rate`, `head_pose`, `face_detected`.

### Proposed Metrics
1.  **Posture Degradation Score**
    *   *Definition:* Deviation of `head_pose` (y-axis/x-axis) from a calibrated "neutral" position over time.
    *   *Insight:* Detects "slouching" or "tech neck" as the day progresses.
    *   *Implementation:* Establish a baseline "neutral" pose at start of session. Track cumulative deviation.

2.  **Visual Distraction Frequency**
    *   *Definition:* Frequency of `looking_at_screen` toggling False.
    *   *Insight:* How often the user looks away from the monitor (e.g., at phone, colleagues).

3.  **Fatigue Index**
    *   *Definition:* Composite of increasing `blink_rate` + decreasing `attention_score` + worsening `posture`.
    *   *Insight:* Use this to trigger "Take a Break" notifications *before* burnout hits.

## 4. Composite Behavioral Metrics

These combine signals from multiple sources.

1.  **Flow State Probability (%)**
    *   *Logic:* (High Typing Consistency) + (Long Window Dwell Time) + (High Visual Attention).
    *   *Use:* Tag sessions as "Deep Work" automatically.

2.  **Frustration Index**
    *   *Logic:* (High Error Rate) + (Rapid App Switching) + (Erratic Mouse/Typing).
    *   *Use:* Suggest a "breathing exercise" intervention.

3.  **Burnout Risk**
    *   *Logic:* (Long Total Hours) + (Low Break Frequency) + (High Fatigue Index).
    *   *Use:* Weekly wellbeing warning.

## Next Steps Plan
1.  **Modify Database:** Add columns to `keystroke_activity` table: `error_count`, `burstiness`.
2.  **Update Logger:** Update `KeystrokeLogger` to compute these locally and insert them.
3.  **Update Processor:** Update `DataProcessor` to use these pre-calculated columns instead of trying to compute them from raw data.
4.  **Frontend:** Visualizing these new metrics (e.g., "Focus Depth" heatmap).
