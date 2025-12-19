import numpy as np
import copy
import torch
from .builder import DATASETS
from .base import BaseDataset

@DATASETS.register_module()
class PoseDatasetNPY(BaseDataset):
    def __init__(self, data_path, label_path, pipeline, split=None, test_mode=False):
        self.data_path = data_path
        self.label_path = label_path
        
        # [수정] __init__에서는 14GB 데이터를 로드하지 않습니다 (4GB 직렬화 에러 방지)
        # 라벨은 크기가 작으므로 여기서 로드해도 무방합니다.
        self.labels = np.load(label_path)
        self.data = None  # 실제 데이터 핸들은 나중에 생성

        # 2. 부모 클래스(BaseDataset) 초기화
        super().__init__(
            ann_file=data_path, 
            pipeline=pipeline, 
            test_mode=test_mode)

    def load_mmap(self):
        """데이터가 필요할 때 워커 프로세스별로 처음 한 번만 파일을 엽니다."""
        if self.data is None:
            # mmap_mode='r'은 파일을 메모리에 올리지 않고 주소만 매핑합니다.
            self.data = np.load(self.data_path, mmap_mode='r')

    def load_annotations(self):
        """프레임워크가 데이터 인덱스를 생성하는 단계"""
        video_infos = []
        for i in range(len(self.labels)):
            # 실제 데이터를 읽지 않고, 인덱스와 라벨 정보만 리스트에 담음
            video_infos.append(dict(index=i, label=self.labels[i]))
        return video_infos

    def prepare_train_frames(self, idx):
        """학습 시 데이터를 로드하고 Pipeline을 태우는 단계"""
        self.load_mmap()
        results = copy.deepcopy(self.video_infos[idx])

        # [수정] (C, T, V, M) -> (M, T, V, C)로 순서 변경
        # 저장된 데이터: (3, 300, 25, 2) -> 파이프라인 기대값: (2, 300, 25, 3)
        raw_data = np.array(self.data[idx]) 
        results['keypoint'] = raw_data.transpose(3, 1, 2, 0) 

        return self.pipeline(results)

    def prepare_test_frames(self, idx):
        """테스트 시 데이터 로드"""
        self.load_mmap()
        results = copy.deepcopy(self.video_infos[idx])
        
        # [수정] 동일하게 순서 변경
        raw_data = np.array(self.data[idx]) 
        results['keypoint'] = raw_data.transpose(3, 1, 2, 0) 
        
        return self.pipeline(results)
