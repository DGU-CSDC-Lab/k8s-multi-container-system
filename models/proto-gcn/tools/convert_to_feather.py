# tools/convert_to_feather.py
import pyarrow.parquet as pq
import pyarrow.feather as feather
import os

def run_conversion():
    input_path = 'data/nturgbd/ntu60_3danno.parquet'
    output_path = 'data/nturgbd/ntu60_3danno.feather'
    
    print(f"Reading {input_path}...")
    # 메모리 맵핑으로 읽어서 RAM 점유 최소화
    table = pq.read_table(input_path, memory_map=True)
    
    print(f"Writing to {output_path} (Uncompressed)...")
    # 압축(compression)을 'uncompressed'로 해야 mmap 시 성능이 가장 좋습니다.
    feather.write_feather(table, output_path, compression='uncompressed')
    print("Conversion finished successfully!")

if __name__ == '__main__':
    run_conversion()