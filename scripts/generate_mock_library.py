"""
生成模拟拉曼光谱库脚本

使用高斯峰生成 10 种标准物质的模拟谱图
用于测试和演示，后续可替换为真实数据
"""
import numpy as np
import json
from pathlib import Path


def generate_gaussian_spectrum(peaks, wavelength_range=(200, 3200), num_points=1024):
    """
    生成高斯模拟谱图

    Args:
        peaks: [(position, intensity, width), ...]
               position: 峰位置 (cm⁻¹)
               intensity: 峰强度 (0-1)
               width: 峰宽度 (cm⁻¹)
        wavelength_range: (min, max) cm⁻¹
        num_points: 点数

    Returns:
        (wavelength, spectrum) 元组
    """
    wavelength = np.linspace(wavelength_range[0], wavelength_range[1], num_points)
    spectrum = np.ones(num_points) * 0.01  # 基线

    for pos, intensity, width in peaks:
        spectrum += intensity * np.exp(-(wavelength - pos)**2 / (2 * width**2))

    # 归一化到 0-1
    spectrum = spectrum / np.max(spectrum)

    return wavelength.tolist(), spectrum.tolist()


# 10 种标准物质（基于真实拉曼光谱特征）
LIBRARY = {
    'silicon': {
        'name': '硅 (Silicon)',
        'cas': '7440-21-3',
        'description': '单晶硅标准物质，特征峰 520 cm⁻¹，用于仪器校准',
        'peaks': [(520, 1.0, 8)]
    },
    'diamond': {
        'name': '金刚石 (Diamond)',
        'cas': '7782-40-3',
        'description': '金刚石标准物质，特征峰 1332 cm⁻¹',
        'peaks': [(1332, 1.0, 6)]
    },
    'graphite': {
        'name': '石墨 (Graphite)',
        'cas': '7782-42-5',
        'description': '石墨标准物质，特征峰 G 峰 1580 cm⁻¹、D 峰 1350 cm⁻¹、2D 峰 2700 cm⁻¹',
        'peaks': [(1350, 0.6, 25), (1580, 1.0, 20), (2700, 0.5, 35)]
    },
    'graphene': {
        'name': '石墨烯 (Graphene)',
        'cas': '7782-42-5',
        'description': '单层石墨烯，特征峰 G 峰 1580 cm⁻¹、2D 峰 2700 cm⁻¹（2D/G>2）',
        'peaks': [(1580, 0.7, 15), (2700, 1.0, 20)]
    },
    'carbon_nanotube': {
        'name': '碳纳米管 (CNT)',
        'cas': '308068-56-6',
        'description': '多壁碳纳米管，特征峰 RBM 峰 150-300 cm⁻¹、D 峰、G 峰',
        'peaks': [(180, 0.4, 20), (1350, 0.5, 25), (1580, 1.0, 18), (2700, 0.4, 30)]
    },
    'benzene': {
        'name': '苯 (Benzene)',
        'cas': '71-43-2',
        'description': '苯标准物质，特征峰 992 cm⁻¹（环呼吸振动）',
        'peaks': [(992, 1.0, 10), (1030, 0.3, 12), (1600, 0.4, 15)]
    },
    'zno': {
        'name': '氧化锌 (ZnO)',
        'cas': '1314-13-2',
        'description': '氧化锌半导体，特征峰 437 cm⁻¹（E2 模）',
        'peaks': [(330, 0.3, 15), (437, 1.0, 12), (580, 0.4, 20)]
    },
    'tio2': {
        'name': '二氧化钛 (TiO2, 锐钛矿)',
        'cas': '13463-67-7',
        'description': '锐钛矿型 TiO2，特征峰 144、399、513、639 cm⁻¹',
        'peaks': [(144, 1.0, 15), (197, 0.4, 12), (399, 0.7, 18), (513, 0.3, 15), (639, 0.5, 20)]
    },
    'al2o3': {
        'name': '氧化铝 (Al₂O₃, 蓝宝石)',
        'cas': '1344-28-1',
        'description': 'α-氧化铝（蓝宝石），特征峰 418、432、578、751 cm⁻¹',
        'peaks': [(380, 0.3, 15), (418, 0.7, 12), (432, 1.0, 10), (578, 0.5, 18), (751, 0.4, 15)]
    },
    'caco3': {
        'name': '碳酸钙 (CaCO₃, 方解石)',
        'cas': '471-34-1',
        'description': '方解石型碳酸钙，特征峰 1086 cm⁻¹（CO₃²⁻对称伸缩）',
        'peaks': [(150, 0.2, 15), (262, 0.3, 12), (712, 0.4, 15), (1086, 1.0, 18), (1436, 0.3, 20)]
    }
}


def main():
    """生成谱库 JSON 文件"""
    # 创建目录
    library_dir = Path('backend/library')
    library_dir.mkdir(exist_ok=True)

    # 生成每个物质的 JSON 文件
    for key, data in LIBRARY.items():
        wavelength, spectrum = generate_gaussian_spectrum(data['peaks'])

        json_data = {
            'id': key,
            'name': data['name'],
            'cas': data['cas'],
            'description': data['description'],
            'peaks': [
                {'position': p[0], 'intensity': p[1], 'width': p[2]}
                for p in data['peaks']
            ],
            'wavelength': wavelength,
            'spectrum': spectrum,
            'metadata': {
                'wavelength_range': [200, 3200],
                'num_points': 1024,
                'unit': 'cm⁻¹',
                'generated_by': 'generate_mock_library.py'
            }
        }

        output_path = library_dir / f'{key}.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f'✓ 生成：{output_path}')

    # 生成索引文件
    index_data = {
        'version': '1.0.0',
        'description': '拉曼光谱标准谱库（模拟数据）',
        'count': len(LIBRARY),
        'substances': [
            {'id': key, 'name': data['name'], 'cas': data['cas']}
            for key, data in LIBRARY.items()
        ]
    }

    index_path = library_dir / 'index.json'
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f'✓ 生成索引：{index_path}')
    print(f'\n共生成 {len(LIBRARY)} 种标准物质谱图')


if __name__ == '__main__':
    main()
