"""
报告生成模块测试
"""
import numpy as np
import pytest
from pathlib import Path
import tempfile

from backend.report_generator import ReportGenerator


class TestReportGenerator:
    """报告生成器测试"""

    @pytest.fixture
    def report_generator(self):
        """创建报告生成器实例"""
        return ReportGenerator()

    @pytest.fixture
    def sample_spectrum_data(self):
        """生成示例光谱数据"""
        wavelengths = np.linspace(200, 3200, 1024)
        intensities = np.random.rand(1024) * 1000
        return {
            'sample_name': '测试样品',
            'operator': '测试员',
            'n_points': 1024,
            'wavelength_start': 200.0,
            'wavelength_end': 3200.0,
            'wavelengths': wavelengths,
            'intensities': intensities,
            'metadata': {
                'batch': 'B001',
                'date': '2026-03-25',
                'note': '测试数据'
            }
        }

    def test_generate_html_report_basic(self, report_generator, sample_spectrum_data):
        """测试生成基本 HTML 报告"""
        html = report_generator.generate_html_report(sample_spectrum_data)

        assert html is not None
        assert '<!DOCTYPE html>' in html
        assert '拉曼光谱分析报告' in html
        assert '测试样品' in html
        assert '测试员' in html
        assert '<svg' in html  # 包含光谱图

        print("✓ 基本 HTML 报告生成测试通过")

    def test_generate_html_report_with_peaks(self, report_generator, sample_spectrum_data):
        """测试生成带峰值分析的 HTML 报告"""
        peak_analysis = {
            'peaks': [
                {'position': 520.0, 'intensity': 800.0, 'snr': 25.5},
                {'position': 1580.0, 'intensity': 600.0, 'snr': 18.2},
                {'position': 2700.0, 'intensity': 400.0, 'snr': 12.8}
            ]
        }

        html = report_generator.generate_html_report(
            sample_spectrum_data,
            peak_analysis=peak_analysis
        )

        assert '峰值分析' in html
        assert '520.00 cm⁻¹' in html
        assert '1580.00 cm⁻¹' in html
        assert 'peak-table' in html

        print("✓ 带峰值分析的 HTML 报告生成测试通过")

    def test_generate_html_report_with_matches(self, report_generator, sample_spectrum_data):
        """测试生成带谱库匹配的 HTML 报告"""
        library_match = {
            'matches': [
                {'name': '硅 (Silicon)', 'score': 0.95, 'cas': '7440-21-3', 'category': '半导体'},
                {'name': '金刚石 (Diamond)', 'score': 0.82, 'cas': '7782-40-3', 'category': '碳材料'}
            ]
        }

        html = report_generator.generate_html_report(
            sample_spectrum_data,
            library_match=library_match
        )

        assert '谱库匹配' in html
        assert '硅 (Silicon)' in html
        assert '匹配度：95.0%' in html
        assert 'match-item' in html

        print("✓ 带谱库匹配的 HTML 报告生成测试通过")

    def test_generate_html_report_to_file(self, report_generator, sample_spectrum_data):
        """测试保存 HTML 报告到文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            
            html = report_generator.generate_html_report(
                sample_spectrum_data,
                output_path=str(output_path)
            )

            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            content = output_path.read_text(encoding='utf-8')
            assert '测试样品' in content

        print("✓ HTML 报告保存到文件测试通过")

    def test_generate_text_report_basic(self, report_generator, sample_spectrum_data):
        """测试生成基本文本报告"""
        text = report_generator.generate_text_report(sample_spectrum_data)

        assert text is not None
        assert '拉曼光谱分析报告' in text
        assert '测试样品' in text
        assert '测试员' in text
        assert '=' in text  # 分隔线

        print("✓ 基本文本报告生成测试通过")

    def test_generate_text_report_with_peaks(self, report_generator, sample_spectrum_data):
        """测试生成带峰值分析的文本报告"""
        peak_analysis = {
            'peaks': [
                {'position': 520.0, 'intensity': 800.0, 'snr': 25.5}
            ]
        }

        text = report_generator.generate_text_report(
            sample_spectrum_data,
            peak_analysis=peak_analysis
        )

        assert '峰值分析' in text
        assert '520.00 cm⁻¹' in text

        print("✓ 带峰值分析的文本报告生成测试通过")

    def test_generate_text_report_with_matches(self, report_generator, sample_spectrum_data):
        """测试生成带谱库匹配的文本报告"""
        library_match = {
            'matches': [
                {'name': '硅 (Silicon)', 'score': 0.95}
            ]
        }

        text = report_generator.generate_text_report(
            sample_spectrum_data,
            library_match=library_match
        )

        assert '谱库匹配' in text
        assert '硅 (Silicon)' in text

        print("✓ 带谱库匹配的文本报告生成测试通过")

    def test_generate_report_empty_peaks(self, report_generator, sample_spectrum_data):
        """测试空峰值列表的处理"""
        peak_analysis = {'peaks': []}
        
        html = report_generator.generate_html_report(
            sample_spectrum_data,
            peak_analysis=peak_analysis
        )
        
        # 不应该有峰值分析部分
        assert '峰值分析' not in html or '<tbody>' not in html
        
        print("✓ 空峰值列表处理测试通过")

    def test_generate_report_no_metadata(self, report_generator):
        """测试无元数据的报告生成"""
        spectrum_data = {
            'sample_name': '无元数据样品',
            'intensities': np.random.rand(100),
            'n_points': 100
        }

        html = report_generator.generate_html_report(spectrum_data)
        assert html is not None
        assert '无元数据样品' in html

        print("✓ 无元数据报告生成测试通过")
