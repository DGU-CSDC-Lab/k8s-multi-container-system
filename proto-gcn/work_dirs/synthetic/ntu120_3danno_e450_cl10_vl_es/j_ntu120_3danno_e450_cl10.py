modality = 'j'
graph = 'nturgb+d'
work_dir = 'work_dirs/synthetic/ntu120_3danno_e450_cl10_vl_es'
model = dict(
    type='RecognizerGCN',
    backbone=dict(
        type='ProtoGCN',
        num_prototype=400,
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
        weight=0.2))
dataset_type = 'PoseDataset'
ann_file = 'data/per_camera/out/ntu120_3danno.pkl'
train_pipeline = [
    dict(type='PreNormalize3D', align_spine=False),
    dict(type='RandomRot', theta=0.2),
    dict(type='GenSkeFeat', feats=['j']),
    dict(type='UniformSampleDecode', clip_len=10),
    dict(type='FormatGCNInput'),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
val_pipeline = [
    dict(type='PreNormalize3D', align_spine=False),
    dict(type='GenSkeFeat', feats=['j']),
    dict(type='UniformSampleDecode', clip_len=10, num_clips=1),
    dict(type='FormatGCNInput'),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
test_pipeline = [
    dict(type='PreNormalize3D', align_spine=False),
    dict(type='GenSkeFeat', feats=['j']),
    dict(type='UniformSampleDecode', clip_len=10, num_clips=10),
    dict(type='FormatGCNInput'),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
data = dict(
    videos_per_gpu=16,
    workers_per_gpu=4,
    test_dataloader=dict(videos_per_gpu=1),
    train=dict(
        type='PoseDataset',
        ann_file='data/per_camera/out/ntu120_3danno.pkl',
        pipeline=[
            dict(type='PreNormalize3D', align_spine=False),
            dict(type='RandomRot', theta=0.2),
            dict(type='GenSkeFeat', feats=['j']),
            dict(type='UniformSampleDecode', clip_len=10),
            dict(type='FormatGCNInput'),
            dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
            dict(type='ToTensor', keys=['keypoint'])
        ],
        split='xsub_train'),
    val=dict(
        type='PoseDataset',
        ann_file='data/per_camera/out/ntu120_3danno.pkl',
        pipeline=[
            dict(type='PreNormalize3D', align_spine=False),
            dict(type='GenSkeFeat', feats=['j']),
            dict(type='UniformSampleDecode', clip_len=10, num_clips=1),
            dict(type='FormatGCNInput'),
            dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
            dict(type='ToTensor', keys=['keypoint'])
        ],
        split='xsub_val'),
    test=dict(
        type='PoseDataset',
        ann_file='data/per_camera/out/ntu120_3danno.pkl',
        pipeline=[
            dict(type='PreNormalize3D', align_spine=False),
            dict(type='GenSkeFeat', feats=['j']),
            dict(type='UniformSampleDecode', clip_len=10, num_clips=10),
            dict(type='FormatGCNInput'),
            dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
            dict(type='ToTensor', keys=['keypoint'])
        ],
        split='xsub_val'))
optimizer = dict(
    type='SGD', lr=0.025, momentum=0.9, weight_decay=0.0005, nesterov=True)
optimizer_config = dict(grad_clip=None)
lr_config = dict(policy='CosineAnnealing', min_lr=0, by_epoch=False)
total_epochs = 450
checkpoint_config = dict(interval=1)
evaluation = dict(interval=1, metrics=['top_k_accuracy'])
log_config = dict(interval=100, hooks=[dict(type='TextLoggerHook')])
dist_params = dict(backend='nccl')
gpu_ids = range(0, 1)
