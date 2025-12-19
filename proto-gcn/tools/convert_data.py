import pickle
import pyarrow as pa
import numpy as np
import sys
import os
import gc

def convert_pkl_to_feather_streaming(pkl_path, feather_path, chunk_size=2000):
    print(f"Loading {pkl_path}...")
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
    
    annotations = data['annotations']
    split_info = str(data['split'])
    total = len(annotations)
    
    del data
    gc.collect()

    print(f"Total: {total}. 정밀도 낮추기(Float16) 및 고성능 압축(ZSTD) 시작...")

    writer = None
    sink = None
    
    try:
        for i in range(0, total, chunk_size):
            end = min(i + chunk_size, total)
            chunk = annotations[i:end]
            
            batch_data = {
                'frame_dir': [], 'label': [], 'total_frames': [],
                'keypoint_data': [], 'keypoint_shape': [], 'keypoint_dtype': [],
                'split_data': [split_info] * len(chunk)
            }

            for item in chunk:
                # 1. Float16으로 변환: 용량 4배 절감 (Float64 기준)
                # 스켈레톤 데이터는 정밀도가 아주 높지 않아도 학습에 지장이 없습니다.
                kp = item['keypoint'].astype(np.float16)
                
                batch_data['frame_dir'].append(item['frame_dir'])
                batch_data['label'].append(item['label'])
                batch_data['total_frames'].append(item['total_frames'])
                batch_data['keypoint_data'].append(kp.tobytes())
                batch_data['keypoint_shape'].append(str(kp.shape))
                batch_data['keypoint_dtype'].append(str(kp.dtype))

            table = pa.Table.from_pydict(batch_data)
            
            if writer is None:
                sink = pa.OSFile(feather_path, 'wb')
                # 2. ZSTD 압축 적용: LZ4보다 압축률이 훨씬 뛰어납니다.
                # 속도와 용량 사이의 최적의 균형점입니다.
                write_options = pa.ipc.IpcWriteOptions(compression='zstd')
                writer = pa.ipc.new_file(sink, table.schema, options=write_options)
            
            writer.write_table(table)
            
            del chunk, batch_data, table
            gc.collect()
            print(f"Processed {end}/{total}...")

    finally:
        if writer:
            writer.close()
        if sink:
            sink.close()
        print(f"변환 완료! 최종 파일: {feather_path}")

if __name__ == '__main__':
    convert_pkl_to_feather_streaming(sys.argv[1], sys.argv[2])