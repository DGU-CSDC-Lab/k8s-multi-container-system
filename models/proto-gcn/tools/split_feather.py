import pyarrow.feather as feather
import os

def split_feather(input_path, output_dir, num_shards=10):
    os.makedirs(output_dir, exist_ok=True)
    table = feather.read_table(input_path, memory_map=True)
    total_rows = len(table)
    shard_size = total_rows // num_shards

    for i in range(num_shards):
        start = i * shard_size
        end = start + shard_size if i < num_shards - 1 else total_rows
        shard_table = table.slice(start, end - start)
        
        output_path = os.path.join(output_dir, f'shard_{i}.feather')
        feather.write_feather(shard_table, output_path, compression='zstd')
        print(f"Saved {output_path} ({start} to {end})")

if __name__ == '__main__':
    split_feather('data/nturgbd/ntu60_3danno.feather', 'data/nturgbd/shards')