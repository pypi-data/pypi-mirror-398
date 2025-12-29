import cv2
import os
import sys
import argparse
import time
import signal
from queue import Queue, Empty
from threading import Thread, Event

def analyze_video(video_path):
    """
    Analyzes a video file and displays key information.
    Args:
        video_path (str): The path to the input video file.
    Returns:
        bool: True if analysis was successful, False otherwise.
    """
    if not os.path.exists(video_path):
        print(f"Error: Input video file not found at '{video_path}'")
        return False

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return False

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0

    cap.release()

    print("\n" + "="*50)
    print("  Video Analysis:")
    print("="*50)
    print(f"  File:        {os.path.basename(video_path)}")
    print(f"  Duration:    {duration:.2f} seconds")
    print(f"  Resolution:  {width}x{height}")
    print(f"  FPS:         {fps:.2f}")
    print(f"  Frames:      {frame_count}")
    print("="*50 + "\n")

    return True

def write_frames_worker(queue, output_folder, video_name, ext, write_params, stop_event):
    """
    Worker thread that writes frames from the queue to disk.

    Args:
        queue (Queue): Queue with tuples (frame_number, frame_data)
        output_folder (str): Output folder
        video_name (str): Base video name
        ext (str): File extension (png, jpg)
        write_params (list): cv2.imwrite parameters
        stop_event (Event): Event to signal graceful shutdown
    """
    while not stop_event.is_set():
        try:
            item = queue.get(timeout=0.1)
            if item is None:  # Señal de terminación
                queue.task_done()
                break

            frame_number, frame = item
            image_filename = os.path.join(output_folder, f"{video_name}_frame_{frame_number:05d}.{ext}")
            cv2.imwrite(image_filename, frame, write_params)
            queue.task_done()
        except Empty:
            continue

def extract_frames(video_path, output_folder, format="png", quality=95, threads=4):
    """
    Extracts all frames from a video and saves them as images.

    Args:
        video_path (str): Path to the input video file.
        output_folder (str): Folder where frames will be saved.
        format (str): Output format: 'png', 'jpg', 'jpeg' (default: 'png').
        quality (int): JPEG quality 1-100 (default: 95, JPEG only).
        threads (int): Number of parallel threads for writing (default: 4).
    """
    start_time = time.time()
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file for processing.")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created directory '{output_folder}' for saving frames.")

    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # Determinar extensión y parámetros según formato
    if format.lower() in ["jpg", "jpeg"]:
        ext = format.lower()  # Respetar el formato especificado (jpg o jpeg)
        write_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    else:
        ext = "png"
        write_params = []

    # Crear cola, evento de parada y workers para escritura paralela
    queue = Queue(maxsize=threads * 2)  # Buffer limitado para evitar alto uso de RAM
    stop_event = Event()
    workers = []

    for _ in range(threads):
        worker = Thread(target=write_frames_worker,
                       args=(queue, output_folder, video_name, ext, write_params, stop_event),
                       daemon=True)
        worker.start()
        workers.append(worker)

    print(f"Extracting frames from '{os.path.basename(video_path)}' as {ext.upper()} with {threads} threads...")

    frame_count = 0
    interrupted = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Enviar frame a la cola para escritura paralela
            queue.put((frame_count, frame))
            frame_count += 1

    except KeyboardInterrupt:
        interrupted = True
        print("\n\n⚠️  Interrupted by user. Cleaning up...")
        stop_event.set()

    finally:
        cap.release()

        if not interrupted:
            # Esperar a que se procesen todos los frames
            queue.join()

        # Señalar a los workers que terminen
        for _ in range(threads):
            try:
                queue.put(None, timeout=0.1)
            except:
                pass

        # Esperar a que todos los workers terminen
        for worker in workers:
            worker.join(timeout=1)

    if interrupted:
        print(f"✓ Extraction cancelled. {frame_count} frames were processed before interruption.")
        sys.exit(130)  # Standard exit code for SIGINT

    elapsed_time = time.time() - start_time

    print(f"\n{'='*50}")
    print(f"  Extraction Complete")
    print(f"{'='*50}")
    print(f"  Frames processed: {frame_count}")
    print(f"  Format:           {ext.upper()}")
    print(f"  Output folder:    {output_folder}")
    print(f"  Time elapsed:     {elapsed_time:.2f} seconds")
    print(f"  Speed:            {frame_count/elapsed_time:.1f} frames/sec")
    print(f"{'='*50}")

def main():
    parser = argparse.ArgumentParser(description="Extract frames from a video file.")
    parser.add_argument("video_path", help="Path to the input video file.")
    parser.add_argument("-o", "--output", default=None,
                        help="Output folder for frames (default: <video_name>_frames)")
    parser.add_argument("-d", "--detail", action="store_true",
                        help="Show detailed video analysis before extraction")
    parser.add_argument("-f", "--format", default="png",
                        choices=["png", "jpg", "jpeg"],
                        help="Output image format (default: png)")
    parser.add_argument("-q", "--quality", type=int, default=95,
                        help="JPEG quality 1-100 (default: 95, only for JPEG format)")
    parser.add_argument("-t", "--threads", type=int, default=4,
                        help="Number of parallel threads for writing (default: 4)")

    args = parser.parse_args()

    # Validar argumentos
    if not os.path.exists(args.video_path):
        print(f"Error: Video file not found at '{args.video_path}'")
        sys.exit(1)

    if args.threads < 1:
        print("Error: Number of threads must be at least 1")
        sys.exit(1)

    if args.quality < 1 or args.quality > 100:
        print("Error: JPEG quality must be between 1 and 100")
        sys.exit(1)

    video_name_no_ext = os.path.splitext(os.path.basename(args.video_path))[0]

    # Analizar el video solo si se solicita
    if args.detail:
        if not analyze_video(args.video_path):
            sys.exit(1)

    # Determinar carpeta de salida
    output_folder = args.output if args.output else f"{video_name_no_ext}_frames"

    # Extraer frames
    extract_frames(args.video_path, output_folder, args.format, args.quality, args.threads)

if __name__ == "__main__":
    main()
