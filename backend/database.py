"""
SQLite 数据库管理模块

提供光谱数据的持久化存储、查询、导出功能

功能:
- 保存/加载光谱数据
- 搜索光谱（按日期、样品、操作者等）
- 批量导出光谱数据
- 校准日志记录
"""
import sqlite3
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

from backend.logging_config import get_logger

log = get_logger(__name__)


@contextmanager
def get_connection(db_path: str):
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


class SpectrumDatabase:
    """光谱数据库管理类"""

    def __init__(self, db_path: str = "spectra.db"):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_tables()
        log.info(f"光谱数据库已初始化：{db_path}")

    def _init_tables(self):
        """创建数据库表"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # 光谱数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spectra (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_name TEXT NOT NULL,
                    operator TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    wavelength_start REAL,
                    wavelength_end REAL,
                    n_points INTEGER,
                    intensities BLOB NOT NULL,
                    wavelengths BLOB,
                    metadata TEXT,
                    tags TEXT
                )
            """)

            # 样品信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    type TEXT,
                    batch_number TEXT,
                    manufacturer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 校准日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calibration_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    calibration_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_data TEXT,
                    error_message TEXT,
                    operator TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_spectra_sample ON spectra(sample_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_spectra_created ON spectra(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_spectra_tags ON spectra(tags)
            """)

            log.info("数据库表结构已创建")

    def save_spectrum(
        self,
        intensities: np.ndarray,
        sample_name: str,
        wavelengths: Optional[np.ndarray] = None,
        operator: str = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        保存光谱数据到数据库

        Args:
            intensities: 强度数组
            sample_name: 样品名称
            wavelengths: 波长数组（可选）
            operator: 操作者
            metadata: 元数据（字典）
            tags: 标签列表

        Returns:
            光谱 ID
        """
        # 数据验证
        if len(intensities) == 0:
            raise ValueError("光谱数据不能为空")

        # 计算波长范围
        n_points = len(intensities)
        if wavelengths is not None:
            wavelength_start = float(wavelengths[0])
            wavelength_end = float(wavelengths[-1])
            wavelengths_blob = wavelengths.astype(np.float64).tobytes()
        else:
            wavelength_start = None
            wavelength_end = None
            wavelengths_blob = None

        # 序列化元数据和标签
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        tags_json = json.dumps(tags, ensure_ascii=False) if tags else None

        # 强度数据序列化
        intensities_blob = intensities.astype(np.float64).tobytes()

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO spectra (
                    sample_name, operator, wavelength_start, wavelength_end,
                    n_points, intensities, wavelengths, metadata, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sample_name, operator, wavelength_start, wavelength_end,
                n_points, intensities_blob, wavelengths_blob, metadata_json, tags_json
            ))
            spectrum_id = cursor.lastrowid

        log.info(f"光谱已保存：ID={spectrum_id}, sample={sample_name}, points={n_points}")
        return spectrum_id

    def load_spectrum(self, spectrum_id: int) -> Optional[Dict[str, Any]]:
        """
        加载光谱数据

        Args:
            spectrum_id: 光谱 ID

        Returns:
            光谱数据字典，包含 id, sample_name, intensities, wavelengths, metadata 等
            如果不存在则返回 None
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM spectra WHERE id = ?
            """, (spectrum_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            # 反序列化数据
            intensities = np.frombuffer(row['intensities'], dtype=np.float64)
            wavelengths = None
            if row['wavelengths']:
                wavelengths = np.frombuffer(row['wavelengths'], dtype=np.float64)
            metadata = json.loads(row['metadata']) if row['metadata'] else None
            tags = json.loads(row['tags']) if row['tags'] else None

            return {
                'id': row['id'],
                'sample_name': row['sample_name'],
                'operator': row['operator'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'wavelength_start': row['wavelength_start'],
                'wavelength_end': row['wavelength_end'],
                'n_points': row['n_points'],
                'intensities': intensities,
                'wavelengths': wavelengths,
                'metadata': metadata,
                'tags': tags
            }

    def search_spectra(
        self,
        sample_name: Optional[str] = None,
        operator: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        搜索光谱数据

        Args:
            sample_name: 样品名称（模糊匹配）
            operator: 操作者
            date_from: 起始日期 (YYYY-MM-DD)
            date_to: 结束日期 (YYYY-MM-DD)
            tags: 标签列表（匹配任意一个标签）
            limit: 最大返回数量

        Returns:
            光谱列表（不包含 intensities 和 wavelengths 大数据）
        """
        query = """
            SELECT id, sample_name, operator, created_at, updated_at,
                   wavelength_start, wavelength_end, n_points, metadata, tags
            FROM spectra WHERE 1=1
        """
        params = []

        if sample_name:
            query += " AND sample_name LIKE ?"
            params.append(f"%{sample_name}%")

        if operator:
            query += " AND operator = ?"
            params.append(operator)

        if date_from:
            query += " AND created_at >= ?"
            params.append(date_from)

        if date_to:
            query += " AND created_at <= ?"
            params.append(date_to)

        if tags:
            # 标签匹配（JSON 包含，匹配任意一个标签）
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f'%"{tag}"%')
            query += " AND (" + " OR ".join(tag_conditions) + ")"

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                metadata = json.loads(row['metadata']) if row['metadata'] else None
                tags_list = json.loads(row['tags']) if row['tags'] else None
                results.append({
                    'id': row['id'],
                    'sample_name': row['sample_name'],
                    'operator': row['operator'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'wavelength_start': row['wavelength_start'],
                    'wavelength_end': row['wavelength_end'],
                    'n_points': row['n_points'],
                    'metadata': metadata,
                    'tags': tags_list
                })

            return results

    def delete_spectrum(self, spectrum_id: int) -> bool:
        """
        删除光谱数据

        Args:
            spectrum_id: 光谱 ID

        Returns:
            是否删除成功
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM spectra WHERE id = ?", (spectrum_id,))
            deleted = cursor.rowcount > 0

        if deleted:
            log.info(f"光谱已删除：ID={spectrum_id}")
        else:
            log.warning(f"光谱不存在：ID={spectrum_id}")

        return deleted

    def export_spectra(
        self,
        spectrum_ids: List[int],
        output_dir: str,
        format: str = 'csv'
    ) -> int:
        """
        批量导出光谱数据

        Args:
            spectrum_ids: 光谱 ID 列表
            output_dir: 输出目录
            format: 导出格式 ('csv' 或 'json')

        Returns:
            成功导出的文件数量
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_count = 0

        for spectrum_id in spectrum_ids:
            spectrum = self.load_spectrum(spectrum_id)
            if spectrum is None:
                log.warning(f"光谱不存在，跳过：ID={spectrum_id}")
                continue

            # 生成文件名
            safe_name = spectrum['sample_name'].replace('/', '_').replace('\\', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"{safe_name}_{spectrum['id']}_{timestamp}"

            if format == 'csv':
                filename = output_path / f"{base_filename}.csv"
                self._export_to_csv(spectrum, filename)
                exported_count += 1
            elif format == 'json':
                filename = output_path / f"{base_filename}.json"
                self._export_to_json(spectrum, filename)
                exported_count += 1
            else:
                log.error(f"不支持的导出格式：{format}")

        log.info(f"成功导出 {exported_count} 个光谱文件到 {output_dir}")
        return exported_count

    def _export_to_csv(self, spectrum: Dict, filename: Path):
        """导出为 CSV 格式"""
        import csv

        intensities = spectrum['intensities']
        wavelengths = spectrum.get('wavelengths')

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写入元数据注释
            writer.writerow(['# Sample:', spectrum['sample_name']])
            writer.writerow(['# Created:', spectrum['created_at']])
            if wavelengths is not None:
                writer.writerow(['# Columns:', 'Wavelength', 'Intensity'])
                for w, i in zip(wavelengths, intensities):
                    writer.writerow([w, i])
            else:
                writer.writerow(['# Columns:', 'Index', 'Intensity'])
                for idx, i in enumerate(intensities):
                    writer.writerow([idx, i])

    def _export_to_json(self, spectrum: Dict, filename: Path):
        """导出为 JSON 格式"""
        # 将 numpy 数组转换为列表
        export_data = spectrum.copy()
        export_data['intensities'] = spectrum['intensities'].tolist()
        if spectrum.get('wavelengths') is not None:
            export_data['wavelengths'] = spectrum['wavelengths'].tolist()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def log_calibration(
        self,
        calibration_type: str,
        status: str,
        result_data: Optional[Dict] = None,
        error_message: Optional[str] = None,
        operator: Optional[str] = None
    ) -> int:
        """
        记录校准日志

        Args:
            calibration_type: 校准类型 ('wavelength', 'intensity', 'dark_noise')
            status: 状态 ('success', 'failed')
            result_data: 校准结果数据
            error_message: 错误信息
            operator: 操作者

        Returns:
            日志 ID
        """
        result_json = json.dumps(result_data) if result_data else None

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO calibration_logs (
                    calibration_type, status, result_data, error_message, operator
                ) VALUES (?, ?, ?, ?, ?)
            """, (calibration_type, status, result_json, error_message, operator))
            log_id = cursor.lastrowid

        log.info(f"校准日志已记录：ID={log_id}, type={calibration_type}, status={status}")
        return log_id

    def get_calibration_history(
        self,
        calibration_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取校准历史

        Args:
            calibration_type: 校准类型（可选）
            limit: 最大返回数量

        Returns:
            校准日志列表
        """
        query = "SELECT * FROM calibration_logs WHERE 1=1"
        params = []

        if calibration_type:
            query += " AND calibration_type = ?"
            params.append(calibration_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                result_data = json.loads(row['result_data']) if row['result_data'] else None
                results.append({
                    'id': row['id'],
                    'calibration_type': row['calibration_type'],
                    'status': row['status'],
                    'result_data': result_data,
                    'error_message': row['error_message'],
                    'operator': row['operator'],
                    'created_at': row['created_at']
                })

            return results

    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # 总光谱数
            cursor.execute("SELECT COUNT(*) FROM spectra")
            total_spectra = cursor.fetchone()[0]

            # 总样品数
            cursor.execute("SELECT COUNT(DISTINCT sample_name) FROM spectra")
            total_samples = cursor.fetchone()[0]

            # 校准日志总数
            cursor.execute("SELECT COUNT(*) FROM calibration_logs")
            total_calibrations = cursor.fetchone()[0]

            # 最近校准
            cursor.execute("""
                SELECT calibration_type, status, created_at
                FROM calibration_logs
                ORDER BY created_at DESC LIMIT 1
            """)
            row = cursor.fetchone()
            last_calibration = {
                'type': row['calibration_type'],
                'status': row['status'],
                'time': row['created_at']
            } if row else None

            return {
                'total_spectra': total_spectra,
                'total_samples': total_samples,
                'total_calibrations': total_calibrations,
                'last_calibration': last_calibration
            }
