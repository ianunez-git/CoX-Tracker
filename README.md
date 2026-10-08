
# CoX Tracker — Old School RuneScape Raid Analytics

**Status:** Work in Progress (WIP)

A Python-based computer vision project focused on extracting raid information from Old School RuneScape screenshots.

The project focuses on Chambers of Xeric (CoX), including Normal and Challenge Mode raids.

## Project Overview

CoX Tracker aims to automate the extraction and analysis of raid statistics from screenshots captured by RuneLite.

The long-term goal is to track raid performance, personal contribution, and reward-related statistics.

## Current Development

The project is currently focused on image processing and numerical data extraction.

Development work includes:

- Locating raid information panels in screenshots.
- Experimenting with OpenCV template matching.
- Handling different panel positions and layouts.
- Building digit templates from sample screenshots.
- Preparing a dataset for numerical recognition.
- Testing detection against Normal and Challenge Mode examples.

These components are experimental and do not yet constitute a complete automated tracking system.

## Technology Stack

- Python 3.12
- OpenCV
- NumPy
- Tesseract OCR (experimental)
- Image processing and template matching
- JSON (planned data persistence)

## Project Structure

```text
CoxTracker/
├── assets/
│   ├── digits/
│   ├── total_template_v1.png
│   └── total_template_v2.png
├── src/
│   ├── filename_parser.py
│   ├── image_reader.py
│   └── raid.py
├── digit_template_builder.py
├── main.py
└── README.md
```

## Development Progress

### Phase 1 — Screenshot Analysis

Exploration of RuneLite screenshot layouts and raid information panels.

### Phase 2 — Panel Detection

Experiments using OpenCV to locate relevant interface elements across different screenshots.

### Phase 3 — Digit Template Builder

Development of a template-generation workflow using known raid point values.

### Phase 4 — Automated Data Extraction

Planned integration of digit recognition and validation into a reusable extraction pipeline.

### Phase 5 — Raid Analytics

Future functionality may include:

- Normal and Challenge Mode completion tracking.
- Total raid points extraction.
- Personal contribution percentage.
- Solo raid identification.
- Statistical analysis of reward probabilities.

## Data and Privacy

Personal screenshots, local datasets, and debugging outputs are excluded from the public repository by default.

Selected anonymized samples may be added later to demonstrate the image processing workflow.

## Disclaimer

This is an independent educational and personal project.

It is not affiliated with Jagex or RuneLite.

Old School RuneScape is a trademark of Jagex Ltd.



## Running the Project

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Screenshot Processing

The main pipeline expects RuneLite screenshots
inside a local `screenshots/` directory.

```bash
python main.py
```

### Digit Template Builder

The template builder processes previously extracted
raid panels stored in `debug_panels/`.

```bash
python digit_template_builder.py
```

**Note:** Sample screenshots and generated debug files
are not included in the repository.

The current implementation is experimental and
requires locally prepared input data.

