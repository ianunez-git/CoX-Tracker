from pathlib import Path
import re

import cv2
import pytesseract


# =========================================================
# CONFIGURATION
# =========================================================

import os
import shutil

# Optional custom Tesseract path.
# If not provided, use the executable available in PATH.

TESSERACT_PATH = os.getenv("TESSERACT_CMD")

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
elif shutil.which("tesseract"):
    pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract")
else:
    print(
        "[WARNING] Tesseract was not found in PATH. "
        "Set TESSERACT_CMD to its executable path."
    )



TOTAL_TEMPLATES = [
    "assets/total_template_v1.png",
    "assets/total_template_v2.png",
]


# =========================================================
# BASIC IMAGE INFORMATION
# =========================================================

def get_image_info(file_path):

    image = cv2.imread(str(file_path))

    if image is None:
        raise ValueError(f"Could not open image: {file_path}")

    height, width = image.shape[:2]

    return {
        "width": width,
        "height": height,
    }


# =========================================================
# TOTAL TEMPLATE DETECTION
# =========================================================

def find_total_template(
    file_path,
    template_paths=None
):

    if template_paths is None:
        template_paths = TOTAL_TEMPLATES

    image = cv2.imread(str(file_path))

    if image is None:
        raise ValueError(f"Could not open image: {file_path}")

    image_gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    best_match = None

    for template_path in template_paths:

        template = cv2.imread(str(template_path))

        if template is None:
            print(
                f"[WARNING] Could not load template: "
                f"{template_path}"
            )
            continue

        template_gray = cv2.cvtColor(
            template,
            cv2.COLOR_BGR2GRAY
        )

        template_height, template_width = (
            template_gray.shape[:2]
        )

        if (
            template_width > image_gray.shape[1]
            or template_height > image_gray.shape[0]
        ):
            continue

        match_result = cv2.matchTemplate(
            image_gray,
            template_gray,
            cv2.TM_CCOEFF_NORMED
        )

        _, max_value, _, max_location = (
            cv2.minMaxLoc(match_result)
        )

        current_match = {
            "x": max_location[0],
            "y": max_location[1],
            "width": template_width,
            "height": template_height,
            "confidence": float(max_value),
            "template": Path(template_path).name,
        }

        if (
            best_match is None
            or current_match["confidence"]
            > best_match["confidence"]
        ):
            best_match = current_match

    return best_match


# =========================================================
# POINTS PANEL EXTRACTION
# =========================================================

def extract_points_panel(
    file_path,
    total_match,
    output_path=None
):

    if total_match is None:
        return None

    image = cv2.imread(str(file_path))

    if image is None:
        raise ValueError(f"Could not open image: {file_path}")

    image_height, image_width = image.shape[:2]

    anchor_x = total_match["x"]
    anchor_y = total_match["y"]

    left_padding = 8
    top_padding = 8

    panel_width = 230
    panel_height = 85

    x1 = max(
        0,
        anchor_x - left_padding
    )

    y1 = max(
        0,
        anchor_y - top_padding
    )

    x2 = min(
        image_width,
        x1 + panel_width
    )

    y2 = min(
        image_height,
        y1 + panel_height
    )

    panel = image[
        y1:y2,
        x1:x2
    ]

    if panel.size == 0:
        return None

    if output_path is not None:

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        cv2.imwrite(
            str(output_path),
            panel
        )

    return {
        "image": panel,
        "x": x1,
        "y": y1,
        "width": x2 - x1,
        "height": y2 - y1,
    }


# =========================================================
# PERSONAL POINTS OCR
# =========================================================

def extract_personal_points(
    panel,
    debug_output_path=None
):
    """
    Extracts personal points from the second row.

    Strategy:
    - Use the Total anchor to obtain the panel.
    - Isolate row 2.
    - Keep only the right-most area where the score is aligned.
    - OCR digits only.
    """

    if panel is None:
        return None

    panel_image = panel["image"]

    height, width = panel_image.shape[:2]

    # =====================================================
    # SECOND ROW
    # =====================================================

    # Keep roughly the right-most 45% of the panel.
    #
    # This gives us more room than the original 50% crop,
    # preventing the first digits from being cut.
    #
    # At the same time it avoids feeding the username
    # to Tesseract.

    x1 = int(width * 0.55)
    x2 = width

    # Tighter vertical crop around row 2
    y1 = int(height * 0.30)
    y2 = int(height * 0.58)

    points_region = panel_image[
        y1:y2,
        x1:x2
    ]

    if points_region.size == 0:
        return None

    # =====================================================
    # GRAYSCALE
    # =====================================================

    gray = cv2.cvtColor(
        points_region,
        cv2.COLOR_BGR2GRAY
    )

    # =====================================================
    # UPSCALE
    # =====================================================

    # 3x is enough here.
    # Too much enlargement exaggerates the pixelated font.

    scale = 3

    enlarged = cv2.resize(
        gray,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    # =====================================================
    # THRESHOLD
    # =====================================================

    # Personal points are white/light gray.
    # Username is orange.
    #
    # A relatively high threshold helps isolate the score.

    _, processed = cv2.threshold(
        enlarged,
        175,
        255,
        cv2.THRESH_BINARY
    )

    # =====================================================
    # DEBUG OUTPUT
    # =====================================================

    if debug_output_path is not None:

        debug_output_path = Path(
            debug_output_path
        )

        debug_output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        cv2.imwrite(
            str(debug_output_path),
            processed
        )

    # =====================================================
    # OCR
    # =====================================================

    raw_text = pytesseract.image_to_string(
        processed,
        config=(
            "--psm 7 "
            "-c tessedit_char_whitelist=0123456789,"
        )
    ).strip()

    # =====================================================
    # CLEAN RESULT
    # =====================================================

    cleaned_text = re.sub(
        r"[^0-9,]",
        "",
        raw_text
    )

    numeric_text = cleaned_text.replace(
        ",",
        ""
    )

    if not numeric_text.isdigit():

        return {
            "points": None,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
        }

    return {
        "points": int(numeric_text),
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
    }


# =========================================================
# TEMPLATE DEBUG
# =========================================================

def save_template_debug(
    file_path,
    match,
    output_dir="debug_matches"
):

    if match is None:
        return None

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    image = cv2.imread(str(file_path))

    if image is None:
        raise ValueError(f"Could not open image: {file_path}")

    x = match["x"]
    y = match["y"]
    w = match["width"]
    h = match["height"]

    cv2.rectangle(
        image,
        (x, y),
        (x + w, y + h),
        (0, 0, 255),
        2
    )

    cv2.putText(
        image,
        f"{match['confidence']:.3f}",
        (x, max(20, y - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2
    )

    output_path = (
        output_dir
        / f"match_{Path(file_path).name}"
    )

    cv2.imwrite(
        str(output_path),
        image
    )

    return output_path