import json
import pathlib
import subprocess
import click
import av
import tqdm

@click.command()
@click.option('--input_video', '-iv', required=True, help='Input mp4 file')
@click.option('--input_json', '-ij', required=True, help='Input json file')
@click.option('--output_dir', '-o', required=True, help='Output dir')
@click.option('--video_downres_ratio', '-vr', default=3, type=int)
@click.option('--crf', default=20, type=str)
def main(input_video, input_json, output_dir, video_downres_ratio, crf):
    # read json
    input_json_data = json.load(open(input_json,'r'))
    print(f"Loaded IMU data from {input_json_data['1']['device name']} with streams {list(input_json_data['1']['streams'].keys())}")
    accl_stream = input_json_data['1']['streams']['ACCL']
    gyro_stream = input_json_data['1']['streams']['GYRO']
    accl_samples = accl_stream['samples']
    gyro_samples = gyro_stream['samples']
    print(f"Using ACCL stream with name {accl_stream['name']} and unit {accl_stream['units']} which contains {len(accl_samples)} samples.")
    print(f"Using GYRO stream with name {gyro_stream['name']} and unit {gyro_stream['units']} which contains {len(gyro_samples)} samples.")
    # start time in seconds
    start_time = accl_samples[0]['cts'] / 1000
    
    # read video metadata
    with av.open(input_video, mode='r') as in_container:
        # get info from input video stream
        in_stream = in_container.streams.video[0]
        in_fps = in_stream.average_rate
        in_frames = in_stream.frames
    
    # allocate output files
    output_dir = pathlib.Path(output_dir)
    # if output_dir.exists():
    #     click.confirm('Output path already exists! Overwrite?', abort=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    out_video_path = output_dir.joinpath('data.mp4')
    out_jsonl_path = output_dir.joinpath('data.jsonl')
        
    # open video file
    print("Writing JsonL")
    with open(out_jsonl_path, mode='w') as out_jsonl:
        next_sample_idx = 0
        for frame_idx in range(in_frames):
            since_start = float(frame_idx / in_fps)
            frame_time = start_time + since_start
    
            # write all IMU data before this frame
            while (accl_samples[next_sample_idx]['cts'] / 1000) <= frame_time:
                this_accl_data = accl_samples[next_sample_idx]
                this_gyro_data = gyro_samples[next_sample_idx]
                
                # write ACCL line
                this_accl_line_data = {
                    'sensor': {
                        'type': 'accelerometer',
                        'values': this_accl_data['value'],
                    },
                    'time': this_accl_data['cts'] / 1000
                }
                
                # write GYRO line
                this_gyro_line_data = {
                    'sensor': {
                        'type': 'gyroscope',
                        'values': this_gyro_data['value']
                    },
                    'time': this_gyro_data['cts'] / 1000
                }
                # write 2 lines at once
                line = '\n'.join([
                    json.dumps(this_accl_line_data),
                    json.dumps(this_gyro_line_data),
                    ''
                ])
                out_jsonl.write(line)
                
                next_sample_idx += 1
            
            # write frame line
            frame_line_data = {
                'frames': [
                    {
                        'cameraInd': 0,
                        'cameraParameters': {
                            'distortionCoefficients': [-0.004973, 0.03975, -0.0374, 0.006239],
                            'distortionModel': 'KANNALA_BRANDT4',
                            'focalLengthX': 284.929992675781,
                            'focalLengthY': 285.165496826172,
                            'principalPointX': 416.4547119140625,
                            'principalPointY': 395.77349853515625
                        },
                        'imuToCamera': [[0.01486, 0.9995, -0.02577, 0.06522],
                                        [-0.9998, 0.01496, 0.003756, -0.0207],
                                        [0.00414, 0.02571, 0.9996, -0.008054],
                                        [0, 0, 0, 1]],
                        'time': frame_time
                    }
                ],
                'number': frame_idx,
                'time': frame_time
            }
            line = json.dumps(frame_line_data) + '\n'
            out_jsonl.write(line)
    print("JsonL Written")
    
    # resize video
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-i', input_video,
        '-vf', f"scale=iw/{video_downres_ratio}:ih/{video_downres_ratio}",
        '-crf', crf,
        str(out_video_path)
    ]
    print(' '.join(ffmpeg_cmd))
    subprocess.run(ffmpeg_cmd)

if __name__ == "__main__":
    main()
