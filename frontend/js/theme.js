/**
 * 拉曼光谱边缘客户端 - 主题定制模块
 * @module theme
 * 
 * P11 改进：支持主题色定制，超越简单的明暗切换
 * 
 * 功能:
 * - 预设主题（暗色、亮色、蓝色、绿色、紫色等）
 * - 自定义主题色
 * - 主题持久化
 * - 实时预览
 * 
 * 使用示例:
 * // 初始化主题管理器
 * const themeManager = initThemeManager();
 * 
 * // 切换预设主题
 * themeManager.setPresetTheme('blue');
 * 
 * // 自定义主题色
 * themeManager.setCustomColor('--accent-color', '#ff6b6b');
 * 
 * // 获取当前主题
 * const current = themeManager.getCurrentTheme();
 */

import { addLog } from './utils.js';

/**
 * 预设主题配置
 */
const PRESET_THEMES = {
  dark: {
    name: '暗色',
    colors: {
      '--bg-primary': '#1a1a2e',
      '--bg-secondary': '#16213e',
      '--bg-tertiary': '#0d0d1a',
      '--text-primary': '#eeeeee',
      '--text-secondary': '#aaaaaa',
      '--border-color': '#333333',
      '--accent-color': '#00d9ff'
    }
  },
  light: {
    name: '亮色',
    colors: {
      '--bg-primary': '#f5f5f5',
      '--bg-secondary': '#ffffff',
      '--bg-tertiary': '#e0e0e0',
      '--text-primary': '#333333',
      '--text-secondary': '#666666',
      '--border-color': '#dddddd',
      '--accent-color': '#0099cc'
    }
  },
  blue: {
    name: '蓝色',
    colors: {
      '--bg-primary': '#0a1628',
      '--bg-secondary': '#112240',
      '--bg-tertiary': '#1a3a5c',
      '--text-primary': '#e6f1ff',
      '--text-secondary': '#8892b0',
      '--border-color': '#233554',
      '--accent-color': '#64ffda'
    }
  },
  green: {
    name: '绿色',
    colors: {
      '--bg-primary': '#0f1a15',
      '--bg-secondary': '#1a2e22',
      '--bg-tertiary': '#2d4a3a',
      '--text-primary': '#e8f5e9',
      '--text-secondary': '#a5d6a7',
      '--border-color': '#2e7d32',
      '--accent-color': '#00e676'
    }
  },
  purple: {
    name: '紫色',
    colors: {
      '--bg-primary': '#1a0a2e',
      '--bg-secondary': '#2e1a4a',
      '--bg-tertiary': '#4a2a6a',
      '--text-primary': '#f3e5f5',
      '--text-secondary': '#ce93d8',
      '--border-color': '#7b1fa2',
      '--accent-color': '#e040fb'
    }
  },
  sunset: {
    name: '日落',
    colors: {
      '--bg-primary': '#2d132c',
      '--bg-secondary': '#4a1942',
      '--bg-tertiary': '#6b2c5a',
      '--text-primary': '#ffe5ec',
      '--text-secondary': '#ffb3c6',
      '--border-color': '#89466a',
      '--accent-color': '#ff6b6b'
    }
  },
  ocean: {
    name: '海洋',
    colors: {
      '--bg-primary': '#001a33',
      '--bg-secondary': '#003366',
      '--bg-tertiary': '#004d99',
      '--text-primary': '#e6f7ff',
      '--text-secondary': '#99d6ff',
      '--border-color': '#0066cc',
      '--accent-color': '#00bfff'
    }
  },
  forest: {
    name: '森林',
    colors: {
      '--bg-primary': '#0d1a0d',
      '--bg-secondary': '#1a331a',
      '--bg-tertiary': '#2d4a2d',
      '--text-primary': '#e8f5e9',
      '--text-secondary': '#c8e6c9',
      '--border-color': '#388e3c',
      '--accent-color': '#66bb6a'
    }
  }
};

