import argparse
from .extractor import UniversalInputExtractor
import os

def main():
    parser = argparse.ArgumentParser(description="Limitless: Universal AI Game Agent")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract actions from videos")
    extract_parser.add_argument("--input", type=str, required=True, help="Path to video or directory")
    extract_parser.add_argument("--templates", type=str, default=None, help="Path to templates (defaults to package templates)")
    extract_parser.add_argument("--output", type=str, default="dataset", help="Output directory")
    extract_parser.add_argument("--rate", type=int, default=1, help="Sample rate")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train the Limitless model")
    train_parser.add_argument("--dataset", type=str, action="append", required=True, help="Dataset directory (can be used multiple times)")
    
    # Run command (Simulator)
    run_parser = subparsers.add_parser("run", help="Run the agent in a game")
    run_parser.add_argument("--window", type=str, required=True, help="Game window title")
    run_parser.add_argument("--model", type=str, required=True, help="Path to model checkpoint")

    # Test Video command
    test_video_parser = subparsers.add_parser("test-video", help="Test the model on a video file")
    test_video_parser.add_argument("--video", type=str, required=True, help="Path to video file")
    test_video_parser.add_argument("--model", type=str, required=True, help="Path to model checkpoint")

    args = parser.parse_args()
    
    if args.command == "extract":
        extractor = UniversalInputExtractor(templates_dir=args.templates)
        if os.path.isdir(args.input):
            extractor.process_directory(args.input, args.output, sample_rate=args.rate)
        else:
            extractor.process_video(args.input, args.output, sample_rate=args.rate)
            
    elif args.command == "train":
        from .train import train
        train(dataset_paths=args.dataset)
        
    elif args.command == "run":
        from .simulator import UniversalGameEnv
        from .model import Limitless
        import torch
        from torchvision import transforms
        import numpy as np
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load checkpoint to determine model dimensions
        checkpoint = torch.load(args.model, map_location=device)
        # Handle both state_dict only and full checkpoint dicts
        state_dict = checkpoint if 'button_head.3.weight' in checkpoint else checkpoint.get('state_dict', checkpoint)
        
        num_buttons = state_dict['button_head.3.weight'].shape[0]
        num_sticks = state_dict['stick_head.3.weight'].shape[0] // 2
        
        print(f"Loading model with {num_buttons} buttons and {num_sticks} sticks...")
        model = Limitless(num_buttons=num_buttons, num_sticks=num_sticks).to(device)
        model.load_state_dict(state_dict)
        model.eval()
        
        env = UniversalGameEnv(window_title=args.window)
        obs, _ = env.reset()
        
        # Fast transform
        mean = torch.tensor([0.485, 0.456, 0.406], device=device).view(1, 3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225], device=device).view(1, 3, 1, 1)
        
        print(f"Running Limitless on {args.window}...")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                # Convert obs to tensor and normalize on GPU
                img_tensor = torch.from_numpy(obs.transpose(2, 0, 1)).to(device).float().div_(255.0)
                img_tensor = (img_tensor.unsqueeze(0) - mean) / std
                
                with torch.no_grad():
                    buttons, sticks = model(img_tensor)
                    buttons = torch.sigmoid(buttons).cpu().numpy()[0]
                    sticks = sticks.cpu().numpy()[0]
                
                # Convert model output to env action
                action = {
                    "buttons": buttons,
                    "sticks": sticks
                }
                
                obs, _, _, _, _ = env.step(action)
        except KeyboardInterrupt:
            print("Stopping agent...")
        finally:
            env.close()
            
    elif args.command == "test-video":
        import cv2
        import torch
        from .model import Limitless
        from torchvision import transforms
        import numpy as np
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load checkpoint to determine model dimensions
        checkpoint = torch.load(args.model, map_location=device)
        num_buttons = checkpoint['button_head.3.weight'].shape[0]
        num_sticks = checkpoint['stick_head.3.weight'].shape[0] // 2
        
        print(f"Loading model with {num_buttons} buttons and {num_sticks} sticks...")
        model = Limitless(num_buttons=num_buttons, num_sticks=num_sticks).to(device)
        model.load_state_dict(checkpoint)
        model.eval()
        
        cap = cv2.VideoCapture(args.video)
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        print(f"Testing Limitless on {args.video}...")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            # Prepare input
            input_tensor = transform(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).unsqueeze(0).to(device)
            
            with torch.no_grad():
                buttons, sticks = model(input_tensor)
                buttons = torch.sigmoid(buttons).cpu().numpy()[0]
                sticks = sticks.cpu().numpy()[0]
            
            # Visualize
            debug_frame = frame.copy()
            
            # Draw sticks
            # Left stick (sticks[0], sticks[1])
            ls_x, ls_y = int(100 + sticks[0] * 50), int(100 + sticks[1] * 50)
            cv2.circle(debug_frame, (100, 100), 50, (255, 255, 255), 1)
            cv2.circle(debug_frame, (ls_x, ls_y), 5, (0, 255, 0), -1)
            
            # Right stick (sticks[2], sticks[3])
            rs_x, rs_y = int(250 + sticks[2] * 50), int(250 + sticks[3] * 50)
            cv2.circle(debug_frame, (250, 250), 50, (255, 255, 255), 1)
            cv2.circle(debug_frame, (rs_x, rs_y), 5, (0, 0, 255), -1)
            
            # Draw buttons (first 10 for brevity)
            for i in range(min(10, len(buttons))):
                color = (0, 255, 0) if buttons[i] > 0.5 else (0, 0, 255)
                cv2.putText(debug_frame, f"B{i}: {buttons[i]:.2f}", (10, 200 + i*20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            cv2.imshow("Limitless Video Test (Press Q to exit)", debug_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
