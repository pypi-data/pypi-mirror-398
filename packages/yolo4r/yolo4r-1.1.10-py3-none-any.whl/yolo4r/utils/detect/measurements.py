# utils/detect/measurements.py
import csv, math, yaml
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from shapely.geometry import Polygon
from collections import defaultdict, deque

# --- Import class lists + canonical config path ---
from .classes_config import FOCUS_CLASSES, CONTEXT_CLASSES
from ..paths import MEASURE_CONFIG_YAML, CONFIGS_DIR


# ---------- CONFIG ----------
class MeasurementConfig:
    """Central configuration for all measurement parameters."""

    DEFAULTS = {
        "avg_group_size": 3,              # grouping for average_counts.csv
        "interval_sec": 5,                # interval for aggregator
        "session_sec": 10,                # not used, but reserved
        "interaction_timeout_sec": 2.0,   # gap before ending an interaction
        "overlap_threshold": 0.1,         # IoU threshold
        "motion_threshold_px": 10.0,      # min pixel movement to count motion
        "motion_min_frames": 3            # min frames to confirm motion
    }

    def __init__(self, config_path=None):
        CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

        self.config_path = Path(config_path) if config_path else MEASURE_CONFIG_YAML

        # If missing - create with defaults
        if not self.config_path.exists():
            with open(self.config_path, "w") as f:
                yaml.safe_dump(self.DEFAULTS, f)

        # Load config
        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        # Apply defaults if missing
        for k, v in self.DEFAULTS.items():
            setattr(self, k, data.get(k, v))

# ---------- INTERVAL CLOCK ----------
class IntervalClock:
    """
    Shared interval rollover mechanism.

    All measurement classes should use this to ensure
    perfectly aligned interval boundaries.
    """

    def __init__(self, interval_sec):
        self.interval_sec = interval_sec
        self.start_ts = None

    def tick(self, ts):
        """
        Advance the clock.

        Returns:
            None              -> interval still active
            datetime (start)  -> interval rolled over; returned value
                                 is the interval start timestamp
        """
        if self.start_ts is None:
            self.start_ts = ts
            return None

        if (ts - self.start_ts).total_seconds() >= self.interval_sec:
            old_start = self.start_ts
            self.start_ts = ts
            return old_start

        return None

# ---------- COUNTING UTILITY ----------
def compute_counts_from_boxes(boxes, names):
    """Compute per-frame counts based on model output."""
    counts = {cls: 0 for cls in FOCUS_CLASSES}

    if CONTEXT_CLASSES:
        # Track full detail: each context class AND total
        for c in CONTEXT_CLASSES:
            counts[c] = 0
        counts["OBJECTS"] = 0

    for b in boxes:
        cls = names.get(b[5])
        if cls in FOCUS_CLASSES:
            counts[cls] += 1
        elif CONTEXT_CLASSES and cls in CONTEXT_CLASSES:
            counts[cls] += 1
            counts["OBJECTS"] += 1

    return add_ratio_to_counts(counts)


