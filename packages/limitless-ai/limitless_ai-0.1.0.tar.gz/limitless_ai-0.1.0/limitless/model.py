import torch
import torch.nn as nn
import torchvision.models as models

class Limitless(nn.Module):
    def __init__(self, num_buttons, num_sticks=2):
        super(Limitless, self).__init__()
        # Use a more powerful backbone for a foundation model
        self.backbone = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        
        # Policy heads - now purely vision-based
        self.button_head = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(512, num_buttons)
        )
        
        self.stick_head = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(512, num_sticks * 2),
            nn.Tanh()
        )

    def forward(self, x):
        # Vision features
        vis_feat = self.backbone(x) # [B, 2048]
        
        buttons = self.button_head(vis_feat)
        sticks = self.stick_head(vis_feat)
        
        return buttons, sticks

if __name__ == "__main__":
    model = Limitless(num_buttons=14)
    dummy_input = torch.randn(2, 3, 224, 224)
    b, s = model(dummy_input)
    print(f"Buttons: {b.shape}, Sticks: {s.shape}")
