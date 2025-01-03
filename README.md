# Loudv1

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/martjay/Loudv1/actions)

A user-friendly application for audio loudness normalization and dynamic range compression.

This project provides a simple and intuitive interface for processing audio files to achieve consistent loudness levels and manage dynamic range. It leverages industry-standard algorithms and techniques to ensure high-quality audio processing.

![]([https://i.imgur.com/your_image_id.png](https://raw.githubusercontent.com/martjay/Loudv1/refs/heads/main/image.jpg))

## Key Features

* **Loudness Normalization:**  Normalizes audio files to a specified target loudness level (LUFS) using the `pyloudnorm` library, adhering to ITU-R BS.1770 standards.
* **Dynamic Range Compression:** Applies dynamic range compression using the `pydub` library to control the difference between the loudest and quietest parts of the audio.
* **Peak Limiting:** Prevents audio clipping by setting a peak limit target in dBFS.
* **Multiple File Processing:** Allows users to upload and process multiple audio files in batch.
* **Output Format Selection:** Supports saving processed audio in both lossless (WAV) and lossy (AAC) formats.
* **Preset Management:** Enables users to save and load custom processing parameter presets for efficient workflow.
* **User-Friendly Interface:** Built with `gradio` for an accessible and easy-to-use web interface.
* **Cache Management:** Includes options to clear processed files and temporary caches.

## Installation

To run Loudv1 locally, you need to have Python installed. Follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Loudv1.git
   cd Loudv1
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Alternatively, you can install the dependencies individually:
   ```bash
   pip install gradio pydub pyloudnorm numpy
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```
   This will launch the Gradio interface, 和 you can access it in your web browser, usually at `http://localhost:7860`.

**Quick Start with `run.bat` (Windows):**

For Windows users, a `run.bat` file is included for convenience. Simply double-click `run.bat` to automatically install the necessary dependencies and launch the application. Ensure you have Python added to your system's PATH for this to work correctly.

## Usage

1. **Upload Audio Files:** Use the "Upload audio files" component to select one or more audio files for processing.
2. **Set Processing Parameters:** Adjust the target loudness, threshold, ratio, attack, release, and peak limit target using the provided number inputs. Tooltips are available for each parameter to explain their function.
3. **Select Output Format:** Choose between "WAV" and "AAC" for the processed audio output format.
4. **Manage Presets:** Save your current settings as a preset using the "Preset Name" input and "Save Preset" button. Load saved presets using the "Load Preset" dropdown. Delete presets using the "Delete Preset" button.
5. **Process Audio:** Click the "Process" button to start processing the uploaded files. The processing status and original/processed LUFS values will be displayed in the table.
6. **Download Processed Files:** Once processing is complete, download the processed files using the "Download Processed Files" component.
7. **Clear List:** Use the "Clear List" button to remove the current file list and reset the processing table.
8. **Clear Cache Files:** The "Clear Cache Files" button removes temporary processed files from the cache directory.
9. **Open Post-Processing Folder:** Click "Open Post-Processing Folder" to directly access the cache directory where processed files are temporarily stored.

## Technologies Used

* **Python:** The primary programming language for the application.
* **Gradio:**  For building the interactive web interface.

## Dependencies

* **Gradio:** ([https://gradio.app/](https://gradio.app/))
    Interactive web interfaces for machine learning models.

* **pydub:** ([https://github.com/jiaaro/pydub](https://github.com/jiaaro/pydub))
    Manipulate audio with an simple and easy high level interface.

* **pyloudnorm:** ([https://github.com/csteinmetz1/pyloudnorm](https://github.com/csteinmetz1/pyloudnorm))
    Audio loudness measurement and normalization (EBU R128 / ITU-R BS.1770).

* **NumPy:** ([https://numpy.org/](https://numpy.org/))
    The fundamental package for scientific computing with Python.

Standard Python libraries used:

* **os:** For interacting with the operating system, such as file path manipulation.
* **tempfile:** For creating temporary files and directories.
* **shutil:** For high-level file operations, like copying files.
* **platform:** For accessing underlying platform identifying data.
* **subprocess:** For spawning new processes.
* **json:** For working with JSON data, used for saving and loading presets.

## License

This project use MIT License.

## Contributing

Contributions are welcome! If you have suggestions for improvements or find any issues, please feel free to open an issue or submit a pull request on the GitHub repository.

## About

Loudv1 offers a straightforward solution for normalizing the loudness and managing the dynamic range of your audio files. Built with Python and a user-friendly Gradio interface, it aims to make professional audio processing techniques accessible to everyone.

## Resources

* [GitHub Repository](https://github.com/martjay/Loudv1)

## Activity

[![GitHub last commit](https://img.shields.io/github/last-commit/martjay/Loudv1)](https://github.com/martjay/Loudv1/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/martjay/Loudv1)](https://github.com/martjay/Loudv1/issues)
[![GitHub pull requests](https://img.shields.io/github/pulls/martjay/Loudv1)](https://github.com/martjay/Loudv1/pulls)

## Footer

© 2025 martjay/Organization.
