import os
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np
from tqdm import tqdm
from .model import Limitless

class GamepadDataset(Dataset):
    def __init__(self, dataset_paths):
        self.target_size = (224, 224)
        all_data = []
        if isinstance(dataset_paths, str):
            dataset_paths = [dataset_paths]
            
        for path in dataset_paths:
            csv_file = os.path.join(path, "labels.csv")
            img_dir = os.path.join(path, "frames")
            if not os.path.exists(csv_file): continue

            df = pd.read_csv(csv_file)
            df['full_img_path'] = df['frame'].apply(lambda x: os.path.join(img_dir, x))
            all_data.append(df)
            print(f"Loaded {len(df)} frames from {path}")

        combined_df = pd.concat(all_data, ignore_index=True)
        self.img_paths = combined_df['full_img_path'].tolist()
        self.btn_cols = [c for c in combined_df.columns if c.startswith('btn_')]
        self.stick_cols = [c for c in combined_df.columns if c.startswith('stick_')]
        
        self.buttons_data = combined_df[self.btn_cols].values.astype('float32')
        self.sticks_data = combined_df[self.stick_cols].values.astype('float32')
        print(f"Total Dataset: {len(self.img_paths)} frames.")

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img = cv2.imread(self.img_paths[idx])
        if img is None:
            img = np.zeros((self.target_size[1], self.target_size[0], 3), dtype=np.uint8)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, self.target_size, interpolation=cv2.INTER_LINEAR)
        
        img_tensor = torch.from_numpy(img.transpose(2, 0, 1))
        return img_tensor, torch.from_numpy(self.buttons_data[idx]), torch.from_numpy(self.sticks_data[idx])

def train(dataset_paths=["dataset"]):
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    device = torch.device("cuda")
    
    dataset = GamepadDataset(dataset_paths)
    train_loader = DataLoader(
        dataset, 
        batch_size=128, 
        shuffle=True, 
        num_workers=8, 
        pin_memory=True, 
        prefetch_factor=4,
        persistent_workers=True
    )

    model = Limitless(num_buttons=len(dataset.btn_cols), num_sticks=len(dataset.stick_cols)//2).to(device)
    model = model.to(memory_format=torch.channels_last)
    
    optimizer = optim.AdamW(model.parameters(), lr=0.0001, fused=True)
    scaler = torch.amp.GradScaler('cuda')
    scheduler = optim.lr_scheduler.OneCycleLR(optimizer, max_lr=0.001, steps_per_epoch=len(train_loader), epochs=20)

    mean = torch.tensor([0.485, 0.456, 0.406], device=device).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225], device=device).view(1, 3, 1, 1)

    print(f"Starting High-Performance Training on {device}...")

    for epoch in range(20):
        model.train()
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/20")
        
        for imgs, btns, stks in pbar:
            imgs = imgs.to(device, non_blocking=True).float().div_(255.0)
            imgs = (imgs - mean) / std
            imgs = imgs.to(memory_format=torch.channels_last)
            
            btns = btns.to(device, non_blocking=True)
            stks = stks.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast('cuda'):
                p_btn, p_stk = model(imgs)
                loss = nn.functional.binary_cross_entropy_with_logits(p_btn, btns) + \
                       nn.functional.mse_loss(p_stk, stks) * 10.0
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

        torch.save(model.state_dict(), "limitless_latest.pth")
        print(f"Epoch {epoch+1} saved.")

if __name__ == "__main__":
    train()

