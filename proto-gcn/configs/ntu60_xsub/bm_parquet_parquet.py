modality = 'bm'
graph = 'nturgb+d'
work_dir = './work_dirs/ntu60_xsub/bm_parquet_parquet'
model = dict(
    type='RecognizerGCN',
    backbone=dict(
        type='ProtoGCN',
        num_prototype=50,
        tcn_ms_cfg=[(3, 1), (3, 2), (3, 3), (3, 4), ('max', 3), '1x1'],
        graph_cfg=dict(
            layout='nturgb+d',
            mode='random',
            num_filter=8,
            init_off=0.04,
            init_std=0.02)),
    cls_head=dict(
        type='SimpleHead',
        joint_cfg='nturgb+d',
        num_classes=60,
        in_channels=384,
        weight=0.3))
dataset_type = 'PoseDatasetParquet'
ann_file = 'data/nturgbd/ntu60_3danno.parquet'
train_pipeline = [
    dict(type='PreNormalize3D', align_spine=False),
    dict(type='RandomRot', theta=0.2),
    dict(type='Spatial_Flip', dataset='nturgb+d', p=0.5),
    dict(type='GenSkeFeat', feats=['bm']),
    dict(type='UniformSampleDecode', clip_len=100),
    dict(type='FormatGCNInput'),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
val_pipeline = [
    dict(type='PreNormalize3D', align_spine=False),
    dict(type='GenSkeFeat', feats=['bm']),
    dict(type='UniformSampleDecode', clip_len=100, num_clips=1),
    dict(type='FormatGCNInput'),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
test_pipeline = [
    dict(type='PreNormalize3D', align_spine=False),
    dict(type='GenSkeFeat', feats=['bm']),
    dict(type='UniformSampleDecode', clip_len=100, num_clips=10),
    dict(type='FormatGCNInput'),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
data = dict(
    videos_per_gpu=16,
    workers_per_gpu=2,
    test_dataloader=dict(videos_per_gpu=1),
    train=dict(
        type='PoseDatasetParquet',
        ann_file='data/nturgbd/ntu60_3danno.parquet',
        pipeline=[
            dict(type='PreNormalize3D', align_spine=False),
            dict(type='RandomRot', theta=0.2),
            dict(type='Spatial_Flip', dataset='nturgb+d', p=0.5),
            dict(type='GenSkeFeat', feats=['bm']),
            dict(type='UniformSampleDecode', clip_len=100),
            dict(type='FormatGCNInput'),
            dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
            dict(type='ToTensor', keys=['keypoint'])
        ],
        split='xsub_train'),
    val=dict(
        type='PoseDatasetParquet',
        ann_file='data/nturgbd/ntu60_3danno.parquet',
        pipeline=[
            dict(type='PreNormalize3D', align_spine=False),
            dict(type='GenSkeFeat', feats=['bm']),
            dict(type='UniformSampleDecode', clip_len=100, num_clips=1),
            dict(type='FormatGCNInput'),
            dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
            dict(type='ToTensor', keys=['keypoint'])
        ],
        split='xsub_val'),
    test=dict(
        type='PoseDatasetParquet',
        ann_file='data/nturgbd/ntu60_3danno.parquet',
        pipeline=[
            dict(type='PreNormalize3D', align_spine=False),
            dict(type='GenSkeFeat', feats=['bm']),
            dict(type='UniformSampleDecode', clip_len=100, num_clips=10),
            dict(type='FormatGCNInput'),
            dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
            dict(type='ToTensor', keys=['keypoint'])
        ],
        split='xsub_val'))
optimizer = dict(
    type='SGD', lr=0.05, momentum=0.9, weight_decay=0.0005, nesterov=True)
optimizer_config = dict(grad_clip=None)
lr_config = dict(policy='CosineAnnealing', min_lr=0, by_epoch=False)
total_epochs = 5
checkpoint_config = dict(interval=1)
evaluation = dict(interval=1, metrics=['top_k_accuracy'])
log_config = dict(interval=100, hooks=[dict(type='TextLoggerHook')])
