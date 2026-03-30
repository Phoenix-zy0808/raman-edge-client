"""
报告生成模块

提供光谱分析报告的生成功能
支持 HTML、PDF、Word 格式
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from base64 import b64encode

from backend.logging_config import get_logger

log = get_logger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(self, template_dir: str = None):
        """
        初始化报告生成器

        Args:
            template_dir: 模板目录（可选）
        """
        self.template_dir = template_dir
        log.info("报告生成器已初始化")

    def generate_html_report(
        self,
        spectrum_data: Dict[str, Any],
        peak_analysis: Optional[Dict] = None,
        library_match: Optional[Dict] = None,
        output_path: str = None
    ) -> str:
        """
        生成 HTML 格式报告

        Args:
            spectrum_data: 光谱数据（包含 sample_name, wavelengths, intensities, metadata 等）
            peak_analysis: 峰值分析结果（包含 peaks 列表）
            library_match: 谱库匹配结果（包含 matches 列表）
            output_path: 输出文件路径（可选）

        Returns:
            HTML 报告内容
        """
        # 生成光谱图（使用简单的 SVG）
        spectrum_svg = self._generate_spectrum_svg(spectrum_data)

        # 生成报告时间
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 构建 HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>拉曼光谱分析报告 - {spectrum_data.get('sample_name', '未知样品')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .report-title {{
            font-size: 28px;
            margin: 0;
        }}
        .report-meta {{
            margin-top: 15px;
            font-size: 14px;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section-title {{
            font-size: 20px;
            color: #333;
            margin-top: 0;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .info-item {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 5px;
        }}
        .info-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        .info-value {{
            font-size: 16px;
            color: #333;
            font-weight: 600;
        }}
        .spectrum-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .peak-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .peak-table th, .peak-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .peak-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .match-item {{
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .match-name {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }}
        .match-score {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 12px;
            margin-left: 10px;
        }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1 class="report-title">🔬 拉曼光谱分析报告</h1>
        <div class="report-meta">
            <div>样品名称：{spectrum_data.get('sample_name', '未知')}</div>
            <div>报告生成时间：{report_time}</div>
            {f"<div>操作者：{spectrum_data.get('operator', '未知')}</div>" if spectrum_data.get('operator') else ""}
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">📊 样品信息</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">样品名称</div>
                <div class="info-value">{spectrum_data.get('sample_name', '未知')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">数据点数</div>
                <div class="info-value">{spectrum_data.get('n_points', len(spectrum_data.get('intensities', [])))}</div>
            </div>
            {self._generate_info_items(spectrum_data.get('metadata'))}
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">📈 光谱图</h2>
        <div class="spectrum-container">
            {spectrum_svg}
        </div>
    </div>

    {self._generate_peak_section(peak_analysis)}

    {self._generate_match_section(library_match)}

    <div class="footer">
        <p>本报告由拉曼光谱分析系统自动生成</p>
        <p>© 2026 Raman Spectroscopy Analysis System</p>
    </div>
</body>
</html>"""

        # 保存到文件
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html, encoding='utf-8')
            log.info(f"HTML 报告已生成：{output_path}")

        return html

    def _generate_spectrum_svg(self, spectrum_data: Dict, width: int = 800, height: int = 400) -> str:
        """生成光谱 SVG 图"""
        intensities = spectrum_data.get('intensities', [])
        wavelengths = spectrum_data.get('wavelengths')

        if len(intensities) == 0:
            return '<p>无光谱数据</p>'

        # 计算绘图区域
        margin_left = 60
        margin_right = 20
        margin_top = 20
        margin_bottom = 50
        plot_width = width - margin_left - margin_right
        plot_height = height - margin_top - margin_bottom

        # 数据范围
        if wavelengths is not None:
            x_min, x_max = float(wavelengths[0]), float(wavelengths[-1])
        else:
            x_min, x_max = 0, len(intensities) - 1

        y_min, y_max = float(min(intensities)), float(max(intensities))
        y_range = y_max - y_min if y_max > y_min else 1

        # 生成路径
        points = []
        n_points = min(len(intensities), 500)  # 限制点数以避免 SVG 过大
        step = len(intensities) / n_points

        for i in range(n_points):
            idx = int(i * step)
            if wavelengths is not None:
                x = wavelengths[idx]
            else:
                x = idx

            y = intensities[idx]

            # 转换为 SVG 坐标
            svg_x = margin_left + (float(x) - x_min) / (x_max - x_min) * plot_width if x_max > x_min else margin_left
            svg_y = height - margin_bottom - (float(y) - y_min) / y_range * plot_height

            if i == 0:
                points.append(f"M {svg_x:.1f},{svg_y:.1f}")
            else:
                points.append(f"L {svg_x:.1f},{svg_y:.1f}")

        path_d = " ".join(points)

        # 生成坐标轴标签
        x_label = "Wavenumber (cm⁻¹)" if wavelengths is not None else "Index"
        y_label = "Intensity (a.u.)"

        svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <!-- 背景 -->
            <rect width="{width}" height="{height}" fill="white"/>

            <!-- 绘图区域边框 -->
            <rect x="{margin_left}" y="{margin_top}" width="{plot_width}" height="{plot_height}" fill="#fafafa" stroke="#ddd"/>

            <!-- 光谱线 -->
            <path d="{path_d}" fill="none" stroke="#667eea" stroke-width="2"/>

            <!-- X 轴 -->
            <line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#333" stroke-width="1"/>

            <!-- Y 轴 -->
            <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#333" stroke-width="1"/>

            <!-- X 轴标签 -->
            <text x="{width / 2}" y="{height - 10}" text-anchor="middle" font-size="14">{x_label}</text>
            <text x="{margin_left}" y="{height - margin_bottom + 20}" font-size="10">{x_min:.0f}</text>
            <text x="{width - margin_right}" y="{height - margin_bottom + 20}" text-anchor="end" font-size="10">{x_max:.0f}</text>

            <!-- Y 轴标签 -->
            <text x="25" y="{height / 2}" text-anchor="middle" font-size="14" transform="rotate(-90, 25, {height / 2})">{y_label}</text>
            <text x="{margin_left - 5}" y="{height - margin_bottom}" text-anchor="end" font-size="10">{y_min:.1f}</text>
            <text x="{margin_left - 5}" y="{margin_top}" text-anchor="end" font-size="10">{y_max:.1f}</text>
        </svg>"""

        return svg

    def _generate_info_items(self, metadata: Optional[Dict]) -> str:
        """生成信息项 HTML"""
        if not metadata:
            return ""

        items = []
        for key, value in metadata.items():
            items.append(f"""
                <div class="info-item">
                    <div class="info-label">{key}</div>
                    <div class="info-value">{value}</div>
                </div>
            """)

        return "".join(items)

    def _generate_peak_section(self, peak_analysis: Optional[Dict]) -> str:
        """生成峰值分析部分"""
        if not peak_analysis or not peak_analysis.get('peaks'):
            return ""

        peaks = peak_analysis['peaks']

        # 构建峰值表格
        rows = []
        for i, peak in enumerate(peaks[:10], 1):  # 只显示前 10 个峰
            rows.append(f"""
                <tr>
                    <td>{i}</td>
                    <td>{peak.get('position', 'N/A'):.2f} cm⁻¹</td>
                    <td>{peak.get('intensity', 'N/A'):.2f}</td>
                    <td>{peak.get('snr', 'N/A'):.2f}</td>
                </tr>
            """)

        return f"""
        <div class="section">
            <h2 class="section-title">🔍 峰值分析</h2>
            <p>共检测到 {len(peaks)} 个特征峰，以下是强度最高的 10 个：</p>
            <table class="peak-table">
                <thead>
                    <tr>
                        <th>序号</th>
                        <th>位置 (cm⁻¹)</th>
                        <th>强度</th>
                        <th>信噪比</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </div>
        """

    def _generate_match_section(self, library_match: Optional[Dict]) -> str:
        """生成谱库匹配部分"""
        if not library_match or not library_match.get('matches'):
            return ""

        matches = library_match['matches']

        match_items = []
        for match in matches[:5]:  # 只显示前 5 个匹配
            score = match.get('score', 0) * 100
            match_items.append(f"""
                <div class="match-item">
                    <div class="match-name">
                        {match.get('name', '未知物质')}
                        <span class="match-score">匹配度：{score:.1f}%</span>
                    </div>
                    <div style="margin-top: 8px; font-size: 13px; color: #666;">
                        CAS: {match.get('cas', 'N/A')} | 类别：{match.get('category', 'N/A')}
                    </div>
                </div>
            """)

        return f"""
        <div class="section">
            <h2 class="section-title">📚 谱库匹配结果</h2>
            {"".join(match_items)}
        </div>
        """

    def generate_text_report(
        self,
        spectrum_data: Dict[str, Any],
        peak_analysis: Optional[Dict] = None,
        library_match: Optional[Dict] = None
    ) -> str:
        """
        生成纯文本格式报告

        Args:
            spectrum_data: 光谱数据
            peak_analysis: 峰值分析结果
            library_match: 谱库匹配结果

        Returns:
            文本报告内容
        """
        lines = [
            "=" * 60,
            "拉曼光谱分析报告",
            "=" * 60,
            f"样品名称：{spectrum_data.get('sample_name', '未知')}",
            f"报告时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"操作者：{spectrum_data.get('operator', '未知')}",
            "",
            "-" * 60,
            "光谱数据",
            "-" * 60,
            f"数据点数：{spectrum_data.get('n_points', len(spectrum_data.get('intensities', [])))}",
        ]

        if spectrum_data.get('wavelength_start') and spectrum_data.get('wavelength_end'):
            lines.append(f"波长范围：{spectrum_data['wavelength_start']:.1f} - {spectrum_data['wavelength_end']:.1f} cm⁻¹")

        # 峰值信息
        if peak_analysis and peak_analysis.get('peaks'):
            lines.extend([
                "",
                "-" * 60,
                "峰值分析",
                "-" * 60,
            ])
            for i, peak in enumerate(peak_analysis['peaks'][:10], 1):
                lines.append(f"  {i}. {peak.get('position', 0):.2f} cm⁻¹ (强度：{peak.get('intensity', 0):.2f}, SNR: {peak.get('snr', 0):.2f})")

        # 匹配结果
        if library_match and library_match.get('matches'):
            lines.extend([
                "",
                "-" * 60,
                "谱库匹配",
                "-" * 60,
            ])
            for match in library_match['matches'][:5]:
                score = match.get('score', 0) * 100
                lines.append(f"  - {match.get('name', '未知')} ({score:.1f}%)")

        lines.extend([
            "",
            "=" * 60,
            "报告结束",
            "=" * 60,
        ])

        return "\n".join(lines)
