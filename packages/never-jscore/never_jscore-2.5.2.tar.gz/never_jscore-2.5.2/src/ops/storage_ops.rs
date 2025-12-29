use deno_core::{OpState, extension, op2};
use std::rc::Rc;

use crate::storage::{ResultStorage, save_hook_data};

/// Op: 存储 JavaScript 执行结果
///
/// 这个 op 允许 JavaScript 代码将执行结果存储到 Rust 端。
/// 使用 #[op2(fast)] 优化性能。
#[op2(fast)]
pub fn op_store_result(state: &mut OpState, #[string] value: String) {
    if let Some(storage) = state.try_borrow_mut::<Rc<ResultStorage>>() {
        storage.store(value);
    }
}

/// Op: 提前返回（用于Hook拦截）- 旧版本，使用 throw error 方式
///
/// 用于在JS执行过程中提前返回结果并终止执行。
/// 这在逆向工程中非常有用，例如Hook XMLHttpRequest.send拦截参数。
///
/// 实现方式：存储值到 ResultStorage 并标记为早期返回，
/// JavaScript 端需要抛出错误来中断执行
#[op2(fast)]
pub fn op_early_return(state: &mut OpState, #[string] value: String) {
    if let Some(storage) = state.try_borrow_mut::<Rc<ResultStorage>>() {
        storage.store(value.clone());
        storage.mark_early_return();
    }
}

/// Op: 保存 Hook 数据到全局存储（新版本，配合 terminate_execution 使用）
///
/// 在调用 op_terminate_execution 前保存数据。
/// 数据保存到全局静态变量，即使 isolate 被终止也能访问。
#[op2]
#[string]
pub fn op_save_hook_data(#[string] data: String) -> String {
    save_hook_data(data.clone());
    data
}

/// Op: 终止 JavaScript 执行
///
/// 调用 V8 的 terminate_execution()，无法被 try-catch 捕获。
/// 必须配合 op_save_hook_data 使用，先保存数据再终止。
///
/// ⚠️ 注意：此 op 需要访问 V8 IsolateHandle，
/// 在 Context 初始化时需要获取并存储 handle。
#[op2(fast)]
pub fn op_terminate_execution(state: &mut OpState) {
    // 从 OpState 中获取 IsolateHandle
    if let Some(handle) = state.try_borrow_mut::<deno_core::v8::IsolateHandle>() {
        handle.terminate_execution();
    }
}

// 扩展
// 注册自定义 ops 到 Deno Core runtime。
// storage 通过 options 传入，并在 state 初始化时设置。
extension!(
    pyexecjs_ext,
    ops = [
        op_store_result,
        op_early_return,
        op_save_hook_data,
        op_terminate_execution
    ],
    options = {
        storage: Rc<ResultStorage>,
    },
    state = |state, options| {
        state.put(options.storage);
    }
);
