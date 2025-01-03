import gradio as gr
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range
import pyloudnorm as pyln
import io
import os
import numpy as np
import tempfile
import shutil
import platform
import subprocess
import json

CACHE_DIR = "gradio_cache"
PRESETS_DIR = "presets"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(PRESETS_DIR, exist_ok=True)

def calculate_lufs(audio_file_path):
    try:
        audio = AudioSegment.from_file(audio_file_path)
        samplerate = audio.frame_rate
        data = np.array(audio.get_array_of_samples())
        if audio.sample_width == 1:
            data = (data / 2**7).astype(np.float32)
        elif audio.sample_width == 2:
            data = (data / 2**15).astype(np.float32)
        elif audio.sample_width == 3:
            data = (data / 2**23).astype(np.float32)
        elif audio.sample_width == 4:
            data = (data / 2**31).astype(np.float32)
        meter = pyln.Meter(samplerate)
        loudness = meter.integrated_loudness(data)
        return loudness
    except Exception as e:
        return f"Unable to calculate LUFS: {str(e)}"

def process_single_audio(file_name, file_list, output_format, target_loudness, threshold, ratio, attack, release, peak_limit_target):
    normalized_file_name = file_name.lower().strip()
    print(f"process_single_audio: Processing file (normalized): {normalized_file_name}, Target Loudness: {target_loudness} LUFS")
    print(f"process_single_audio: Dynamic compression parameters - threshold={threshold}, ratio={ratio}, attack={attack}, release={release}")
    print(f"process_single_audio: Peak limit target - {peak_limit_target} dBFS")
    audio_file_obj = next((f for f in file_list if os.path.basename(f.name).lower().strip() == normalized_file_name), None)
    if not audio_file_obj:
        print(f"process_single_audio: File not found: {file_name}")
        return "File not found", None

    try:
        audio = AudioSegment.from_file(audio_file_obj.name)
        compressed_audio = compress_dynamic_range(audio, threshold=threshold, ratio=ratio, attack=attack, release=release)
        gain_reduction = max(0, compressed_audio.max_dBFS - peak_limit_target)
        limited_audio = compressed_audio - gain_reduction
        samplerate = limited_audio.frame_rate
        data = np.array(limited_audio.get_array_of_samples())
        if limited_audio.sample_width == 1:
            data = (data / 2**7).astype(np.float32)
        elif limited_audio.sample_width == 2:
            data = (data / 2**15).astype(np.float32)
        elif limited_audio.sample_width == 3:
            data = (data / 2**23).astype(np.float32)
        elif limited_audio.sample_width == 4:
            data = (data / 2**31).astype(np.float32)
        meter = pyln.Meter(samplerate)
        loudness = meter.integrated_loudness(data)
        delta_loudness = target_loudness - loudness
        normalized_audio = limited_audio.apply_gain(delta_loudness)
        output_buffer = io.BytesIO()
        normalized_audio.export(output_buffer, format=output_format.lower())
        output_buffer.seek(0)

        original_name, ext = os.path.splitext(file_name)
        cache_file_path = os.path.join(CACHE_DIR, f"{original_name}_processed.{output_format.lower()}")
        with open(cache_file_path, "wb") as f:
            f.write(output_buffer.read())

        print(f"process_single_audio: File processing completed, saved to cache: {cache_file_path}")
        return "Completed", cache_file_path

    except Exception as e:
        print(f"process_single_audio: Processing failed: {str(e)}")
        return f"Processing failed: {str(e)}", None

def on_file_upload(audio_files, file_info_state):
    file_info = []
    for audio_file in audio_files:
        file_name = os.path.basename(audio_file.name)
        print(f"on_file_upload: Filename added to file_info: {file_name}")
        lufs = calculate_lufs(audio_file.name)
        file_info.append([file_name, "Waiting to process", lufs, None])
    return gr.update(value=file_info), file_info

def process_all(file_info_list, file_list, output_format, target_loudness_input, threshold, ratio, attack, release, peak_limit_target):
    print(f"process_all: Start processing all files, target loudness: -{target_loudness_input} LUFS")
    print(f"process_all: Dynamic compression parameters - threshold={threshold}, ratio={ratio}, attack={attack}, release={release}")
    print(f"process_all: Peak limit target - {peak_limit_target} dBFS")
    print(f"process_all: Initial file_info_list={file_info_list}")
    print(f"process_all: file_list={[f.name for f in file_list]}")
    updated_file_info = []
    download_files = []
    for item in file_info_list:
        filename = item[0]
        print(f"process_all: Start processing file: {filename}")
        status, output_file_path = process_single_audio(filename, file_list, output_format, -target_loudness_input, threshold, ratio, attack, release, peak_limit_target)
        print(f"process_all: File {filename} processing result - Status: {status}, Output path: {output_file_path}")
        processed_lufs = None
        if output_file_path:
            processed_lufs = calculate_lufs(output_file_path)
            download_files.append(output_file_path)
        updated_file_info.append([filename, status, item[2], processed_lufs])
        print(f"process_all: Updated file_info - {updated_file_info[-1]}")

    print(f"process_all: Processing completed, updated file_info_list={updated_file_info}")
    return gr.update(value=updated_file_info), download_files

