use std::cell::RefCell;
use std::sync::{Arc, Mutex};
use once_cell::sync::Lazy;

/// 全局 Hook 数据存储
///
/// 在调用 terminate_execution() 前保存 Hook 拦截的数据。
/// 使用全局静态变量确保数据在 V8 isolate 终止后仍然可访问。
static HOOK_DATA: Lazy<Arc<Mutex<Option<String>>>> = Lazy::new(|| Arc::new(Mutex::new(None)));

/// JavaScript 执行结果存储
///
/// 用于在 Rust 和 JavaScript 之间传递执行结果。
/// 通过 Deno Core 的 op 机制，JavaScript 可以将结果存储到这里。
pub struct ResultStorage {
    pub value: RefCell<Option<String>>,
    early_return: RefCell<bool>,  // 标记是否是提前返回（用于Hook拦截）
    terminated: RefCell<bool>,    // 标记是否应该终止runtime
}

impl ResultStorage {
    pub fn new() -> Self {
        Self {
            value: RefCell::new(None),
            early_return: RefCell::new(false),
            terminated: RefCell::new(false),
        }
    }

    pub fn clear(&self) {
        *self.value.borrow_mut() = None;
        *self.early_return.borrow_mut() = false;
        *self.terminated.borrow_mut() = false;
    }

    pub fn store(&self, value: String) {
        *self.value.borrow_mut() = Some(value);
    }

    pub fn take(&self) -> Option<String> {
        self.value.borrow_mut().take()
    }

    /// 标记为提前返回（Hook拦截）
    pub fn mark_early_return(&self) {
        *self.early_return.borrow_mut() = true;
    }

    /// 检查是否是提前返回
    pub fn is_early_return(&self) -> bool {
        *self.early_return.borrow()
    }

    /// 标记为已终止（强制停止runtime）
    pub fn mark_terminated(&self) {
        *self.terminated.borrow_mut() = true;
    }

    /// 检查是否应该终止
    pub fn is_terminated(&self) -> bool {
        *self.terminated.borrow()
    }
}

impl Default for ResultStorage {
    fn default() -> Self {
        Self::new()
    }
}

/// 保存 Hook 拦截的数据到全局存储
///
/// 这个函数在 JS 调用 __saveAndTerminate__() 时被调用，
/// 数据会保存到全局变量中，即使 V8 isolate 被终止也能访问。
pub fn save_hook_data(data: String) {
    let mut guard = HOOK_DATA.lock().unwrap();
    *guard = Some(data);
}

/// 获取保存的 Hook 数据
///
/// 从全局存储中读取之前保存的 Hook 数据。
/// 通常在 JS 被 terminate_execution() 终止后调用。
pub fn get_hook_data() -> Option<String> {
    let guard = HOOK_DATA.lock().unwrap();
    guard.clone()
}

/// 清空保存的 Hook 数据
///
/// 在开始新的 JS 执行前调用，避免读取到旧数据。
pub fn clear_hook_data() {
    let mut guard = HOOK_DATA.lock().unwrap();
    *guard = None;
}
