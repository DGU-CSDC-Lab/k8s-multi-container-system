import numpy as np
import pickle
import sys
import os
import pyarrow as pa
import pyarrow.parquet as pq

def convert_pkl_to_parquet_streaming(src, dst):
    print(f"Loading {src} into memory (Initial Load)...")
    with open(src, 'rb') as f:
        raw_data = pickle.load(f)

    if isinstance(raw_data, dict) and 'annotations' in raw_data:
        data_list = raw_data['annotations']
        split_info = str(raw_data.get('split', {}))
        print(f"NTU format detected. Total: {len(data_list)} items.")
    else:
        data_list = raw_data
        split_info = "{}"
        print(f"List format detected. Total: {len(data_list)} items.")

    # Parquet 스키마 정의 (데이터 구조 고정)
    schema = pa.schema([
        ('frame_dir', pa.string()),
        ('label', pa.int64()),
        ('total_frames', pa.int64()),
        ('keypoint_bin', pa.binary()),
        ('kp_shape', pa.string()),
        ('kp_dtype', pa.string()),
        ('split_data', pa.string())
    ])

    print(f"Starting Streaming conversion to {dst}...")
    # ParquetWriter를 사용하여 파일 핸들을 열어둠
    with pq.ParquetWriter(dst, schema, compression='snappy') as writer:
        batch_size = 500  # 500개씩 끊어서 처리 (RAM 압박 최소화)
        for i in range(0, len(data_list), batch_size):
            batch_data = data_list[i:i + batch_size]
            
            rows = []
            for item in batch_data:
                rows.append({
                    'frame_dir': item['frame_dir'],
                    'label': int(item['label']),
                    'total_frames': int(item['total_frames']),
                    'keypoint_bin': item['keypoint'].tobytes(),
                    'kp_shape': str(item['keypoint'].shape),
                    'kp_dtype': str(item['keypoint'].dtype),
                    'split_data': split_info
                })
            
            # 리스트를 테이블로 변환 후 바로 디스크에 기록
            table = pa.Table.from_pylist(rows, schema=schema)
            writer.write_table(table)
            
            if (i + batch_size) % 5000 == 0 or (i + batch_size) >= len(data_list):
                print(f"Progress: {min(i + batch_size, len(data_list))}/{len(data_list)} processed...")

    final_size = os.path.getsize(dst) / (1024**3)
    print(f"Success! Parquet file created: {final_size:.2f} GB")

if __name__ == "__main__":
    convert_pkl_to_parquet_streaming(sys.argv[1], sys.argv[2])