def clear_list(file_info_state):
    print("Executing clear cache...")
    clear_cache()
    print("Cache cleared, preparing to clear page elements...")
    return gr.update(value=[]), gr.update(value=[]), gr.update(value=None), gr.update(value=None)

def clear_cache():
    print("Clearing cache started...")
    try:
        # 清理 Gradio 临时缓存目录，但不删除 gradio 目录本身
        temp_dir = tempfile.gettempdir()
        gradio_temp_cache_dir = os.path.join(temp_dir, "gradio")
        print(f"Clearing contents of Gradio temporary cache directory: {gradio_temp_cache_dir}")
        try:
            if os.path.exists(gradio_temp_cache_dir):
                for item in os.listdir(gradio_temp_cache_dir):
                    item_path = os.path.join(gradio_temp_cache_dir, item)
                    try:
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Unable to delete {item_path}. Reason: {e}")
                print(f"Contents of Gradio temporary cache directory cleared: {gradio_temp_cache_dir}")
            else:
                print(f"Gradio temporary cache directory not found: {gradio_temp_cache_dir}")
        except Exception as e:
            print(f"Error occurred while clearing Gradio temporary cache directory: {e}")

        # 清理项目文件夹下的缓存，不清空目录本身
        project_cache_dir = CACHE_DIR
        print(f"Clearing contents of project cache directory: {project_cache_dir}")
        try:
            if os.path.exists(project_cache_dir):
                for item in os.listdir(project_cache_dir):
                    item_path = os.path.join(project_cache_dir, item)
                    try:
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Unable to delete {item_path}. Reason: {e}")
                print(f"Contents of project cache directory cleared: {project_cache_dir}")
            else:
                print(f"Project cache directory not found: {project_cache_dir}")
        except Exception as e:
            print(f"Error occurred while clearing project cache directory contents: {e}")

        print("Clearing cache completed.")
        return "Cache cleared"
    except Exception as overall_e:
        print(f"A serious error occurred while clearing the cache: {overall_e}")
        return f"Failed to clear cache: {overall_e}"

def batch_save_processed_files(file_info_list, uploaded_files_state):
    if not uploaded_files_state:
        print("batch_save_processed_files: No files uploaded, unable to determine save path.")
        return "No files uploaded, unable to determine save path."

    first_uploaded_file = uploaded_files_state[0].name
    upload_dir = os.path.dirname(first_uploaded_file)
    output_dir = os.path.join(upload_dir, "Normalized Loudness")
    os.makedirs(output_dir, exist_ok=True)

    saved_files = []
    print(f"batch_save_processed_files: Preparing to save file information:")
    for item in file_info_list:
        print(f"  Filename: {item[0]}, Status: {item[1]}, Output path: {item[3]}")
        if item[1] == "Completed" and item[3] is not None:
            source_path = item[3]
            filename = item[0]
            output_filename = f"{os.path.splitext(filename)[0]}_processed{os.path.splitext(source_path)[1]}"
            destination_path = os.path.join(output_dir, output_filename)
            try:
                shutil.copy2(source_path, destination_path)
                saved_files.append(output_filename)
                print(f"batch_save_processed_files: File {filename} saved successfully to {destination_path}")
            except Exception as e:
                print(f"batch_save_processed_files: Failed to save file {filename}: {e}")
        else:
            print(f"batch_save_processed_files: File {item[0]} not processed or no output path, skipping save.")

    if saved_files:
        message = f"Processed files saved to: {output_dir}"
        print(f"batch_save_processed_files: {message}")
        return message
    else:
        message = "No processed files available to save."
        print(f"batch_save_processed_files: {message}")
        return message

