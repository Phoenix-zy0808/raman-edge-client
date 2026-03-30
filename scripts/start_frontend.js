#!/usr/bin/env node
/**
 * 拉曼光谱边缘客户端 - 前端开发服务器
 * 
 * 功能:
 * - 启动 HTTP 服务器提供前端静态文件
 * - 支持热重载（文件变化自动刷新）
 * - 支持 CORS（用于前后端分离开发）
 * 
 * 使用方法:
 *    # 启动开发服务器（默认端口 8080）
 *    node scripts/start_frontend.js
 * 
 *    # 指定端口
 *    node scripts/start_frontend.js --port 3000
 * 
 *    # 生产模式（禁用热重载）
 *    node scripts/start_frontend.js --prod
 * 
 *    # 使用 npm
 *    npm run dev
 *    npm run dev -- --port 3000
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// 项目根目录
const ROOT_DIR = path.join(__dirname, '..');
const FRONTEND_DIR = path.join(ROOT_DIR, 'frontend');

// 默认配置
const DEFAULT_CONFIG = {
    port: 8080,
    host: 'localhost',
    prod: false,
    watch: true,
    open: false
};

// MIME 类型映射
const MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.eot': 'application/vnd.ms-fontobject'
};

/**
 * 解析命令行参数
 */
function parseArgs() {
    const args = process.argv.slice(2);
    const config = { ...DEFAULT_CONFIG };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];

        if (arg === '--port' || arg === '-p') {
            config.port = parseInt(args[++i], 10) || DEFAULT_CONFIG.port;
        } else if (arg === '--host' || arg === '-H') {
            config.host = args[++i] || DEFAULT_CONFIG.host;
        } else if (arg === '--prod') {
            config.prod = true;
            config.watch = false;
        } else if (arg === '--no-watch') {
            config.watch = false;
        } else if (arg === '--open' || arg === '-o') {
            config.open = true;
        } else if (arg === '--help' || arg === '-h') {
            printHelp();
            process.exit(0);
        }
    }

    return config;
}

/**
 * 打印帮助信息
 */
function printHelp() {
    console.log(`
🔬 拉曼光谱边缘客户端 - 前端开发服务器

使用方法:
    node scripts/start_frontend.js [选项]

选项:
    -p, --port <port>     端口号（默认：8080）
    -H, --host <host>     主机名（默认：localhost）
    --prod                生产模式（禁用热重载）
    --no-watch            禁用文件监听
    -o, --open            启动后自动打开浏览器
    -h, --help            显示帮助信息

示例:
    # 启动开发服务器
    node scripts/start_frontend.js

    # 指定端口
    node scripts/start_frontend.js --port 3000

    # 生产模式
    node scripts/start_frontend.js --prod

    # 使用 npm
    npm run dev
`);
}

/**
 * 创建 HTTP 服务器
 */
function createServer(config) {
    const server = http.createServer((req, res) => {
        // 解析 URL
        let urlPath = req.url === '/' ? '/index.html' : req.url;
        
        // 移除查询参数
        urlPath = urlPath.split('?')[0];

        // 构建文件路径
        const filePath = path.join(FRONTEND_DIR, urlPath);

        // 安全检查：防止目录遍历攻击
        const normalizedPath = path.normalize(filePath);
        if (!normalizedPath.startsWith(FRONTEND_DIR)) {
            res.writeHead(403);
            res.end('禁止访问');
            return;
        }

        // 获取文件扩展名
        const ext = path.extname(filePath).toLowerCase();
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';

        // 读取文件
        fs.readFile(filePath, (err, content) => {
            if (err) {
                if (err.code === 'ENOENT') {
                    res.writeHead(404);
                    res.end('文件不存在：' + urlPath);
                } else {
                    res.writeHead(500);
                    res.end('服务器错误：' + err.code);
                }
            } else {
                // 添加 CORS 头（用于前后端分离开发）
                res.setHeader('Access-Control-Allow-Origin', '*');
                res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
                res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
                
                // 禁用缓存（开发模式）
                if (!config.prod) {
                    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
                    res.setHeader('Pragma', 'no-cache');
                    res.setHeader('Expires', '0');
                }

                res.writeHead(200, { 'Content-Type': contentType });
                res.end(content);
            }
        });
    });

    return server;
}

