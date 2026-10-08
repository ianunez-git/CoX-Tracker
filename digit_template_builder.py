from pathlib import Path

import cv2
import numpy as np


# =========================================================
# CONFIGURATION
# =========================================================

PANELS_DIR = Path("debug_panels")
OUTPUT_DIR = Path("debug_digits")

IGNORE_FILES = {
    "Normal_1_panel.png",
}

# =========================================================
# KNOWN VALUES
# =========================================================

KNOWN_VALUES = {
    "CM_5_panel.png": "26,837",
    "Normal_117_panel.png": "32,627",
    "Normal_15_panel.png": "16,320",
    "Normal_32_panel.png": "19,339",
    "Normal_43_panel.png": "23,895",
    "Normal_86_panel.png": "17,636",
}

# =========================================================
# EXTRACT PERSONAL POINTS ROW
# =========================================================



def extract_points_row(panel_image):
    """
    Dynamically extracts the personal-points row.

    The approximate location is known, but RuneLite panel
    placement can vary by a few pixels. We therefore search
    vertically around the expected position and select the
    band containing the strongest text signal.
    """

    height, width = panel_image.shape[:2]

    # -----------------------------------------------------
    # Approximate expected position
    # -----------------------------------------------------

    expected_center = int(height * 0.46)

    # Search only a few pixels above/below that position.
    search_radius = max(
        4,
        int(height * 0.06)
    )

    # Half-height of the final row crop.
    half_height = max(
        7,
        int(height * 0.115)
    )

    # -----------------------------------------------------
    # Create brightness mask
    # -----------------------------------------------------

    gray = cv2.cvtColor(
        panel_image,
        cv2.COLOR_BGR2GRAY
    )

    _, bright_mask = cv2.threshold(
        gray,
        100,
        255,
        cv2.THRESH_BINARY
    )

    # -----------------------------------------------------
    # Test candidate centers
    # -----------------------------------------------------

    best_center = expected_center
    best_score = -1

    for center_y in range(
        max(half_height, expected_center - search_radius),
        min(
            height - half_height,
            expected_center + search_radius + 1
        )
    ):

        y1 = center_y - half_height
        y2 = center_y + half_height + 1

        candidate = bright_mask[
            y1:y2,
            :
        ]

        score = cv2.countNonZero(
            candidate
        )

        if score > best_score:

            best_score = score
            best_center = center_y

    # -----------------------------------------------------
    # Final crop
    # -----------------------------------------------------

    y1 = max(
        0,
        best_center - half_height
    )

    y2 = min(
        height,
        best_center + half_height + 1
    )

    return panel_image[
        y1:y2,
        :
    ]


# =========================================================
# ISOLATE WHITE SCORE
# =========================================================

def isolate_score(row):
    """
    Keeps bright low-saturation pixels corresponding
    primarily to the white score.
    """

    hsv = cv2.cvtColor(
        row,
        cv2.COLOR_BGR2HSV
    )

    lower = np.array(
        [0, 0, 145]
    )

    upper = np.array(
        [180, 85, 255]
    )

    mask = cv2.inRange(
        hsv,
        lower,
        upper
    )

    return mask


# =========================================================
# FIND ACTIVE COLUMN GROUPS
# =========================================================

def find_column_groups(mask):
    """
    Segments characters using vertical projection.

    A character may consist of several disconnected pieces,
    but those pieces occupy the same horizontal column range.

    Returns groups of active columns.
    """

    # Count white pixels in each X column.
    column_activity = np.any(
        mask > 0,
        axis=0
    )

    groups = []

    start = None

    for x, active in enumerate(
        column_activity
    ):

        if active and start is None:

            start = x

        elif not active and start is not None:

            end = x - 1

            groups.append(
                (start, end)
            )

            start = None

    # Handle group reaching final column.
    if start is not None:

        groups.append(
            (
                start,
                len(column_activity) - 1
            )
        )

    return groups


# =========================================================
# FILTER GROUPS
# =========================================================

def filter_groups(mask, groups):
    """
    Removes tiny noise while preserving digits
    and punctuation.
    """

    valid = []

    height = mask.shape[0]

    for x1, x2 in groups:

        width = x2 - x1 + 1

        crop = mask[
            0:height,
            x1:x2 + 1
        ]

        white_pixels = cv2.countNonZero(
            crop
        )

        if white_pixels < 3:
            continue

        valid.append({
            "x1": x1,
            "x2": x2,
            "width": width,
            "pixels": white_pixels,
        })

    return valid


# =========================================================
# SAVE DEBUG
# =========================================================