def open_post_processing_folder():
    folder_path = CACHE_DIR
    if platform.system() == "Windows":
        os.startfile(folder_path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", folder_path])
    elif platform.system() == "Linux":
        subprocess.run(["xdg-open", folder_path])
    else:
        print(f"Unsupported operating system: {platform.system()}")

def save_preset(preset_name, threshold, ratio, attack, release, peak_limit_target):
    preset_data = {
        "threshold": threshold,
        "ratio": ratio,
        "attack": attack,
        "release": release,
        "peak_limit_target": peak_limit_target
    }
    preset_file_path = os.path.join(PRESETS_DIR, f"{preset_name}.json")
    with open(preset_file_path, "w") as f:
        json.dump(preset_data, f, indent=4)
    print(f"Preset saved: {preset_name}")
    return gr.Dropdown(choices=get_available_presets(), value=preset_name)

def load_preset(preset_name):
    preset_file_path = os.path.join(PRESETS_DIR, f"{preset_name}.json")
    with open(preset_file_path, "r") as f:
        preset_data = json.load(f)
    return (
        preset_data["threshold"],
        preset_data["ratio"],
        preset_data["attack"],
        preset_data["release"],
        preset_data["peak_limit_target"],
    )

def get_available_presets():
    return [f.replace(".json", "") for f in os.listdir(PRESETS_DIR) if f.endswith(".json")]

def refresh_presets():
    return gr.Dropdown(choices=get_available_presets())

def delete_preset(available_presets):
    selected_preset = available_presets
    if selected_preset:
        preset_file_path = os.path.join(PRESETS_DIR, f"{selected_preset}.json")
        try:
            os.remove(preset_file_path)
            print(f"Preset deleted: {selected_preset}")
            return gr.Dropdown(choices=get_available_presets())
        except FileNotFoundError:
            print(f"Preset file not found: {preset_file_path}")
            return gr.Dropdown(choices=get_available_presets())
        except Exception as e:
            print(f"Failed to delete preset: {e}")
            return gr.Dropdown(choices=get_available_presets())
    else:
        print("No preset selected for deletion.")
        return gr.Dropdown(choices=get_available_presets())

with gr.Blocks(theme='JohnSmith9982/small_and_pretty') as iface:
    uploaded_files_state = gr.State([])
    output_format_state = gr.State("WAV")
    file_info_state = gr.State([])
    file_output = gr.Dataframe(headers=["Filename", "Processing Status", "Original LUFS", "Processed LUFS"])
    download_output = gr.Files(label="Download Processed Files")
    with gr.Row():
        with gr.Column():
            audio_input = gr.File(file_types=["audio"], label="Upload audio files", file_count="multiple")
        with gr.Column():
            output_format_label_html = """
                <span title='**Output Format:** Select the file type to save the processed audio.\n\n* **WAV:** A lossless format that retains all audio details, offering the best quality but resulting in larger files, suitable for scenarios requiring the highest fidelity.\n* **AAC:** A lossy format that reduces file size through compression, providing good audio quality, suitable for network transmission and mobile devices.'>
                    Output Format
                </span>
            """
            gr.HTML(output_format_label_html)
            output_format = gr.Radio(["WAV", "AAC"], value="WAV", label="")
            attack_label_html = """
                <span title='**Attack (ms):** The speed at which the dynamic range compressor starts reducing the volume after the audio signal's loudness exceeds the set Threshold. The unit is milliseconds (one-thousandth of a second).\n\n* **Function:** Affects the processing of sudden sounds (transients) in the audio. A shorter attack time can control sudden loud sounds, like drum hits, more quickly but might make the sound seem "muffled." A longer attack time preserves the impact of these sounds.\n* **Beginner Tip:** If your audio contains many sudden, sharp sounds, try a shorter attack time (e.g., 5ms). If you want to preserve the natural impact of sounds, try a longer attack time (e.g., 20ms).'>
                    Attack (ms)
                </span>
            """
            gr.HTML(attack_label_html)
            attack_input = gr.Number(value=5.0, label="")
            release_label_html = """
                <span title='**Release (ms):** The speed at which the dynamic range compressor stops reducing the volume and returns to the original volume after the audio signal's loudness falls below the Threshold. The unit is milliseconds.\n\n* **Function:** Affects the smoothness of the compression process and the "breathing" of the sound. A shorter release time will cause the volume to recover quickly, which may lead to unnatural pumping or "breathing" effects. A longer release time makes volume changes smoother.\n* **Beginner Tip:** If your audio has a fast tempo, try a shorter release time (e.g., 50ms). If the tempo is slower, or you want more natural-sounding changes, try a longer release time (e.g., 150ms).'>
                    Release (ms)
                </span>
            """
            gr.HTML(release_label_html)
            release_input = gr.Number(value=50.0, label="")
        with gr.Column():
            target_loudness_label_html = """
                <span title='**Target Loudness (LUFS):** The overall loudness level you want the processed audio to achieve. LUFS is a unit for measuring audio loudness; the smaller the value, the quieter the sound.\n\n* **Function:** Unifies the volume of different audio files, preventing sudden changes in loudness during playback.\n* **Beginner Tip:** For online videos or music, common target loudness levels are between -16 LUFS and -14 LUFS. For podcasts or audiobooks, you can set it to -19 LUFS to -16 LUFS.'>
                    Set Loudness Value -
                </span>
            """
            gr.HTML(target_loudness_label_html)
            target_loudness_input = gr.Number(value=16, precision=0, label="")
            threshold_label_html = """
                <span title='**Threshold (dBFS):** Sets a loudness "gate." When the audio signal's loudness exceeds this value, the dynamic range compressor starts working to reduce the volume. The unit is dBFS.\n\n* **Function:** Controls when the dynamic range compressor starts. Only sounds exceeding the threshold will be compressed.\n* **Beginner Tip:** You can set the threshold slightly below the loudest parts of your audio. For example, if the loudest part of the audio is -10 dBFS, you could try setting the threshold to -15 dBFS. Lowering the threshold will cause more sounds to be compressed.'>
                    Threshold (dBFS)
                </span>
            """
            gr.HTML(threshold_label_html)
            threshold_input = gr.Number(value=-20.0, label="")
            ratio_label_html = """
                <span title='**Ratio:** Indicates the amount of compression applied when the audio signal's loudness exceeds the Threshold. For example, a ratio of 2:1 means that if the sound exceeds the threshold by 2 decibels, it will only increase by 1 decibel.\n\n* **Function:** Controls the degree of dynamic range reduction. A higher ratio will make the dynamic range smaller and the sound more "compact."\n* **Beginner Tip:** If you only want to slightly control volume fluctuations, use a lower ratio (e.g., 2:1 or 3:1). If you need to reduce the dynamic range more significantly, use a higher ratio (e.g., 4:1 or higher).'>
                    Ratio
                </span>
            """
            gr.HTML(ratio_label_html)
            ratio_input = gr.Number(value=2.0, label="")
        with gr.Column():
            peak_limit_target_label_html = """
                <span title='**Peak Limit Target (dBFS):** Sets the maximum loudness level allowed for the processed audio. The unit is dBFS.\n\n* **Function:** Prevents audio signal overload (causing clipping or distortion), ensuring sound quality.\n* **Beginner Tip:** Usually set to a value slightly below 0 dBFS, such as -1 dBFS or -2 dBFS. 0 dBFS is the maximum volume for digital audio; exceeding this value can lead to clipping distortion.'>
                    Peak Limit Target (dBFS)
                </span>
            """
            gr.HTML(peak_limit_target_label_html)
            peak_limit_target_input = gr.Number(value=-3.0, label="")
            preset_name_input = gr.Textbox(label="Preset Name")
            available_presets = gr.Dropdown(choices=get_available_presets(), label="Load Preset", interactive=True)
            save_preset_button = gr.Button("Save Preset")
            delete_preset_button = gr.Button("Delete Preset")
        with gr.Column():
            pass # The fourth column is now empty
    with gr.Row():
        process_button = gr.Button("Process")
        clear_list_button = gr.Button("Clear List")
        clear_cache_button = gr.Button("Clear Cache Files")
        open_cache_folder_button = gr.Button("Open Post-Processing Folder")

    def update_uploaded_files(files):
        return files

    audio_input.upload(update_uploaded_files, inputs=audio_input, outputs=uploaded_files_state, queue=False)
    audio_input.upload(on_file_upload, inputs=[audio_input, file_info_state], outputs=[file_output, file_info_state], queue=False)
    output_format.change(lambda x: x, inputs=output_format, outputs=output_format_state)
    process_button.click(
        process_all,
        inputs=[file_info_state, uploaded_files_state, output_format_state, target_loudness_input, threshold_input, ratio_input, attack_input, release_input, peak_limit_target_input],
        outputs=[file_output, download_output],
    )
    delete_preset_button.click(
        delete_preset,
        inputs=[available_presets],
        outputs=[available_presets],
    )
    save_preset_button.click(
        save_preset,
        inputs=[preset_name_input, threshold_input, ratio_input, attack_input, release_input, peak_limit_target_input],
        outputs=[available_presets],
    )
    available_presets.change(
        load_preset,
        inputs=[available_presets],
        outputs=[threshold_input, ratio_input, attack_input, release_input, peak_limit_target_input],
    )
    clear_list_button.click(
        clear_list,
        inputs=file_info_state,
        outputs=[file_output, file_info_state, download_output, audio_input]
    )
    clear_cache_button.click(clear_cache)
    open_cache_folder_button.click(open_post_processing_folder)

iface.launch()
