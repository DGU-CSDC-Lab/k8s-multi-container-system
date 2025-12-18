# ---------------------------------------------------------
# 방법론: Memory-mapped Numpy (.npy) 기반 고속 데이터 로딩
# ---------------------------------------------------------

modality = 'bm'
graph = 'nturgb+d'
# 실험 결과 구분을 위해 work_dir 변경
work_dir = f'./work_dirs/ntu60_xsub/bm_npy_memmap'

model = dict(
    type='RecognizerGCN',
    backbone=dict(
        type='ProtoGCN',
        num_prototype=50,
        tcn_ms_cfg=[(3, 1), (3, 2), (3, 3), (3, 4), ('max', 3), '1x1'],
        graph_cfg=dict(layout=graph, mode='random', num_filter=8, init_off=.04, init_std=.02)),
    cls_head=dict(type='SimpleHead', joint_cfg='nturgb+d', num_classes=60, in_channels=384, weight=0.3))

# --- [방법론 핵심 설정 변경] ---
# pose_dataset_npy.py에 정의한 클래스명으로 변경
dataset_type = 'PoseDatasetNPY' 

# .npy 파일 경로 설정 (변환 스크립트로 생성한 파일들)
train_data_path = 'data/nturgbd/ntu60_train_data.npy'
train_label_path = 'data/nturgbd/ntu60_train_label.npy'
val_data_path = 'data/nturgbd/ntu60_val_data.npy'
val_label_path = 'data/nturgbd/ntu60_val_label.npy'

# 파이프라인은 기존 bm.py와 100% 동일하게 유지 (변인 통제)
train_pipeline = [
    dict(type='PreNormalize3D', align_spine=False),
    dict(type='RandomRot', theta=0.2),
    dict(type='Spatial_Flip', dataset='nturgb+d', p=0.5),
    dict(type='GenSkeFeat', feats=[modality]),
    dict(type='UniformSampleDecode', clip_len=100),
    dict(type='FormatGCNInput'),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
val_pipeline = [
    dict(type='PreNormalize3D', align_spine=False),
    dict(type='GenSkeFeat', feats=[modality]),
    dict(type='UniformSampleDecode', clip_len=100, num_clips=1),
    dict(type='FormatGCNInput'),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
test_pipeline = [
    dict(type='PreNormalize3D', align_spine=False),
    dict(type='GenSkeFeat', feats=[modality]),
    dict(type='UniformSampleDecode', clip_len=100, num_clips=10),
    dict(type='FormatGCNInput'),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]

data = dict(
    videos_per_gpu=16,  # npy 방식은 메모리 효율이 좋아 32를 유지해도 안정적입니다.
    workers_per_gpu=4,  # CPU 부하가 낮아져서 4명(Worker)이 동시에 데이터를 밀어줘도 거뜬합니다.
    test_dataloader=dict(videos_per_gpu=1),
    train=dict(
        type=dataset_type, 
        data_path=train_data_path, 
        label_path=train_label_path, 
        pipeline=train_pipeline, 
        split='xsub_train'),
    val=dict(
        type=dataset_type, 
        data_path=val_data_path, 
        label_path=val_label_path, 
        pipeline=val_pipeline, 
        split='xsub_val'),
    test=dict(
        type=dataset_type, 
        data_path=val_data_path, 
        label_path=val_label_path, 
        pipeline=test_pipeline, 
        split='xsub_val'))

# --- [시스템 효율 극대화 옵션] ---
# Mixed Precision 학습을 활성화하여 RTX 3080의 Tensor Core를 활용합니다.
fp16 = dict(loss_scale='dynamic')

# 나머지 학습 설정은 원본과 동일하게 유지
optimizer = dict(type='SGD', lr=0.05, momentum=0.9, weight_decay=0.0005, nesterov=True)
optimizer_config = dict(grad_clip=None)
lr_config = dict(policy='CosineAnnealing', min_lr=0, by_epoch=False)
total_epochs = 5
checkpoint_config = dict(interval=1)
evaluation = dict(interval=1, metrics=['top_k_accuracy'])
log_config = dict(interval=100, hooks=[dict(type='TextLoggerHook')])
