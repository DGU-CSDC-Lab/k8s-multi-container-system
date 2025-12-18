import mmcv
import numpy as np
import os.path as osp
import pyarrow.parquet as pq
import ast
from .base import BaseDataset
from .builder import DATASETS

@DATASETS.register_module()
class PoseDatasetParquet(BaseDataset):
    def __init__(self, ann_file, pipeline, split=None, **kwargs):
        self.split = split
        self.ann_file = ann_file
        self.pq_reader = None
        super().__init__(ann_file, pipeline, start_index=0, modality='Pose', **kwargs)

    def load_annotations(self):
        """행 그룹(Row Group)과 내부 인덱스를 매핑하여 IndexError/TypeError 원천 봉쇄"""
        f = pq.ParquetFile(self.ann_file)
        
        # 1. split_data 읽기 (0번 행 그룹에서만)
        first_row = f.read_row_group(0, columns=['split_data']).slice(0, 1).to_pandas()
        raw_split = first_row['split_data'].iloc[0]
        split_dict = ast.literal_eval(raw_split) if isinstance(raw_split, str) else raw_split
        target_filenames = set(split_dict.get(self.split, [])) if self.split else None

        video_infos = []
        # 2. 모든 행 그룹을 돌며 각 행의 '정확한 주소'를 기록
        for rg_idx in range(f.num_row_groups):
            # 인덱싱에 필요한 최소 컬럼만 로드
            rg_table = f.read_row_group(rg_idx, columns=['frame_dir', 'label', 'total_frames'])
            df_rg = rg_table.to_pandas()
            
            for local_idx, row in df_rg.iterrows():
                if target_filenames is None or row['frame_dir'] in target_filenames:
                    video_infos.append({
                        'rg_idx': rg_idx,     # 몇 번째 행 그룹인지
                        'local_idx': local_idx, # 그 그룹 안에서 몇 번째인지
                        'frame_dir': osp.join(self.data_prefix, row['frame_dir']),
                        'label': int(row['label']),
                        'total_frames': int(row['total_frames'])
                    })
        
        print(f" >>> [Split: {self.split}] 인덱싱 완료: {len(video_infos)}개 샘플")
        return video_infos

    def prepare_train_frames(self, idx):
        # 1. 미리 저장한 '지도' 정보 꺼내기
        info = self.video_infos[idx]
        rg_idx = info['rg_idx']
        lc_idx = info['local_idx']
        
        if self.pq_reader is None:
            self.pq_reader = pq.ParquetFile(self.ann_file, memory_map=True)
            
        # 2. [버전 호환성 최강] read_row_group으로 그룹 전체를 읽고 slice로 한 줄만 선택
        # indices 인자를 쓰지 않으므로 TypeError가 발생하지 않습니다.
        rg_table = self.pq_reader.read_row_group(rg_idx, columns=['keypoint_bin', 'kp_shape', 'kp_dtype'])
        row = rg_table.slice(lc_idx, 1).to_pandas().iloc[0]

        # 3. 결과 딕셔너리 구성
        results = info.copy()
        kp_bin = row['keypoint_bin']
        kp_shape = ast.literal_eval(row['kp_shape']) if isinstance(row['kp_shape'], str) else row['kp_shape']
        kp_dtype = row['kp_dtype']
        
        results['keypoint'] = np.frombuffer(kp_bin, dtype=kp_dtype).reshape(kp_shape).astype(np.float32)
        
        return self.pipeline(results)

    def prepare_test_frames(self, idx):
        return self.prepare_train_frames(idx)

    def __getitem__(self, idx):
        return self.prepare_test_frames(idx) if self.test_mode else self.prepare_train_frames(idx)