/**
 * 主题存储键
 */
const THEME_STORAGE_KEY = 'raman_theme';

/**
 * 主题管理器类
 */
export class ThemeManager {
  constructor() {
    this.currentTheme = 'dark';
    this.customColors = {};
    this.listeners = [];
    
    // 加载保存的主题
    this._loadSavedTheme();
  }

  /**
   * 加载保存的主题
   */
  _loadSavedTheme() {
    try {
      const saved = localStorage.getItem(THEME_STORAGE_KEY);
      if (saved) {
        const { theme, customColors } = JSON.parse(saved);
        this.currentTheme = theme || 'dark';
        this.customColors = customColors || {};
        this._applyTheme();
      } else {
        this._applyTheme();
      }
    } catch (error) {
      console.warn('[Theme] 加载主题失败:', error);
      this._applyTheme();
    }
  }

  /**
   * 保存主题
   */
  _saveTheme() {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify({
        theme: this.currentTheme,
        customColors: this.customColors
      }));
    } catch (error) {
      console.warn('[Theme] 保存主题失败:', error);
    }
  }

  /**
   * 应用主题
   */
  _applyTheme() {
    const root = document.documentElement;
    const theme = PRESET_THEMES[this.currentTheme];
    
    if (theme) {
      // 应用预设主题颜色
      Object.entries(theme.colors).forEach(([prop, value]) => {
        root.style.setProperty(prop, value);
      });
      
      // 应用自定义颜色覆盖
      Object.entries(this.customColors).forEach(([prop, value]) => {
        root.style.setProperty(prop, value);
      });
    }
    
    this._notifyListeners();
    addLog(`主题已切换为：${theme?.name || this.currentTheme}`, 'info');
  }

  /**
   * 添加主题变化监听器
   * @param {Function} listener - 监听函数
   * @returns {Function} 取消监听函数
   */
  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * 通知监听器
   */
  _notifyListeners() {
    const theme = this.getCurrentTheme();
    this.listeners.forEach(listener => {
      try {
        listener(theme);
      } catch (error) {
        console.error('[Theme] 监听器执行失败:', error);
      }
    });
  }

  /**
   * 设置预设主题
   * @param {string} themeKey - 主题键名
   */
  setPresetTheme(themeKey) {
    if (!PRESET_THEMES[themeKey]) {
      console.warn(`[Theme] 未知主题：${themeKey}`);
      return false;
    }
    
    this.currentTheme = themeKey;
    this.customColors = {}; // 清除自定义颜色
    this._applyTheme();
    this._saveTheme();
    return true;
  }

  /**
   * 设置自定义颜色
   * @param {string} property - CSS 属性名
   * @param {string} value - 颜色值
   */
  setCustomColor(property, value) {
    this.customColors[property] = value;
    this._applyTheme();
    this._saveTheme();
  }

  /**
   * 获取所有预设主题
   * @returns {Object} 预设主题对象
   */
  getPresetThemes() {
    return { ...PRESET_THEMES };
  }

  /**
   * 获取当前主题
   * @returns {Object} 当前主题信息
   */
  getCurrentTheme() {
    const preset = PRESET_THEMES[this.currentTheme];
    return {
      key: this.currentTheme,
      name: preset?.name || '自定义',
      colors: {
        ...preset?.colors,
        ...this.customColors
      },
      isCustom: Object.keys(this.customColors).length > 0
    };
  }

  /**
   * 重置为主题默认值
   */
  resetTheme() {
    this.customColors = {};
    this._applyTheme();
    this._saveTheme();
  }

  /**
   * 切换明暗主题
   * @returns {string} 新主题键名
   */
  toggleDarkLight() {
    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.setPresetTheme(newTheme);
    return newTheme;
  }

  /**
   * 获取主题色板（用于 UI 展示）
   * @returns {Array} 主题色板数组
   */
  getThemePalette() {
    return Object.entries(PRESET_THEMES).map(([key, theme]) => ({
      key,
      name: theme.name,
      primary: theme.colors['--bg-primary'],
      accent: theme.colors['--accent-color']
    }));
  }
}

