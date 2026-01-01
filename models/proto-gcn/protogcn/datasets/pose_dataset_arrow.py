import mmcv
import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
import ast
import os.path as osp
from .base import BaseDataset
from .builder import DATASETS

@DATASETS.register_module()
class PoseDatasetParquet(BaseDataset):
    def __init__(self, ann_file, pipeline, split=None, **kwargs):
        self.ann_file = ann_file
        self.split = split
        self.pq_file = None # 워커별 핸들
        super().__init__(ann_file, pipeline, start_index=0, **kwargs)

    def load_annotations(self):
        # 인덱싱 단계: 파일 전체를 읽지 않고 '메타데이터'만 봅니다.
        table = pq.read_table(self.ann_file, columns=['frame_dir', 'label', 'split_data'])
        
        # (이후 split 필터링 로직은 이전과 동일하게 수행)
        # video_infos에 idx와 label 등을 저장
        # ... 
        return video_infos

    def __getitem__(self, idx):
        if self.pq_file is None:
            # 워커 프로세스에서 처음 호출될 때 파일을 엽니다.
            self.pq_file = pq.ParquetFile(self.ann_file)
        
        actual_idx = self.video_infos[idx]['_idx']
        
        # 특정 행만 읽기 (Parquet의 핵심 기능)
        row = self.pq_file.read_row_group(actual_idx // 1000).to_pandas().iloc[actual_idx % 1000] 
        # (주의: Row group 크기에 따라 인덱싱 방식은 최적화 가능)
        
        # 데이터 복원
        keypoint = np.frombuffer(row['keypoint_bin'], 
                                dtype=row['keypoint_dtype']).reshape(eval(row['keypoint_shape']))
        
        results = {
            'frame_dir': row['frame_dir'],
            'label': int(row['label']),
            'total_frames': int(row['total_frames']),
            'keypoint': keypoint.astype(np.float32)
        }
        return self.pipeline(results)