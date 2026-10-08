from pathlib import Path

from src.filename_parser import parse_filename

from src.image_reader import (
    get_image_info,
    find_total_template,
    extract_points_panel,
    extract_personal_points,
    save_template_debug,
)


# =========================================================
# CONFIGURATION
# =========================================================

SCREENSHOTS_DIR = Path("screenshots")

DEBUG_PANELS_DIR = Path("debug_panels")

DEBUG_OCR_DIR = Path("debug_ocr")

MATCH_THRESHOLD = 0.75


# =========================================================
# MAIN
# =========================================================

def main():

    print("=== CoX Tracker v0.1 ===\n")

    if not SCREENSHOTS_DIR.exists():

        print(
            "No existe la carpeta screenshots."
        )

        return

    files = sorted(
        file
        for file in SCREENSHOTS_DIR.iterdir()
        if file.suffix.lower()
        in {".png", ".jpg", ".jpeg"}
    )

    if not files:

        print(
            "No se encontraron capturas."
        )

        return

    DEBUG_PANELS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DEBUG_OCR_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    raids = []

    ignored = 0

    points_detected = 0
    points_failed = 0

    # =====================================================
    # PROCESS FILES
    # =====================================================

    for file in files:

        result = parse_filename(file)

        # -------------------------------------------------
        # Ignore unrelated files
        # -------------------------------------------------

        if not result:

            ignored += 1

            print(
                f"[IGNORADO] {file.name}"
            )

            continue

        raids.append(result)

        # -------------------------------------------------
        # Image information
        # -------------------------------------------------

        image_info = get_image_info(file)

        width = image_info["width"]
        height = image_info["height"]

        print(
            f"{result['mode']} "
            f"#{result['kc']} "
            f"| {width}x{height}"
        )

        # -------------------------------------------------
        # Find Total anchor
        # -------------------------------------------------

        total_match = find_total_template(
            file
        )

        if total_match is None:

            print(
                "   Total: NOT FOUND"
            )

            points_failed += 1

            print()

            continue

        confidence = (
            total_match["confidence"]
        )

        if confidence >= MATCH_THRESHOLD:

            status = "MATCH"

        else:

            status = "REVIEW"

        print(
            f"   [{status}] "
            f"Total at "
            f"({total_match['x']}, "
            f"{total_match['y']}) "
            f"| confidence="
            f"{confidence:.3f}"
        )

        save_template_debug(
            file,
            total_match
        )

        # -------------------------------------------------
        # Safe filenames
        # -------------------------------------------------

        safe_mode = (
            result["mode"]
            .replace(" ", "_")
        )

        identifier = (
            f"{safe_mode}_"
            f"{result['kc']}"
        )

        # -------------------------------------------------
        # Extract panel
        # -------------------------------------------------

        panel_output = (
            DEBUG_PANELS_DIR
            / f"{identifier}_panel.png"
        )

        panel = extract_points_panel(
            file,
            total_match,
            output_path=panel_output
        )

        if panel is None:

            print(
                "   Panel: ERROR"
            )

            points_failed += 1

            print()

            continue

        # -------------------------------------------------
        # Extract personal points
        # -------------------------------------------------

        ocr_output = (
            DEBUG_OCR_DIR
            / f"{identifier}_personal_points.png"
        )

        points_result = extract_personal_points(
            panel,
            debug_output_path=ocr_output
        )

        if (
            points_result is None
            or points_result["points"] is None
        ):

            points_failed += 1

            print(
                "   Personal points: "
                "NOT FOUND"
            )

            if points_result:

                print(
                    f"   OCR raw: "
                    f"'{points_result['raw_text']}'"
                )

        else:

            points_detected += 1

            points = (
                points_result["points"]
            )

            print(
                f"   Personal points: "
                f"{points:,}"
            )

            print(
                f"   OCR raw: "
                f"'{points_result['raw_text']}'"
            )

        print()

    # =====================================================
    # SUMMARY
    # =====================================================

    print(
        "--------------------------------"
    )

    print(
        f"Capturas encontradas: "
        f"{len(files)}"
    )

    print(
        f"Raids reconocidos:    "
        f"{len(raids)}"
    )

    print(
        f"Ignorados:            "
        f"{ignored}"
    )

    print(
        f"Puntos detectados:    "
        f"{points_detected}"
    )

    print(
        f"Lecturas fallidas:     "
        f"{points_failed}"
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()