def add_ratio_to_counts(counts):
    """Add human-readable ratios only when context classes are enabled."""
    if not CONTEXT_CLASSES:
        return counts

    # Use only focus classes for ratio
    focus_values = [int(counts.get(cls, 0)) for cls in FOCUS_CLASSES]

    non_zero = [v for v in focus_values if v != 0]
    if len(non_zero) > 1:
        gcd_val = non_zero[0]
        for v in non_zero[1:]:
            gcd_val = math.gcd(gcd_val, v)
        if gcd_val > 1:
            focus_values = [v // gcd_val for v in focus_values]

    counts["RATIO"] = ":".join(str(v) for v in focus_values)
    return counts


# ---------- Counter ----------
# -- counts & averaged counts --
class Counter:
    def __init__(self, out_folder=None, config=None, start_time=None):
        self.out_folder = Path(out_folder) if out_folder else None
        self.config = config or MeasurementConfig()
        self.start_time = start_time

        # ---- Interval Clock ----
        self.clock = IntervalClock(self.config.interval_sec)

        self.snapshot_buffer = []
        self.creation_ref = None
        self.group_number = 1

    def update_counts(self, boxes, names, timestamp=None):
        now = timestamp or datetime.now()

        # ---- Interval Rollover ----
        boundary = self.clock.tick(now)
        if boundary is None:
            return

        counts = compute_counts_from_boxes(boxes, names)

        # Convert system timestamp to video timestamp
        if self.start_time:
            if not self.creation_ref:
                self.creation_ref = boundary
            elapsed = (boundary - self.creation_ref).total_seconds()
            video_ts = self.start_time + timedelta(seconds=elapsed)
        else:
            video_ts = boundary

        self.snapshot_buffer.append((video_ts, counts))

    # ---- Helper: compute averages ----
    def _compute_averages(self):
        if not self.snapshot_buffer:
            return []

        group_size = self.config.avg_group_size
        averages = []

        for i in range(0, len(self.snapshot_buffer), group_size):
            block = self.snapshot_buffer[i : i + group_size]

            summed = defaultdict(float)
            for _, c in block:
                for cls, val in c.items():
                    if cls not in ("RATIO",):
                        summed[cls] += val

            divisor = len(block)
            avg_counts = {cls: summed[cls] / divisor for cls in summed}
            avg_counts = add_ratio_to_counts(avg_counts)

            midpoint = block[0][0] + (block[-1][0] - block[0][0]) / 2
            averages.append(
                {
                    "Group": self.group_number,
                    "Time": midpoint.strftime("%H:%M:%S"),
                    "Counts": avg_counts,
                }
            )
            self.group_number += 1

        return averages

    def save_results(self):
        """Save counts.csv and average_counts.csv."""
        if not self.out_folder:
            return None

        self.out_folder.mkdir(parents=True, exist_ok=True)
        saved = []

        all_cols = (
            FOCUS_CLASSES
            + (["OBJECTS"] if CONTEXT_CLASSES else [])
            + (["RATIO"] if CONTEXT_CLASSES else [])
        )

        # SNAPSHOT CSV
        f_snap = self.out_folder / "counts.csv"
        with open(f_snap, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["TIME"] + all_cols)
            for ts, c in self.snapshot_buffer:
                row = [ts.strftime("%H:%M:%S")] + [c.get(cls, "") for cls in all_cols]
                w.writerow(row)
        saved.append(f_snap)

        # AVERAGE CSV
        averages = self._compute_averages()
        if averages:
            f_avg = self.out_folder / "average_counts.csv"
            with open(f_avg, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["GROUP", "TIME"] + all_cols)
                for a in averages:
                    row = [a["Group"], a["Time"]] + [
                        a["Counts"].get(cls, "") for cls in all_cols
                    ]
                    w.writerow(row)
            saved.append(f_avg)

        return saved


#   ----- INTERACTIONS -----
class Interactions:
    def __init__(self, out_folder=None, config=None, start_time=None, is_obb=False):
        self.out_folder = Path(out_folder) if out_folder else None
        self.config = config or MeasurementConfig()
        self.start_time = start_time
        self.is_obb = is_obb

        self.active = {}
        self.records = []
        self.ref_time = None

    def _normalize(self, dt):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    def _video_time(self, ts):
        if not self.start_time or not self.ref_time:
            return ts

        delta = (self._normalize(ts) - self._normalize(self.ref_time)).total_seconds()
        return self.start_time + timedelta(seconds=delta)

    #   ----- ROTATED OBB POLYGON BUILDER -----
    def _obb_to_polygon(self, box):
        """
        Convert xyxy OBB-aligned bounding box to a polygon.
        NOTE: xyxy from r.obb.xyxy is the bounding rectangle in the frame.
        For true rotation, UltraLytics currently does not expose the rotated quad,
        so we use the bounding rectangle as a polygon.
        """
        x1, y1, x2, y2 = box[:4]
        return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

    #   ----- ROTATED IoU (POLYGON) -----
    def _iou_polygon(self, boxA, boxB):
        polyA = Polygon(self._obb_to_polygon(boxA))
        polyB = Polygon(self._obb_to_polygon(boxB))

        if not polyA.is_valid or not polyB.is_valid:
            return 0.0

        inter = polyA.intersection(polyB).area
        if inter <= 0:
            return 0.0

        union = polyA.area + polyB.area - inter
        if union <= 0:
            return 0.0

        return inter / union

    #   ----- AXIS-ALIGNED IoU (AABB) -----
    def _iou_aabb(self, a, b):
        ax1, ay1, ax2, ay2 = a[:4]
        bx1, by1, bx2, by2 = b[:4]

        iw = max(0, min(ax2, bx2) - max(ax1, bx1))
        ih = max(0, min(ay2, by2) - max(ay1, by1))
        if iw == 0 or ih == 0:
            return 0.0

        inter = iw * ih
        union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
        if union <= 0:
            return 0.0

        return inter / union

    #   ----- UNIVERSAL OVERLAP CHECK -----
    def _overlap(self, a, b, threshold):
        if self.is_obb:
            return self._iou_polygon(a, b) > threshold
        else:
            return self._iou_aabb(a, b) > threshold

    #   ----- MAIN INTERACTION ENGINE -----
    def process_frame(self, boxes, names, ts):
        if not self.ref_time:
            self.ref_time = ts

        video_ts = self._video_time(ts)

        birds = [b for b in boxes if names.get(b[5]) in FOCUS_CLASSES]
        objs = [
            b
            for b in boxes
            if CONTEXT_CLASSES and names.get(b[5]) in CONTEXT_CLASSES
        ]

        active_now = set()

        if CONTEXT_CLASSES:
            for b in birds:
                name_b = names.get(b[5])
                for o in objs:
                    name_o = names.get(o[5])

                    if b is o:
                        continue

                    if self._overlap(b, o, self.config.overlap_threshold):
                        pair = (name_b, name_o)
                        active_now.add(pair)
                        self._activate(pair, video_ts)

        else:
            # Bird-to-bird interactions
            for i, b1 in enumerate(birds):
                for j, b2 in enumerate(birds):
                    if j <= i:
                        continue
                    name1, name2 = names.get(b1[5]), names.get(b2[5])
                    if name1 == name2:
                        continue
                    if self._overlap(b1, b2, self.config.overlap_threshold):
                        pair = tuple(sorted((name1, name2)))
                        active_now.add(pair)
                        self._activate(pair, video_ts)

        self._finalize_inactive(active_now, video_ts)

    #   ----- ACTIVATE INTERACTION -----
    def _activate(self, pair, ts):
        if pair not in self.active:
            self.active[pair] = {"start": ts, "last": ts}
        else:
            self.active[pair]["last"] = ts

    #   ----- FINALIZE INACTIVE INTERACTIONS -----
    def _finalize_inactive(self, active_now, ts):
        ended = []
        for pair, info in self.active.items():
            if (
                pair not in active_now
                and (ts - info["last"]).total_seconds()
                >= self.config.interaction_timeout_sec
            ):
                self._record(pair, info["start"], info["last"])
                ended.append(pair)
        for p in ended:
            del self.active[p]

    #   ----- FINALIZE ALL -----
    def finalize(self):
        for pair, info in self.active.items():
            self._record(pair, info["start"], info["last"])
        self.active.clear()
        return self.records

    #   ----- RECORD INTERACTION -----
    def _record(self, pair, start, end):
        dur = round((end - start).total_seconds(), 2)
        if dur <= 0:
            return

        if CONTEXT_CLASSES:
            row = {
                "TIME0": start.strftime("%H:%M:%S"),
                "TIME1": end.strftime("%H:%M:%S"),
                "FOCUS": pair[0],
                "CONTEXT": pair[1],
                "DURATION": dur,
            }
        else:
            row = {
                "TIME0": start.strftime("%H:%M:%S"),
                "TIME1": end.strftime("%H:%M:%S"),
                "CLASS1": pair[0],
                "CLASS2": pair[1],
                "DURATION": dur,
            }

        self.records.append(row)

    #   ----- SAVE RESULTS -----
    def save_results(self):
        if not self.records or not self.out_folder:
            return None

        self.out_folder.mkdir(parents=True, exist_ok=True)
        out_file = self.out_folder / "interactions.csv"

        if CONTEXT_CLASSES:
            headers = ["TIME0", "TIME1", "FOCUS", "CONTEXT", "DURATION"]
        else:
            headers = ["TIME0", "TIME1", "CLASS1", "CLASS2", "DURATION"]

        with open(out_file, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for r in sorted(self.records, key=lambda x: x["TIME0"]):
                w.writerow(r)

        return out_file


# ---------- Aggregator ----------
# -- interval aggregation & summary --
class Aggregator:
    def __init__(self, out_folder, config=None, start_time=None):
        self.out_folder = Path(out_folder)
        self.config = config or MeasurementConfig()
        self.start_time = start_time

        self.frame_data = []  # (timestamp, counts)
        self.intervals = []

    def push_frame_data(
        self,
        timestamp,
        current_boxes_list=None,
        names=None,
        counts_dict=None,
    ):
        if counts_dict is None and current_boxes_list and names:
            counts_dict = compute_counts_from_boxes(current_boxes_list, names)

        counts_dict = dict(counts_dict)
        counts_dict.pop("RATIO", None)

        self.frame_data.append((timestamp, counts_dict))

    def aggregate_intervals(self):
        if not self.frame_data:
            return []

        self.frame_data.sort(key=lambda x: x[0])
        intervals = []
        interval_counts = defaultdict(list)

        interval_start = self.frame_data[0][0]
        interval_end = interval_start + timedelta(
            seconds=self.config.interval_sec
        )

        for ts, counts in self.frame_data:
            if ts >= interval_end:
                intervals.append(
                    self._finalize_interval(interval_start, interval_counts)
                )
                interval_counts.clear()
                interval_start = interval_end
                interval_end = interval_start + timedelta(
                    seconds=self.config.interval_sec
                )

            for cls, val in counts.items():
                interval_counts[cls].append(val)

        if interval_counts:
            intervals.append(
                self._finalize_interval(interval_start, interval_counts)
            )

        self.intervals = intervals
        return intervals

    def _finalize_interval(self, start_ts, interval_counts):
        summed = {cls: sum(vals) for cls, vals in interval_counts.items()}

        if CONTEXT_CLASSES:
            obj_total = sum(summed.get(c, 0) for c in CONTEXT_CLASSES)
            summed = {cls: summed.get(cls, 0) for cls in FOCUS_CLASSES}
            summed["OBJECTS"] = obj_total

        summed = add_ratio_to_counts(summed)

        midpoint = start_ts + timedelta(seconds=self.config.interval_sec / 2)
        return {"TIME": midpoint.strftime("%H:%M:%S"), "Counts": summed}

    def save_interval_results(self):
        intervals = self.aggregate_intervals()
        if not intervals:
            return None

        self.out_folder.mkdir(parents=True, exist_ok=True)
        out_file = self.out_folder / "frame_counts.csv"

        all_cols = (
            FOCUS_CLASSES
            + (["OBJECTS"] if CONTEXT_CLASSES else [])
            + (["RATIO"] if CONTEXT_CLASSES else [])
        )

        with open(out_file, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["TIME"] + all_cols)
            for iv in intervals:
                row = [iv["TIME"]] + [
                    iv["Counts"].get(cls, "") for cls in all_cols
                ]
                w.writerow(row)

        return out_file

    def save_session_summary(self):
        if not self.frame_data:
            return None

        # Ensure intervals exist (interval-level counts)
        if not self.intervals:
            self.aggregate_intervals()

        intervals = self.intervals
        if not intervals:
            return None

        # ---- session window size in intervals ----
        interval_sec = float(getattr(self.config, "interval_sec", 1) or 1)
        session_sec = float(getattr(self.config, "session_sec", interval_sec) or interval_sec)

        # Session window should be >= 1 interval; if session_sec < interval_sec, treat as 1 interval
        intervals_per_session = max(1, int(round(session_sec / interval_sec)))

        session_totals = defaultdict(float)
        session_rates = defaultdict(list)

        # ---- roll intervals into session windows ----
        for i in range(0, len(intervals), intervals_per_session):
            block = intervals[i : i + intervals_per_session]
            if not block:
                continue

            block_duration = max(1e-9, len(block) * interval_sec)  # protect against 0

            block_totals = defaultdict(float)
            for iv in block:
                for cls, val in iv["Counts"].items():
                    if cls != "RATIO":
                        block_totals[cls] += float(val)

            # accumulate totals over whole run + per-session window rate samples
            for cls, total in block_totals.items():
                session_totals[cls] += total
                session_rates[cls].append(total / block_duration)

        # ---- Merge context classes → OBJECTS ----
        if CONTEXT_CLASSES:
            obj_total = sum(session_totals.pop(c, 0.0) for c in CONTEXT_CLASSES)
            session_totals["OBJECTS"] = obj_total

            obj_rates = []
            for c in CONTEXT_CLASSES:
                obj_rates.extend(session_rates.pop(c, []))
            session_rates["OBJECTS"] = obj_rates or [0.0]

        focus_total = sum(session_totals.get(cls, 0.0) for cls in FOCUS_CLASSES) or 1.0

        summary_rows = []
        for cls, total in session_totals.items():
            rates = session_rates.get(cls, [])
            mean_rate = sum(rates) / len(rates) if rates else 0.0
            std_dev = (
                math.sqrt(sum((r - mean_rate) ** 2 for r in rates) / len(rates))
                if rates
                else 0.0
            )

            prop = (total / focus_total) if cls in FOCUS_CLASSES else "n/a"

            summary_rows.append(
                {
                    "CLASS": cls,
                    "TOTAL_COUNT": round(total, 3),
                    "AVG_RATE": round(mean_rate, 3),
                    "STD_DEV": round(std_dev, 3),
                    "PROP": prop if isinstance(prop, str) else round(prop, 3),
                }
            )

        # ---- Save ----
        self.out_folder.mkdir(parents=True, exist_ok=True)
        out_file = self.out_folder / "session_summary.csv"

        with open(out_file, "w", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["CLASS", "TOTAL_COUNT", "AVG_RATE", "STD_DEV", "PROP"],
            )
            w.writeheader()
            for row in summary_rows:
                w.writerow(row)

        return out_file

# ---------- Motion Analysis ----------
class Motion:
    """
    Interval-based, per-object motion analysis with jitter suppression.

    Motion is counted ONLY if:
    - displacement >= threshold
    - sustained for >= min_frames
    - counted once per object per interval
    """
    def __init__(self, paths, frame_width, frame_height, config=None):
        self.out_folder = Path(paths["motion"])
        self.config = config or MeasurementConfig()

        self.motion_threshold_px = float(self.config.motion_threshold_px)
        self.min_frames = int(getattr(self.config, "motion_min_frames", 3))

        # ---- Interval clock ----
        self.clock = IntervalClock(self.config.interval_sec)

        # ---- Per-class state ----
        self.prev_centers = defaultdict(list)
        self.persist = defaultdict(lambda: defaultdict(int))
        self.locked = defaultdict(set)

        # ---- Interval accumulators ----
        self.motion_events = defaultdict(int)
        self.interval_displacement = defaultdict(float)
        self.frames_with_motion = defaultdict(int)
        self.interval_frames = 0

        # ---- Output buffers ----
        self.rows_counts = []
        self.rows_intensity = []
        self.rows_prevalence = []

    # ---------------- Geometry ----------------
    def _center(self, box):
        x1, y1, x2, y2 = box[:4]
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def _dist(self, a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    def log_transform(x):
        """
        Motion intensity values are log-transformed using log(1 + x)
        to suppress extreme outliers and stabilize variance.
        """
        return round(math.log1p(x), 3)

    # ---------------- Frame processing ----------------
    def process_frame(self, boxes, names, ts):
        self.interval_frames += 1

        # --- Collect centers ---
        current = defaultdict(list)
        for b in boxes:
            cls = names.get(b[5])
            if cls in FOCUS_CLASSES:
                current[cls].append(self._center(b))

        # --- Compare to previous ---
        for cls in FOCUS_CLASSES:
            curr = current.get(cls, [])
            prev = self.prev_centers.get(cls, [])

            if not curr or not prev:
                self.prev_centers[cls] = curr
                continue

            used_prev = set()

            for i, c in enumerate(curr):
                best_j = None
                best_d = None

                for j, p in enumerate(prev):
                    if j in used_prev:
                        continue
                    d = self._dist(c, p)
                    if best_d is None or d < best_d:
                        best_d = d
                        best_j = j

                if best_j is None:
                    continue

                used_prev.add(best_j)

                if best_d >= self.motion_threshold_px:
                    self.persist[cls][best_j] += 1
                else:
                    self.persist[cls][best_j] = 0

                if (
                    self.persist[cls][best_j] >= self.min_frames
                    and best_j not in self.locked[cls]
                ):
                    self.motion_events[cls] += 1
                    self.interval_displacement[cls] += best_d
                    self.frames_with_motion[cls] += 1
                    self.locked[cls].add(best_j)

            self.prev_centers[cls] = curr

        # ---- EXPLICIT INTERVAL ROLLOVER ----
        boundary = self.clock.tick(ts)
        if boundary:
            self._finalize_interval(boundary)
            self._reset_interval()


    # ---------------- Finalization ----------------
    def _finalize_interval(self, ts):
        t = ts.strftime("%H:%M:%S")

        counts = add_ratio_to_counts(
            {cls: self.motion_events.get(cls, 0) for cls in FOCUS_CLASSES}
        )

        intensity = {
            cls: round(math.log1p(self.interval_displacement.get(cls, 0.0)), 3)
            for cls in FOCUS_CLASSES
        }

        prevalence = {
            cls: round(
                self.frames_with_motion.get(cls, 0) / max(self.interval_frames, 1),
                3
            )
            for cls in FOCUS_CLASSES
        }

        self.rows_counts.append({"TIME": t, **counts})
        self.rows_intensity.append({"TIME": t, **intensity})
        self.rows_prevalence.append({"TIME": t, **prevalence})

    def _reset_interval(self):
        self.motion_events.clear()
        self.interval_displacement.clear()
        self.frames_with_motion.clear()
        self.persist.clear()
        self.locked.clear()
        self.interval_frames = 0

    # ---------------- Saving ----------------
    def save_results(self):
        if not self.rows_counts:
            return None

        self.out_folder.mkdir(parents=True, exist_ok=True)
        outputs = []

        outputs.append(self._write("motion_counts.csv", self.rows_counts, True))
        outputs.append(self._write("motion_intensity.csv", self.rows_intensity))
        outputs.append(self._write("motion_prevalence.csv", self.rows_prevalence))

        return [p for p in outputs if p]

    def _write(self, name, rows, include_ratio=False):
        headers = ["TIME"] + FOCUS_CLASSES
        if include_ratio and CONTEXT_CLASSES:
            headers += ["RATIO"]

        out = self.out_folder / name
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return out
