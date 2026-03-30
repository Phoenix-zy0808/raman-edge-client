"""
数据库模块测试

测试 SQLite 数据库的保存、加载、搜索、导出功能
"""
import numpy as np
import pytest
from pathlib import Path
import tempfile
import os

from backend.database import SpectrumDatabase


class TestSpectrumDatabase:
    """光谱数据库测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = SpectrumDatabase(db_path)
        yield db
        
        # 清理临时文件
        os.unlink(db_path)

    def test_init_creates_tables(self, temp_db):
        """测试初始化时创建表结构"""
        # 验证数据库文件存在
        assert Path(temp_db.db_path).exists()
        
        # 验证可以获取统计信息（说明表结构正确）
        stats = temp_db.get_statistics()
        assert 'total_spectra' in stats
        assert stats['total_spectra'] == 0
        
        print("✓ 数据库表结构创建测试通过")

    def test_save_and_load_spectrum(self, temp_db):
        """测试保存和加载光谱"""
        # 生成测试光谱
        wavelengths = np.linspace(200, 3200, 1024)
        intensities = np.random.rand(1024) * 1000
        
        # 保存
        spectrum_id = temp_db.save_spectrum(
            intensities=intensities,
            sample_name="测试样品",
            wavelengths=wavelengths,
            operator="测试员",
            metadata={"batch": "B001", "note": "测试数据"},
            tags=["测试", "拉曼"]
        )
        
        assert spectrum_id > 0
        
        # 加载
        loaded = temp_db.load_spectrum(spectrum_id)
        
        assert loaded is not None
        assert loaded['sample_name'] == "测试样品"
        assert loaded['operator'] == "测试员"
        assert loaded['n_points'] == 1024
        assert len(loaded['intensities']) == 1024
        assert len(loaded['wavelengths']) == 1024
        assert loaded['metadata']['batch'] == "B001"
        assert "测试" in loaded['tags']
        
        print(f"✓ 光谱保存和加载测试通过，ID={spectrum_id}")

    def test_save_spectrum_without_wavelengths(self, temp_db):
        """测试保存不带波长的光谱"""
        intensities = np.random.rand(512) * 1000
        
        spectrum_id = temp_db.save_spectrum(
            intensities=intensities,
            sample_name="无波长样品"
        )
        
        loaded = temp_db.load_spectrum(spectrum_id)
        assert loaded['wavelengths'] is None
        assert loaded['wavelength_start'] is None
        assert loaded['wavelength_end'] is None
        
        print("✓ 无波长光谱保存测试通过")

    def test_search_spectra(self, temp_db):
        """测试搜索光谱"""
        # 保存多个光谱
        for i in range(5):
            temp_db.save_spectrum(
                intensities=np.random.rand(100) * 1000,
                sample_name=f"样品_{i}",
                operator="测试员" if i % 2 == 0 else "管理员",
                tags=["测试"] if i < 3 else ["生产"]
            )
        
        # 按样品名搜索
        results = temp_db.search_spectra(sample_name="样品_2")
        assert len(results) == 1
        assert results[0]['sample_name'] == "样品_2"
        
        # 按操作者搜索
        results = temp_db.search_spectra(operator="测试员")
        assert len(results) == 3  # 0, 2, 4
        
        # 按标签搜索
        results = temp_db.search_spectra(tags=["测试"])
        assert len(results) == 3
        
        print("✓ 光谱搜索测试通过")

    def test_delete_spectrum(self, temp_db):
        """测试删除光谱"""
        spectrum_id = temp_db.save_spectrum(
            intensities=np.random.rand(100) * 1000,
            sample_name="待删除样品"
        )
        
        # 验证存在
        loaded = temp_db.load_spectrum(spectrum_id)
        assert loaded is not None
        
        # 删除
        success = temp_db.delete_spectrum(spectrum_id)
        assert success
        
        # 验证已删除
        loaded = temp_db.load_spectrum(spectrum_id)
        assert loaded is None
        
        # 删除不存在的 ID
        success = temp_db.delete_spectrum(99999)
        assert not success
        
        print("✓ 光谱删除测试通过")

    def test_export_spectra_csv(self, temp_db):
        """测试导出光谱为 CSV"""
        spectrum_id = temp_db.save_spectrum(
            intensities=np.array([1.0, 2.0, 3.0, 4.0]),
            sample_name="导出测试",
            wavelengths=np.array([200.0, 300.0, 400.0, 500.0])
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            count = temp_db.export_spectra([spectrum_id], tmpdir, format='csv')
            assert count == 1
            
            # 验证文件存在
            files = list(Path(tmpdir).glob("*.csv"))
            assert len(files) == 1
            
            # 验证文件内容
            content = files[0].read_text(encoding='utf-8')
            assert "导出测试" in content
            assert "200.0" in content
        
        print("✓ CSV 导出测试通过")

    def test_export_spectra_json(self, temp_db):
        """测试导出光谱为 JSON"""
        spectrum_id = temp_db.save_spectrum(
            intensities=np.array([1.0, 2.0, 3.0]),
            sample_name="JSON 导出测试"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            count = temp_db.export_spectra([spectrum_id], tmpdir, format='json')
            assert count == 1
            
            files = list(Path(tmpdir).glob("*.json"))
            assert len(files) == 1
        
        print("✓ JSON 导出测试通过")

    def test_log_calibration(self, temp_db):
        """测试记录校准日志"""
        log_id = temp_db.log_calibration(
            calibration_type="wavelength",
            status="success",
            result_data={"correction": 0.5, "r_squared": 0.99},
            operator="测试员"
        )
        
        assert log_id > 0
        
        # 获取校准历史
        history = temp_db.get_calibration_history(calibration_type="wavelength")
        assert len(history) > 0
        assert history[0]['status'] == "success"
        assert history[0]['result_data']['correction'] == 0.5
        
        print(f"✓ 校准日志记录测试通过，ID={log_id}")

    def test_get_statistics(self, temp_db):
        """测试获取数据库统计"""
        # 保存一些数据
        for i in range(3):
            temp_db.save_spectrum(
                intensities=np.random.rand(100),
                sample_name=f"样品_{i}"
            )
        
        # 记录校准
        temp_db.log_calibration("wavelength", "success")
        temp_db.log_calibration("intensity", "failed", error_message="测试错误")
        
        stats = temp_db.get_statistics()
        
        assert stats['total_spectra'] == 3
        assert stats['total_samples'] == 3
        assert stats['total_calibrations'] == 2
        assert stats['last_calibration'] is not None
        
        print("✓ 数据库统计测试通过")

    def test_save_empty_spectrum_fails(self, temp_db):
        """测试保存空光谱应该失败"""
        with pytest.raises(ValueError, match="光谱数据不能为空"):
            temp_db.save_spectrum(
                intensities=np.array([]),
                sample_name="空样品"
            )
        
        print("✓ 空光谱保存失败测试通过")