def save_debug(
    panel_name,
    row,
    mask,
    groups
):
    """
    Saves diagnostic images and individual character crops.
    """

    stem = Path(
        panel_name
    ).stem

    output = (
        OUTPUT_DIR
        / stem
    )

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Original row
    # -----------------------------------------------------

    cv2.imwrite(
        str(
            output
            / "01_row.png"
        ),
        row
    )

    # -----------------------------------------------------
    # Binary mask
    # -----------------------------------------------------

    cv2.imwrite(
        str(
            output
            / "02_mask.png"
        ),
        mask
    )

    # -----------------------------------------------------
    # Visualization
    # -----------------------------------------------------

    debug = cv2.cvtColor(
        mask,
        cv2.COLOR_GRAY2BGR
    )

    height = mask.shape[0]

    for index, group in enumerate(
        groups
    ):

        x1 = group["x1"]
        x2 = group["x2"]

        # Find actual vertical limits for this character.
        character_area = mask[
            :,
            x1:x2 + 1
        ]

        points = cv2.findNonZero(
            character_area
        )

        if points is None:
            continue

        bx, by, bw, bh = (
            cv2.boundingRect(points)
        )

        y1 = by
        y2 = by + bh - 1

        # Draw character box.
        cv2.rectangle(
            debug,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),
            1
        )

        # Index above/below when possible.
        cv2.putText(
            debug,
            str(index),
            (
                x1,
                max(7, y1 - 1)
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.22,
            (0, 0, 255),
            1
        )

        # -------------------------------------------------
        # Individual character crop
        # -------------------------------------------------

        char_crop = mask[
            y1:y2 + 1,
            x1:x2 + 1
        ]

        cv2.imwrite(
            str(
                output
                / f"char_{index:02d}.png"
            ),
            char_crop
        )

    cv2.imwrite(
        str(
            output
            / "03_columns.png"
        ),
        debug
    )

# =========================================================
# SAVE LABELED DIGIT SAMPLES
# =========================================================

def save_labeled_samples(
    panel_name,
    mask,
    groups,
    known_value
):

    
    """
    Saves segmented characters as labeled OSRS samples.

    Example:

        known_value = "26,837"

        char_00 -> 2
        char_01 -> 6
        char_02 -> comma
        char_03 -> 8
        char_04 -> 3
        char_05 -> 7
    """

    if len(groups) != len(known_value):

        print(
            f"[DATASET ERROR] {panel_name}: "
            f"{len(groups)} groups != "
            f"{len(known_value)} expected characters"
        )

        return False

    digits_dir = Path(
        "assets/digits"
    )

    digits_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    height = mask.shape[0]

    panel_id = (
        Path(panel_name)
        .stem
        .replace("_panel", "")
    )

    for index, (
        group,
        character
    ) in enumerate(
        zip(groups, known_value)
    ):

        x1 = group["x1"]
        x2 = group["x2"]

        character_area = mask[
            :,
            x1:x2 + 1
        ]

        points = cv2.findNonZero(
            character_area
        )

        if points is None:
            continue

        _, y, _, h = cv2.boundingRect(
            points
        )

        char_crop = mask[
            y:y + h,
            x1:x2 + 1
        ]

        # Comma cannot be used directly as a useful
        # filename label.
        label = (
            "comma"
            if character == ","
            else character
        )

        label_dir = (
            digits_dir
            / label
        )

        label_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_name = (
            f"{panel_id}_{index:02d}.png"
        )

        cv2.imwrite(
            str(
                label_dir
                / output_name
            ),
            char_crop
        )

    return True


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=== CoX Digit Template Builder v0.3 ===\n"
    )

    # -----------------------------------------------------
    # Validate input directory
    # -----------------------------------------------------

    if not PANELS_DIR.exists():

        print(
            "No existe debug_panels."
        )

        return

    # -----------------------------------------------------
    # Create output directories
    # -----------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    Path(
        "assets/digits"
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Find generated panel images
    # -----------------------------------------------------

    panel_files = sorted(
        PANELS_DIR.glob(
            "*_panel.png"
        )
    )

    processed = 0
    dataset_created = 0

    # -----------------------------------------------------
    # Process panels
    # -----------------------------------------------------

    for panel_file in panel_files:

        # Ignore known invalid test panels.
        if panel_file.name in IGNORE_FILES:

            print(
                f"[IGNORADO] "
                f"{panel_file.name}"
            )

            continue

        # ---------------------------------------------
        # Load panel
        # ---------------------------------------------

        panel = cv2.imread(
            str(panel_file)
        )

        if panel is None:

            print(
                f"[ERROR] "
                f"{panel_file.name}"
            )

            continue

        # ---------------------------------------------
        # Extract personal-points row
        # ---------------------------------------------

        row = extract_points_row(
            panel
        )

        # ---------------------------------------------
        # Create white-score mask
        # ---------------------------------------------

        mask = isolate_score(
            row
        )

        # ---------------------------------------------
        # Segment characters using columns
        # ---------------------------------------------

        raw_groups = find_column_groups(
            mask
        )

        groups = filter_groups(
            mask,
            raw_groups
        )

        # ---------------------------------------------
        # Save diagnostic images
        # ---------------------------------------------

        save_debug(
            panel_file.name,
            row,
            mask,
            groups
        )

        # ---------------------------------------------
        # Look for known real value
        # ---------------------------------------------

        known_value = KNOWN_VALUES.get(
            panel_file.name
        )

        # ---------------------------------------------
        # Build labeled dataset
        # ---------------------------------------------

        if known_value is not None:

            success = save_labeled_samples(
                panel_file.name,
                mask,
                groups,
                known_value
            )

            if success:
                dataset_created += 1

        else:

            print(
                f"[SIN ETIQUETA] "
                f"{panel_file.name}"
            )

        # ---------------------------------------------
        # Console information
        # ---------------------------------------------

        print(
            f"{panel_file.name}"
            f" -> "
            f"{len(groups)} "
            f"column groups",
            end=""
        )

        if known_value is not None:

            print(
                f" | expected: "
                f"{known_value}"
            )

        else:

            print()

        processed += 1

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print(
        "\n----------------------------"
    )

    print(
        f"Paneles procesados: "
        f"{processed}"
    )

    print(
        f"Paneles agregados al dataset: "
        f"{dataset_created}"
    )

    print(
        f"Debug output: "
        f"{OUTPUT_DIR}"
    )

    print(
        "Dataset: assets/digits"
    )


if __name__ == "__main__":
    main()