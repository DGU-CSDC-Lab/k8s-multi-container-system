modality = 'bm'
graph = 'nturgb+d'
# 1. 작업 디렉토리 명칭 변경
work_dir = f'./work_dirs/ntu60_xsub/bm_parquet'

model = dict(
    type='RecognizerGCN',
    backbone=dict(
        type='ProtoGCN',
        num_prototype=50,
        tcn_ms_cfg=[(3, 1), (3, 2), (3, 3), (3, 4), ('max', 3), '1x1'],
        graph_cfg=dict(layout=graph, mode='random', num_filter=8, init_off=.04, init_std=.02)),
    cls_head=dict(type='SimpleHead', joint_cfg='nturgb+d', num_classes=60, in_channels=384, weight=0.3))

# 2. 데이터셋 타입 및 경로 수정
dataset_type = 'PoseDatasetParquet'  # Parquet 전용 클래스 명칭
ann_file = 'data/nturgbd/ntu60_3danno.parquet'  # 변환된 .parquet 파일 경로

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
    videos_per_gpu=16,
    # 3. workers_per_gpu 설정
    # Parquet는 효율적이라 2 정도까지는 올려도 되지만, 
    # 처음엔 안정성을 위해 0으로 테스트 후 차근차근 올려보세요.
    workers_per_gpu=2, 
    test_dataloader=dict(videos_per_gpu=1),
    train=dict(type=dataset_type, ann_file=ann_file, pipeline=train_pipeline, split='xsub_train'),
    val=dict(type=dataset_type, ann_file=ann_file, pipeline=val_pipeline, split='xsub_val'),
    test=dict(type=dataset_type, ann_file=ann_file, pipeline=test_pipeline, split='xsub_val'))

optimizer = dict(type='SGD', lr=0.05, momentum=0.9, weight_decay=0.0005, nesterov=True)
optimizer_config = dict(grad_clip=None)
lr_config = dict(policy='CosineAnnealing', min_lr=0, by_epoch=False)
total_epochs = 5
checkpoint_config = dict(interval=1)
evaluation = dict(interval=1, metrics=['top_k_accuracy'])
log_config = dict(interval=100, hooks=[dict(type='TextLoggerHook')])