/**
 * 初始化主题管理器
 * @returns {ThemeManager}
 */
export function initThemeManager() {
  return new ThemeManager();
}

/**
 * 获取主题管理器实例（单例模式）
 */
let themeManagerInstance = null;

export function getThemeManager() {
  if (!themeManagerInstance) {
    themeManagerInstance = new ThemeManager();
  }
  return themeManagerInstance;
}

/**
 * 创建主题选择器 UI
 * @param {string} containerSelector - 容器选择器
 * @param {ThemeManager} themeManager - 主题管理器实例
 * @returns {{destroy: Function}}
 */
export function createThemeSelector(containerSelector, themeManager) {
  const container = document.querySelector(containerSelector);
  if (!container) {
    console.warn('[Theme] 未找到容器:', containerSelector);
    return { destroy: () => {} };
  }

  const palette = themeManager.getThemePalette();
  const currentTheme = themeManager.getCurrentTheme().key;

  container.innerHTML = `
    <div class="theme-selector" role="group" aria-label="主题选择">
      ${palette.map(theme => `
        <button 
          class="theme-option ${theme.key === currentTheme ? 'active' : ''}"
          data-theme="${theme.key}"
          aria-label="选择${theme.name}主题"
          aria-pressed="${theme.key === currentTheme}"
          style="--theme-primary: ${theme.primary}; --theme-accent: ${theme.accent};"
        >
          <span class="theme-preview"></span>
          <span class="theme-name">${theme.name}</span>
        </button>
      `).join('')}
    </div>
  `;

  const handleClick = (e) => {
    const button = e.target.closest('.theme-option');
    if (button) {
      const themeKey = button.dataset.theme;
      themeManager.setPresetTheme(themeKey);
      
      // 更新 UI
      container.querySelectorAll('.theme-option').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === themeKey);
        btn.setAttribute('aria-pressed', btn.dataset.theme === themeKey);
      });
    }
  };

  container.addEventListener('click', handleClick);

  return {
    destroy() {
      container.removeEventListener('click', handleClick);
      container.innerHTML = '';
    }
  };
}

/**
 * P11 新增：创建焦点陷阱（Focus Trap）
 * 限制键盘导航在对话框内，符合 WCAG 2.1 AA 标准
 * 
 * @param {HTMLElement} container - 容器元素
 * @returns {{destroy: Function}} 销毁函数
 */
export function createFocusTrap(container) {
    if (!container) {
        console.warn('[FocusTrap] 容器元素不存在');
        return { destroy: () => {} };
    }

    const focusableElements = container.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) {
        console.warn('[FocusTrap] 容器内无可聚焦元素');
        return { destroy: () => {} };
    }

    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    /**
     * 处理 Tab 键按下事件
     */
    function handleKeydown(e) {
        if (e.key !== 'Tab') return;

        if (e.shiftKey) {
            // Shift + Tab：反向导航
            if (document.activeElement === firstFocusable) {
                e.preventDefault();
                lastFocusable.focus();
            }
        } else {
            // Tab：正向导航
            if (document.activeElement === lastFocusable) {
                e.preventDefault();
                firstFocusable.focus();
            }
        }
    }

    // 保存对容器的引用，用于销毁
    const trapContainer = container;

    // 添加事件监听器
    container.addEventListener('keydown', handleKeydown);

    // 自动聚焦到第一个可聚焦元素
    firstFocusable.focus();

    return {
        /**
         * 销毁焦点陷阱
         */
        destroy() {
            container.removeEventListener('keydown', handleKeydown);
        }
    };
}

// 导出预设主题配置
export { PRESET_THEMES };
