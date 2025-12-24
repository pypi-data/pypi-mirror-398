"""
Zero-DCE++ Model Architecture
"""

import torch
import torch.nn as nn


class DCENet(nn.Module):
    """Deep Curve Estimation Network"""
    def __init__(self, num_iterations=8):
        super().__init__()
        self.num_iterations = num_iterations
        
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 32, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(32, 32, kernel_size=3, stride=1, padding=1)
        self.conv4 = nn.Conv2d(32, 32, kernel_size=3, stride=1, padding=1)
        self.conv5 = nn.Conv2d(64, 32, kernel_size=3, stride=1, padding=1)
        self.conv6 = nn.Conv2d(64, 32, kernel_size=3, stride=1, padding=1)
        self.conv7 = nn.Conv2d(64, 3 * num_iterations, kernel_size=3, stride=1, padding=1)
        self.relu = nn.ReLU(inplace=True)
        
    def forward(self, x):
        x1 = self.relu(self.conv1(x))
        x2 = self.relu(self.conv2(x1))
        x3 = self.relu(self.conv3(x2))
        x4 = self.relu(self.conv4(x3))
        x5 = self.relu(self.conv5(torch.cat([x4, x3], dim=1)))
        x6 = self.relu(self.conv6(torch.cat([x5, x2], dim=1)))
        curve_params = torch.tanh(self.conv7(torch.cat([x6, x1], dim=1)))
        return curve_params


class ZeroDCEPP(nn.Module):
    """Zero-DCE++ Model for Low-Light Image Enhancement"""
    def __init__(self, num_iterations=8):
        super().__init__()
        self.num_iterations = num_iterations
        self.dce_net = DCENet(num_iterations=num_iterations)
        
    def enhance(self, x, curve_params):
        """Apply curve adjustment iteratively"""
        enhanced = x
        for i in range(self.num_iterations):
            curve = curve_params[:, i*3:(i+1)*3, :, :]
            enhanced = enhanced - curve * (enhanced * (1 - enhanced))
            enhanced = torch.clamp(enhanced, 0, 1)
        return enhanced
    
    def forward(self, x):
        curve_params = self.dce_net(x)
        enhanced = self.enhance(x, curve_params)
        return enhanced, curve_params
