/**
 * 拉曼光谱边缘客户端 - 类型定义模块
 * @module types
 * 
 * P11 修复（第五轮）：与后端 error_handler.py 错误码完全对齐
 * 错误码定义必须与 backend/error_handler.py 中的 ErrorCode 保持一致
 */

// ==================== API 响应格式 ====================

/**
 * API 响应状态码
 * 与后端 backend/error_handler.py 中的 ErrorCode 完全一致
 * 
 * 错误码分类:
 * 0-99:    系统级错误
 * 100-199: 设备相关错误
 * 200-249: 数据采集错误
 * 250-279: 校准相关错误（波长、强度、自动曝光）
 * 300-349: 数据处理错误
 * 350-399: 谱图数据错误
 * 400-499: 文件操作错误
 * 500-599: 网络/通信错误
 */
export const ErrorCode = {
    // ==================== 系统级错误 (0-99) ====================
    SUCCESS: 0,
    UNKNOWN_ERROR: 0,  // 后端实际为 0，但 success=true 时表示成功
    INVALID_PARAMETER: 1,
    NOT_INITIALIZED: 2,
    OUT_OF_MEMORY: 3,
    UNSUPPORTED_OPERATION: 4,

    // ==================== 设备相关错误 (100-199) ====================
    DEVICE_NOT_FOUND: 100,
    DEVICE_INIT_FAILED: 101,
    DEVICE_CONNECTION_FAILED: 102,
    DEVICE_DISCONNECTED: 103,
    DEVICE_BUSY: 104,
    DEVICE_TIMEOUT: 105,
    DEVICE_STATE_ERROR: 106,

    // ==================== 数据采集错误 (200-249) ====================
    ACQUISITION_NOT_STARTED: 200,
    ACQUISITION_FAILED: 201,
    ACQUISITION_TIMEOUT: 202,
    SPECTRUM_READ_FAILED: 203,
    SPECTRUM_INVALID: 204,
    SPECTRUM_EMPTY: 205,

    // ==================== 校准相关错误 (250-279) ====================
    // 通用校准错误 (250-254)
    CALIBRATION_FAILED: 250,
    CALIBRATION_TIMEOUT: 251,
    REFERENCE_PEAK_NOT_FOUND: 252,
    CALIBRATION_DATA_INVALID: 253,

    // 波长校准错误 (255-259)
    WAVELENGTH_CALIBRATION_ERROR: 255,

    // 强度校准错误 (260-264)
    INTENSITY_CALIBRATION_ERROR: 260,
    INTENSITY_REFERENCE_INVALID: 261,

    // 自动曝光错误 (265-269)
    AUTO_EXPOSURE_TIMEOUT: 265,
    AUTO_EXPOSURE_FAILED: 266,

    // ==================== 数据处理错误 (300-349) ====================
    ALGORITHM_FAILED: 300,
    SMOOTHING_FAILED: 301,
    BASELINE_CORRECTION_FAILED: 302,
    PEAK_DETECTION_FAILED: 303,
    LIBRARY_MATCH_FAILED: 304,
    PEAK_AREA_CALCULATION_FAILED: 305,

    // ==================== 谱图数据错误 (350-399) ====================
    INVALID_SPECTRUM_FORMAT: 350,
    SPECTRUM_DIMENSION_MISMATCH: 351,
    SPECTRUM_WAVELENGTH_RANGE_ERROR: 352,

    // ==================== 文件操作错误 (400-499) ====================
    FILE_NOT_FOUND: 400,
    FILE_READ_FAILED: 401,
    FILE_WRITE_FAILED: 402,
    FILE_FORMAT_UNSUPPORTED: 403,
    FILE_PERMISSION_DENIED: 404,

    // ==================== 网络/通信错误 (500-599) ====================
    NETWORK_ERROR: 500,
    CONNECTION_TIMEOUT: 501,
    BRIDGE_ERROR: 502
};

/**
 * 错误码描述（用于日志和提示）
 */
