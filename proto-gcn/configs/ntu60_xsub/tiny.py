model = dict(
    type='RecognizerGCN',
    backbone=dict(
        type='STGCN',
        gcn_adaptive=True,
        gcn_with_res=True,
        tcn_type='mstcn',
        graph_cfg=dict(layout='nturgb+d', mode='spatial')),
    cls_head=dict(type='GCNHead', num_classes=60, in_channels=256))

dataset_type = 'PoseDataset'
ann_file = 'data/nturgbd/ntu60_3danno.pkl'
train_pipeline = [
    dict(type='PreNormalize3D'),
    dict(type='RandomScale', scale=0.1),
    dict(type='RandomRot'),
    dict(type='GenSkeFeat', dataset='nturgb+d', feats=['j']),
    dict(type='UniformSampleFrames', clip_len=100),
    dict(type='PoseDecode'),
    dict(type='FormatGCNInput', num_person=2),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
val_pipeline = [
    dict(type='PreNormalize3D'),
    dict(type='GenSkeFeat', dataset='nturgb+d', feats=['j']),
    dict(type='UniformSampleFrames', clip_len=100, num_clips=1, test_mode=True),
    dict(type='PoseDecode'),
    dict(type='FormatGCNInput', num_person=2),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]
test_pipeline = [
    dict(type='PreNormalize3D'),
    dict(type='GenSkeFeat', dataset='nturgb+d', feats=['j']),
    dict(type='UniformSampleFrames', clip_len=100, num_clips=10, test_mode=True),
    dict(type='PoseDecode'),
    dict(type='FormatGCNInput', num_person=2),
    dict(type='Collect', keys=['keypoint', 'label'], meta_keys=[]),
    dict(type='ToTensor', keys=['keypoint'])
]

data = dict(
    videos_per_gpu=1,  # 최소값
    workers_per_gpu=1,  # 최소값
    test_dataloader=dict(videos_per_gpu=1),
    train=dict(type=dataset_type, ann_file=ann_file, pipeline=train_pipeline, split='xsub_train'),
    val=dict(type=dataset_type, ann_file=ann_file, pipeline=val_pipeline, split='xsub_val'),
    test=dict(type=dataset_type, ann_file=ann_file, pipeline=test_pipeline, split='xsub_val'))

# optimizer
optimizer = dict(type='SGD', lr=0.1, momentum=0.9, weight_decay=0.0001, nesterov=True)
optimizer_config = dict(grad_clip=None)

# learning policy
lr_config = dict(policy='CosineAnnealing', by_epoch=False, min_lr=0)
total_epochs = 2  # 짧게 설정

checkpoint_config = dict(interval=1)
evaluation = dict(interval=1, metrics=['top_k_accuracy', 'mean_class_accuracy'], topk=(1, 5))
log_config = dict(interval=100, hooks=[dict(type='TextLoggerHook')])

# runtime settings
log_level = 'INFO'
work_dir = './work_dirs/tiny_test'
