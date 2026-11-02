# Custom Camshaft Counter - source reference

Jurius Azar: recognition and report-generation code. Niklas Lowe: mechanical system and motion implementation.

## Key
- `integrated/Class-2024-04-30.py`: April 30, 2024 demonstration snapshot. `AnalyzeImage` / `findCamContours` detect and orient a part; `decodeCode` tries QR readers then template matching; `DetectCam` handles empty and unknown slots; the main loop scans and builds a label grid.
- `integrated/ReportUpload.py`: color overlay, counts, PDF, stable Drive URL and QR generation.
- `integrated/Arduino.py`: serial interface to the G-code motion controller.
- `integrated/Upload_code.py` and `MasterMind.py`: upload and competition game support.
- `development/`: selected original threshold, rotation, recognition, and report-layout experiments. These are separate snapshots, not a fabricated commit history or a single runnable application.

## Status and setup
The physical project was completed and used at LSM. The integrated snapshot defaults to stored-image simulation (`bSimulateAll = True`) using color-labeled demonstration pucks. It is not the production part-number configuration. 

Imports in ReportUpload.py perform Google authentication, even in simulation. To run the original integrated program requires a configured Python desktop environment, the dependencies listed in requirements-reference.txt, the native ZBar library where required, your own Google OAuth configuration, your own Drive folder IDs, and an Arial font file available at the path expected by the code. Historical scripts contain local paths and interactive OpenCV windows and may require environment-specific setup. Physical operation additionally requires the original camera, controller and calibration.  

## Packaging changes
Account-specific Drive folder/file IDs were replaced with REPLACE_WITH_YOUR_DRIVE_ID. 

MANIFEST.json maps each included original asset to its archive location and records a hash of the shareable file. It identifies which code files had Drive identifiers removed. Dependencies in requirements-reference.txt were inferred from source imports for reference, not recovered from a lockfile.
