# 使用示例
from read_bdf import BDFEDFReader


def main():
    """主函数示例"""
    
    # 1. 创建读取器
    filepath = r"E:\project\qlsdk-project\C256RS_450025430001_251223182657.bdf"  # 或 "sample.edf"
    
    try:
        # 使用上下文管理器自动管理文件
        with BDFEDFReader(filepath) as reader:
            
            # 2. 获取文件信息
            file_info = reader.get_file_info()
            print("=== 文件信息 ===")
            for key, value in file_info.items():
                print(f"{key}: {value}")
            print()
            
            # 3. 获取通道信息
            channel_info = reader.get_channel_info()
            print("=== 通道信息 (前3个) ===")
            for i in range(min(3, len(channel_info))):
                info = channel_info[i]
                print(f"通道 {i} ({info['label']}):")
                print(f"  采样率: {info['sample_frequency']} Hz")
                print(f"  物理范围: [{info['physical_min']}, {info['physical_max']}] {info['physical_dimension']}")
                print(f"  数字范围: [{info['digital_min']}, {info['digital_max']}]")
                print(f"  增益: {info['gain']:.6f}, 偏移: {info['offset']:.6f}")
                print()
            
            # 4. 读取指定时间段的数据
            start_time = 20.0  # 10秒
            end_time = 30.0    # 12秒
            
            print(f"=== 读取 {start_time}s 到 {end_time}s 的数据 ===")
            
            # 读取所有通道的物理值
            data_physical = reader.read_data(
                start_time=start_time,
                end_time=end_time,
                output_type='digital',  # 或 'digital'/'physical'
                return_as_dataframe=True
            )
            
            # 5. 显示统计信息
            stats = reader.get_channel_statistics(data_physical)
            print("=== 统计信息 ===")
            for channel_idx, stat in stats.items():
                print(f"通道 {channel_idx} ({stat['label']}):")
                print(f"  样本数: {stat['count']}")
                print(f"  范围: [{stat['min']:.2f}, {stat['max']:.2f}]")
                print(f"  均值: {stat['mean']:.2f} ± {stat['std']:.2f}")
                print()
            
            # 6. 获取DataFrame
            if 'dataframe' in data_physical:
                df = data_physical['dataframe']
                print("=== DataFrame 前5行 ===")
                print(df.head())
                print()
                print("=== DataFrame 信息 ===")
                print(df.info())
            
            # 7. 导出为CSV
            reader.export_to_csv(data_physical, "output_data.csv")
            
            # 8. 读取特定通道
            print("\n=== 读取特定通道 ===")
            channel_indices = [0, 1, 2]  # 前3个通道
            data_channels = reader.read_data(
                start_time=15.0,
                end_time=16.0,
                channel_indices=channel_indices,
                output_type='digital'  # 数字值
            )
            
            for channel_idx, channel_data in data_channels['channels'].items():
                print(f"通道 {channel_idx} 前5个数字值: {channel_data['data'][:5]}")
            
            # 9. 通过标签获取通道
            try:
                eeg_channel_idx = reader.get_channel_by_label("EEG")
                print(f"\nEEG通道索引: {eeg_channel_idx}")
            except ValueError as e:
                print(f"未找到EEG通道: {e}")
            
            # 10. 读取标注
            annotations = reader.read_annotations()
            if annotations:
                print("\n=== 文件标注 ===")
                for i, annot in enumerate(annotations[:5]):  # 显示前5个
                    print(f"{i+1}. 时间: {annot['onset']:.2f}s, "
                          f"时长: {annot['duration']:.2f}s, "
                          f"描述: {annot['description']}")
            
            # 11. 绘制图形
            try:
                reader.plot_segment(
                    data_dict=data_physical,
                    channel_indices=[0, 1, 2],
                    figsize=(12, 8),
                    save_path="plot.png"
                )
            except Exception as e:
                print(f"绘图失败: {e}")
    
    except FileNotFoundError:
        print(f"文件不存在: {filepath}")
    except Exception as e:
        print(f"处理文件时出错: {e}")

def batch_process_files(file_list, output_dir="output"):
    """
    批量处理多个文件
    """
    import os
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filepath in file_list:
        if not os.path.exists(filepath):
            print(f"文件不存在: {filepath}")
            continue
        
        print(f"\n处理文件: {filepath}")
        
        try:
            reader = BDFEDFReader(filepath)
            reader.open()
            
            # 获取文件名
            filename = os.path.basename(filepath)
            base_name = os.path.splitext(filename)[0]
            
            # 读取前30秒的数据
            data = reader.read_data(
                start_time=0,
                end_time=30,
                output_type='physical',
                return_as_dataframe=True
            )
            
            # 导出CSV
            csv_path = os.path.join(output_dir, f"{base_name}.csv")
            reader.export_to_csv(data, csv_path)
            
            # 导出统计信息
            stats = reader.get_channel_statistics(data)
            stats_path = os.path.join(output_dir, f"{base_name}_stats.json")
            
            import json
            with open(stats_path, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            
            print(f"  已保存: {csv_path}")
            print(f"  已保存: {stats_path}")
            
            reader.close()
            
        except Exception as e:
            print(f"  处理失败: {e}")

# 命令行接口
if __name__ == "__main__":
    main()
    # import argparse
    
    # parser = argparse.ArgumentParser(description='读取BDF/EDF文件并提取数据')
    # parser.add_argument('filepath', help='BDF/EDF文件路径')
    # parser.add_argument('--start', type=float, default=0, help='开始时间(秒)')
    # parser.add_argument('--end', type=float, default=10, help='结束时间(秒)')
    # parser.add_argument('--channels', type=str, default=1 help='通道索引(逗号分隔)')
    # parser.add_argument('--output-type', choices=['physical', 'digital'], default='physical',
    #                    help='输出类型: physical(物理值) 或 digital(数字值)')
    # parser.add_argument('--output', help='输出CSV文件路径')
    # parser.add_argument('--plot', action='store_true', help='绘制图表')
    
    # args = parser.parse_args()
    
    # # 解析通道参数
    # channel_indices = None
    # if args.channels:
    #     channel_indices = [int(c.strip()) for c in args.channels.split(',')]
    
    # # 处理文件
    # with BDFEDFReader(args.filepath) as reader:
    #     data = reader.read_data(
    #         start_time=args.start,
    #         end_time=args.end,
    #         channel_indices=channel_indices,
    #         output_type=args.output_type,
    #         return_as_dataframe=True
    #     )
        
    #     # 输出到控制台
    #     if 'dataframe' in data:
    #         print(f"读取了 {len(data['dataframe'])} 个样本")
    #         print("\n前10个样本:")
    #         print(data['dataframe'].head(10))
        
    #     # 导出到CSV
    #     if args.output:
    #         reader.export_to_csv(data, args.output)
    #         print(f"\n数据已导出到: {args.output}")
        
    #     # 绘制图表
    #     if args.plot:
    #         reader.plot_segment(data, channel_indices=channel_indices)