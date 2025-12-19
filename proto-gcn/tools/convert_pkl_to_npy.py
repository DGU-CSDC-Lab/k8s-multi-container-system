import numpy as np
import pickle
import os

def convert_ntu_pkl(pkl_path, out_dir):
    print(f"🚀 Loading {pkl_path}...")
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
    
    annotations = data['annotations']
    # 목표 규격: 좌표(3), 최대프레임(300), 조인트(25), 인원(2)
    C_target, T_target, V_target, M_target = 3, 300, 25, 2

    if 'split' in data:
        train_identifiers = set(data['split']['xsub_train'])
    else:
        train_subjects = {1, 2, 4, 5, 8, 9, 13, 14, 15, 16, 17, 18, 19, 25, 27, 28, 31, 34, 35, 38}

    for split_tag in ['train', 'val']:
        print(f"📦 Processing {split_tag} split...")
        
        split_data = []
        for ann in annotations:
            identifier = ann.get('frame_dir', ann.get('item_name', ''))
            is_train = False
            if 'split' in data:
                if identifier in train_identifiers: is_train = True
            else:
                try:
                    sub_id = int(identifier[identifier.find('P')+1:identifier.find('P')+4])
                    if sub_id in train_subjects: is_train = True
                except: continue
            
            if (split_tag == 'train' and is_train) or (split_tag == 'val' and not is_train):
                split_data.append(ann)

        num_samples = len(split_data)
        # 고정 크기 배열 생성 (float32)
        skeletons = np.zeros((num_samples, C_target, T_target, V_target, M_target), dtype=np.float32)
        labels = np.zeros(num_samples, dtype=np.int64)
        
        for i, ann in enumerate(split_data):
            kp = ann['keypoint'] # 원본 (M, T, V, C) 또는 (C, T, V, M)
            
            # [차원 교정 핵심] (M, T, V, C) -> (C, T, V, M)으로 변경
            # 사용자님의 데이터가 (1, 103, 25, 3)이므로 3번째 축(C)을 앞으로 보냅니다.
            if kp.shape[-1] == 3: # 마지막 축이 좌표(XYZ)인 경우
                kp = kp.transpose(3, 1, 2, 0) # (C, T, V, M)으로 변환
            
            # 데이터 채우기 (최대 크기를 넘지 않도록 슬라이싱)
            c_orig, t_orig, v_orig, m_orig = kp.shape
            c_min = min(c_orig, C_target)
            t_min = min(t_orig, T_target)
            v_min = min(v_orig, V_target)
            m_min = min(m_orig, M_target)
            
            skeletons[i, :c_min, :t_min, :v_min, :m_min] = kp[:c_min, :t_min, :v_min, :m_min]
            labels[i] = ann['label']
        
        data_path = os.path.join(out_dir, f'ntu60_{split_tag}_data.npy')
        label_path = os.path.join(out_dir, f'ntu60_{split_tag}_label.npy')
        
        print(f"💾 Saving {num_samples} samples to {data_path}...")
        np.save(data_path, skeletons)
        np.save(label_path, labels)

if __name__ == '__main__':
    base_dir = 'data/nturgbd'
    convert_ntu_pkl(os.path.join(base_dir, 'ntu60_3danno.pkl'), base_dir)
    print("✨ All dimensions corrected and saved!")