/**
 * 监听文件变化
 */
function watchFiles(config) {
    const chokidar = require('chokidar');
    
    const watcher = chokidar.watch(FRONTEND_DIR, {
        ignored: /node_modules/,
        persistent: true,
        ignoreInitial: true
    });

    watcher.on('change', (filePath) => {
        const relativePath = path.relative(FRONTEND_DIR, filePath);
        console.log(`📝 文件变化：${relativePath}`);
    });

    watcher.on('add', (filePath) => {
        const relativePath = path.relative(FRONTEND_DIR, filePath);
        console.log(`📄 新增文件：${relativePath}`);
    });

    watcher.on('unlink', (filePath) => {
        const relativePath = path.relative(FRONTEND_DIR, filePath);
        console.log(`🗑️  删除文件：${relativePath}`);
    });

    return watcher;
}

/**
 * 打开浏览器
 */
function openBrowser(url) {
    const platform = process.platform;
    let command;

    if (platform === 'win32') {
        command = spawn('cmd', ['/c', 'start', url]);
    } else if (platform === 'darwin') {
        command = spawn('open', [url]);
    } else {
        command = spawn('xdg-open', [url]);
    }

    command.on('error', (err) => {
        console.warn('⚠️ 无法自动打开浏览器:', err.message);
    });
}

/**
 * 启动服务器
 */
function startServer(config) {
    const server = createServer(config);
    const url = `http://${config.host}:${config.port}`;

    server.listen(config.port, config.host, () => {
        console.log('\n' + '='.repeat(60));
        console.log('🚀 拉曼光谱边缘客户端 - 前端开发服务器');
        console.log('='.repeat(60));
        console.log(`\n📍 访问地址：${url}`);
        console.log(`📂 前端目录：${FRONTEND_DIR}`);
        console.log(`🔧 运行模式：${config.prod ? '生产' : '开发'}`);
        console.log(`👀 文件监听：${config.watch ? '启用' : '禁用'}`);
        console.log('\n按 Ctrl+C 停止服务器\n');

        // 自动打开浏览器
        if (config.open) {
            openBrowser(url);
        }
    });

    // 监听文件变化
    let watcher;
    if (config.watch) {
        try {
            watcher = watchFiles(config);
        } catch (err) {
            console.warn('⚠️ 文件监听不可用:', err.message);
            console.warn('   请安装 chokidar: npm install chokidar');
        }
    }

    // 优雅关闭
    process.on('SIGINT', () => {
        console.log('\n👋 正在关闭服务器...');
        
        if (watcher) {
            watcher.close();
        }

        server.close(() => {
            console.log('✅ 服务器已关闭');
            process.exit(0);
        });
    });

    // 错误处理
    server.on('error', (err) => {
        if (err.code === 'EADDRINUSE') {
            console.error(`❌ 端口 ${config.port} 已被占用`);
            console.error('   请尝试其他端口：node scripts/start_frontend.js --port 3000');
        } else {
            console.error('❌ 服务器错误:', err);
        }
        process.exit(1);
    });
}

/**
 * 检查依赖
 */
function checkDependencies() {
    try {
        require.resolve('chokidar');
        console.log('✅ chokidar 已安装（文件监听可用）');
    } catch (err) {
        console.log('⚠️ chokidar 未安装（文件监听不可用）');
        console.log('   请运行：npm install chokidar');
    }
}

/**
 * 主函数
 */
function main() {
    const config = parseArgs();

    console.log('\n🔬 拉曼光谱边缘客户端 - 前端开发工具');
    console.log('-'.repeat(60));

    // 检查依赖
    checkDependencies();

    // 检查前端目录
    if (!fs.existsSync(FRONTEND_DIR)) {
        console.error(`❌ 前端目录不存在：${FRONTEND_DIR}`);
        process.exit(1);
    }

    // 检查 index.html
    const indexHtml = path.join(FRONTEND_DIR, 'index.html');
    if (!fs.existsSync(indexHtml)) {
        console.error(`❌ index.html 不存在：${indexHtml}`);
        process.exit(1);
    }

    // 启动服务器
    startServer(config);
}

// 运行主函数
main();
