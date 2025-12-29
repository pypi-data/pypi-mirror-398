import numpy as np

def notch_filter_50hz(data: np.ndarray, 
                     fs: float,
                     notch_width: float = 2.0,
                     max_harmonics: int = 5) -> np.ndarray:
    """
    多通道50Hz谐波陷波滤波器
    
    参数：
    data : 输入信号，形状为 [通道数, 采样点数] 的二维数组
    fs : 采样频率 (Hz)
    notch_width : 陷波带宽 (Hz)，默认2Hz
    max_harmonics : 最大谐波次数，默认处理前10次谐波
    
    返回：
    滤波后的信号，形状与输入相同
    """
    # 输入校验
    if data.ndim != 2:
        raise ValueError("输入必须为二维数组 [channels, samples]")
    if fs <= 0:
        raise ValueError("采样频率必须为正数")

    n_channels, n_samples = data.shape
    nyquist = fs / 2
    processed = np.empty_like(data)
    
    # 生成频率轴
    freqs = np.fft.fftfreq(n_samples, 1/fs)
    
    for ch in range(n_channels):
        # FFT变换
        fft_data = np.fft.fft(data[ch])
        
        # 生成陷波掩模
        mask = np.ones(n_samples, dtype=bool)
        
        # 计算需要消除的谐波
        for k in range(1, max_harmonics+1):
            target_freq = 50 * k
            
            # 超过奈奎斯特频率则停止
            if target_freq > nyquist:
                break
                
            # 生成陷波范围
            notch_range = (np.abs(freqs - target_freq) <= notch_width/2) | \
                          (np.abs(freqs + target_freq) <= notch_width/2)
            
            mask &= ~notch_range
        
        # 应用频域滤波
        filtered_fft = fft_data * mask
        
        # 逆变换并取实数部分
        processed[ch] = np.real(np.fft.ifft(filtered_fft))
    
    return processed