export const ErrorCodeDescription = {
    [ErrorCode.SUCCESS]: "操作成功",
    [ErrorCode.UNKNOWN_ERROR]: "未知错误",
    [ErrorCode.INVALID_PARAMETER]: "参数无效",
    [ErrorCode.NOT_INITIALIZED]: "系统未初始化",
    [ErrorCode.DEVICE_NOT_FOUND]: "未找到设备",
    [ErrorCode.DEVICE_INIT_FAILED]: "设备初始化失败",
    [ErrorCode.DEVICE_CONNECTION_FAILED]: "设备连接失败",
    [ErrorCode.DEVICE_DISCONNECTED]: "设备已断开",
    [ErrorCode.DEVICE_BUSY]: "设备忙",
    [ErrorCode.DEVICE_TIMEOUT]: "设备响应超时",
    [ErrorCode.ACQUISITION_NOT_STARTED]: "采集未开始",
    [ErrorCode.ACQUISITION_FAILED]: "数据采集失败",
    [ErrorCode.ACQUISITION_TIMEOUT]: "采集超时",
    [ErrorCode.SPECTRUM_READ_FAILED]: "光谱读取失败",
    [ErrorCode.SPECTRUM_INVALID]: "光谱数据无效",
    [ErrorCode.SPECTRUM_EMPTY]: "光谱数据为空",
    [ErrorCode.CALIBRATION_FAILED]: "校准失败",
    [ErrorCode.CALIBRATION_TIMEOUT]: "校准超时",
    [ErrorCode.REFERENCE_PEAK_NOT_FOUND]: "未找到参考峰",
    [ErrorCode.CALIBRATION_DATA_INVALID]: "校准数据无效",
    [ErrorCode.WAVELENGTH_CALIBRATION_ERROR]: "波长校准错误",
    [ErrorCode.INTENSITY_CALIBRATION_ERROR]: "强度校准错误",
    [ErrorCode.INTENSITY_REFERENCE_INVALID]: "强度参考谱图无效",
    [ErrorCode.AUTO_EXPOSURE_TIMEOUT]: "自动曝光超时",
    [ErrorCode.AUTO_EXPOSURE_FAILED]: "自动曝光失败",
    [ErrorCode.ALGORITHM_FAILED]: "算法执行失败",
    [ErrorCode.SMOOTHING_FAILED]: "平滑滤波失败",
    [ErrorCode.BASELINE_CORRECTION_FAILED]: "基线校正失败",
    [ErrorCode.PEAK_DETECTION_FAILED]: "峰值检测失败",
    [ErrorCode.LIBRARY_MATCH_FAILED]: "谱库匹配失败",
    [ErrorCode.PEAK_AREA_CALCULATION_FAILED]: "峰面积计算失败",
    [ErrorCode.INVALID_SPECTRUM_FORMAT]: "光谱数据格式无效",
    [ErrorCode.SPECTRUM_DIMENSION_MISMATCH]: "光谱维度不匹配",
    [ErrorCode.SPECTRUM_WAVELENGTH_RANGE_ERROR]: "光谱波长范围错误",
    [ErrorCode.FILE_NOT_FOUND]: "文件不存在",
    [ErrorCode.FILE_READ_FAILED]: "文件读取失败",
    [ErrorCode.FILE_WRITE_FAILED]: "文件写入失败",
    [ErrorCode.FILE_FORMAT_UNSUPPORTED]: "不支持的文件格式",
    [ErrorCode.FILE_PERMISSION_DENIED]: "文件访问被拒绝",
    [ErrorCode.NETWORK_ERROR]: "网络错误",
    [ErrorCode.CONNECTION_TIMEOUT]: "连接超时",
    [ErrorCode.BRIDGE_ERROR]: "通信桥接错误"
};

/**
 * 可重试的错误码列表
 * 只包含暂时性错误，重试可能成功
 * 永久错误（如参数无效、数据格式错误等）不在此列
 */
export const RETRYABLE_ERROR_CODES = [
    // 设备相关（暂时性错误）
    ErrorCode.DEVICE_BUSY,
    ErrorCode.DEVICE_TIMEOUT,
    ErrorCode.DEVICE_CONNECTION_FAILED,
    ErrorCode.DEVICE_DISCONNECTED,

    // 采集相关（可能是暂时干扰）
    ErrorCode.ACQUISITION_TIMEOUT,
    ErrorCode.SPECTRUM_READ_FAILED,

    // 校准相关（超时类错误）
    ErrorCode.CALIBRATION_TIMEOUT,
    ErrorCode.AUTO_EXPOSURE_TIMEOUT,

    // 网络相关
    ErrorCode.NETWORK_ERROR,
    ErrorCode.CONNECTION_TIMEOUT
];

/**
 * API 响应对象
 * 
 * 与后端 backend/error_handler.py 中的 ApiResponse 类保持一致
 * 
 * @typedef {Object} ApiResponse
 * @property {boolean} success - 是否成功
 * @property {number|null} error_code - 错误码（成功时为 null）
 * @property {string} message - 响应消息
 * @property {Object|null} data - 响应数据，失败时为 null
 * @property {number} timestamp - 响应时间戳
 */

/**
 * 创建成功的 API 响应
 * @param {Object} data - 响应数据
 * @param {string} message - 响应消息
 * @returns {ApiResponse}
 */
export function createSuccessResponse(data, message = "操作成功") {
    return {
        success: true,
        error_code: null,
        message: message,
        data: data,
        timestamp: Date.now() / 1000
    };
}

