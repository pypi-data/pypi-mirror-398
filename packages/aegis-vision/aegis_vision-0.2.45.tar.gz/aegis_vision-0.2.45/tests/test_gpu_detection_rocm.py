import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from aegis_vision.gpu_detection_rocm import ROCmGPUDetector

class TestROCmDetection(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_rocm_smi_detection(self, mock_run):
        """Test rocm-smi command parsing."""
        # Mock successful rocm-smi output
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "device, product name\n0, AMD Instinct MI300X\n"
        mock_run.return_value = mock_proc
        
        result = ROCmGPUDetector.detect_via_rocm_smi()
        
        self.assertTrue(result["detected"])
        self.assertEqual(len(result["gpus"]), 1)
        self.assertEqual(result["gpus"][0]["name"], "AMD Instinct MI300X")

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.device_count')
    @patch('torch.cuda.get_device_name')
    @patch('torch.cuda.get_device_properties')
    def test_pytorch_rocm_detection(self, mock_props, mock_name, mock_count, mock_available):
        """Test PyTorch ROCm backend detection."""
        # Mock PyTorch ROCm environment
        with patch('torch.version') as mock_version:
            mock_version.rocm = "7.0.0"
            mock_available.return_value = True
            mock_count.return_value = 1
            mock_name.return_value = "AMD Instinct MI300X"
            
            props = MagicMock()
            props.total_memory = 192 * 1024 * 1024 * 1024 # 192GB
            props.gcnArchName = "gfx942"
            mock_props.return_value = props
            
            result = ROCmGPUDetector.detect_via_pytorch()
            
            self.assertTrue(result["available"])
            self.assertEqual(result["version"], "7.0.0")
            self.assertEqual(len(result["devices"]), 1)
            self.assertEqual(result["devices"][0]["name"], "AMD Instinct MI300X")
            self.assertEqual(result["devices"][0]["arch"], "gfx942")

if __name__ == '__main__':
    unittest.main()
