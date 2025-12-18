import mmcv
import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
import ast
import os.path as osp
from .base import BaseDataset
from .builder import DATASETS

@DATASETS.register_module()
class PoseDatasetArrow(BaseDataset):
    def __init__(self, ann_file, pipeline, split=None, **kwargs):
        self.split = split
        self.table = None  # 워커 복사 방지를 위해 초기값은 None
        
        # BaseDataset 초기화 (내부에서 load_annotations 호출)
        super().__init__(ann_file, pipeline, start_index=0, **kwargs)

    def load_annotations(self):
        """인덱스 생성 시점에 label 정보를 포함하여 Evaluation 시 KeyError 방지"""
        if not osp.exists(self.ann_file):
            raise FileNotFoundError(f"Annotation file not found: {self.ann_file}")

        # 임시로 테이블 로드 (메모리 맵핑 모드)
        tmp_table = feather.read_table(self.ann_file, memory_map=True)
        
        # 1. 필터링 및 평가에 필요한 컬럼만 추출
        all_frame_dirs = tmp_table.column('frame_dir').to_pylist()
        all_labels = tmp_table.column('label').to_pylist()  # 평가(Evaluation)용 라벨 로드
        
        # 2. split 정보 파싱 (train/val 분리용)
        split_raw = tmp_table.column('split_data')[0].as_py()
        if isinstance(split_raw, str):
            try:
                split_dict = ast.literal_eval(split_raw)
            except:
                split_dict = {}
        else:
            split_dict = split_raw if isinstance(split_raw, dict) else {}
        
        # 3. 현재 split에 해당하는 데이터만 필터링하여 리스트 생성
        target_dirs = set(split_dict.get(self.split, []))
        
        video_infos = []
        if target_dirs:
            for i, fd in enumerate(all_frame_dirs):
                if fd in target_dirs:
                    # _idx는 실제 파일의 행 번호, label은 평가 시 필요한 정답
                    video_infos.append({
                        "_idx": i, 
                        "label": int(all_labels[i])
                    })
        else:
            # split 정보가 없을 경우 전체 데이터 사용
            for i in range(len(all_frame_dirs)):
                video_infos.append({
                    "_idx": i, 
                    "label": int(all_labels[i])
                })
            
        print(f"[{self.split}] Successfully indexed {len(video_infos)} samples with labels.")
        
        # 임시 테이블 명시적 해제
        del tmp_table
        return video_infos

    def _get_table(self):
        """각 워커(Process)가 데이터를 요청할 때 독립적인 Memory-mapped File 연결 생성"""
        if self.table is None:
            self.table = feather.read_table(self.ann_file, memory_map=True)
        return self.table

    def __getitem__(self, idx):
        table = self._get_table()
        # load_annotations에서 저장해둔 실제 행 인덱스 가져오기
        actual_idx = self.video_infos[idx]['_idx']
        
        # 해당 행만 슬라이싱 (실제 데이터는 이때 RAM에 올라옴)
        row = table.slice(actual_idx, 1)
        
        # 바이너리 데이터 복원
        kp_bin = row.column('keypoint_data')[0].as_buffer()
        kp_shape = ast.literal_eval(row.column('keypoint_shape')[0].as_py())
        kp_dtype = row.column('keypoint_dtype')[0].as_py()
        
        # float32로 변환하여 연산 안전성 확보
        keypoint = np.frombuffer(kp_bin, dtype=kp_dtype).reshape(kp_shape).astype(np.float32)
        
        results = {
            'frame_dir': row.column('frame_dir')[0].as_py(),
            'label': self.video_infos[idx]['label'], # 미리 로드된 라벨 사용
            'total_frames': int(row.column('total_frames')[0].as_py()),
            'keypoint': keypoint
        }
        
        return self.pipeline(results)