/**
 * 创建失败的 API 响应
 * @param {number} code - 错误码
 * @param {string} message - 错误消息
 * @param {Object|null} data - 附加数据（可选）
 * @returns {ApiResponse}
 */
export function createErrorResponse(code, message, data = null) {
    return {
        success: false,
        error_code: code,
        message: message,
        data: data,
        timestamp: Date.now() / 1000
    };
}

/**
 * 检查 API 响应是否成功
 * @param {ApiResponse} response - API 响应
 * @returns {boolean}
 */
export function isResponseSuccess(response) {
    return response && response.success === true;
}

/**
 * 检查错误是否可重试
 * @param {number} errorCode - 错误码
 * @returns {boolean}
 */
export function isRetryableError(errorCode) {
    return RETRYABLE_ERROR_CODES.includes(errorCode);
}

/**
 * 解析 API 响应，失败时根据错误码判断是否可重试
 * @param {ApiResponse} response - API 响应
 * @returns {Object} 包含 { success, data, error, retryable }
 */
export function parseResponseData(response) {
    if (!isResponseSuccess(response)) {
        const errorCode = response.error_code || ErrorCode.UNKNOWN_ERROR;
        return {
            success: false,
            data: null,
            error: response.message || "操作失败",
            errorCode: errorCode,
            retryable: isRetryableError(errorCode)
        };
    }
    return {
        success: true,
        data: response.data,
        error: null,
        errorCode: null,
        retryable: false
    };
}

// ==================== 校准相关类型 ====================

/**
 * 波长校准结果
 * @typedef {Object} WavelengthCalibrationResult
 * @property {number} correction - 校正值 (cm⁻¹)
 * @property {number} r_squared - 拟合优度
 * @property {number[]} reference_peaks - 使用的参考峰位置
 * @property {string} calibrated_at - 校准时间
 */

/**
 * 强度校准结果
 * @typedef {Object} IntensityCalibrationResult
 * @property {number[]} correction_curve - 校正曲线
 * @property {number[]} wavelength_range - 波长范围 [min, max]
 * @property {string} calibrated_at - 校准时间
 */

/**
 * 自动曝光结果
 * @typedef {Object} AutoExposureResult
 * @property {number} final_integration_time - 最终积分时间 (ms)
 * @property {number} final_intensity - 最终强度
 * @property {number} iterations - 迭代次数
 * @property {boolean} converged - 是否收敛
 */

/**
 * 校准状态
 * @typedef {Object} CalibrationStatus
 * @property {Object} wavelength - 波长校准状态
 * @property {boolean} wavelength.calibrated - 是否已校准
 * @property {number} wavelength.correction - 校正值
 * @property {string} wavelength.calibrated_at - 校准时间
 * @property {Object} intensity - 强度校准状态
 * @property {boolean} intensity.calibrated - 是否已校准
 * @property {string} intensity.calibrated_at - 校准时间
 */

// ==================== 工具函数 ====================

/**
 * 将后端返回的 JSON 字符串解析为 ApiResponse 对象
 * @param {string} jsonString - JSON 字符串
 * @returns {ApiResponse}
 * @throws {Error} 如果解析失败
 */
export function parseApiResponse(jsonString) {
    try {
        const response = JSON.parse(jsonString);
        // 确保响应对象包含必需的字段
        if (response.success === undefined) {
            // 兼容旧格式：code=0 表示成功
            response.success = (response.code === 0 || response.error_code === 0);
        }
        // 统一 error_code 字段
        if (response.error_code === undefined && response.code !== undefined) {
            response.error_code = response.code;
        }
        return response;
    } catch (e) {
        throw new Error(`解析 API 响应失败：${e.message}`);
    }
}

/**
 * 将 ApiResponse 对象序列化为 JSON 字符串
 * @param {ApiResponse} response - API 响应
 * @returns {string} JSON 字符串
 */
export function serializeApiResponse(response) {
    return JSON.stringify(response);
}

/**
 * 获取错误码描述
 * @param {number} errorCode - 错误码
 * @returns {string} 错误描述
 */
export function getErrorDescription(errorCode) {
    return ErrorCodeDescription[errorCode] || `未知错误码：${errorCode}`;
}

// ==================== 导出到全局（用于调试） ====================

if (typeof window !== 'undefined') {
    window.ApiResponseTypes = {
        ErrorCode,
        ErrorCodeDescription,
        RETRYABLE_ERROR_CODES,
        createSuccessResponse,
        createErrorResponse,
        isResponseSuccess,
        isRetryableError,
        parseResponseData,
        parseApiResponse,
        getErrorDescription
    };
}
