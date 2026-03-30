/**
 * 全局测试设置（在测试环境启动前运行）
 */
export default function globalSetup() {
  // 设置测试环境变量
  process.env.NODE_ENV = 'test';
  
  // 静默 console.log（可选）
  // global.console = {
  //   ...console,
  //   log: () => {},
  //   debug: () => {},
  //   info: () => {}
  // };
}
